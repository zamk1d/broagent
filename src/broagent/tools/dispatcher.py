from broagent.page_control.collector import collect_elements, collect_regions
from broagent.page_control.actions import click, type_text, goto
from broagent.safety.confirm import is_dangerous, ask_user_confirmation


class ToolDispatcher:
    def __init__(self, page):
        self.page = page
        self._last_elements: list[dict] = []

    def run(self, name: str, args: dict) -> str:

        if name == "list_regions":
            return str(collect_regions(self.page))

        if name == "list_elements":
            region_id = args.get("region_id", None)
            self._last_elements = collect_elements(self.page, region_id=region_id)
            print(len(self._last_elements))
            print(str(self._last_elements))
            return str(self._last_elements)

        if name == "click":
            element_id = args["element_id"]
            element_text = self._find_text(element_id)

            if is_dangerous("click", element_text):
                if not ask_user_confirmation("click", element_text):
                    return "Пользователь отклонил это действие. Выбери другой путь."

            return click(self.page, element_id)

        if name == "type_text":
            return type_text(self.page, args["element_id"], args["text"])

        if name == "goto":
            return goto(self.page, args["url"])

        return f"Неизвестный инструмент: {name}"

    def _find_text(self, element_id: int) -> str:
        for el in self._last_elements:
            if el["id"] == element_id:
                return el["text"]
        return ""
