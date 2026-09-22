from playwright.sync_api import sync_playwright


class BrowserSession:
    def __init__(self, profile_dir: str = "./profile"):
        self.profile_dir = profile_dir
        self._playwright = None
        self._context = None
        self.page = None

    def start(self):
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            self.profile_dir,
            headless=False,
            args=["--start-maximized"],
            no_viewport=True
        )
        self.page = self._context.new_page()
        return self.page

    def stop(self):
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
