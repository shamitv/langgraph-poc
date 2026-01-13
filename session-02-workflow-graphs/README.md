# Healthcare Care Coordinator — Agentic AI Demo

A **multi-agent LangGraph application** demonstrating policy-aware care coordination for healthcare scheduling. This demo showcases supervisor-based agent orchestration, tool calling, and conditional routing patterns.

> [!IMPORTANT]
> This is a **demonstration** for educational purposes only. It is **NOT** medical advice and should not be used for real healthcare decisions.

---

## Overview

The Healthcare Care Coordinator simulates a patient intake workflow where:
1. A **Supervisor** routes requests between specialized agents
2. A **Triage Nurse** gathers patient information and checks policies
3. A **Care Coordinator** synthesizes findings into a patient-friendly plan

The system demonstrates how to build compliant, policy-aware agentic workflows using LangGraph.

---

## Architecture

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "LangGraph Application"
        SUP["🎯 Supervisor<br/>(Router)"]
        TN["🩺 Triage Nurse<br/>(Information Gatherer)"]
        CC["📝 Care Coordinator<br/>(Plan Synthesizer)"]
        TOOLS["🔧 Tool Node<br/>(LangGraph ToolNode)"]
    end
    
    subgraph "Mock Healthcare Tools"
        T1["patient_record"]
        T2["appointment_slots"]
        T3["medication_info"]
        T4["coverage_check"]
        T5["policy_check"]
    end
    
    subgraph "Infrastructure"
        LLM["LLM Backend<br/>(OpenAI-compatible)"]
        LOG["Logging System<br/>(HTTP + LLM)"]
    end
    
    SUP --> TN
    SUP --> CC
    TN <--> TOOLS
    TOOLS --> T1 & T2 & T3 & T4 & T5
    TN --> LLM
    CC --> LLM
    SUP --> LLM
    LLM --> LOG
```

### Agent Workflow (State Machine)

```mermaid
stateDiagram-v2
    [*] --> Supervisor: Start
    
    Supervisor --> TriageNurse: needs_info
    Supervisor --> CareCoordinator: ready_for_plan
    Supervisor --> [*]: end
    
    TriageNurse --> Tools: tool_calls
    TriageNurse --> Supervisor: no_tools
    
    Tools --> TriageNurse: return_results
    
    CareCoordinator --> Supervisor: plan_complete
    
    note right of Supervisor: Routes based on<br/>conversation state
    note right of TriageNurse: Can loop through<br/>tools multiple times
    note right of CareCoordinator: Produces<br/>[FINAL ANSWER]
```

---

## Agentic Flow

### Detailed Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant S as Supervisor
    participant T as Triage Nurse
    participant TL as Tool Node
    participant C as Care Coordinator
    participant LLM as LLM Backend

    U->>S: Patient request
    
    rect rgb(240, 248, 255)
        Note over S: Phase 1: Routing
        S->>LLM: Decide next agent
        LLM-->>S: "triage_nurse"
    end
    
    rect rgb(255, 248, 240)
        Note over T,TL: Phase 2: Information Gathering (Loop)
        S->>T: Route to triage
        T->>LLM: Request with tools bound
        LLM-->>T: Tool calls (patient_record, policy_check, etc.)
        T->>TL: Execute tools
        TL-->>T: Tool results
        T->>LLM: Process results, maybe call more tools
        LLM-->>T: [TRIAGE NOTES] or more tool calls
    end
    
    rect rgb(240, 255, 240)
        Note over S: Phase 3: Re-routing
        T->>S: Triage complete
        S->>LLM: Decide next agent
        LLM-->>S: "care_coordinator"
    end
    
    rect rgb(255, 240, 255)
        Note over C: Phase 4: Plan Synthesis
        S->>C: Route to coordinator
        C->>LLM: Generate patient plan
        LLM-->>C: [FINAL ANSWER]
    end
    
    C->>S: Plan complete
    S-->>U: Final care coordination plan
```

---

## Component Details

### 1. Supervisor Node

The supervisor is the **orchestrator** that decides which agent should handle the request next.

| Decision | Trigger Condition |
|----------|-------------------|
| `triage_nurse` | Patient info, coverage, or policy checks needed |
| `care_coordinator` | Triage notes present, ready for synthesis |
| `end` | Final plan already exists |

**Failsafe**: Maximum 12 supervisor calls to prevent infinite loops.

---

### 2. Triage Nurse Node

The triage nurse **gathers information** using available tools and produces structured `[TRIAGE NOTES]`.

**Responsibilities:**
- Fetch patient demographics, allergies, conditions
- Check appointment availability
- Verify insurance coverage
- Validate against policy constraints
- Propose compliant alternatives when requests are blocked

---

### 3. Care Coordinator Node

The care coordinator **synthesizes** all gathered information into a patient-friendly plan.

**Output Sections:**
1. **Summary** — Brief overview
2. **Appointment Recommendation** — Visit type + specialty
3. **Available Slots** — Top scheduling options
4. **Coverage & Pre-Auth Notes** — Insurance details
5. **Policy Check Results** — PASS/REQUIRES_REVIEW/BLOCKED
6. **Next Steps** — Patient action items
7. **Safety Note** — When to seek urgent care

---

### 4. Tool Node

Built using LangGraph's `ToolNode`, this node executes tool calls from the triage nurse.

| Tool | Purpose |
|------|---------|
| `patient_record` | Demographics, conditions, allergies, meds, insurance |
| `appointment_slots` | Available slots by clinic, specialty, date range |
| `medication_info` | High-level drug/service information |
| `coverage_check` | Copay and pre-auth requirements |
| `policy_check` | Compliance validation (BLOCKED/REQUIRES_REVIEW/PASS) |

---

## Policy Engine

The `policy_check` tool enforces healthcare compliance rules:

```mermaid
flowchart LR
    subgraph "Policy Rules"
        R1["🚫 Controlled Substances<br/>No telehealth initiation"]
        R2["⚠️ Antibiotics<br/>Require clinician assessment"]
        R3["📋 Imaging (MRI)<br/>Prior authorization required"]
        R4["👶 Minors<br/>Guardian consent required"]
    end
    
    R1 --> |BLOCKED| OUT
    R2 --> |REQUIRES_REVIEW| OUT
    R3 --> |REQUIRES_REVIEW| OUT
    R4 --> |REQUIRES_REVIEW| OUT
    
    OUT["Policy Decision"]
```

---

## State Management

The application uses LangGraph's `StateGraph` with the following state schema:

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # Conversation history
    next: str                                 # Routing decision
```

**Key Pattern**: Messages accumulate across the graph using `add_messages`, preserving full conversation context for each agent.

---

## Logging & Observability

### HTTP Layer Logging
- Captures raw HTTP requests/responses
- Useful for debugging OpenAI-compatible API integration

### LLM Layer Logging
- Logs serialized LangChain messages
- Tracks each agent's prompts and responses
- Output: `llm_log/run_<timestamp>/`

---

## Running the Demo

### Prerequisites

```bash
pip install langchain-openai langchain-core langgraph httpx python-dotenv
```

### Configuration

Set environment variables or create a `.env` file:

```bash
BASE_URL=http://localhost:8070/v1   # OpenAI-compatible endpoint
MODEL=Qwen3-1.7B                     # Model identifier
OPENAI_API_KEY=NONE                  # Required for OpenAI, use "NONE" for local
```

### Execute

```bash
cd session-02-workflow-graphs
python healthcare_care_coordinator.py
```

### Sample Output

The demo runs a sample scenario:
> Patient PT-1001 wants a refill and prefers telehealth. They mention 'oxycodone' for back pain and also ask about getting an MRI soon.

The system will:
1. Retrieve patient record
2. Check policy (oxycodone → BLOCKED for telehealth)
3. Check MRI coverage (prior auth required)
4. Propose compliant alternatives
5. Output a structured care coordination plan

---

## Policy Architecture (LLM-Driven)

The policy engine uses a **documentation-driven approach** where business rules are defined in markdown files instead of hardcoded logic.

### How It Works

```mermaid
flowchart LR
    A["policy_check()"] --> B["Load policies/*.md"]
    B --> C["Send to LLM with request"]
    C --> D["LLM interprets rules"]
    D --> E["Return structured JSON"]
```

1. **Policy documents** in `policies/` define rules in human-readable markdown
2. **At runtime**, the `policy_check` tool loads all policy files
3. **LLM interprets** the policies in context of the specific request
4. **Structured output** returns PASS/REQUIRES_REVIEW/BLOCKED with details

### Policy Files

| File | Description |
|------|-------------|
| `controlled_substances.md` | Opioids, Schedule II-V drug restrictions |
| `medication_prescribing.md` | Antibiotics, allergy conflict checks |
| `imaging_services.md` | MRI/CT prior authorization requirements |
| `patient_consent.md` | Minor consent, guardian requirements |
| `visit_type_restrictions.md` | Telehealth vs in-person rules |

### Benefits

- **No code changes** to update policies — just edit markdown
- **Audit trail** via Git history of policy changes
- **Business analyst friendly** — policies are human-readable
- **Contextual interpretation** — LLM understands nuance beyond keyword matching

---

## Key Concepts Demonstrated

| Concept | Implementation |
|---------|----------------|
| **Multi-agent orchestration** | Supervisor routes between specialized agents |
| **Tool calling** | Triage nurse invokes mock healthcare tools |
| **Conditional routing** | Graph edges based on state decisions |
| **Looping patterns** | Triage ↔ Tools loop until complete |
| **State accumulation** | Messages persist across graph traversal |
| **Policy enforcement** | Tool-based compliance checking |
| **Graceful degradation** | Failsafe limits prevent infinite loops |

---

## Extending the Demo

### Add New Tools
1. Define a new `@tool` decorated function
2. Add to the `tools` list
3. Update triage nurse's system prompt

### Modify Policy Rules
- Edit the `policy_check` function
- Add new violation/warning conditions

### Change Routing Logic
- Modify the `supervisor` node's decision logic
- Update `add_conditional_edges` if adding new agents

---

## License

This demo is part of the **Agentic AI with LangGraph Workshop Series**. See the root [LICENSE](../LICENSE) file.
