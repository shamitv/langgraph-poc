# Agentic AI with LangGraph — Hands-on Workshop Series

This repository contains a progressive set of hands-on sessions that take participants from:
**LLM basics → structured outputs → tool calling → LangGraph workflows → looping agents**.

Each session includes multiple labs (scripts) and exercises. You can run the labs on either:
- a **local OpenAI-compatible server** (recommended for workshops), or
- **OpenAI** via `OPENAI_API_KEY` + `BASE_URL=https://api.openai.com/v1`.

---

## Quick start

### 1) Install dependencies
```bash
pip install langchain-openai langchain-core langgraph pydantic pytest
```

### 2) Set environment variables (example)
**OpenAI:**
```bash
export BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="..."
export MODEL="gpt-4o-mini"
export TEMP="0"
```

**Local OpenAI-compatible server:**
```bash
export BASE_URL="http://localhost:8090/v1"
export API_KEY="NONE"
export MODEL="Ministral-3B-Instruct"
export TEMP="0"
```

### 3) Run Session 1
```bash
python lab_01_hello_world.py
python lab_02_structured_output.py
python lab_prep.py
python lab_03_tool_calling_minutes.py
python lab_04_langchain_to_langgraph.py
```

---

## Sessions

### Session 1 — Foundations (Labs 01–04)
Prompting → structured output → tools → basic LangGraph.

- [Session 1 README](README_Session_1.md)

**Labs**
- **Lab 01:** `lab_01_hello_world.py` — LLM “Hello World” (messages → text)
- **Lab 02:** `lab_02_structured_output.py` — structured output with Pydantic (messages → JSON)
- **Lab 03:** `lab_03_tool_calling_minutes.py` — tool calling minutes pipeline (list/read/write)
- **Lab 04:** `lab_04_langchain_to_langgraph.py` — LangChain call inside a single-node LangGraph

---

### Session 2 — Workflow Graphs (Labs 05–07)
Multi-node graphs, routing, structured nodes, tool nodes, observability.

- [Session 2 README](README_Session_2.md)

**Labs (planned)**
- **Lab 05:** `lab_05_multinode_routing.py` — conditional routing between nodes
- **Lab 06:** `lab_06_structured_minutes_graph.py` — structured extraction as a graph node (+ retries)
- **Lab 07:** `lab_07_minutes_tools_graph.py` — tools inside LangGraph (end-to-end minutes workflow)

---

### Session 3 — Agentic Graphs (Labs 08–10)
Loops, reflection, termination conditions, and a full coding-agent capstone.

- [Session 3 README](README_Session_3.md)

**Labs (planned)**
- **Lab 08:** `lab_08_agent_loop_pattern.py` — generic plan/act/reflect loop
- **Lab 09:** `lab_09_coding_agent.py` — capstone: problem + tests → code → fix until PASS
- **Lab 10:** `lab_10_agent_hardening.py` — guardrails, timeouts, budgets, logging, optional HITL

---

## Repo structure (current + expected)

```
.
├── README.md
├── README_Session_1.md
├── README_Session_2.md
├── README_Session_3.md
├── README_LLM_Lab.md
├── lab_01_hello_world.py
├── lab_02_structured_output.py
├── lab_03_tool_calling_minutes.py
├── lab_04_langchain_to_langgraph.py
├── lab_prep.py
├── meetings/
└── minutes/
```

---

## Teaching notes (recommended)
- Keep `TEMP=0` for reproducibility during demos.
- Encourage participants to inspect:
  - prompts (system + user)
  - tool calls and tool outputs
  - state transitions across graph nodes
- For safety, tools should restrict filesystem access to allowlisted directories only.

---

## Troubleshooting

### “Model call failed” / connection errors
- Verify your endpoint is running (`BASE_URL`)
- Verify model name (`MODEL`) is available on your endpoint
- For OpenAI: ensure `OPENAI_API_KEY` is set

### Package import errors
- Reinstall dependencies:
```bash
pip install -U langgraph langchain-openai langchain-core pydantic pytest
```

---

## License
Add your preferred license here (MIT/Apache-2.0/etc.).
