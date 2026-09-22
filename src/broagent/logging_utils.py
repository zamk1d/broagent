"""
Цветное логирование агента. Единственное место, которое знает,
как выглядит вывод в терминале. Если завтра захочется писать в файл
или навесить loguru — меняется только этот модуль.
"""

import json
import sys

# если вывод не в терминал (пайп, файл) — цвета не нужны
_USE_COLOR = sys.stdout.isatty()


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"


def _paint(text: str, *codes: str) -> str:
    if not _USE_COLOR:
        return text
    return "".join(codes) + text + C.RESET


def _truncate(text, limit: int = 300) -> str:
    text = str(text).replace("\n", " ⏎ ")
    if len(text) <= limit:
        return text
    return text[:limit] + _paint(f"... (+{len(text) - limit} симв.)", C.DIM)


def _print_block_lines(prefix: str, text: str):
    lines = str(text).splitlines() or [""]
    for line in lines:
        print(_paint(prefix, C.GRAY) + line)


# ─── публичный API ─────────────────────────────────────────────────────────

def banner(title: str):
    line = "─" * 62
    print()
    print(_paint(line, C.GRAY))
    print(_paint(f"  {title}", C.BOLD, C.CYAN))
    print(_paint(line, C.GRAY))


def step(n: int, total: int):
    print()
    print(_paint(f"┌─ шаг {n}/{total} ", C.BOLD, C.BLUE) + _paint("─" * 44, C.GRAY))


def user_input(text: str):
    print(_paint("👤 задача: ", C.BOLD, C.CYAN) + str(text))


def llm_request(step_num: int, messages: list, tools_count: int):
    print(
        _paint("│ ", C.GRAY)
        + _paint("→ запрос к модели", C.BOLD, C.MAGENTA)
        + _paint(f"   шаг {step_num}, сообщений: {len(messages)}, инструментов: {tools_count}", C.DIM)
    )


def llm_response_text(text: str):
    print(_paint("│ ", C.GRAY) + _paint("← ответ модели: текст (без tool_calls)", C.BOLD, C.GREEN))
    _print_block_lines("│   ", text if text else "(пусто)")


def llm_response_tool_calls(tool_calls):
    print(
        _paint("│ ", C.GRAY)
        + _paint("← ответ модели: вызов инструментов", C.BOLD, C.GREEN)
        + _paint(f"   ({len(tool_calls)})", C.DIM)
    )


def tool_call(name: str, args: dict):
    args_str = json.dumps(args, ensure_ascii=False)
    print(
        _paint("│   ", C.GRAY)
        + _paint("⚙ ", C.YELLOW)
        + _paint(name, C.BOLD, C.YELLOW)
        + _paint(f"({_truncate(args_str, 180)})", C.DIM)
    )


def tool_result(name: str, result, elapsed_ms: int | None = None):
    tail = f"   [{elapsed_ms} ms]" if elapsed_ms is not None else ""
    print(
        _paint("│   ", C.GRAY)
        + _paint("✓ ", C.GREEN)
        + _paint(name, C.GREEN)
        + _paint(" → ", C.GRAY)
        + _truncate(result, 300)
        + _paint(tail, C.DIM)
    )


def tool_error(name: str, err):
    print(
        _paint("│   ", C.GRAY)
        + _paint("✗ ", C.RED)
        + _paint(name, C.BOLD, C.RED)
        + _paint(f" → ошибка: {err}", C.RED)
    )


def final(text):
    print()
    print(_paint("└─ ФИНАЛЬНЫЙ ОТВЕТ ", C.BOLD, C.GREEN) + _paint("─" * 42, C.GRAY))
    _print_block_lines("  ", text if text else "(пусто)")
    print(_paint("─" * 62, C.GRAY))


def warn(text: str):
    print(_paint("⚠  ", C.YELLOW) + _paint(text, C.YELLOW))


def error(text: str):
    print(_paint("✗  ", C.RED) + _paint(text, C.RED))


def info(text: str):
    print(_paint("·  ", C.GRAY) + text)