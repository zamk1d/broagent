from .. import logging_utils as log

DANGEROUS_WORDS = [
    "оплатить", "оплата", "купить", "удалить", "удалить аккаунт", "подтвердить заказ",
    "отправить заказ", "перевести деньги", "перевод", "отписаться", "unsubscribe",
    "delete", "remove account", "pay", "confirm order", "place order",
    "checkout", "purchase", "send money", "transfer",
]


def is_dangerous(action_name: str, element_text: str) -> bool:
    if action_name not in ("click", "type_text"):
        return False
    text = (element_text or "").lower()
    return any(word in text for word in DANGEROUS_WORDS)


def ask_user_confirmation(action_name: str, element_text: str) -> bool:
    prompt = log.confirmation_prompt(action_name, element_text)
    answer = input(prompt)
    return answer.strip().lower() in ("y", "yes", "да", "д")
