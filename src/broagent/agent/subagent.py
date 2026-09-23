"""Специализированный саб-агент: отвечает на один конкретный вопрос о
текущем состоянии страницы, вместо того чтобы основной агент сам разгребал
сырой список элементов. Это и есть требуемый заданием паттерн 'sub-agent
architecture' — а заодно способ не раздувать контекст основного цикла
(вместо list_elements на 2-4 тысячи символов агент получает 1-2 предложения).

На Anthropic саб-агент реально видит скриншот страницы (vision) — именно
так референсное решение ловит вещи вроде «форма не отправилась, не хватает
даты вылета». На Groq (текстовые модели без vision) используется fallback
на видимый текст страницы — хуже, чем скриншот, но лучше, чем ничего."""

import base64

from .. import config
from ..page_control.collector import read_text, read_dialog_text
from .llm_client import ask_model

SUBAGENT_SYSTEM = (
    "Ты — вспомогательный агент. Смотришь на текущее состояние веб-страницы "
    "(скриншот и/или текст) и отвечаешь на один конкретный вопрос коротко "
    "и по существу (1-3 предложения), без вступлений. Если на странице есть "
    "сообщение об ошибке, предупреждение, незаполненное обязательное поле "
    "или форма явно не была принята — обязательно скажи об этом, даже если "
    "вопрос был не об этом напрямую."
)


def ask_page(page, question: str) -> str:
    screenshot_b64 = None
    if config.PROVIDER == "anthropic":
        try:
            screenshot_b64 = base64.b64encode(page.screenshot(type="png")).decode()
        except Exception:
            screenshot_b64 = None

    dialog_text = read_dialog_text(page)
    page_text = read_text(page)

    context_parts = []
    if dialog_text:
        context_parts.append(f"Открыто модальное окно/диалог, вот его содержимое:\n{dialog_text}")
    context_parts.append(f"Общий текст страницы (может быть неполным, если страница длинная):\n{page_text[:1800]}")
    text_context = "\n\n".join(context_parts)

    if screenshot_b64:
        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": screenshot_b64},
            },
            {"type": "text", "text": f"Вопрос: {question}\n\n{text_context}"},
        ]
    else:
        content = [{"type": "text", "text": f"Вопрос: {question}\n\n{text_context}"}]

    messages = [{"role": "user", "content": content}]

    try:
        response = ask_model(SUBAGENT_SYSTEM, messages, tools=[])
    except Exception as e:
        return f"саб-агент недоступен: {e}"

    texts = [b["text"] for b in response["content"] if b.get("type") == "text"]
    return "\n".join(texts).strip() or "(саб-агент не дал ответа)"