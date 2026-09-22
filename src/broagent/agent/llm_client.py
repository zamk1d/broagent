import json
import os
import re

from openai import OpenAI, APIStatusError
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(
    base_url=os.getenv("GROQ_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = str(os.getenv("GROQ_MODEL"))


class ModelToolCallError(Exception):
    """Модель упорно зовёт инструмент, которого нет в списке."""
    def __init__(self, message: str, bad_name: str | None = None, failed_generation: str | None = None):
        super().__init__(message)
        self.bad_name = bad_name
        self.failed_generation = failed_generation


def _guess_bad_name(failed_generation: str, valid_names: set[str]) -> str:
    """Достаём имя несуществующего инструмента из сырого вывода модели."""
    if not failed_generation:
        return "?"
    try:
        obj = json.loads(failed_generation)
        name = obj.get("name")
        if isinstance(name, str) and name not in valid_names:
            return name
    except Exception:
        pass
    m = re.search(r'"name"\s*:\s*"([^"]+)"', failed_generation)
    if m and m.group(1) not in valid_names:
        return m.group(1)
    return "?"


def ask_model(messages: list, tools: list, max_retries: int = 2):
    """
    Делает запрос к модели. Если Groq отклоняет вызов из-за несуществующего
    имени инструмента (это бывает у gpt-oss — модель по инерции пишет
    'commentary'/'analysis'), добавляем уточнение и пробуем ещё раз.
    """
    valid_names = {t["function"]["name"] for t in tools}

    for attempt in range(max_retries + 1):
        try:
            response = _client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
            )
            return response.choices[0].message

        except APIStatusError as e:
            body = getattr(e, "body", None) or {}
            err = body.get("error", {}) if isinstance(body, dict) else {}

            if err.get("code") != "tool_use_failed":
                raise

            failed = err.get("failed_generation", "")
            bad = _guess_bad_name(failed, valid_names)

            if attempt == max_retries:
                raise ModelToolCallError(
                    f"модель упорно зовёт несуществующий инструмент '{bad}'",
                    bad_name=bad,
                    failed_generation=failed,
                ) from e

            # просим модель исправиться и пробуем снова
            messages.append({
                "role": "system",
                "content": (
                    f"Твой предыдущий вызов был отклонён: ты попытался вызвать "
                    f"инструмент '{bad}', которого не существует. "
                    f"Доступные инструменты: {sorted(valid_names)}. "
                    f"Вызывай только их. Не используй имена вроде "
                    f"'commentary', 'analysis', 'final' — это не инструменты."
                ),
            })