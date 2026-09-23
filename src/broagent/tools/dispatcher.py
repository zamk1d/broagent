from ..page_control.collector import collect_elements, collect_regions, read_text
from ..page_control import actions as act
from ..safety.confirm import is_dangerous, ask_user_confirmation
from ..agent.subagent import ask_page
from .. import logging_utils as log


class ToolDispatcher:

    def __init__(self, session):
        self.session = session
        self._last_elements: list[dict] = []

    def run(self, name: str, args: dict) -> str:
        page = self.session.page
        if page is None:
            return "Активная вкладка недоступна (возможно, была закрыта)."

        if name == "list_regions":
            return str(collect_regions(page))

        if name == "list_elements":
            region_id = args.get("region_id")
            elements = collect_elements(page, region_id=region_id)

            query = (args.get("query") or "").lower()
            if query:
                elements = [el for el in elements if query in el["text"].lower()]

            self._last_elements = elements

            limit = int(args.get("limit") or 40)
            offset = int(args.get("offset") or 0)
            page_slice = elements[offset:offset + limit]

            return str({
                "total": len(elements),
                "offset": offset,
                "limit": limit,
                "items": page_slice,
            })

        if name == "read_text":
            return read_text(page, region_id=args.get("region_id"))

        if name == "ask_page":
            return ask_page(page, args["question"])

        if name == "click":
            element_id = args["element_id"]
            element_text = self._find_text(element_id)

            if is_dangerous("click", element_text):
                if not ask_user_confirmation("click", element_text):
                    return "Пользователь отклонил это действие. Выбери другой путь и сообщи об этом в finish."

            result = act.click(page, element_id)
            self._last_elements = []
            return result

        if name == "type_text":
            element_text = self._find_text(args["element_id"])
            if is_dangerous("type_text", element_text):
                if not ask_user_confirmation("type_text", element_text):
                    return "Пользователь отклонил это действие."
            result = act.type_text(page, args["element_id"], args["text"], submit=bool(args.get("submit", False)))
            self._last_elements = []
            return result

        if name == "select_option":
            result = act.select_option(page, args["element_id"], args["value"])
            self._last_elements = []
            return result

        if name == "goto":
            result = act.goto(page, args["url"])
            self._last_elements = []
            return result

        if name == "go_back":
            result = act.go_back(page)
            self._last_elements = []
            return result

        if name == "scroll_page":
            return act.scroll_page(page, args.get("direction", "down"), int(args.get("amount") or 1200))

        if name == "wait":
            return act.wait_seconds(page, args.get("seconds", 1))

        if name == "current_url":
            return act.current_url(page)

        if name == "ask_user":
            answer = input(f"\n❓ {args['question']}\n> ")
            return f"Ответ пользователя: {answer}"

        return f"Неизвестный инструмент: {name}"

    def _find_text(self, element_id: int) -> str:
        for el in self._last_elements:
            if el["id"] == element_id:
                return el["text"]
        return ""