from playwright.sync_api import sync_playwright, Page

from .. import logging_utils as log


class BrowserSession:
    """Держит persistent-контекст Chromium и следит за тем, какая вкладка
    сейчас активна — это критично, потому что клик может открыть новую
    вкладку/попап, и агент должен продолжить работу именно в ней, а не
    в оставленной позади старой странице."""

    def __init__(self, profile_dir: str = "./profile", start_url: str = "about:blank"):
        self.profile_dir = profile_dir
        self.start_url = start_url
        self._playwright = None
        self._context = None
        self._pages: list[Page] = []
        self._active: Page | None = None

    @property
    def page(self) -> Page:
        """Текущая активная вкладка. Инструменты должны брать page именно
        через это свойство на каждый вызов, а не кэшировать ссылку —
        активная вкладка может смениться в любой момент."""
        return self._active

    def start(self) -> "BrowserSession":
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            self.profile_dir,
            headless=False,
            args=["--start-maximized"],
            no_viewport=True,
        )
        self._context.on("page", self._on_new_page)

        first_page = self._context.new_page()
        self._register(first_page)
        self._active = first_page
        try:
            first_page.goto(self.start_url, wait_until="domcontentloaded", timeout=15000)
        except Exception:
            pass
        return self

    def stop(self):
        try:
            if self._context:
                self._context.close()
        finally:
            if self._playwright:
                self._playwright.stop()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def _register(self, page: Page):
        self._pages.append(page)
        page.on("dialog", self._on_dialog)
        page.on("close", lambda: self._on_page_closed(page))

    def _on_new_page(self, page: Page):
        self._register(page)
        self._active = page
        try:
            page.wait_for_load_state("domcontentloaded", timeout=8000)
        except Exception:
            pass
        log.info(f"  ⓘ открылась новая вкладка: {page.url}")

    def _on_page_closed(self, page: Page):
        if page in self._pages:
            self._pages.remove(page)
        if self._active is page:
            self._active = self._pages[-1] if self._pages else None

    def _on_dialog(self, dialog):
        message = (dialog.message or "").strip()
        if dialog.type == "beforeunload":
            dialog.accept()
            log.dialog_seen(dialog.type, message, "accept (навигация)")
        else:
            dialog.dismiss()
            log.dialog_seen(dialog.type, message, "dismiss")
