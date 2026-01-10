# Session 2 — Workflow Graphs: State, Routing, Structured Nodes, and Tool Nodes

Session 2 starts from where Session 1 ended: you can run a **basic LangGraph**.  
Now we’ll turn that into real workflows: multiple nodes, typed state, conditional routing, and tool-powered pipelines.

---

## Learning objectives

By the end of Session 2, participants can:
- Build **multi-node LangGraphs** with typed state
- Route execution using **conditional edges** (if/else)
- Use **structured outputs** inside graph nodes (Pydantic validation)
- Add **tool nodes** safely (allowlists, path safety)
- Debug graphs using streaming/events and lightweight run logs

---

## Prerequisites

- Completed Session 1 (Labs 01–04)
- Packages:
  - `pip install langgraph langchain-openai langchain-core pydantic`

---

## Agenda (recommended)

- 0:00–0:10 — Recap: state, nodes, edges; why routing matters
- 0:10–0:45 — Lab 05: Multi-node graph + router
- 0:45–1:20 — Lab 06: Structured extraction as a graph node (+ retries)
- 1:20–2:00 — Lab 07: Tool calling workflow as a graph (minutes pipeline in LangGraph)

---

## Lab 05 — Multi-node graph with a router

### Goal
Create a graph that routes between different paths based on the user request.

### New concepts
- Add `intent` and `route` fields to state
- Use conditional edges to select a branch

### Suggested graph
```
START
  └─> classify_intent
        ├─(intent="qa")──────────> answer_node ──> END
        └─(intent="minutes")─────> extract_node ──> END
```

### Deliverable
- `lab_05_multinode_routing.py`
- State includes: `messages`, `intent`, `result`

### Exercises
- Add a 3rd branch (e.g., “summarize”)
- Add a “fallback” branch when intent is unknown

---

## Lab 06 — Structured output node (minutes extraction)

### Goal
Reuse your Lab 02 schema, but implement extraction as a LangGraph node with validation and retries.

### New concepts
- Node returns validated structured data into state
- Retry strategy on schema validation errors

### Suggested graph
```
START -> extract_minutes_structured -> END
```
(Yes: still simple, but now it’s a reusable node in bigger graphs.)

### Deliverable
- `lab_06_structured_minutes_graph.py`
- `MinutesSchema` (Pydantic) used inside node

### Exercises
- Add 1–2 new schema fields (`attendees`, `risks`)
- Add “repair prompt” retry when validation fails

---

## Lab 07 — Tools inside LangGraph (minutes pipeline)

### Goal
Move the minutes pipeline into a graph that uses tools for list/read/write.

### New concepts
- Tool nodes (safe I/O)
- Per-file processing pattern (loop/subgraph)
- Observability: show tool calls, store run logs

### Suggested graph (high level)
```
START -> list_files -> (for each file: read -> extract -> write) -> END
```

### Deliverables
- `lab_07_minutes_tools_graph.py`
- A `minutes/run_log.jsonl` with per-file outcomes

### Exercises
- Enforce filesystem allowlist in tools
- Add a summary report at the end (files processed, failures)

---

## Wrap-up & bridge to Session 3

Session 2 ends with:  
✅ You can build workflow graphs with routing, structured nodes, and tools.

In Session 3 you’ll make it *agentic*:
- loops (until success / max iters)
- reflection and self-correction
- a full **coding agent** that writes code and iterates until tests pass
