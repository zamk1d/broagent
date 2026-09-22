from broagent.browser.session import BrowserSession
from broagent.agent.loop import run_agent


def main():
    task = input("Какую задачу дать агенту? ")

    with BrowserSession() as page:
        page.goto("https://hh.ru/")  # стартовая страница, при желании поменяйте
        run_agent(page, task)
        input("\nEnter, чтобы закрыть браузер...")


if __name__ == "__main__":
    main()
