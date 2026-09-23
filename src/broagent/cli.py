import sys

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from . import config
from . import logging_utils as log
from .browser.session import BrowserSession
from .agent.loop import run_agent


def _check_config():
    if config.PROVIDER not in ("anthropic", "groq"):
        log.error(f"Неизвестный BROAGENT_PROVIDER={config.PROVIDER!r}, допустимо: anthropic | groq")
        sys.exit(1)
    if config.PROVIDER == "anthropic" and not config.ANTHROPIC_API_KEY:
        log.error("BROAGENT_PROVIDER=anthropic, но ANTHROPIC_API_KEY не задан. Впиши ключ в .env.")
        sys.exit(1)
    if config.PROVIDER == "groq" and not config.GROQ_API_KEY:
        log.error("BROAGENT_PROVIDER=groq, но GROQ_API_KEY не задан. Впиши ключ в .env.")
        sys.exit(1)


def main():
    _check_config()
    log.banner()
    log.info(f"Провайдер: {config.PROVIDER} · модель: {config.active_model_name()} · профиль браузера: {config.PROFILE_DIR}")
    log.info("Открываю браузер…")

    history: list = []

    with BrowserSession(config.PROFILE_DIR, config.START_URL) as session:
        log.info("Браузер открыт. Наберите /help для списка команд.\n")

        while True:
            try:
                task = input("\033[1m› \033[0m").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not task:
                continue

            if task in ("/exit", "/quit"):
                break
            if task == "/help":
                log.help_panel()
                continue
            if task == "/url":
                page = session.page
                log.info(page.url if page else "(нет активной вкладки)")
                continue
            if task == "/new":
                history = []
                log.info("История задач сброшена, следующая задача начнётся с чистого листа.")
                continue

            log.user_task(task)
            summary, history = run_agent(session, task, history)
            log.final_summary(summary or "")

    log.info("Пока!")


if __name__ == "__main__":
    main()