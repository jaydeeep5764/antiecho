"""
AntiEcho Command Line Interface.
Provides visual inspection of conversation logs and demo benchmarking.
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from antiecho.core import AntiEcho

console = Console()

SAMPLE_CONVERSATION = [
    {
        "role": "system",
        "content": "You are an expert backend engineer."
    },
    {
        "role": "user",
        "content": "We are using Python 3.12 and SQLite. Please write a user database migration script. Don't use third-party ORMs."
    },
    {
        "role": "assistant",
        "content": (
            "Certainly! As you mentioned, we are using Python 3.12 and SQLite without third-party ORMs. "
            "Here is the database migration script:\n\n"
            "```python\n"
            "import sqlite3\n\n"
            "def run_migration():\n"
            "    conn = sqlite3.connect('app.db')\n"
            "    cur = conn.cursor()\n"
            "    cur.execute('''CREATE TABLE IF NOT EXISTS users (\n"
            "        id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "        username TEXT NOT NULL,\n"
            "        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n"
            "    )''')\n"
            "    conn.commit()\n"
            "    conn.close()\n"
            "    print('Migration complete')\n\n"
            "if __name__ == '__main__':\n"
            "    run_migration()\n"
            "```\n\n"
            "Let me know if you would like me to modify anything else!"
        )
    },
    {
        "role": "user",
        "content": (
            "I ran it and got this error:\n"
            "Traceback (most recent call last):\n"
            "  File \"migrate.py\", line 15, in <module>\n"
            "    run_migration()\n"
            "  File \"migrate.py\", line 4, in run_migration\n"
            "    conn = sqlite3.connect('app.db')\n"
            "sqlite3.OperationalError: unable to open database file"
        )
    },
    {
        "role": "assistant",
        "content": (
            "Certainly! As you mentioned, since we are using Python 3.12 and SQLite, this operational error "
            "occurs when the target directory does not exist or lacks write permissions. "
            "Let's fix it by ensuring the directory exists:\n\n"
            "```python\n"
            "import sqlite3\n"
            "import os\n\n"
            "def run_migration(db_path='app.db'):\n"
            "    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)\n"
            "    conn = sqlite3.connect(db_path)\n"
            "    cur = conn.cursor()\n"
            "    cur.execute('''CREATE TABLE IF NOT EXISTS users (\n"
            "        id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "        username TEXT NOT NULL UNIQUE\n"
            "    )''')\n"
            "    conn.commit()\n"
            "    conn.close()\n"
            "```\n\n"
            "Let me know if you need any further assistance!"
        )
    },
    {
        "role": "user",
        "content": "Awesome, that worked perfectly! Now add email to the schema."
    },
    {
        "role": "assistant",
        "content": (
            "Certainly! As you mentioned, we are using Python 3.12 and SQLite without third-party ORMs. "
            "Here is the updated migration with the email column:\n\n"
            "```python\n"
            "import sqlite3\n"
            "import os\n\n"
            "def run_migration(db_path='app.db'):\n"
            "    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)\n"
            "    conn = sqlite3.connect(db_path)\n"
            "    cur = conn.cursor()\n"
            "    cur.execute('''CREATE TABLE IF NOT EXISTS users (\n"
            "        id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "        username TEXT NOT NULL UNIQUE,\n"
            "        email TEXT NOT NULL UNIQUE\n"
            "    )''')\n"
            "    conn.commit()\n"
            "    conn.close()\n"
            "```\n\n"
            "Feel free to ask if you need anything else!"
        )
    }
]


@click.group()
def main():
    """AntiEcho: Stop LLM Context Echoing, Repetition Loops & Memory Poisoning."""
    pass


@main.command()
@click.argument("file", type=click.Path(exists=True), required=False)
def inspect(file: Optional[str]):
    """Inspect and sanitize a JSON chat transcript file, or run the built-in demo."""
    if file:
        with open(file, "r", encoding="utf-8") as f:
            messages = json.load(f)
    else:
        console.print(Panel(
            "[bold cyan]AntiEcho Live Demo[/bold cyan]\n"
            "[dim]Simulating a 7-turn coding conversation plagued with boilerplate, repetitive echoes, and resolved errors.[/dim]",
            box=box.ROUNDED
        ))
        messages = SAMPLE_CONVERSATION

    engine = AntiEcho()
    cleaned = engine.clean(messages)
    stats = engine.stats

    if not stats:
        console.print("[red]No stats generated.[/red]")
        return

    # Visual Table Results
    table = Table(title="[bold green]AntiEcho Context Optimization Results[/bold green]", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Before", style="yellow")
    table.add_column("After (AntiEcho)", style="green")
    table.add_column("Improvement", style="magenta bold")

    table.add_row(
        "Estimated Tokens",
        f"{stats.original_tokens:,}",
        f"{stats.cleaned_tokens:,}",
        f"-{stats.tokens_saved:,} tokens (-{stats.reduction_percent:.1f}%)"
    )
    table.add_row(
        "Characters",
        f"{stats.original_chars:,}",
        f"{stats.cleaned_chars:,}",
        f"-{stats.original_chars - stats.cleaned_chars:,} chars"
    )
    table.add_row(
        "Boilerplate & Echoes",
        "Present in every turn",
        "Stripped cleanly",
        f"{stats.echoes_pruned} echoes removed"
    )
    table.add_row(
        "Resolved Error Traces",
        "Verbose stack traces",
        "Collapsed to 1-line ref",
        f"{stats.resolved_errors_collapsed} error traces collapsed"
    )
    table.add_row(
        "Superseded Code Drafts",
        "Redundant full files",
        "Collapsed to pointers",
        f"{stats.code_blocks_superseded} code blocks superseded"
    )
    table.add_row(
        "Active Facts & Directives",
        "Buried in raw history",
        "Cleanly pinned in header",
        f"{stats.active_facts_pinned} directives preserved"
    )

    console.print(table)
    console.print()
    console.print(Panel(
        f"[bold white]Summary:[/bold white] [green]{stats.summary()}[/green]\n"
        f"[dim]Models will no longer fixate on old errors, repeat boilerplate, or suffer context drift.[/dim]",
        box=box.ROUNDED
    ))


if __name__ == "__main__":
    main()
