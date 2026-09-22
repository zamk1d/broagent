from broagent.browser.session import BrowserSession
from broagent.agent.loop import run_agent
from broagent import logging_utils as log


def main():
    log.banner("Broagent")
    task = input("Какую задачу дать агенту? ")

    with BrowserSession() as page:
        run_agent(page, task)
        input("\nEnter, чтобы закрыть браузер...")


if __name__ == "__main__":
    main()