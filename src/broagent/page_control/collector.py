import time
from playwright.sync_api import Page

_COLLECT_JS = """
(args) => {
    const { region_id } = args;

    document.querySelectorAll('[data-agent-id]').forEach(
        (el) => el.removeAttribute('data-agent-id')
    );

    const root = region_id === null
        ? document
        : document.querySelector(`[data-agent-region="${region_id}"]`);

    if (!root) return [];

    const nodes = root.querySelectorAll('a, button, input, textarea, select, [role="button"], [contenteditable="true"]');
    const result = [];
    let counter = 0;
    nodes.forEach((el) => {
        const r = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        const visible = r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
        if (!visible) return;

        // Если поверх элемента лежит что-то другое (например, открытое
        // модальное окно) — реальный пользователь не смог бы по нему
        // кликнуть, значит и агенту предлагать его не нужно. Проверяем
        // только если элемент сейчас в пределах вьюпорта.
        const cx = r.left + r.width / 2;
        const cy = r.top + r.height / 2;
        const inViewport = cx >= 0 && cy >= 0 && cx <= window.innerWidth && cy <= window.innerHeight;
        if (inViewport) {
            const topEl = document.elementFromPoint(cx, cy);
            if (topEl && topEl !== el && !el.contains(topEl) && !topEl.contains(el)) {
                return;
            }
        }

        const id = counter++;
        el.setAttribute('data-agent-id', id);

        const text = el.innerText ? el.innerText.trim().slice(0, 140) : '';
        const label = el.getAttribute('aria-label')
            || el.getAttribute('placeholder')
            || el.getAttribute('title')
            || el.getAttribute('name')
            || '';

        result.push({
            id: id,
            tag: el.tagName.toLowerCase(),
            type: el.tagName.toLowerCase() === 'select' ? 'select' : (el.getAttribute('type') || ''),
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
        const r = el.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return;

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

_READ_TEXT_JS = """
(args) => {
    const { region_id } = args;
    const root = region_id === null
        ? document.body
        : document.querySelector(`[data-agent-region="${region_id}"]`);
    if (!root) return '';
    return root.innerText || '';
}
"""


def _settle(page: Page):
    """Даём SPA дорендериться. goto/click возвращаются часто раньше, чем
    JS успевает построить DOM — без этого list_elements/list_regions
    регулярно ловят пустую страницу сразу после навигации."""
    try:
        page.wait_for_load_state("domcontentloaded", timeout=6000)
    except Exception:
        pass


def collect_elements(page: Page, region_id: int | None = None) -> list[dict]:
    _settle(page)
    result = page.evaluate(_COLLECT_JS, {"region_id": region_id})
    if not result:
        time.sleep(0.9)
        result = page.evaluate(_COLLECT_JS, {"region_id": region_id})
    return result


def collect_regions(page: Page) -> list[dict]:
    _settle(page)
    result = page.evaluate(_PAGE_BLOCKS)
    if not result:
        time.sleep(0.9)
        result = page.evaluate(_PAGE_BLOCKS)
    return result


_ALERTS_JS = """
() => {
    // Общие ARIA-паттерны валидации/уведомлений (не селекторы конкретного
    // сайта, а веб-стандарт доступности) — так агент видит "укажите дату
    // вылета" и подобные сообщения, а не только результат самого клика.
    const nodes = document.querySelectorAll(
        '[role="alert"], [aria-live="assertive"], [aria-live="polite"], [aria-invalid="true"]'
    );
    const texts = [];
    nodes.forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return;
        const t = (el.innerText || el.getAttribute('aria-label') || '').trim();
        if (t) texts.push(t.slice(0, 200));
    });
    return [...new Set(texts)];
}
"""


_DIALOG_JS = """
() => {
    const dialogs = document.querySelectorAll('[role="dialog"], [aria-modal="true"], dialog');
    let best = null;
    let bestArea = 0;
    dialogs.forEach((el) => {
        const r = el.getBoundingClientRect();
        const area = r.width * r.height;
        if (area > 0 && area > bestArea) { bestArea = area; best = el; }
    });
    if (!best) return null;
    return (best.innerText || '').trim().slice(0, 2000);
}
"""


def read_dialog_text(page: Page) -> str | None:
    try:
        return page.evaluate(_DIALOG_JS)
    except Exception:
        return None


def read_alerts(page: Page) -> list[str]:
    try:
        return page.evaluate(_ALERTS_JS)
    except Exception:
        return []


def read_text(page: Page, region_id: int | None = None) -> str:
    _settle(page)
    text = page.evaluate(_READ_TEXT_JS, {"region_id": region_id})
    text = (text or "").strip()
    if len(text) > 4000:
        text = text[:4000] + "\n… [обрезано]"
    return text