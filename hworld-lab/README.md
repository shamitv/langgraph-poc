# Agentic AI Hands-on Labs: Hello World → Structured Output → Tool Calling → LangGraph

This is a progressive, hands-on walkthrough of **four** increasingly “agentic” patterns:

1) **LLM Hello World** — simple prompt → text response  
2) **LLM + Structured Output** — prompt → validated Pydantic object  
3) **LLM + Tools** — model calls functions to list/read/save files  
4) **LangChain → LangGraph** — the same LLM call, wrapped as a **single-node graph** (your bridge to real agentic graphs)

Each stage builds on the previous one using the same mental model:

> Write clear instructions → make outputs reliable → let the model act (safely) → orchestrate with a graph.

---

## Prerequisites

- Python 3.10+ recommended
- Packages:

```bash
pip install langchain-openai langchain-core langgraph pydantic
```

> If you’re using a local OpenAI-compatible server, make sure it’s running before you start.

---

## Repository layout

```
.
├── lab_01_hello_world.py
├── lab_02_structured_output.py
├── lab_03_tool_calling_minutes.py
├── lab_04_langchain_to_langgraph.py
├── tool_prep.py                 # creates ./meetings and ./minutes with sample data
├── meetings/                    # input .txt notes (created by tool_prep.py)
└── minutes/                     # output .json minutes (created by tool_prep.py)
```



---

## Endpoint configuration (OpenAI or local)

These labs use `ChatOpenAI` from `langchain-openai`, which can talk to:

- **OpenAI**
- **Any OpenAI-compatible endpoint** (local servers, gateways, etc.)

### Environment variables (used across all labs)

- `MODEL` (default: `Ministral-3B-Instruct`)
- `BASE_URL` (default: `http://localhost:8090/v1`)
- `TEMP` (default: `0`)
- `API_KEY` (default: `NONE`)
- `OPENAI_API_KEY` (fallback if `API_KEY` not set)

### PowerShell example (Windows)

```powershell
$env:MODEL="gpt-4o-mini"
$env:BASE_URL="https://api.openai.com/v1"
$env:OPENAI_API_KEY="YOUR_KEY"
$env:TEMP="0"
```

### Bash example (macOS/Linux)

```bash
export MODEL="gpt-4o-mini"
export BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="YOUR_KEY"
export TEMP="0"
```

---

## Component 1 — LLM Hello World (Text In → Text Out)

### Goal
Send a **system + user** prompt and print the model’s text response.

### Run
```bash
python lab_01_hello_world.py
```

### Expected result
- The script prints your config, your prompt, and the assistant response.

---

## Component 2 — LLM + Structured Output (Text In → JSON Out)

### Goal
Make outputs automation-friendly by enforcing a **Pydantic schema**.

### Run
```bash
python lab_02_structured_output.py
```

### Expected result
- The script prints multiple JSON objects that match the schema (validated by Pydantic).

---

## Component 3 — LLM with Tools (Agentic Automation)

### Goal
Let the model **call tools** to complete a multi-step workflow:
- list meeting files
- read each file
- generate minutes
- validate and save minutes JSON

### Prep input data
Generate sample meetings + output folders:

```bash
python tool_prep.py
```

This creates:
- `./meetings/` populated with sample `.txt`
- `./minutes/` output directory

### Run
```bash
python lab_03_tool_calling_minutes.py
```

### Expected result
- terminal shows meeting files discovered
- each meeting gets processed
- minutes saved to `./minutes/*.json`

---

## Component 4 — LangChain → LangGraph (Single-node Graph)

### Goal
Show that LangGraph is **orchestration + state** around the same core LLM call.

This lab runs the same prompt twice:
1) **LangChain style**: `llm.invoke(messages)` (Component 1 pattern)  
2) **LangGraph style**: a **single-node graph** that reads state, calls the LLM, and returns updated state

### Run
```bash
python lab_04_langchain_to_langgraph.py
```

### Expected result
- You’ll see two outputs:
  - **LANGCHAIN (Lab 1 style)** output
  - **LANGGRAPH (single-node graph)** output

> They may not be byte-identical (sampling, server variance), but the point is: **LangGraph wraps the same model call in a graph + state machine**.

---

## Suggested lab flow (instructor-friendly)

### Step 1: Hello World
- Change the user prompt and observe changes.
- Toggle temperature between 0 and 0.7 and compare stability.

### Step 2: Structured Output
- Add fields (e.g., `attendees`, `discussion_points`) and observe schema effects.
- Add constraints and see what validation failures look like.

### Step 3: Tools
- Inspect tool-call traces: what did the model request and why?
- Intentionally break a meeting file (empty / weird encoding) and see how the loop behaves.
- Add a new tool: `summarize_all_minutes(minutes_dir)` to produce a global summary.

### Step 4: LangChain → LangGraph
- Run Lab 4 and point out the 3 primitives:
  - **State** (typed dict flowing through the graph)
  - **Node** (function that reads/writes state)
  - **Edges** (execution order)
- Micro-exercise: add a second node that post-processes the AI response and connect it.

---

## Troubleshooting

### “No meeting files found”
- Ensure `./meetings` exists and contains `.txt`
- Run:
  ```bash
  python tool_prep.py
  ```

### “Tool calling doesn’t happen”
- Your model/server likely does not support function/tool calling.
- Options:
  - Use a tool-capable model
  - Switch to an endpoint that supports tool calling

### “Validation failed in save_minutes”
- The model produced output that didn’t match the schema.
- In this lab, the tool returns the validation error so the model can correct and retry.

### “LangGraph import errors”
- Ensure installs are present:
  ```bash
  pip install langgraph langchain-openai langchain-core
  ```

---

## Next extensions (optional)
- Add fields: `attendees`, `risks`, `open_questions`
- Add a PII redaction tool before saving
- Add unit tests that parse every saved JSON into `MeetingMinutes`
- Turn the tool loop into a **LangGraph multi-node workflow** (LLM node ↔ tool node, retries, and routing)

Happy building!
