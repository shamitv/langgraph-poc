"""
lab_01_hello_world.py — Component 1: LLM Hello World (Text In → Text Out)

Goal
----
Send a simple prompt to an OpenAI-compatible chat endpoint and print the response.

Prereqs
-------
pip install langchain-openai langchain-core

Environment options
-------------------
A) Local OpenAI-compatible server (default in this script):
   - base_url: http://localhost:8090/v1
   - api_key: any string often works for local servers (e.g., "NONE")

B) OpenAI:
   - set OPENAI_API_KEY in your environment
   - set BASE_URL to https://api.openai.com/v1 (or just remove base_url and api_key lines)

Run
---
python lab_01_hello_world.py

Optional env vars
-----------------
MODEL      : model name (default: "Ministral-3B-Instruct")
BASE_URL   : OpenAI-compatible endpoint (default: "http://localhost:8090/v1")
API_KEY    : API key (default: "NONE")
TEMP       : temperature (default: 0)
"""

from __future__ import annotations

import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def main() -> None:
    # -------------------------------------------------------------------------
    # 1) Read configuration from environment (keeps the lab flexible)
    # -------------------------------------------------------------------------
    model = os.getenv("MODEL", "Ministral-3B-Instruct")
    base_url = os.getenv("BASE_URL", "http://localhost:8090/v1")
    api_key = os.getenv("API_KEY", "NONE")

    # Temperature controls randomness: 0 = most deterministic (good for labs)
    try:
        temperature = float(os.getenv("TEMP", "0"))
    except ValueError:
        temperature = 0.0

    # -------------------------------------------------------------------------
    # 2) Create the chat model wrapper
    # -------------------------------------------------------------------------
    print("\n=== LLM CONNECTION DETAILS ===")
    print(f"model     : {model}")
    print(f"base_url  : {base_url}")
    print(f"api_key   : {'***' if api_key else 'NOT SET'}")
    print(f"temp      : {temperature}")
    print()

    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        timeout=120,
    )

    # -------------------------------------------------------------------------
    # 3) Build messages: system + user (like OpenAI "roles")
    # -------------------------------------------------------------------------
    system_prompt = (
        "You are a helpful assistant. "
        "Keep answers short and clear unless asked for more detail."
    )

    user_prompt = (
        "Hello! In one sentence, explain what an LLM is, then give one practical example."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    # -------------------------------------------------------------------------
    # 4) Call the model and print the response text
    # -------------------------------------------------------------------------
    response = llm.invoke(messages)

    print("\n=== CONFIG ===")
    print(f"model     : {model}")
    print(f"base_url  : {base_url}")
    print(f"temp      : {temperature}")

    print("\n=== PROMPT ===")
    print(user_prompt)

    print("\n=== RESPONSE ===")
    print(response.content)


if __name__ == "__main__":
    main()
