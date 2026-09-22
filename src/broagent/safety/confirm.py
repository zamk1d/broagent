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
    answer = input(
        f"\n⚠️  Агент хочет выполнить '{action_name}' по элементу "
        f"с текстом '{element_text}'. Разрешить? (y/n): "
    )
    return answer.strip().lower() == "y"
