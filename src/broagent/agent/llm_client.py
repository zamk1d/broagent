import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(
    base_url=os.getenv("GROQ_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

MODEL = str(os.getenv("GROQ_MODEL"))


def ask_model(messages: list, tools: list):
    response = _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
    )
    return response.choices[0].message
