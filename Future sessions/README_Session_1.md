# Session 1 — Foundations: Prompting → Structured Output → Tools → Basic LangGraph

This session is a progressive, hands-on walkthrough of four labs that establish the core primitives you’ll reuse in every agentic workflow:

1) **LLM Hello World** (messages → text response)  
2) **LLM + Structured Output** (messages → validated Pydantic object)  
3) **LLM + Tools** (model calls safe file tools)  
4) **LangChain → LangGraph** (same call, now inside a graph node)

By the end of Session 1 you will have a **basic LangGraph** (single-node) and a mental model for how later sessions add routing, tools, and loops.

---

## Learning objectives

By the end of this session, participants can:
- Send a system + user prompt and interpret responses
- Enforce **schema-conformant output** using Pydantic + structured output
- Use **tool calling** to safely interact with files (list/read/write)
- Explain what **LangGraph** adds (state + nodes + edges) and run a basic graph

---

## Prerequisites

- Python 3.10+
- A model endpoint:
  - **Local OpenAI-compatible server** (recommended for labs), OR
  - **OpenAI** (set `OPENAI_API_KEY` and `BASE_URL=https://api.openai.com/v1`)
- Packages:
  - `pip install langchain-openai langchain-core langgraph pydantic`

---

## Repo layout (expected)

```
.
├── README_LLM_Lab.md
├── lab_01_hello_world.py
├── lab_02_structured_output.py
├── lab_03_tool_calling_minutes.py
├── lab_04_langchain_to_langgraph.py
├── lab_prep.py   (or tool_prep.py)
├── meetings/     # input .txt notes (created by prep script)
└── minutes/      # output .json minutes (created by prep script)
```

---

## Environment variables (same across labs)

- `MODEL` (default varies per lab; e.g., `Ministral-3B-Instruct`)
- `BASE_URL` (default: `http://localhost:8090/v1`)
- `API_KEY` (default: `NONE` for many local servers)
- `OPENAI_API_KEY` (fallback if `API_KEY` isn’t set)
- `TEMP` (default: `0`)

Example (PowerShell):

```powershell
$env:MODEL="gpt-4o-mini"
$env:BASE_URL="https://api.openai.com/v1"
$env:OPENAI_API_KEY="..."
$env:TEMP="0"
```

---

## Agenda (recommended)

- 0:00–0:10 — Setup + endpoints + “messages” mental model
- 0:10–0:30 — Lab 01: Hello World
- 0:30–1:05 — Lab 02: Structured output (Pydantic)
- 1:05–1:40 — Lab 03: Tool calling minutes pipeline
- 1:40–2:00 — Lab 04: LangChain → LangGraph (single node) + wrap-up

---

## Lab 01 — Hello World

### Goal
Send a system + user prompt and print the model response.

### Run
```bash
python lab_01_hello_world.py
```

### Exercises
- Change `TEMP` and compare outputs
- Change the system prompt to enforce a style (bullet points, one sentence, etc.)

---

## Lab 02 — Structured output

### Goal
Extract “meeting minutes” into a validated Pydantic object.

### Run
```bash
python lab_02_structured_output.py
```

### Exercises
- Add a new field to the schema (`attendees`, `risks`, `open_questions`)
- Add a retry strategy for validation errors

---

## Lab 03 — Tool calling (minutes pipeline)

### Goal
Use tools to process a directory of meeting notes:
- list meeting files
- read file text
- extract structured minutes
- save minutes JSON

### Prep
```bash
python lab_prep.py
```
(This creates `./meetings` and `./minutes` with sample data.)

### Run
```bash
python lab_03_tool_calling_minutes.py
```

### Exercises
- Add a run log (`minutes/run_log.jsonl`) with: filename, timestamp, tool calls
- Restrict file access to an allowlisted root (security)

---

## Lab 04 — LangChain → LangGraph (single-node graph)

### Goal
Show the *same* LLM call now lives inside a LangGraph node with state.

### Run
```bash
python lab_04_langchain_to_langgraph.py
```

### Exercises
- Add one more node (e.g., “postprocess response”) and connect it
- Print the final state (messages list) to show how state accumulates

---

## Wrap-up & bridge to Session 2

**Key takeaway:** LangGraph doesn’t change the model call — it adds **state + orchestration**.

In Session 2 you’ll:
- build **multi-node graphs**
- add **routing**
- integrate **structured output nodes** + **tool nodes** inside graphs
