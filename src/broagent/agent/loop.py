import json
import time

from broagent.agent.llm_client import ask_model, ModelToolCallError
from broagent.tools.schemas import TOOLS
from broagent.tools.dispatcher import ToolDispatcher
from broagent import logging_utils as log

MAX_TOOL_HISTORY = 5          # сколько последних tool-результатов хранить целиком
TRUNCATE_AT = 1500
MAX_STEPS = 25

INSTRUCTION = (
    "Ты — браузерный ассистент. Твоя задача — выполнять поручения пользователя, "
    "управляя реальным браузером через инструменты. Ты универсален: работаешь "
    "с любым сайтом, любой страницей, любой задачей. Не предполагай заранее, "
    "как устроен сайт — смотри на то, что реально на странице.\n"
    "\n"
    "ИНСТРУМЕНТЫ:\n"
    "- goto(url) — перейти на страницу.\n"
    "- list_regions() — крупные блоки текущей страницы (header/main/footer/...).\n"
    "- list_elements(region_id, query, limit, offset) — интерактивные элементы "
    "(ссылки, кнопки, поля) с их id и текстом.\n"
    "- click(element_id) — кликнуть по элементу.\n"
    "- type_text(element_id, text) — ввести текст в поле.\n"
    "- finish(summary) — завершить задачу с кратким итогом.\n"
    "Используй ТОЛЬКО эти имена. Никаких 'commentary', 'analysis', 'final', "
    "'browse', 'search' и подобных выдуманных инструментов не существует.\n"
    "\n"
    "ОБЩИЙ ПОРЯДОК РАБОТЫ:\n"
    "1. Пойми, что именно просит пользователь: найти информацию, что-то нажать, "
    "заполнить форму, сравнить, собрать список, зайти на конкретный сайт.\n"
    "2. Реши, с какой страницы начать. Если пользователь не указал URL, "
    "а задача похожа на поиск в интернете — начни с поисковика или известного "
    "сайта по теме. Если не знаешь точно — не выдумывай URL, лучше спроси "
    "пользователя через finish.\n"
    "3. Открой страницу через goto.\n"
    "4. Осмотрись: на больших страницах сначала list_regions, потом list_elements "
    "с region_id нужного блока. На маленьких можно сразу list_elements.\n"
    "5. Действуй по одному шагу: клик, ввод, переход. После каждого действия "
    "проверяй результат.\n"
    "6. Когда задача выполнена — вызови finish с конкретным итогом "
    "(что нашёл, что сделал, что получилось).\n"
    "\n"
    "ПРАВИЛА РАБОТЫ С ЭЛЕМЕНТАМИ:\n"
    "- id элементов валидны только для текущего состояния страницы. После "
    "click/goto/type_text страница могла измениться — вызови list_elements заново, "
    "прежде чем ссылаться на id.\n"
    "- Не кликай по элементу, если не понимаешь, что он делает. Сначала читай текст.\n"
    "- Если в списке несколько похожих элементов — используй query в list_elements, "
    "чтобы отфильтровать нужные, вместо того чтобы угадывать по id.\n"
    "- Если задача — «найди / покажи список / какие есть», обычно НЕ нужно "
    "открывать каждую найденную ссылку. Собери заголовки и вызови finish. "
    "Переходить внутрь нужно только если пользователь явно просит «открой», "
    "«посмотри детали», «откликнись» и т.п.\n"
    "- Опасные действия (оплата, удаление, подтверждение заказа) требуют "
    "подтверждения пользователя — это делается автоматически, но не пытайся "
    "обходить запрос на подтверждение.\n"
    "\n"
    "ПРАВИЛА ЭКОНОМИИ И ТОЧНОСТИ:\n"
    "- Не запрашивай всю страницу целиком, если задача локальная. Используй "
    "region_id, query, limit, offset, чтобы получать только нужное.\n"
    "- Не повторяй один и тот же вызов с теми же аргументами, если результат "
    "не изменился. Если предыдущий шаг не дал результата — попробуй другой "
    "подход, а не копируй его.\n"
    "- Если инструмент вернул ошибку — прочитай её, пойми причину и попробуй "
    "иначе, а не вызывай тот же инструмент с теми же аргументами.\n"
    "- Если ты не уверен, что делать дальше — сформулируй промежуточный вывод "
    "и вызови finish с пояснением, что удалось и где застрял. Не заканчивай "
    "работу пустым сообщением.\n"
    "\n"
    "ЗАВЕРШЕНИЕ:\n"
    "- Задача считается выполненной, когда пользователь получил то, что просил, "
    "или когда дальше двигаться некуда.\n"
    "- Всегда завершай через finish с конкретным итогом, а не просто текстом.\n"
    "- В summary пиши результат по существу: что нашёл, что сделал, какие данные "
    "получил. Не пересказывай шаги, не пиши «я вызвал list_elements».\n"
)


def _trim_history(messages: list):
    """Оставляем нетронутыми последние N tool-сообщений, остальные урезаем.

    messages содержит и dict'ы (system/user/tool), и объекты ChatCompletionMessage
    (ответы модели), поэтому работаем через универсальный доступ к полям.
    """
    def role_of(m):
        if isinstance(m, dict):
            return m.get("role")
        return getattr(m, "role", None)

    tool_indices = [i for i, m in enumerate(messages) if role_of(m) == "tool"]
    if len(tool_indices) <= MAX_TOOL_HISTORY:
        return
    for i in tool_indices[:-MAX_TOOL_HISTORY]:
        if not isinstance(messages[i], dict):
            continue
        content = messages[i].get("content", "")
        if len(content) > TRUNCATE_AT:
            messages[i]["content"] = content[:TRUNCATE_AT] + "... [история обрезана]"

def run_agent(page, task: str):
    dispatcher = ToolDispatcher(page)
    messages = [
        {"role": "system", "content": INSTRUCTION},
        {"role": "user", "content": task},
    ]

    log.banner("Запуск агента")
    log.user_input(task)
    empty_strikes = 0
    for step_idx in range(MAX_STEPS):
        step_num = step_idx + 1
        log.step(step_num, MAX_STEPS)
        _trim_history(messages)
        log.llm_request(step_num, messages, len(TOOLS))

        t0 = time.time()
        try:
            message = ask_model(messages, TOOLS)
        except ModelToolCallError as e:
            log.error(f"модель зовёт несуществующий инструмент '{e.bad_name}'")
            if e.failed_generation:
                log.info(f"сырой вывод модели: {e.failed_generation}")
            return None
        except Exception as e:
            log.error(f"модель вернула ошибку: {e}")
            return None
        llm_ms = int((time.time() - t0) * 1000)
        log.info(f"модель ответила за {llm_ms} ms")

        messages.append(message)

        # Выход №1: модель ответила текстом без вызова инструментов.
        if not message.tool_calls:
            content = (message.content or "").strip()
            if not content:
                empty_strikes += 1
                log.warn(f"модель вернула пустой ответ ({empty_strikes}/3)")
                if empty_strikes >= 3:
                    log.error("модель упорно молчит, останавливаюсь")
                    return None
                messages.append({
                    "role": "system",
                    "content": (
                        "Ты не вызвал ни одного инструмента и не написал ответ. "
                        "Либо вызови подходящий инструмент, либо вызови finish "
                        "с кратким итогом уже сделанного."
                    ),
                })
                continue
            log.llm_response_text(content)
            log.final(content)
            return content

        log.llm_response_tool_calls(message.tool_calls)

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError as e:
                log.tool_error(name, f"не удалось распарсить аргументы: {e}")
                args = {}

            log.tool_call(name, args)

            # Выход №2: модель явно сообщила, что задача решена.
            if name == "finish":
                summary = args.get("summary")
                log.final(summary)
                return summary

            t1 = time.time()
            try:
                result = dispatcher.run(name, args)
            except Exception as e:
                log.tool_error(name, e)
                result = f"Ошибка выполнения инструмента {name}: {e}"
            tool_ms = int((time.time() - t1) * 1000)

            log.tool_result(name, result, tool_ms)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })

    # Выход №3: исчерпан лимит шагов.
    log.warn(f"Достигнут лимит в {MAX_STEPS} шагов, останавливаюсь.")
    return None