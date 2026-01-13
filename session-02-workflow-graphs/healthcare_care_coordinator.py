"""
Healthcare Agent Demo (LangGraph)
- Supervisor routes: triage_nurse -> tools (optional loop) -> supervisor -> care_coordinator -> END
- Includes:
  - Raw HTTP logging (httpx transport wrapper) for debugging OpenAI-compatible servers
  - LLM request/response logging (LangChain message serialization)
  - Mock healthcare tools: patient_record, appointment_slots, medication_info, coverage_check, policy_check
  - Policy check examples: controlled substances restrictions, pre-auth requirements, age/guardian rules, visit-type limits
NOTE: This is a demo for care coordination. It is NOT medical advice.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import TypedDict, Annotated

import httpx
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import StdOutCallbackHandler
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


# ----------------------------
# Config
# ----------------------------
llm_type = "vllm"  # e.g., "llama.cpp", "vllm", "qwen3", etc.
llm_url = os.getenv("BASE_URL", "http://localhost:8070/v1")  # OpenAI-compatible base URL
model_id = os.getenv("MODEL", "Qwen3-1.7B")                  # server model name/id


# ----------------------------
# Raw HTTP Logger (httpx)
# ----------------------------
class RawHTTPLogger:
    """
    Logs raw HTTP requests/responses for debugging API integration issues.
    Wraps httpx transport and intercepts all HTTP traffic.
    """

    def __init__(self, base_dir: str = "llm_log"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join(os.path.dirname(__file__), base_dir, "http_raw", f"session_{timestamp}")
        os.makedirs(self.log_dir, exist_ok=True)
        self.request_counter = 0
        print(f"[Raw HTTP Logger] Logging to: {self.log_dir}")

    def _next_req_id(self) -> int:
        self.request_counter += 1
        return self.request_counter

    def log_request(self, request: httpx.Request) -> int:
        """Log raw HTTP request. Returns request id."""
        req_id = self._next_req_id()

        body_content = None
        body_json = None
        if request.content:
            try:
                body_content = request.content.decode("utf-8")
                try:
                    body_json = json.loads(body_content)
                except json.JSONDecodeError:
                    pass
            except UnicodeDecodeError:
                body_content = f"<binary data: {len(request.content)} bytes>"

        request_data = {
            "request_id": req_id,
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "body_raw": body_content,
            "body_json": body_json,
        }

        filepath = os.path.join(self.log_dir, f"{req_id:03d}_http_request.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(request_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"[Raw HTTP] Request #{req_id}: {request.method} {request.url}")
        return req_id

    def log_response(self, req_id: int, response: httpx.Response) -> None:
        """Log raw HTTP response."""
        body_content = None
        body_json = None
        try:
            body_content = response.text
            try:
                body_json = json.loads(body_content)
            except json.JSONDecodeError:
                pass
        except Exception as e:
            body_content = f"<error reading body: {e}>"

        elapsed_seconds = None
        try:
            elapsed_seconds = response.elapsed.total_seconds()
        except Exception:
            pass

        response_data = {
            "request_id": req_id,
            "timestamp": datetime.now().isoformat(),
            "status_code": response.status_code,
            "reason_phrase": response.reason_phrase,
            "headers": dict(response.headers),
            "body_raw": body_content,
            "body_json": body_json,
            "elapsed_seconds": elapsed_seconds,
        }

        filepath = os.path.join(self.log_dir, f"{req_id:03d}_http_response.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"[Raw HTTP] Response #{req_id}: {response.status_code} {response.reason_phrase}")

    def log_error(self, req_id: int, error: Exception) -> None:
        error_data = {
            "request_id": req_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_repr": repr(error),
        }

        filepath = os.path.join(self.log_dir, f"{req_id:03d}_http_error.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"[Raw HTTP] Error #{req_id}: {type(error).__name__}: {error}")


class LoggingHTTPTransport(httpx.HTTPTransport):
    """Custom httpx transport that logs all requests and responses."""

    def __init__(self, logger: RawHTTPLogger, **kwargs):
        super().__init__(**kwargs)
        self.logger = logger

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        req_id = self.logger.log_request(request)
        try:
            response = super().handle_request(request)
            # Ensure body is available for logging
            response.read()
            self.logger.log_response(req_id, response)
            return response
        except Exception as e:
            self.logger.log_error(req_id, e)
            raise


def create_logging_http_client(logger: RawHTTPLogger, **kwargs) -> httpx.Client:
    transport = LoggingHTTPTransport(logger=logger, **kwargs)
    return httpx.Client(transport=transport, timeout=httpx.Timeout(60.0))


# ----------------------------
# LLM JSON Logger
# ----------------------------
class LLMLogger:
    """Logs all LLM requests and responses to JSON files."""

    def __init__(self, base_dir: str = "llm_log"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join(os.path.dirname(__file__), base_dir, f"run_{timestamp}")
        os.makedirs(self.log_dir, exist_ok=True)
        self.call_counter = 0
        print(f"[LLM Logger] Logging to: {self.log_dir}")

    def _message_to_dict(self, msg) -> dict:
        result = {
            "type": type(msg).__name__,
            "content": getattr(msg, "content", None),
        }
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            result["tool_calls"] = msg.tool_calls
        if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
            result["additional_kwargs"] = msg.additional_kwargs
        return result

    def log_request(self, caller: str, messages: list) -> int:
        self.call_counter += 1
        call_id = self.call_counter
        request_data = {
            "call_id": call_id,
            "caller": caller,
            "timestamp": datetime.now().isoformat(),
            "messages": [self._message_to_dict(m) for m in messages],
        }
        filepath = os.path.join(self.log_dir, f"{call_id:03d}_request.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(request_data, f, indent=2, ensure_ascii=False, default=str)
        return call_id

    def log_response(self, call_id: int, response) -> None:
        response_data = {
            "call_id": call_id,
            "timestamp": datetime.now().isoformat(),
            "response": self._message_to_dict(response),
        }
        filepath = os.path.join(self.log_dir, f"{call_id:03d}_response.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False, default=str)


http_logger = RawHTTPLogger()
logging_http_client = create_logging_http_client(http_logger)

llm_logger = LLMLogger()

# Failsafe to avoid infinite loops
supervisor_call_count = 0
MAX_SUPERVISOR_CALLS = 12


# ----------------------------
# Shared State + Helpers
# ----------------------------
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next: str  # supervisor routing token


def last_human_text(state: AgentState) -> str:
    for m in reversed(state["messages"]):
        if getattr(m, "type", None) == "human":
            return m.content
    return ""


def sanitize_messages(messages: list) -> list:
    """
    Some OpenAI-compatible backends error on consecutive assistant messages.
    This removes consecutive AIMessage runs, keeping only the most recent AIMessage in each run.
    """
    if llm_type.lower() != "llama.cpp":
        return messages

    if not messages:
        return messages

    result = []
    for msg in messages:
        if result and isinstance(msg, AIMessage) and isinstance(result[-1], AIMessage):
            # Replace previous AI message with current one
            discarded = result[-1]
            preview = discarded.content[:200] + ("..." if len(discarded.content) > 200 else "")
            print(f"[DISCARDED AI MESSAGE] {preview}")
            result[-1] = msg
        else:
            result.append(msg)
    return result


# ----------------------------
# Mock Tools — Healthcare (Care Coordination)
# ----------------------------
@tool("patient_record")
def patient_record(patient_id: str) -> str:
    """
    Retrieve patient demographics, conditions, allergies, current meds, insurance plan,
    and preferred clinic details. (Mock data for demo)
    """
    records = {
        "PT-1001": {
            "patient_id": "PT-1001",
            "name": "Jordan Lee",
            "age": 34,
            "sex": "F",
            "allergies": ["penicillin"],
            "conditions": ["asthma", "seasonal allergies"],
            "current_meds": ["albuterol inhaler", "cetirizine"],
            "insurance_plan": "ACME-HMO-SILVER",
            "preferred_clinic": "Downtown Primary Care",
            "preferred_visit_type": "telehealth",
        },
        "PT-2002": {
            "patient_id": "PT-2002",
            "name": "Sam Patel",
            "age": 16,
            "sex": "M",
            "allergies": [],
            "conditions": ["migraine"],
            "current_meds": ["ibuprofen (OTC)"],
            "insurance_plan": "ACME-PPO-GOLD",
            "preferred_clinic": "Northside Pediatrics",
            "preferred_visit_type": "in_person",
        },
    }
    if patient_id in records:
        return json.dumps(records[patient_id], indent=2)
    return f"Patient '{patient_id}' not found. Available: PT-1001, PT-2002"


@tool("appointment_slots")
def appointment_slots(clinic: str, specialty: str, date_range: str) -> str:
    """
    Return available appointment slots for a clinic and specialty within a date range.
    date_range examples: 'next_7_days', 'next_14_days'. (Mock data)
    """
    slots = {
        ("Downtown Primary Care", "primary_care", "next_7_days"): [
            {"type": "telehealth", "start": "2026-01-15 10:30", "provider": "Dr. Kim"},
            {"type": "in_person", "start": "2026-01-16 16:00", "provider": "Dr. Kim"},
            {"type": "telehealth", "start": "2026-01-17 09:00", "provider": "NP Rivera"},
        ],
        ("Downtown Primary Care", "pulmonology", "next_14_days"): [
            {"type": "in_person", "start": "2026-01-22 11:00", "provider": "Dr. Chen"},
            {"type": "in_person", "start": "2026-01-28 14:30", "provider": "Dr. Chen"},
        ],
        ("Northside Pediatrics", "pediatrics", "next_7_days"): [
            {"type": "in_person", "start": "2026-01-15 15:00", "provider": "Dr. Owens"},
            {"type": "telehealth", "start": "2026-01-18 12:00", "provider": "Dr. Owens"},
        ],
        ("Imaging Center A", "radiology", "next_14_days"): [
            {"type": "in_person", "start": "2026-01-20 10:00", "provider": "Radiology"},
            {"type": "in_person", "start": "2026-01-27 13:00", "provider": "Radiology"},
        ],
    }

    key = (clinic, specialty, date_range)
    if key in slots:
        return json.dumps({"clinic": clinic, "specialty": specialty, "date_range": date_range, "slots": slots[key]}, indent=2)

    return json.dumps(
        {"clinic": clinic, "specialty": specialty, "date_range": date_range, "slots": [], "note": "No slots found for that combination."},
        indent=2,
    )


@tool("medication_info")
def medication_info(drug: str) -> str:
    """
    Return high-level medication info (NOT dosing instructions).
    (Mock, for demo only.)
    """
    db = {
        "albuterol": {
            "class": "short-acting bronchodilator",
            "common_use": "relief of acute asthma symptoms (rescue inhaler)",
            "notes": ["Often requires periodic clinician review for refill policies.", "Check interaction/allergy history."],
        },
        "amoxicillin": {
            "class": "antibiotic (penicillin family)",
            "common_use": "bacterial infections (requires clinician evaluation)",
            "notes": ["Contraindicated if penicillin allergy is present.", "Typically not prescribed without appropriate evaluation."],
        },
        "oxycodone": {
            "class": "opioid analgesic (controlled substance)",
            "common_use": "moderate-to-severe pain (strict policy controls)",
            "notes": ["Controlled substance: additional safeguards and in-person requirements may apply."],
        },
        "mri_lumbar_spine": {
            "class": "diagnostic imaging",
            "common_use": "evaluation of back pain with specific clinical indications",
            "notes": ["Often requires clinical assessment and may require prior authorization."],
        },
    }
    k = drug.strip().lower()
    if k in db:
        return json.dumps({"item": drug, **db[k]}, indent=2)
    return json.dumps({"item": drug, "note": "Not found in mock medication/service database."}, indent=2)


@tool("coverage_check")
def coverage_check(insurance_plan: str, service: str) -> str:
    """
    Return mock coverage details: copay, pre-auth, limitations.
    """
    plan = insurance_plan.strip().upper()
    svc = service.strip().lower()

    # Mock rules
    matrix = {
        "ACME-HMO-SILVER": {
            "primary_care_visit": {"copay": "$25", "preauth_required": False},
            "specialist_visit": {"copay": "$50", "preauth_required": False},
            "mri": {"copay": "$150", "preauth_required": True},
            "controller_inhaler_refill": {"copay": "$10", "preauth_required": False},
        },
        "ACME-PPO-GOLD": {
            "primary_care_visit": {"copay": "$20", "preauth_required": False},
            "specialist_visit": {"copay": "$40", "preauth_required": False},
            "mri": {"copay": "$100", "preauth_required": True},
        },
    }

    if plan not in matrix:
        return json.dumps({"insurance_plan": plan, "service": service, "note": "Unknown plan in mock coverage DB."}, indent=2)

    # Simple mapping
    if "mri" in svc or "imaging" in svc:
        key = "mri"
    elif "specialist" in svc or "pulmon" in svc or "neuro" in svc:
        key = "specialist_visit"
    elif "visit" in svc or "primary" in svc:
        key = "primary_care_visit"
    elif "inhaler" in svc or "refill" in svc:
        key = "controller_inhaler_refill"
    else:
        key = "primary_care_visit"

    return json.dumps({"insurance_plan": plan, "service": service, **matrix[plan].get(key, {})}, indent=2)


@tool("policy_check")
def policy_check(request_type: str, details: str) -> str:
    """
    Check proposed appointments/medications/services against policy criteria.
    Example policy constraints (mock):
      - Controlled substances (e.g., oxycodone) not eligible for telehealth initiation/refill.
      - Antibiotics require clinician evaluation; no direct OTC-style dispensing.
      - Imaging (MRI) requires prior authorization and clinical indications; often after in-person assessment.
      - Minors require guardian consent for scheduling and certain care pathways.
    """
    rt = request_type.strip().lower()
    d = details.lower()

    violations = []
    warnings = []
    requirements = []

    # Controlled substances
    if "oxycodone" in d or "opioid" in d or "controlled" in d:
        violations.append("Controlled substance request: not allowed via telehealth; in-person evaluation required.")
        requirements.append("Verify identity + controlled-substance protocol; require clinician assessment.")

    # Antibiotics / allergy
    if "amoxicillin" in d or "antibiotic" in d:
        warnings.append("Antibiotics generally require clinician assessment; avoid prescribing without evaluation.")
        if "penicillin" in d:
            violations.append("Potential penicillin allergy conflict; alternative must be assessed by clinician.")

    # Imaging / MRI
    if "mri" in d:
        requirements.append("Prior authorization required for MRI under most plans.")
        warnings.append("MRI typically scheduled after clinical evaluation unless red-flag criteria met.")

    # Minors
    if "age: 16" in d or "minor" in d:
        requirements.append("Guardian consent required for scheduling and communications.")

    # Visit type restrictions
    if "telehealth" in d and ("controlled substance" in " ".join(violations).lower()):
        violations.append("Telehealth visit type not permitted for this request.")

    # Build response
    if violations:
        return json.dumps(
            {
                "request_type": rt,
                "status": "BLOCKED",
                "violations": violations,
                "warnings": warnings,
                "requirements": requirements,
            },
            indent=2,
        )

    if warnings or requirements:
        return json.dumps(
            {
                "request_type": rt,
                "status": "REQUIRES_REVIEW",
                "violations": [],
                "warnings": warnings,
                "requirements": requirements,
            },
            indent=2,
        )

    return json.dumps({"request_type": rt, "status": "PASS", "violations": [], "warnings": [], "requirements": []}, indent=2)


tools = [patient_record, appointment_slots, medication_info, coverage_check, policy_check]
tool_node = ToolNode(tools)


# ----------------------------
# Model
# ----------------------------
llm = ChatOpenAI(
    model=model_id,
    temperature=0,
    base_url=llm_url,
    api_key=os.getenv("OPENAI_API_KEY", "NONE"),
    callbacks=[StdOutCallbackHandler()],
    http_client=logging_http_client,
)

# Tools-bound LLM used by triage agent
triage_llm = llm.bind_tools(tools)


# ----------------------------
# Nodes
# ----------------------------
def supervisor(state: AgentState) -> dict:
    """
    Decide what happens next:
      - triage_nurse: gather facts, call tools
      - care_coordinator: synthesize final plan
      - end: stop
    """
    global supervisor_call_count
    supervisor_call_count += 1

    if supervisor_call_count > MAX_SUPERVISOR_CALLS:
        print(f"[SUPERVISOR FAILSAFE] Exceeded {MAX_SUPERVISOR_CALLS} calls; forcing end.")
        return {"next": "end"}

    # Stop if we already have a final answer
    for m in reversed(state["messages"]):
        content = getattr(m, "content", "") or ""
        if isinstance(m, SystemMessage) and content.startswith("[FINAL ANSWER]"):
            print("[SUPERVISOR] Found [FINAL ANSWER]; ending workflow.")
            return {"next": "end"}

    prompt = (
        "You are supervising a healthcare care-coordination workflow (NOT medical diagnosis).\n"
        "Agents available:\n"
        "- triage_nurse: gathers patient context, checks appointment availability, coverage, and policy constraints.\n"
        "- care_coordinator: writes a clear patient-facing plan using triage notes + tool outputs.\n\n"
        "Routing rules:\n"
        "1) If patient info/appointments/coverage/policy checks are needed -> triage_nurse\n"
        "2) If triage notes are present and sufficient to draft the plan -> care_coordinator\n"
        "3) If a final plan already exists -> end\n\n"
        "Return exactly ONE token: triage_nurse, care_coordinator, or end."
    )

    clean_messages = sanitize_messages(state["messages"])
    messages_to_send = [SystemMessage(content=prompt)] + clean_messages

    call_id = llm_logger.log_request("supervisor", messages_to_send)
    resp = llm.invoke(messages_to_send)
    llm_logger.log_response(call_id, resp)

    raw = (resp.content or "").strip()
    # Remove <think> blocks if present (e.g., Qwen thinking mode)
    decision = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip().lower()

    # Extract just the token
    for token in ("triage_nurse", "care_coordinator", "end"):
        if token in decision:
            decision = token
            break

    if decision not in ("triage_nurse", "care_coordinator", "end"):
        print(f"[SUPERVISOR] Unexpected decision: '{raw[:200]}...' -> defaulting to triage_nurse")
        decision = "triage_nurse"

    status_messages = {
        "triage_nurse": "🩺 Gathering details, checking policy & availability...",
        "care_coordinator": "📝 Drafting care coordination plan...",
        "end": "✅ Workflow complete.",
    }
    print(f"\n>>> {status_messages.get(decision, '')}\n")
    return {"next": decision}


def triage_nurse(state: AgentState) -> dict:
    """
    Triage nurse agent:
      - Can call tools to fetch patient record, medication/service info, coverage, policy, appointment slots.
      - Produces [TRIAGE NOTES] when enough info is gathered.
    """
    question = last_human_text(state)

    sys = SystemMessage(
        content=(
            "You are the TRIAGE NURSE agent for care coordination (NOT medical diagnosis).\n"
            "Goal: gather enough information to route/schedule the right appointment and ensure policy/coverage compliance.\n\n"
            "Available tools:\n"
            "- patient_record(patient_id): demographics, conditions, allergies, meds, plan, preferred clinic\n"
            "- medication_info(drug_or_service): high-level info (no dosing)\n"
            "- coverage_check(insurance_plan, service): copay + pre-auth (mock)\n"
            "- policy_check(request_type, details): BLOCKED / REQUIRES_REVIEW / PASS (mock)\n"
            "- appointment_slots(clinic, specialty, date_range): slot options (mock)\n\n"
            "Instructions:\n"
            "- Use tools to gather facts and run coverage + policy checks for requested meds/services/visit types.\n"
            "- If something is BLOCKED, propose compliant alternatives (e.g., in-person visit instead of telehealth).\n"
            "- When you have enough info, write [TRIAGE NOTES] summarizing:\n"
            "  1) patient context (age, key conditions/allergies)\n"
            "  2) requested item(s)\n"
            "  3) recommended visit type + specialty routing\n"
            "  4) appointment options\n"
            "  5) coverage + policy outcomes\n"
            "- Do NOT write the final patient-facing plan. The care coordinator will do that.\n"
        )
    )

    clean_messages = sanitize_messages(state["messages"])
    messages_to_send = [sys] + clean_messages + [HumanMessage(content=question)]

    call_id = llm_logger.log_request("triage_nurse", messages_to_send)
    ai = triage_llm.invoke(messages_to_send)
    llm_logger.log_response(call_id, ai)

    # User-friendly tool call status (optional)
    if getattr(ai, "tool_calls", None):
        for tc in ai.tool_calls:
            name = tc.get("name", "unknown")
            print(f">>> 🔧 Triage calling tool: {name}")

    # Return the AIMessage so ToolNode can execute tool_calls if present
    return {"messages": [ai]}


def care_coordinator(state: AgentState) -> dict:
    """
    Care coordinator agent:
      - Uses all messages (including tool outputs) to compose a patient-friendly plan.
      - No tool calling here; synthesis only.
    """
    question = last_human_text(state)

    sys = SystemMessage(
        content=(
            "You are the CARE COORDINATOR agent.\n"
            "Use [TRIAGE NOTES] and any tool outputs to write a patient-friendly care coordination plan.\n\n"
            "Output requirements:\n"
            "- Keep it operational: scheduling, next steps, what info is needed, what is allowed by policy.\n"
            "- Do not provide dosing instructions or medical diagnosis.\n"
            "- Include clear sections:\n"
            "  1) SUMMARY\n"
            "  2) APPOINTMENT RECOMMENDATION (visit type + specialty)\n"
            "  3) AVAILABLE SLOTS (top options)\n"
            "  4) COVERAGE & PRE-AUTH NOTES\n"
            "  5) POLICY CHECK RESULTS (PASS/REQUIRES_REVIEW/BLOCKED + what to do)\n"
            "  6) NEXT STEPS (what patient should do)\n"
            "  7) SAFETY NOTE (seek urgent care/ER if severe symptoms)\n\n"
            "End by returning a final response.\n"
        )
    )

    clean_messages = sanitize_messages(state["messages"])
    messages_to_send = [sys] + clean_messages + [HumanMessage(content=question)]

    call_id = llm_logger.log_request("care_coordinator", messages_to_send)
    resp = llm.invoke(messages_to_send)
    llm_logger.log_response(call_id, resp)

    answer = resp.content or ""
    return {
        "messages": [SystemMessage(content=f"[FINAL ANSWER]\n{answer}")],
        "next": "end",
    }


# ----------------------------
# Conditional routing helper
# ----------------------------
def triage_should_use_tools(state: AgentState) -> str:
    """
    If last message from triage contains tool_calls -> go to ToolNode.
    Else go back to supervisor.
    """
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return "supervisor"


# ----------------------------
# Build Graph
# ----------------------------
graph = StateGraph(AgentState)

graph.add_node("supervisor", supervisor)
graph.add_node("triage_nurse", triage_nurse)
graph.add_node("tools", tool_node)
graph.add_node("care_coordinator", care_coordinator)

graph.set_entry_point("supervisor")

# Supervisor routing
graph.add_conditional_edges(
    "supervisor",
    lambda s: s["next"],
    {
        "triage_nurse": "triage_nurse",
        "care_coordinator": "care_coordinator",
        "end": END,
    },
)

# Triage -> tools or supervisor
graph.add_conditional_edges(
    "triage_nurse",
    triage_should_use_tools,
    {
        "tools": "tools",
        "supervisor": "supervisor",
    },
)

# Tools -> triage (so triage can interpret tool outputs and optionally call more tools)
graph.add_edge("tools", "triage_nurse")

# Coordinator -> supervisor (supervisor will end upon seeing [FINAL ANSWER])
graph.add_edge("care_coordinator", "supervisor")

app = graph.compile()


# ----------------------------
# Run Demo
# ----------------------------
if __name__ == "__main__":
    supervisor_call_count = 0

    # Sample scenario query: refill + visit type + policy/coverage checks
    sample_query = (
        "Patient PT-1001 wants a refill and prefers telehealth. "
        "They mention 'oxycodone' for back pain and also ask about getting an MRI soon. "
        "Please propose a compliant appointment plan and check coverage/policy constraints."
    )

    print("=" * 80)
    print("HEALTHCARE CARE COORDINATION AGENT — POLICY-AWARE DEMO")
    print("=" * 80)
    print(f"\nPATIENT REQUEST:\n{sample_query}\n")
    print("=" * 80)

    result = app.invoke(
        {
            "messages": [HumanMessage(content=sample_query)],
            "next": "triage_nurse",
        }
    )

    print("\n" + "=" * 80)
    print("FINAL CARE COORDINATION PLAN")
    print("=" * 80)
    print(result["messages"][-1].content)
