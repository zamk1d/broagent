import json

from broagent.agent.llm_client import ask_model
from broagent.tools.schemas import TOOLS
from broagent.tools.dispatcher import ToolDispatcher

MAX_STEPS = 25
INSTRUCTION = ("Ты - браузерный ассистент. У тебя есть инструменты для выполнения задач, среди которых"
               "есть list_regions и list_elements(region_id:int|None=None). Для экономии токенов ты можешь"
               "сначала вызвать list_regions - получить id регионов, после чего вызвать list_elements с id нужного"
               "региона, что позволит тебе получить конкретно те объекты, которые понадобятся тебе для решения задачи")


def run_agent(page, task: str):
    dispatcher = ToolDispatcher(page)
    messages = [
        {"role": "system", "content": INSTRUCTION},
        {"role": "user", "content": task}
    ]

    for step in range(MAX_STEPS):
        message = ask_model(messages, TOOLS)
        messages.append(message)

        if not message.tool_calls:
            print("Модель (без вызова инструмента):", message.content)
            return message.content

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"[шаг {step}] → {name}({args})")

            if name == "finish":
                print("Готово:", args.get("summary"))
                return args.get("summary")

            result = dispatcher.run(name, args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })

    print(f"Достигнут лимит в {MAX_STEPS} шагов, останавливаюсь.")
    return None
