"""
Hands-on Lab: Structured Outputs (Meeting Minutes) using LangChain + Pydantic

What this script does:
1) Defines a strict JSON-like schema (Pydantic models) for meeting minutes.
2) Wraps an OpenAI-compatible chat model (here: a *local* server via base_url).
3) Uses LangChain's `with_structured_output(...)` so the model returns data that
   matches the schema (summary, decisions, action items).
4) Iterates through 10 sample prompts and prints the structured output as JSON.

Prereqs (install once):
  pip install pydantic langchain-openai langchain-core

Run:
  python lab_02_structured_output.py

Notes:
- Your local server must expose an OpenAI-compatible endpoint at:
    http://localhost:8090/v1
- The model name must match what your server expects.

Reference : https://docs.langchain.com/oss/python/langgraph/workflows-agents

"""

from __future__ import annotations

import os
from pathlib import Path

# Pydantic is used to define the "structured output" schema.
# The model output will be parsed/validated into these classes.
from pydantic import BaseModel, Field

# ChatOpenAI is LangChain's OpenAI-compatible chat model wrapper.
# It works with OpenAI, and with local servers that mimic OpenAI's API.
from langchain_openai import ChatOpenAI

# These message classes let you send a system instruction + a user prompt,
# in a structured way, similar to OpenAI "roles".
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


# ----------------------------
# 1) Define output schema (Pydantic models)
# ----------------------------
class ActionItem(BaseModel):
    """
    One action item extracted from the notes.
    """
    task: str                     # What needs to be done
    owner: str | None = None      # Who owns it (None if not specified)
    due_date: str | None = None   # ISO date (YYYY-MM-DD) if possible, else None


class MeetingMinutes(BaseModel):
    """
    Full structured output for meeting minutes.
    This is the top-level schema we want the LLM to return.
    """
    summary: str
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)


# ----------------------------
# 2) Configure the LLM client (OpenAI-compatible local endpoint)
# ----------------------------
# Read configuration from environment (keeps the lab flexible)
_model = os.getenv("MODEL", "Ministral-3B-Instruct")
_base_url = os.getenv("BASE_URL", "http://localhost:8090/v1")
_api_key = os.getenv("API_KEY", "NONE")

print("\n=== LLM CONNECTION DETAILS ===")
print(f"model     : {_model}")
print(f"base_url  : {_base_url}")
print(f"api_key   : {'***' if _api_key else 'NOT SET'}")
print()

local_llm = ChatOpenAI(
    model=_model,
    base_url=_base_url,
    api_key=_api_key,
)


# ----------------------------
# 3) Helper: print Pydantic objects as JSON (supports v1 + v2)
# ----------------------------
def dump_json(obj: BaseModel) -> str:
    """
    Convert a Pydantic model instance into pretty JSON for printing.

    Why the version check?
    - Pydantic v2 uses `model_dump_json(...)`
    - Pydantic v1 uses `json(...)`
    This helper keeps the lab code working across both versions.
    """
    if hasattr(obj, "model_dump_json"):      # Pydantic v2
        return obj.model_dump_json(indent=2)
    return obj.json(indent=2)                # Pydantic v1


# ----------------------------
# 4) Turn on "structured output" mode in LangChain
# ----------------------------
# This is the key line:
# It "augments" the LLM so `.invoke(...)` returns a *MeetingMinutes* object.
#
# Under the hood, LangChain will:
# - Tell the model about the schema (often via tool-calling / JSON schema)
# - Parse the model response into the Pydantic class
# - Validate fields & types (task must be str, etc.)
structured_llm = local_llm.with_structured_output(MeetingMinutes)


# ----------------------------
# 5) System prompt: rules that guide extraction
# ----------------------------
SYSTEM_INSTRUCTIONS = (
    "You convert meeting notes into structured minutes.\n"
    "Rules:\n"
    "- Put only firm decisions in decisions.\n"
    "- Action items must be concrete tasks.\n"
    "- If owner or due date is missing, output null.\n"
    '- If a due date is present, format as ISO "YYYY-MM-DD" if possible.\n'
    "- Keep summary brief.\n"
)


# ----------------------------
# 6) Ten sample prompts to demonstrate different meeting-note styles
# ----------------------------
PROMPTS = [
    # 1) Weekly engineering sync
    """Turn these notes into minutes with decisions + action items.
Notes:
- API latency spikes after 6pm IST. Might be batch job?
- Decided: move nightly job from 6pm to 11pm.
- Rahul to add dashboard panel for p95 + error rate by tomorrow.
- Neha to check if Redis eviction policy changed last deploy.
- Next sync: Friday.""",

    # 2) Product roadmap meeting
    """Convert the following into structured minutes.
Transcript snippets:
- PM: “We should ship onboarding v2 this sprint.”
- Eng: “Risky unless we drop analytics refactor.”
- Decision: onboarding v2 ships; analytics refactor moved to next sprint.
- Action: Aditi to update Jira epics and sprint board today.
- Action: Mohit to write migration notes for support team (no date mentioned).""",

    # 3) Incident postmortem
    """Create clean minutes from this postmortem discussion.
- 02:10 UTC alert fired. 02:18 rollback started. 02:27 recovery confirmed.
- Root cause suspected: config flag enabled in prod without canary.
- Decision: enforce change management checklist for prod flags.
- Action: SRE team to add “flag diff” step in deploy pipeline by 2026-01-10.
- Action: Riya to draft a short RCA summary for leadership.""",

    # 4) Hiring loop debrief
    """Summarize as minutes with decisions and action items.
- Candidate strong in systems, weaker in SQL.
- Team split: 2 “hire”, 1 “no hire”.
- Decision: request a 30-min SQL exercise before final decision.
- Action: Sameer to prepare SQL exercise and send to recruiter by Wednesday.
- Action: Kavita to schedule follow-up interview.""",

    # 5) Cross-functional launch readiness
    """Turn the following into structured minutes.
- Launch date proposed: Jan 20. Marketing says OK; Sales wants Jan 27.
- Decision: soft launch Jan 20, full launch Jan 27.
- Action: Priya to finalize press draft by 2026-01-12.
- Action: Arjun to confirm pricing page copy by 2026-01-14.
- Action: Dev team to implement feature flag + rollback plan (no owner named).""",

    # 6) Vendor / procurement call
    """Convert these call notes into minutes.
- Vendor offering 15% discount if 2-year commitment.
- We need annual payment option; legal review pending.
- Decision: proceed with 1-year contract only (no 2-year).
- Action: Nitin to request revised quote by Monday.
- Action: Legal to review DPA and share redlines (no due date).""",

    # 7) Research discussion
    """Produce minutes. If something is not a firm decision, don’t list it as a decision.
Notes:
- “Maybe we should try reranker model X” (not finalized)
- “Let’s definitely benchmark on dataset Y first” (agreed)
- Action: Anjali to run baseline eval on dataset Y by 2026-01-08.
- “Could also add multilingual tests later” (optional idea)""",

    # 8) Customer feedback review
    """Create meeting minutes from these bullets.
- Top complaints: slow exports, confusing billing labels.
- Decision: exports performance is P0 for next sprint.
- Decision: rename “Usage Units” to “Credits” on invoices.
- Action: Farhan to open performance investigation ticket today.
- Action: Design team to propose invoice wording changes by next Thursday.""",

    # 9) Leadership update
    """Turn this into minutes with decisions and action items.
- We will not expand to 2 new countries in Q1. Focus on existing market retention.
- Budget approved for 2 additional support hires.
- Action: HR to start hiring pipeline (no date).
- Action: Finance to circulate updated budget sheet by 2026-01-07.""",

    # 10) Chaos notes
    """Clean these messy notes into minutes. Use null for missing owners/dates.
- decid: stop using old auth endpoint by feb
- ai: update docs + notify integrators
- ai: rotate api keys for partnerX (urgent)
- next meeting maybe Tue?
- also talked about “rate limit errors” after new release""",
]


# ----------------------------
# 7) Main loop: send each prompt, print structured JSON
# ----------------------------
def main() -> None:
    """
    For each prompt:
    - Build message list (system + user)
    - Call the structured LLM
    - Receive a validated MeetingMinutes object
    - Print pretty JSON so learners can see the extracted structure
    """
    for i, user_prompt in enumerate(PROMPTS, start=1):
        # Visual separators in terminal output (helps in a lab)
        print("\n" + "=" * 90)
        print(f"PROMPT {i}")
        print("=" * 90)

        # Messages mimic ChatML roles:
        # - SystemMessage: high-level instructions that apply to all prompts
        # - HumanMessage: the specific meeting notes to parse
        messages = [
            SystemMessage(content=SYSTEM_INSTRUCTIONS),
            HumanMessage(content=user_prompt),
        ]

        try:
            # Because we used `with_structured_output(MeetingMinutes)`,
            # LangChain returns an instance of MeetingMinutes (not raw text).
            minutes: MeetingMinutes = structured_llm.invoke(messages)

            # Pretty print JSON for easy reading / copy-paste into docs
            print(dump_json(minutes))

        except Exception as e:
            # Common causes in a lab:
            # - Local server not running / wrong base_url
            # - Model name mismatch
            # - Server doesn't support tool-calling / JSON schema
            # - Timeout or connection issues
            print(f"ERROR on prompt {i}: {e}")


# Standard Python entry-point guard:
# The code inside runs only when you execute the script directly,
# not when importing it as a module.
if __name__ == "__main__":
    main()
