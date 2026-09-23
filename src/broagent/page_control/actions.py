from playwright.sync_api import Page

from .collector import read_alerts


def _settle(page: Page):
    try:
        page.wait_for_load_state("domcontentloaded", timeout=6000)
    except Exception:
        pass


def _locate(page: Page, element_id: int):
    return page.locator(f'[data-agent-id="{element_id}"]')


def _with_alerts(page: Page, base_result: str) -> str:
    alerts = read_alerts(page)
    if alerts:
        base_result += "\n⚠ страница показывает: " + " | ".join(alerts[:3])
    return base_result


def click(page: Page, element_id: int) -> str:
    loc = _locate(page, element_id)
    count = loc.count()
    if count == 0:
        return f"элемент {element_id} не найден (страница, вероятно, изменилась — вызови list_elements заново)"
    target = loc.first if count > 1 else loc
    try:
        target.click(timeout=5000)
    except Exception as e:
        return f"клик по элементу {element_id} не удался: {e}"
    _settle(page)
    suffix = f" (найдено {count} совпадений, кликнул первое)" if count > 1 else ""
    result = f"clicked element {element_id}{suffix}, текущий адрес: {page.url}"
    return _with_alerts(page, result)


def type_text(page: Page, element_id: int, text: str, submit: bool = False) -> str:
    loc = _locate(page, element_id)
    count = loc.count()
    if count == 0:
        return f"элемент {element_id} не найден"
    target = loc.first if count > 1 else loc
    try:
        target.fill(text, timeout=5000)
        if submit:
            target.press("Enter")
            _settle(page)
    except Exception as e:
        return f"не удалось ввести текст в {element_id}: {e}"
    suffix = f" (найдено {count} совпадений, взял первое)" if count > 1 else ""
    result = f"typed into element {element_id}{suffix}" + (", нажал Enter" if submit else "")
    return _with_alerts(page, result) if submit else result


def select_option(page: Page, element_id: int, value: str) -> str:
    loc = _locate(page, element_id)
    if loc.count() == 0:
        return f"элемент {element_id} не найден"
    try:
        loc.select_option(label=value, timeout=5000)
        return f"в select {element_id} выбрано по подписи: {value}"
    except Exception:
        pass
    try:
        loc.select_option(value=value, timeout=5000)
        return f"в select {element_id} выбрано по значению: {value}"
    except Exception as e:
        return f"не удалось выбрать '{value}' в select {element_id}: {e}"


def goto(page: Page, url: str) -> str:
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception as e:
        return f"не удалось перейти на {url}: {e}"
    _settle(page)
    return f"navigated to {page.url}"


def go_back(page: Page) -> str:
    try:
        page.go_back(wait_until="domcontentloaded", timeout=10000)
    except Exception as e:
        return f"не удалось вернуться назад: {e}"
    _settle(page)
    return f"вернулся назад, текущий адрес: {page.url}"


def scroll_page(page: Page, direction: str = "down", amount: int = 1200) -> str:
    delta = amount if direction == "down" else -amount
    page.mouse.wheel(0, delta)
    page.wait_for_timeout(300)
    return f"проскроллил {direction} на {amount}px"


def wait_seconds(page: Page, seconds: float) -> str:
    seconds = max(0.0, min(float(seconds), 5.0))
    page.wait_for_timeout(int(seconds * 1000))
    return f"подождал {seconds} c"


def current_url(page: Page) -> str:
    return page.url