def click(page, element_id: int) -> str:
    page.locator(f'[data-agent-id="{element_id}"]').click()
    return f"clicked element {element_id}"


def type_text(page, element_id: int, text: str) -> str:
    page.locator(f'[data-agent-id="{element_id}"]').fill(text)
    return f"typed into element {element_id}"


def goto(page, url: str) -> str:
    page.goto(url)
    return f"navigated to {url}"
