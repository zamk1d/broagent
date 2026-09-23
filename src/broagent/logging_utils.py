from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich import box

console = Console()


def banner():
    console.print(
        Panel.fit(
            "[bold cyan]broagent[/bold cyan] · автономный браузерный ассистент на Claude",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )


def help_panel():
    console.print(
        Panel(
            "[bold]/help[/bold]   — эта справка\n"
            "[bold]/url[/bold]    — текущий адрес страницы\n"
            "[bold]/new[/bold]    — начать новую задачу без истории предыдущей\n"
            "[bold]/exit[/bold]   — закрыть браузер и выйти (или Ctrl+D)\n\n"
            "Просто введите задачу текстом — агент начнёт её выполнять.\n"
            "Ctrl+C во время работы прерывает текущую задачу и возвращает в чат.",
            title="Команды",
            border_style="grey50",
        )
    )


def user_task(task: str):
    console.print(Rule(style="grey35"))
    console.print(f"[bold white]›[/bold white] {task}")


def step_header(n: int, total: int):
    console.print(f"\n[grey50]─ шаг {n}/{total} ─────────────────────────[/grey50]")


def thinking(step_num: int):
    return console.status(f"[cyan]модель думает (шаг {step_num})…[/cyan]", spinner="dots")


def model_timing(ms: int):
    console.print(f"[grey42]  модель ответила за {ms} ms[/grey42]")


def assistant_text(text: str):
    console.print(Panel(text.strip(), title="Claude", border_style="blue", box=box.ROUNDED))


def tool_call(name: str, args: dict):
    arg_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
    console.print(f"  [yellow]⚙ {name}[/yellow]({arg_str})")


def tool_result(name: str, result: str, ms: int):
    text = str(result)
    preview = text if len(text) <= 300 else text[:300] + f"… (+{len(text) - 300} симв.)"
    console.print(f"  [green]✓[/green] {name} → {preview}  [grey42][{ms} ms][/grey42]")


def tool_error(name: str, err):
    console.print(f"  [red]✗ {name} → ошибка: {err}[/red]")


def warn(msg: str):
    console.print(f"[yellow]⚠ {msg}[/yellow]")


def error(msg: str):
    console.print(f"[bold red]✗ {msg}[/bold red]")


def info(msg: str):
    console.print(f"[grey58]{msg}[/grey58]")


def confirmation_prompt(action_name: str, element_text: str) -> str:
    console.print(
        Panel(
            f"Агент хочет выполнить [bold]{action_name}[/bold] по элементу:\n« {element_text} »",
            title="⚠ Требуется подтверждение",
            border_style="yellow",
        )
    )
    return "    Разрешить? (y/n): "


def final_summary(text: str):
    console.print(
        Panel(text.strip() or "(агент не дал итога)", title="✅ Готово", border_style="green", box=box.ROUNDED)
    )


def interrupted():
    console.print("\n[yellow]⏸ Задача прервана пользователем (Ctrl+C).[/yellow]")


def dialog_seen(kind: str, message: str, action: str):
    console.print(f"[grey42]  ⓘ браузер показал {kind} диалог: «{message}» → {action}[/grey42]")
