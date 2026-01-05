# LLM Hands-on Lab: Hello World → Structured Output → Tool Calling

This lab is a progressive, hands-on walkthrough of three increasingly powerful patterns:

1) **LLM Hello World** (simple prompt → text response)  
2) **LLM + Structured Output** (prompt → validated Pydantic object)  
3) **LLM + Tools** (LLM calls functions to list/read/save files)

Each stage builds directly on the previous one, using the same mental model:
> “Write clear instructions, then make outputs more reliable and automatable.”

---

## What you’ll build

By the end of the lab you’ll have a working “minutes pipeline” that:

- Finds meeting notes in `./meetings/*.txt`
- Reads each meeting file
- Produces structured minutes (summary, decisions, action_items)
- Saves JSON results to `./minutes/*.json`

---

## Prerequisites

### Python
- Python 3.10+ recommended (3.11/3.12 ideal)

### Install dependencies
```bash
pip install pydantic langchain-openai langchain-core
```

### Model / Server requirements
These labs use `ChatOpenAI` from `langchain_openai` with an **OpenAI-compatible endpoint**.

- If using a **local server** (OpenAI-compatible):
  - Example base URL: `http://localhost:8090/v1`
  - Make sure it supports:
    - **Basic chat** (for Lab 1)
    - **Structured output / JSON mode or tool-calling** (for Labs 2 and 3)
- If using OpenAI directly:
  - set `OPENAI_API_KEY` and use the default OpenAI endpoint

> **Tool calling lab (Lab 3)** specifically requires a model/server that supports tool/function calling.

---

## Repository / Folder structure

Recommended structure:

```
.
├── lab_01_hello_world.py
├── lab_02_structured_output.py
├── lab_03_tool_calling_minutes.py
├── tool_prep.py
├── meetings/        # input .txt notes (created by tool_prep.py)
└── minutes/         # output .json minutes (created by tool_prep.py)
```

---

## Component 1 — LLM Hello World (Text In → Text Out)

### Goal
Learn the simplest flow:
- send a system + user prompt
- print the text response

### What you’ll learn
- How `ChatOpenAI` is configured (`model`, `base_url`, `api_key`)
- How messages work (`SystemMessage`, `HumanMessage`)
- Why **temperature=0** helps reproducibility in labs

### Run
```bash
python lab_01_hello_world.py
```

Expected output: a plain text response.

---

## Component 2 — LLM with Structured Output (Text In → Validated Object)

### Goal
Convert messy meeting notes into a strict schema:

- `summary: str`
- `decisions: list[str]`
- `action_items: list[{task, owner, due_date}]`

### What you’ll learn
- Defining a **Pydantic** schema for the output
- Using LangChain’s `with_structured_output(...)`
- Printing validated output as JSON

### Run
```bash
python lab_02_structured_output.py
```

Expected output: 10 JSON blobs (one per prompt), each matching the schema.

> This stage is the “bridge” between chat and automation: once output is structured, downstream code becomes easy.

---

## Component 3 — LLM with Tools (Agentic Automation)

### Goal
Let the model call tools to complete a workflow:

#### Tools included
1. **List meeting files**
   - Scans `./meetings` and returns `.txt` file paths  
2. **Read file**
   - Reads a meeting note file and returns its content  
3. **Save minutes**
   - Validates the minutes JSON against the Pydantic schema and saves into `./minutes`

### What you’ll learn
- Defining tools with `@tool`
- Binding tools to a model with `.bind_tools(...)`
- Implementing a simple **tool loop**:
  - model requests tool calls
  - Python executes tools
  - tool results fed back to the model
- Validating output inside a tool (real-world pattern)

### Prep input data
First generate sample meetings:
```bash
python tool_prep.py
```

This will create:
- `./meetings/` populated with sample `.txt`
- `./minutes/` output directory

### Run the tool-calling pipeline
```bash
python lab_03_tool_calling_minutes.py
```

Expected results:
- terminal shows found meeting files
- each meeting gets processed
- JSON minutes saved to `./minutes/*.json`

---

## Suggested Lab Flow (Instructor-friendly)

### Step 1: Hello World
- Change the user prompt and observe changes.
- Toggle temperature between 0 and 0.7 and compare output stability.

### Step 2: Structured Output
- Add fields (e.g., `attendees`, `discussion_points`)
- Observe how schema changes influence output.
- Add validation constraints and see failure modes.

### Step 3: Tools
- Inspect tool trace logs to see exactly what the model requested.
- Intentionally break a meeting file (empty / weird encoding) and see how tool results affect the model’s behavior.
- Add a new tool:
  - `summarize_all_minutes(minutes_dir)` producing a global weekly summary

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
  - (Fallback) call tools directly in Python (not model-called), but that changes the learning objective.

### “Validation failed in save_minutes”
- The model produced output that didn’t match the schema.
- In this lab, the tool returns the validation error so the model can correct and retry.

---

## What success looks like

After completing all 3 components, you can:
- call an LLM reliably
- enforce a strict output schema for automation
- integrate tools so the model can execute multi-step workflows
- persist results to disk for downstream apps (UI, dashboards, RAG indexing, etc.)

---

## Next Extensions (Optional)
- Add `attendees`, `risks`, `open_questions` fields
- Add a PII redaction tool before saving
- Add a “global summary” tool across all saved minutes
- Add unit tests that parse every saved JSON into `MeetingMinutes`

Happy building!
