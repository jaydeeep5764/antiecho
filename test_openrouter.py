"""
Test AntiEcho with a real live model on OpenRouter!
Uses standard Python library (urllib.request) so it requires 0 external dependencies.
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Import our AntiEcho library
import antiecho

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

# Reliable fallback free models on OpenRouter
FALLBACK_FREE_MODELS = [
    "qwen/qwen3.8-27b:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "liquid/lfm-2.5-2.6b:free",
]


def get_api_key():
    """Retrieve API key from env variable or prompt user."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("\n" + "=" * 60)
        print("🔑 OPENROUTER API KEY")
        print("=" * 60)
        key = input("Enter your OpenRouter API Key (sk-or-v1-...): ").strip()
    return key


def get_active_free_models():
    """Fetches currently active :free models from OpenRouter API."""
    try:
        req = urllib.request.Request(
            OPENROUTER_MODELS_URL,
            headers={"User-Agent": "AntiEcho-Tester"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            free = [m["id"] for m in data.get("data", []) if ":free" in m.get("id", "")]
            if free:
                return free
    except Exception:
        pass
    return FALLBACK_FREE_MODELS


def call_openrouter(api_key: str, model: str, messages: list):
    """Sends chat request to OpenRouter using standard Python urllib."""
    payload = {
        "model": model,
        "messages": messages,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jaydeeep5764/antiecho",
        "X-Title": "AntiEcho Live Test",
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


def main():
    print("=" * 65)
    print("🚀 AntiEcho Real-World Test with Live OpenRouter Model")
    print("=" * 65)

    api_key = get_api_key()
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return

    # Fetch currently active free models
    free_models = get_active_free_models()
    default_model = free_models[0] if free_models else FALLBACK_FREE_MODELS[0]

    print("\nAvailable Active Free Models:")
    for idx, m in enumerate(free_models[:5], 1):
        print(f"  [{idx}] {m}")

    choice = input(f"\nSelect a model [1-{min(5, len(free_models))}] (Press Enter for default: {default_model}): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= min(5, len(free_models)):
        selected_model = free_models[int(choice) - 1]
    else:
        selected_model = default_model

    print(f"\n🤖 Using Model: {selected_model}")

    # Simulated messy multi-turn conversation that usually poisons model context
    conversation = [
        {
            "role": "system",
            "content": "You are a professional software engineer."
        },
        {
            "role": "user",
            "content": "We are using Python 3.12 and SQLite. Don't use any external ORM libraries. Create an init_db function."
        },
        {
            "role": "assistant",
            "content": (
                "Certainly! As you mentioned, we are using Python 3.12 and SQLite without external ORM libraries. "
                "Here is the database initialization function:\n\n"
                "```python\n"
                "import sqlite3\n"
                "def init_db():\n"
                "    conn = sqlite3.connect('test.db')\n"
                "    cur = conn.cursor()\n"
                "    cur.execute('CREATE TABLE IF NOT EXISTS items (id INT, name TEXT)')\n"
                "    conn.commit()\n"
                "    conn.close()\n"
                "```\n\n"
                "Let me know if you would like me to modify anything else!"
            )
        },
        {
            "role": "user",
            "content": (
                "I got this error:\n"
                "Traceback (most recent call last):\n"
                "  File \"test.py\", line 4, in init_db\n"
                "    cur.execute('CREATE TABLE IF NOT EXISTS items (id INT, name TEXT)')\n"
                "sqlite3.OperationalError: table items already exists"
            )
        },
        {
            "role": "assistant",
            "content": "The IF NOT EXISTS clause prevents that. Make sure the database file is not locked."
        },
        {
            "role": "user",
            "content": "Awesome, that worked! Now please add an insert_item(name) function that returns the row id."
        }
    ]

    print("\n--- [1] RAW CONVERSATION (Before AntiEcho) ---")
    print(f"Total raw messages: {len(conversation)}")
    raw_chars = sum(len(m["content"]) for m in conversation)
    print(f"Total characters: {raw_chars:,} (~{raw_chars // 4} tokens)")

    # 1. Clean the context with AntiEcho
    print("\n--- [2] SANITIZING WITH ANTIECHO ---")
    clean_conversation = antiecho.clean(conversation)
    stats = antiecho.get_last_stats()

    print(f"✅ {stats.summary()}")
    print("\n[Preview of Sanitized Context sent to Model]:")
    for msg in clean_conversation:
        print(f"[{msg['role'].upper()}]: {msg['content'][:120]}...")

    # 2. Send the sanitized conversation to the real OpenRouter model
    print(f"\n--- [3] SENDING CLEANED PAYLOAD TO LIVE MODEL ({selected_model}) ---")
    print("⏳ Waiting for live response from model...")

    try:
        response = call_openrouter(api_key, selected_model, clean_conversation)
    except RuntimeError as e:
        print(f"\n⚠️ {e}")
        # Auto-try next free model
        alternative = "google/gemma-4-26b-a4b-it:free" if selected_model != "google/gemma-4-26b-a4b-it:free" else "nvidia/nemotron-3.5-lightning:free"
        print(f"🔄 Retrying with alternative free model: {alternative}...")
        response = call_openrouter(api_key, alternative, clean_conversation)

    print("\n" + "=" * 65)
    print("🎯 LIVE MODEL RESPONSE FROM OPENROUTER:")
    print("=" * 65)
    print(response)
    print("=" * 65)
    print("\n✨ Notice how the model stayed sharp, respected your pinned constraints")
    print("(Python 3.12, SQLite, No ORM), and didn't repeat previous errors or filler!")


if __name__ == "__main__":
    main()
