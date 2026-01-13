"""
Hands-on Lab: Tool Calling + Structured Minutes (LangChain + Pydantic)

Lab goal
--------
You will build a tiny "minutes pipeline" where the LLM *calls tools* to:
1) list all meeting .txt files in ./meetings
2) read each meeting file
3) save extracted minutes JSON into ./minutes

Key idea
--------
Instead of your Python code directly reading/writing files, the *model* is allowed to
invoke safe, pre-defined tools. Your Python loop only orchestrates the overall flow.

Prereqs
-------
pip install pydantic langchain-openai langchain-core

Folder setup
------------
Create:
  ../data/meetings/transcripts   (put .txt meeting notes here)
  ../data/meetings/minutes       (will be created if missing)

Example file: ../data/meetings/transcripts/meeting_001.txt
----------------------------------------
Attendees: Rahul, Neha
Decided: move job to 11pm
Rahul to add dashboard by 2026-01-10

Run
---
python lab_tool_calling_minutes.py

Notes / Troubleshooting
-----------------------
- Tool calling requires a model/server that supports function/tool calling.
- If your local server at base_url does NOT support tool calling, the model may ignore tools.
  In that case, use an OpenAI tool-capable model OR adapt this lab to call the tools directly.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


# =============================================================================
# 1) Structured output schema we want to SAVE (Pydantic)
# =============================================================================

# Categories for classifying meeting types
MEETING_CATEGORIES = [
    "engineering_sync",      # Regular engineering/tech team sync
    "product_roadmap",       # Product planning and roadmap discussions
    "incident_postmortem",   # Post-incident reviews and RCAs
    "hiring",                # Interview debriefs and hiring discussions
    "launch_readiness",      # Product/feature launch planning
    "vendor_procurement",    # Vendor calls and procurement discussions
    "research",              # Research and experimentation discussions
    "customer_feedback",     # Customer feedback and support reviews
    "leadership",            # Leadership updates and strategy
    "other",                 # General/uncategorized meetings
]

# Type alias for category (Pydantic will validate against this)
MeetingCategory = Literal[
    "engineering_sync",
    "product_roadmap",
    "incident_postmortem",
    "hiring",
    "launch_readiness",
    "vendor_procurement",
    "research",
    "customer_feedback",
    "leadership",
    "other",
]


class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    due_date: str | None = None  # Prefer YYYY-MM-DD if present, else null


class MeetingMinutes(BaseModel):
    category: MeetingCategory     # Type of meeting
    summary: str
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)


def minutes_schema_for_prompt() -> str:
    """
    Return JSON schema as a string so we can embed it in the system prompt.

    Why?
    - When doing tool calling (vs strict "with_structured_output"), the model is not
      automatically forced to match MeetingMinutes.
    - Providing the schema in the prompt reduces ambiguity and improves consistency.
    """
    try:
        # Pydantic v2
        schema = MeetingMinutes.model_json_schema()
    except AttributeError:
        # Pydantic v1 fallback
        schema = MeetingMinutes.schema()
    return json.dumps(schema, indent=2)


# =============================================================================
# 2) Tools (these are the ONLY filesystem actions the LLM is allowed to do)
# =============================================================================
@tool
def list_meeting_files(meetings_dir: str) -> dict:
    """
    List all .txt files in the meetings directory.

    Input:
      meetings_dir: path to directory containing meeting .txt files

    Output (dict):
      {"files": ["meetings/a.txt", "meetings/b.txt", ...]}

    Security note:
    - In a real app you would harden path handling and permissions.
    - For a lab, we keep it simple and only list *.txt.
    """
    base = Path(meetings_dir).expanduser().resolve()
    if not base.exists() or not base.is_dir():
        return {"files": [], "error": f"Directory not found: {str(base)}"}

    files = sorted(str(p) for p in base.glob("*.txt") if p.is_file())
    return {"files": files}


@tool
def read_text_file(path: str) -> dict:
    """
    Read a UTF-8 text file and return its contents.

    Input:
      path: file path

    Output (dict):
      {"path": "<path>", "content": "<file text>"}
    """
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return {"path": str(p), "content": "", "error": f"File not found: {str(p)}"}

    try:
        content = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # If your meeting notes might not be UTF-8, you can add more handling here.
        content = p.read_text(encoding="utf-8", errors="replace")

    return {"path": str(p), "content": content}


@tool
def save_minutes(minutes_dir: str, input_path: str, minutes: dict) -> dict:
    """
    Validate minutes against MeetingMinutes schema and save as JSON into minutes_dir.

    Inputs:
      minutes_dir: output directory (e.g., "./minutes")
      input_path:  original meeting file path (used to derive output filename)
      minutes:     dict containing MeetingMinutes-like fields

    Output (dict):
      {"output_path": ".../meeting_001.json", "saved": true}
      or {"saved": false, "error": "..."} on validation failure

    Why validate inside the tool?
    - It gives immediate feedback to the model (and learners) if the structure is wrong.
    - The model can then correct and try saving again.
    """
    out_dir = Path(minutes_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    in_path = Path(input_path).expanduser().resolve()
    out_name = in_path.stem + ".json"
    out_path = out_dir / out_name

    # Validate structure with Pydantic (this is the "contract" of the lab)
    try:
        try:
            # Pydantic v2
            validated = MeetingMinutes.model_validate(minutes)
            minutes_dict = validated.model_dump()
        except AttributeError:
            # Pydantic v1 fallback
            validated = MeetingMinutes.parse_obj(minutes)
            minutes_dict = validated.dict()
    except Exception as e:
        return {
            "saved": False,
            "output_path": str(out_path),
            "error": f"Validation failed: {e}",
        }

    out_path.write_text(json.dumps(minutes_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"saved": True, "output_path": str(out_path)}


TOOLS = [list_meeting_files, read_text_file, save_minutes]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}  # Used by our tool-loop executor


# =============================================================================
# 3) LLM configuration (OpenAI-compatible)
# =============================================================================
# Read configuration from environment (keeps the lab flexible)
_model = os.getenv("MODEL", "Ministral-3B-Instruct")
_base_url = os.getenv("BASE_URL", "http://localhost:8090/v1")
_api_key = os.getenv("API_KEY", "NONE")

print("\n=== LLM CONNECTION DETAILS ===")
print(f"model     : {_model}")
print(f"base_url  : {_base_url}")
print(f"api_key   : {'***' if _api_key else 'NOT SET'}")
print()

llm = ChatOpenAI(
    model=_model,
    base_url=_base_url,
    api_key=_api_key,
    temperature=0,
    timeout=120,
).bind_tools(TOOLS)  # <-- This enables tool calling: the model can request tool executions


# =============================================================================
# 4) Minimal "tool loop" executor (no Agent framework required)
# =============================================================================
def _call_tool(tool_obj: Any, args: dict) -> Any:
    """
    Call a LangChain tool in a version-tolerant way.

    - Newer LangChain tools support .invoke(args)
    - Some older variants may use .run(...)
    """
    if hasattr(tool_obj, "invoke"):
        return tool_obj.invoke(args)
    # Fallback: try run(**args)
    return tool_obj.run(**args)


def run_tool_loop(messages: list, max_rounds: int = 10) -> tuple[Any, list[tuple[str, dict, Any]], dict]:
    """
    Run the conversation until the model stops requesting tool calls.

    Returns:
      final_ai_message: last AI message (no more tool calls)
      trace: a list of (tool_name, tool_args, tool_result) executed in order
      stats: dict with timing and token usage info

    How it works:
    - Call LLM with current messages.
    - If it requests tool calls, execute them in Python.
    - Append ToolMessage results back to the conversation.
    - Repeat until the AI stops calling tools or max_rounds is reached.
    """
    trace: list[tuple[str, dict, Any]] = []
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    llm_call_count = 0
    start_time = time.time()

    for _ in range(max_rounds):
        ai_msg = llm.invoke(messages)
        messages.append(ai_msg)
        llm_call_count += 1

        # Accumulate token usage from each LLM call
        usage = getattr(ai_msg, "response_metadata", {}).get("token_usage", {})
        total_input_tokens += usage.get("prompt_tokens", 0)
        total_output_tokens += usage.get("completion_tokens", 0)
        total_tokens += usage.get("total_tokens", 0)

        tool_calls = getattr(ai_msg, "tool_calls", None) or []
        if not tool_calls:
            elapsed = time.time() - start_time
            stats = {
                "elapsed_time": elapsed,
                "llm_calls": llm_call_count,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_tokens,
            }
            return ai_msg, trace, stats

        # Execute each requested tool call
        for call in tool_calls:
            name = call.get("name")
            args = call.get("args", {}) or {}
            call_id = call.get("id")

            tool_obj = TOOLS_BY_NAME.get(name)
            if tool_obj is None:
                tool_result = {"error": f"Unknown tool: {name}"}
            else:
                tool_result = _call_tool(tool_obj, args)

            trace.append((name, args, tool_result))

            # ToolMessage content must be a string; JSON is a good standard.
            messages.append(
                ToolMessage(
                    tool_call_id=call_id,
                    content=json.dumps(tool_result, ensure_ascii=False),
                )
            )

    raise RuntimeError("Tool loop exceeded max_rounds (model may be stuck calling tools).")


# =============================================================================
# 5) Lab pipeline:
#    (A) Ask model to list meetings via tool
#    (B) Iterate in Python over each meeting file
#    (C) For each file, ask model to read + extract + save via tools
# =============================================================================
# Resolve paths relative to this script's location (not CWD)
_SCRIPT_DIR = Path(__file__).parent.resolve()
MEETINGS_DIR = str(_SCRIPT_DIR / "../data/meetings/transcripts")
MINUTES_DIR = str(_SCRIPT_DIR / "../data/meetings/minutes")

# System prompt used for per-file processing.
# We explicitly tell the model to:
#  - call read_text_file
#  - produce minutes matching schema
#  - call save_minutes
PROCESS_SYSTEM = f"""
You are a tool-using assistant that converts meeting notes into structured minutes.

You MUST use tools when appropriate:
- Use read_text_file(path) to load meeting content
- Then create a minutes object that matches this JSON schema exactly:
{minutes_schema_for_prompt()}

Rules for minutes:
- category: classify into one of: """ + ', '.join(MEETING_CATEGORIES) + """
- summary: brief, 1-3 sentences
- decisions: include only firm decisions
- action_items: concrete tasks; set owner/due_date to null if missing
- due_date: prefer ISO YYYY-MM-DD if clearly stated, else null

Finally:
- Call save_minutes(minutes_dir, input_path, minutes) to write the JSON output.

If save_minutes returns a validation error:
- Fix the minutes structure and call save_minutes again.
"""


def main() -> None:
    # Ensure output directory exists (even though tool will create it too)
    Path(MINUTES_DIR).mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Step A: Use tool calling to list meeting files
    # -------------------------------------------------------------------------
    list_messages = [
        SystemMessage(
            content=(
                "You are a tool-using assistant. "
                "When asked to list files, call the list_meeting_files tool."
            )
        ),
        HumanMessage(
            content=f"List all .txt meeting files in this directory: {MEETINGS_DIR}. "
                    f"Use the tool list_meeting_files."
        ),
    ]

    _, list_trace, list_stats = run_tool_loop(list_messages)

    # Print stats for listing operation
    print(f"\n--- LLM Call Stats (listing) ---")
    print(f"time       : {list_stats['elapsed_time']:.2f}s")
    print(f"llm calls  : {list_stats['llm_calls']}")
    print(f"input tok  : {list_stats['input_tokens']}")
    print(f"total tok  : {list_stats['total_tokens']}")

    # Pull file list directly from the tool result (most reliable for labs)
    meeting_files: list[str] = []
    for tool_name, _, tool_result in list_trace:
        if tool_name == "list_meeting_files" and isinstance(tool_result, dict):
            meeting_files = tool_result.get("files", []) or []

    print(f"\nFound {len(meeting_files)} meeting file(s).")
    for f in meeting_files:
        print(f" - {f}")

    if not meeting_files:
        print("\nNo meeting files found. Add .txt files to ../data/meetings/transcripts and rerun.")
        return

    # -------------------------------------------------------------------------
    # Step B: Iterate in Python; for each file the MODEL reads + saves via tools
    # -------------------------------------------------------------------------
    for idx, meeting_path in enumerate(meeting_files, start=1):
        print("\n" + "=" * 90)
        print(f"Processing meeting {idx}/{len(meeting_files)}: {meeting_path}")
        print("=" * 90)

        per_file_messages = [
            SystemMessage(content=PROCESS_SYSTEM),
            HumanMessage(
                content=(
                    "Process this meeting file end-to-end.\n"
                    f"- input_path: {meeting_path}\n"
                    f"- minutes_dir: {MINUTES_DIR}\n\n"
                    "Steps you should follow:\n"
                    "1) Call read_text_file(path=input_path)\n"
                    "2) Produce minutes dict matching the schema\n"
                    "3) Call save_minutes(minutes_dir, input_path, minutes)\n"
                    "Return a short confirmation with the output_path."
                )
            ),
        ]

        final_msg, trace, stats = run_tool_loop(per_file_messages)

        # Print LLM call stats for this file
        print(f"\n--- LLM Call Stats ---")
        print(f"time       : {stats['elapsed_time']:.2f}s")
        print(f"llm calls  : {stats['llm_calls']}")
        print(f"input tok  : {stats['input_tokens']}")
        print(f"total tok  : {stats['total_tokens']}")

        # Show what got saved (from tool trace) for deterministic lab feedback
        saved_paths = [
            t_res.get("output_path")
            for t_name, _, t_res in trace
            if t_name == "save_minutes" and isinstance(t_res, dict) and t_res.get("saved") is True
        ]

        if saved_paths:
            print(f"\n✅ Saved minutes: {saved_paths[-1]}")
        else:
            # If save failed, print the last save error to help learners debug
            save_errors = [
                t_res.get("error")
                for t_name, _, t_res in trace
                if t_name == "save_minutes" and isinstance(t_res, dict) and t_res.get("saved") is False
            ]
            print("\n❌ Did not save minutes.")
            if save_errors:
                print(f"Last save error: {save_errors[-1]}")
            print("\nModel final message:")
            print(final_msg.content)

    print("\nDone. Check the ../data/meetings/minutes directory for JSON outputs.")


if __name__ == "__main__":
    main()


# =============================================================================
# OPTIONAL LAB EXTENSIONS (Ideas)
# =============================================================================
# 1) Add a new tool: summarize_all_minutes(minutes_dir) that produces an overall summary.
# 2) Add schema fields: attendees, risks, open_questions. Validate in save tool.
# 3) Add "privacy filter" tool that redacts emails/phone numbers before saving.
# 4) Add retry logic:
#    - If the model fails to call tools, detect and re-prompt with stronger instructions.
# 5) Add unit tests:
#    - Validate every saved JSON can be parsed into MeetingMinutes.
#    - Ensure no action item has empty task.
# =============================================================================
