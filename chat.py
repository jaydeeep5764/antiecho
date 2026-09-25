"""
Interactive Live Chat with Live OpenRouter Models & Real-Time AntiEcho Sanitization.
Calculates dynamic context inspection on every single turn as you chat.
"""

from __future__ import annotations
import os
import sys
import json
import urllib.request
import urllib.error

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

import antiecho

console = Console()

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

FALLBACK_MODELS = [
    "qwen/qwen3.8-27b:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "liquid/lfm-2.5-2.6b:free",
]


def get_api_key() -> str:
    """Retrieve API key from env variable or prompt user."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        console.print(Panel(
            "[bold cyan]🔑 OpenRouter API Key Required[/bold cyan]\n"
            "[dim]Get a free key at: https://openrouter.ai/keys[/dim]",
            box=box.ROUNDED
        ))
        key = console.input("[bold yellow]Enter OpenRouter API Key (sk-or-v1-...): [/bold yellow]").strip()
    return key


def get_active_free_models() -> list[str]:
    """Fetches currently active free models from OpenRouter."""
    try:
        req = urllib.request.Request(OPENROUTER_MODELS_URL, headers={"User-Agent": "AntiEcho-Chat"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            free = [m["id"] for m in data.get("data", []) if ":free" in m.get("id", "")]
            if free:
                return free
    except Exception:
        pass
    return FALLBACK_MODELS


def call_openrouter(api_key: str, model: str, messages: list[dict]) -> str:
    """Sends chat request to OpenRouter using standard Python urllib."""
    payload = {
        "model": model,
        "messages": messages,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jaydeeep5764/antiecho",
        "X-Title": "AntiEcho Live Chat",
    }

    req = urllib.request.Request(
        OPENROUTER_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("error", {}).get("message", error_body)
        except Exception:
            msg = error_body
        raise RuntimeError(f"OpenRouter Error ({e.code}): {msg}")


def print_turn_inspection(turn_num: int, stats: antiecho.CleaningStats, active_facts: list[str]):
    """Renders a dynamic live inspection card for the current conversation turn."""
    table = Table(
        title=f"[bold green]Turn {turn_num} Live Inspection Check[/bold green]",
        box=box.ROUNDED,
        show_header=True
    )
    table.add_column("Live Metric", style="cyan")
    table.add_column("Before", style="yellow")
    table.add_column("After (AntiEcho)", style="green")
    table.add_column("Turn Impact", style="magenta bold")

    table.add_row(
        "Estimated Tokens",
        f"{stats.original_tokens:,}",
        f"{stats.cleaned_tokens:,}",
        f"-{stats.tokens_saved} ({stats.reduction_percent:.1f}%)" if stats.tokens_saved > 0 else "Optimal"
    )
    table.add_row(
        "Characters",
        f"{stats.original_chars:,}",
        f"{stats.cleaned_chars:,}",
        f"-{stats.original_chars - stats.cleaned_chars} chars"
    )
    table.add_row(
        "Echoes & Boilerplate",
        f"{stats.echoes_pruned} detected" if stats.echoes_pruned > 0 else "None",
        "Stripped cleanly",
        f"{stats.echoes_pruned} removed"
    )
    table.add_row(
        "Resolved Error Traces",
        f"{stats.resolved_errors_collapsed} detected" if stats.resolved_errors_collapsed > 0 else "None",
        "Collapsed to 1-line",
        f"{stats.resolved_errors_collapsed} collapsed"
    )

    console.print(table)

    if active_facts:
        facts_preview = " • ".join(active_facts[:4])
        console.print(f"[dim cyan]📌 Active Pinned Directives:[/dim cyan] [dim white]{facts_preview}[/dim white]")
    console.print()


def main():
    console.print(Panel(
        "[bold cyan]🔇 AntiEcho Live Interactive Terminal[/bold cyan]\n"
        "[dim]Chat in real-time with an AI model. AntiEcho dynamically inspects, de-echoes, and calculates savings on every single turn.[/dim]\n"
        "[dim]Type [bold red]'exit'[/bold red] to quit, or [bold yellow]'clear'[/bold yellow] to reset context.[/dim]",
        box=box.ROUNDED
    ))

    api_key = get_api_key()
    if not api_key:
        console.print("[red]No API key provided. Exiting.[/red]")
        return

    # Fetch live models
    free_models = get_active_free_models()
    default_model = free_models[0]

    console.print("\n[bold]Select an Active Free Model:[/bold]")
    for idx, m in enumerate(free_models[:5], 1):
        console.print(f"  [cyan][{idx}][/cyan] {m}")

    choice = console.input(f"\nChoose model [1-{min(5, len(free_models))}] (Enter for default [green]{default_model}[/green]): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= min(5, len(free_models)):
        model = free_models[int(choice) - 1]
    else:
        model = default_model

    console.print(f"\n[bold green]✓ Connected to model:[/bold green] [bold white]{model}[/bold white]\n")

    engine = antiecho.AntiEcho()
    conversation = [
        {"role": "system", "content": "You are a helpful and intelligent software assistant."}
    ]
    turn_num = 1

    while True:
        try:
            user_input = console.input("[bold blue]You > [/bold blue]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session ended.[/dim]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            console.print("[yellow]Exiting AntiEcho Live. Goodbye![/yellow]")
            break
        if user_input.lower() == "clear":
            conversation = [{"role": "system", "content": "You are a helpful and intelligent software assistant."}]
            engine = antiecho.AntiEcho()
            turn_num = 1
            console.print("[green]Context cleared! Starting fresh.[/green]\n")
            continue

        # Add user message
        conversation.append({"role": "user", "content": user_input})

        # 1. LIVE DYNAMIC INSPECTION & CLEANING
        cleaned_messages = engine.clean(conversation)
        stats = engine.stats

        # Extract active facts for display
        active_facts = list(engine.memory.constraints | engine.memory.facts)

        # Print live turn inspection table
        if stats:
            print_turn_inspection(turn_num, stats, active_facts)

        # 2. CALL REAL MODEL WITH SANITIZED CONTEXT
        console.print(f"[dim]Sending {stats.cleaned_tokens if stats else 'N/A'} tokens to {model}...[/dim]")
        try:
            reply = call_openrouter(api_key, model, cleaned_messages)
        except RuntimeError as e:
            console.print(f"[bold red]API Error:[/bold red] {e}")
            conversation.pop() # remove failed turn
            continue

        # Print Model Reply
        console.print(f"\n[bold green]{model} >[/bold green]")
        console.print(reply)
        console.print("-" * 65 + "\n")

        # Save assistant reply to history
        conversation.append({"role": "assistant", "content": reply})
        turn_num += 1


if __name__ == "__main__":
    main()
