import time

from .. import config
from .. import logging_utils as log
from ..tools.schemas import TOOLS
from ..tools.dispatcher import ToolDispatcher
from .llm_client import ask_model

MAX_TOOL_RESULT_HISTORY = 4
TRUNCATE_AT = 700

SYSTEM_PROMPT = (
    "Ты — браузерный ассистент. Твоя задача — выполнять поручения пользователя, "
    "управляя реальным браузером через инструменты. Ты универсален: работаешь "
    "с любым сайтом, любой страницей, любой задачей. Не предполагай заранее, "
    "как устроен сайт, какие у него адреса страниц или тексты кнопок — смотри "
    "на то, что реально отображается, через list_regions/list_elements/read_text.\n"
    "\n"
    "ОБЩИЙ ПОРЯДОК РАБОТЫ:\n"
    "1. Пойми, что именно просит пользователь.\n"
    "2. Если пользователь не указал URL и задача похожа на поиск — начни "
    "с известного релевантного сайта или поисковика. Если совсем не знаешь, "
    "с чего начать — спроси через ask_user, не выдумывай URL наугад.\n"
    "3. После goto/click страница могла ещё не дорендериться — если "
    "list_elements или list_regions вернули пусто, попробуй тот же вызов ещё "
    "раз перед тем как менять стратегию: часто это просто SPA, которой нужно "
    "чуть больше времени, а не то, что сайт пустой.\n"
    "4. На больших страницах сначала list_regions, потом list_elements с "
    "region_id нужного блока. Если задача — «прочитай/найди информацию», "
    "используй read_text вместо перебора кнопок.\n"
    "5. Действуй по одному шагу и проверяй результат. id элементов валидны "
    "только для текущего состояния DOM — после click/goto/type_text вызывай "
    "list_elements заново, прежде чем ссылаться на id.\n"
    "6. После клика по кнопкам вида «Найти», «Отправить», «Продолжить», "
    "«Купить» — НЕ считай действие успешным просто потому, что не было "
    "исключения. Результат click сам покажет предупреждение, если страница "
    "его показала; если сомневаешься, что реально произошло — спроси "
    "ask_page («форма отправилась? есть ли ошибка валидации?»), прежде чем "
    "искать обходной путь. Часто «ничего не изменилось» значит не «сайт "
    "сломан», а «не заполнено обязательное поле».\n"
    "7. Если задача — «найди / покажи список» — обычно не нужно открывать "
    "каждую ссылку, собери нужное и вызови finish. Открывать детали нужно, "
    "только если пользователь явно просит.\n"
    "8. Если сайт использует бесконечную прокрутку и нужного не видно — "
    "scroll_page, потом list_elements заново.\n"
    "9. Опасные действия (оплата, удаление, отправка заказа) потребуют "
    "подтверждения у пользователя — это происходит автоматически внутри "
    "click/type_text, просто вызывай их как обычно.\n"
    "\n"
    "ask_page — саб-агент, который смотрит на страницу целиком (скриншот "
    "и/или текст) и коротко отвечает на конкретный вопрос о её состоянии. "
    "Используй его вместо повторных list_elements, когда тебе нужен не "
    "список кнопок, а понимание, что сейчас происходит на странице.\n"
    "\n"
    "ЭКОНОМИЯ: не запрашивай данные, которые тебе не нужны, используй limit/"
    "offset/query/region_id. Не повторяй один и тот же вызов с теми же "
    "аргументами, если результат не менялся — если инструмент вернул ошибку "
    "или пустоту второй раз подряд, попробуй другой подход.\n"
    "\n"
    "ЗАВЕРШЕНИЕ: всегда завершай через finish с конкретным итогом по существу "
    "(что нашёл/сделал/какие данные получил), а не пересказом шагов."
)


def _new_history() -> list:
    return []


def _truncate_old_tool_results(messages: list):
    tool_result_positions = []
    for msg_idx, msg in enumerate(messages):
        if msg.get("role") != "user":
            continue
        for block_idx, block in enumerate(msg.get("content", [])):
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tool_result_positions.append((msg_idx, block_idx))

    if len(tool_result_positions) <= MAX_TOOL_RESULT_HISTORY:
        return

    for msg_idx, block_idx in tool_result_positions[:-MAX_TOOL_RESULT_HISTORY]:
        block = messages[msg_idx]["content"][block_idx]
        content = block.get("content", "")
        if isinstance(content, str) and len(content) > TRUNCATE_AT:
            block["content"] = content[:TRUNCATE_AT] + "… [история обрезана]"


def run_agent(session, task: str, history: list | None = None) -> tuple[str | None, list]:
    dispatcher = ToolDispatcher(session)
    messages = history if history is not None else _new_history()
    messages.append({"role": "user", "content": [{"type": "text", "text": task}]})

    empty_strikes = 0

    try:
        for step_idx in range(config.MAX_STEPS):
            step_num = step_idx + 1
            log.step_header(step_num, config.MAX_STEPS)
            _truncate_old_tool_results(messages)

            t0 = time.time()
            try:
                with log.thinking(step_num):
                    response = ask_model(SYSTEM_PROMPT, messages, TOOLS)
            except Exception as e:
                log.error(f"провайдер модели вернул ошибку: {e}")
                return None, messages
            llm_ms = int((time.time() - t0) * 1000)
            log.model_timing(llm_ms)

            messages.append({"role": "assistant", "content": response["content"]})

            text_parts = [b["text"] for b in response["content"] if b.get("type") == "text" and b.get("text", "").strip()]
            tool_uses = [b for b in response["content"] if b.get("type") == "tool_use"]

            if text_parts:
                log.assistant_text("\n".join(text_parts))

            if not tool_uses:
                if text_parts:
                    summary = "\n".join(text_parts)
                    return summary, messages
                empty_strikes += 1
                log.warn(f"модель вернула пустой ответ ({empty_strikes}/3)")
                if empty_strikes >= 3:
                    log.error("модель упорно молчит, останавливаюсь")
                    return None, messages
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": "Ты не вызвал ни одного инструмента и не написал ответ. "
                                "Либо вызови подходящий инструмент, либо вызови finish "
                                "с кратким итогом уже сделанного.",
                    }],
                })
                continue

            tool_result_blocks = []
            finished_summary = None

            for tool_use in tool_uses:
                name = tool_use["name"]
                args = tool_use.get("input") or {}
                tool_use_id = tool_use["id"]
                log.tool_call(name, args)

                if name == "finish":
                    finished_summary = args.get("summary", "")
                    tool_result_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": "задача завершена",
                    })
                    continue

                t1 = time.time()
                try:
                    result = dispatcher.run(name, args)
                except Exception as e:
                    log.tool_error(name, e)
                    result = f"Ошибка выполнения инструмента {name}: {e}"
                tool_ms = int((time.time() - t1) * 1000)
                log.tool_result(name, result, tool_ms)

                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": str(result),
                })

            messages.append({"role": "user", "content": tool_result_blocks})

            if finished_summary is not None:
                return finished_summary, messages

        log.warn(f"Достигнут лимит в {config.MAX_STEPS} шагов, останавливаюсь.")
        return None, messages

    except KeyboardInterrupt:
        log.interrupted()
        return None, messages