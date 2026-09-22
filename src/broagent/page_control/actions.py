from playwright.sync_api import Page


def click(page, element_id: int) -> str:
    loc = page.locator(f'[data-agent-id="{element_id}"]')
    count = loc.count()
    if count == 0:
        return f"элемент {element_id} не найден (страница, вероятно, изменилась)"
    if count > 1:
        # такого быть не должно после фикса collector.py, но пусть не падает
        loc.first.click()
        return f"клик по элементу {element_id} (найдено {count} совпадений, кликнул первое)"
    loc.click()
    return f"clicked element {element_id}"


def type_text(page, element_id: int, text: str) -> str:
    loc = page.locator(f'[data-agent-id="{element_id}"]')
    count = loc.count()
    if count == 0:
        return f"элемент {element_id} не найден"
    if count > 1:
        loc.first.fill(text)
        return f"ввёл текст в {element_id} (найдено {count} совпадений, взял первое)"
    loc.fill(text)
    return f"typed into element {element_id}"


def goto(page, url: str) -> str:
    page.goto(url)
    return f"navigated to {url}"

def current_url(page) -> str:
    return page.url