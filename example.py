"""
Quick demonstration script for AntiEcho.
Run this directly in VS Code to see how AntiEcho sanitizes context and saves tokens!
"""

import json
import antiecho

# A realistic multi-turn conversation with boilerplate, echoes, and a resolved error
chat_history = [
    {
        "role": "system",
        "content": "You are an expert backend engineer."
    },
    {
        "role": "user",
        "content": "We are using Python 3.12 and SQLite. Please create an auth table. Don't use third-party ORMs."
    },
    {
        "role": "assistant",
        "content": (
            "Certainly! As you mentioned, we are using Python 3.12 and SQLite without third-party ORMs. "
            "Here is the database schema:\n\n"
            "```python\n"
            "import sqlite3\n"
            "# 10 lines of setup code...\n"
            "```\n\n"
            "Let me know if you would like me to modify anything else!"
        )
    },
    {
        "role": "user",
        "content": (
            "I ran it and got this error:\n"
            "Traceback (most recent call last):\n"
            "  File \"auth.py\", line 10, in <module>\n"
            "    conn = sqlite3.connect('users.db')\n"
            "sqlite3.OperationalError: unable to open database file"
        )
    },
    {
        "role": "assistant",
        "content": "Ensure the directory exists before connecting. Use os.makedirs."
    },
    {
        "role": "user",
        "content": "Awesome, that worked! Now let's add password hashing."
    },
    {
        "role": "assistant",
        "content": (
            "Certainly! As you mentioned, we are using Python 3.12 and SQLite without third-party ORMs. "
            "Here is how we add bcrypt hashing..."
        )
    }
]

print("=" * 60)
print("1. BEFORE ANTIECHO (Original Messages)")
print("=" * 60)
for msg in chat_history:
    print(f"[{msg['role'].upper()}]: {msg['content'][:100]}...\n")

# Sanitize with AntiEcho in 1 line
cleaned_history = antiecho.clean(chat_history)
stats = antiecho.get_last_stats()

print("=" * 60)
print("2. AFTER ANTIECHO (Sanitized Messages)")
print("=" * 60)
for msg in cleaned_history:
    print(f"[{msg['role'].upper()}]:\n{msg['content']}\n")

print("=" * 60)
print("3. SAVINGS & OPTIMIZATION STATS")
print("=" * 60)
print(stats.summary())
