from broagent.page_control.collector import collect_elements, collect_regions
from broagent.page_control.actions import click, type_text, goto, current_url
from broagent.safety.confirm import is_dangerous, ask_user_confirmation
from broagent import logging_utils as log


class ToolDispatcher:
    def __init__(self, page):
        self.page = page
        self._last_elements: list[dict] = []

    def run(self, name: str, args: dict) -> str:

        if name == "list_regions":
            return str(collect_regions(self.page))

        if name == "list_elements":
            region_id = args.get("region_id", None)
            elements = collect_elements(self.page, region_id=region_id)

            query = (args.get("query") or "").lower()
            if query:
                elements = [el for el in elements if query in el["text"].lower()]

            self._last_elements = elements

            limit = int(args.get("limit") or 20)
            offset = int(args.get("offset") or 0)
            page_slice = elements[offset:offset + limit]

            return str({
                "total": len(elements),
                "offset": offset,
                "limit": limit,
                "items": page_slice,
            })

        if name == "click":
            element_id = args["element_id"]
            element_text = self._find_text(element_id)

            if is_dangerous("click", element_text):
                if not ask_user_confirmation("click", element_text):
                    return "Пользователь отклонил это действие. Выбери другой путь."

            result = click(self.page, element_id)
            self._last_elements = []      # DOM мог поменяться
            return result

        if name == "type_text":
            result = type_text(self.page, args["element_id"], args["text"])
            self._last_elements = []      # могли появиться подсказки/фильтры
            return result

        if name == "goto":
            result = goto(self.page, args["url"])
            self._last_elements = []
            return result

        if name == "ask_user":
            answer = input(f"\n❓ {args['question']}\n> ")
            return f"Ответ пользователя: {answer}"

        if name == "current_url":
            url = current_url(self.page)
            return url

        return f"Неизвестный инструмент: {name}"

    def _find_text(self, element_id: int) -> str:
        for el in self._last_elements:
            if el["id"] == element_id:
                return el["text"]
        return ""