from playwright.sync_api import Page

_COLLECT_JS = """
(args) => {
    const { region_id } = args;
    
    document.querySelectorAll('[data-agent-id]').forEach(
        (el) => el.removeAttribute('data-agent-id')
    );
    
    // если region_id не передан — ищем по всей странице, как раньше;
    // если передан — сначала находим регион и ищем только внутри него
    const root = region_id === null
        ? document
        : document.querySelector(`[data-agent-region="${region_id}"]`);

    if (!root) return [];  // регион не нашёлся (например, страница уже изменилась)

    const nodes = root.querySelectorAll('a, button, input, textarea, select');
    const result = [];
    let counter = 0;
    nodes.forEach((el) => {
        const r = el.getBoundingClientRect();
        const visible = r.width > 0 && r.height > 0;
        if (!visible) return;

        const id = counter++;
        el.setAttribute('data-agent-id', id);

        const text = el.innerText ? el.innerText.trim() : '';
        const label = el.getAttribute('aria-label')
            || el.getAttribute('placeholder')
            || el.getAttribute('title')
            || el.getAttribute('name')
            || '';

        result.push({
            id: id,
            tag: el.tagName.toLowerCase(),
            text: text || label,
        });
    });
    return result;
}
"""

_PAGE_BLOCKS = """
() => {
    const landmarks = document.querySelectorAll(
        'header, nav, main, footer, aside, section, [role="navigation"], [role="main"], [role="banner"], [role="contentinfo"]'
    );
    const result = [];
    let counter = 0;
    landmarks.forEach((el) => {
        const id = counter++;
        el.setAttribute('data-agent-region', id);

        const label = el.getAttribute('aria-label')
            || el.querySelector('h1, h2')?.innerText?.trim()
            || '';

        const interactiveCount = el.querySelectorAll('a, button, input, textarea, select').length;

        result.push({
            region_id: id,
            tag: el.tagName.toLowerCase(),
            label: label,
            interactive_elements_count: interactiveCount,
        });
    });
    return result;
}
"""


def collect_elements(page: Page, region_id: int | None = None) -> list[dict]:
    return page.evaluate(_COLLECT_JS, {"region_id": region_id})


def collect_regions(page: Page) -> list[dict]:
    return page.evaluate(_PAGE_BLOCKS)