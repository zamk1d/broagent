from broagent import logging_utils as log

DANGEROUS_WORDS = [
    "оплатить", "купить", "удалить", "подтвердить заказ",
    "delete", "pay", "confirm order", "checkout", "purchase",
]


def is_dangerous(action_name: str, element_text: str) -> bool:
    if action_name != "click":
        return False
    text = (element_text or "").lower()
    return any(word in text for word in DANGEROUS_WORDS)


def ask_user_confirmation(action_name: str, element_text: str) -> bool:
    log.warn(
        f"Агент хочет выполнить '{action_name}' по элементу: «{element_text}»"
    )
    answer = input(_prompt())
    return answer.strip().lower() == "y"


def _prompt() -> str:
    # отдельная функция, чтобы цвет можно было отключить одним движением
    try:
        from broagent.logging_utils import _paint, C
        return _paint("    Разрешить? (y/n): ", C.BOLD, C.YELLOW)
    except Exception:
        return "    Разрешить? (y/n): "