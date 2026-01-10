# Session 3 — Agentic Graphs: Loops, Reflection, and a Full Coding Agent Capstone

Session 3 turns “workflow graphs” into **agents** by adding:
- loops
- termination conditions
- reflection/self-correction
- tool-driven evaluation (tests)

The capstone is a full coding agent:
> Given a problem statement + tests, write code, run tests, fix failures, repeat until PASS.

---

## Learning objectives

By the end of Session 3, participants can:
- Implement **looping LangGraphs** with max-iteration safety
- Use a plan/act/reflect pattern to drive decisions
- Connect tools that “evaluate reality” (compile/run/pytest)
- Build an agent that iterates using error output as feedback until tests pass
- Add basic hardening: timeouts, allowlists, budgets, run logs

---

## Prerequisites

- Completed Session 2 (Labs 05–07)
- Packages:
  - `pip install langgraph langchain-openai langchain-core pytest pydantic`

---

## Agenda (recommended)

- 0:00–0:10 — Agentic mental model: loop + tools + termination
- 0:10–0:45 — Lab 08: Generic agent loop pattern (plan → act → reflect)
- 0:45–1:40 — Lab 09: Capstone coding agent (problem + tests → PASS)
- 1:40–2:00 — Lab 10: Hardening + observability (timeouts, budgets, HITL optional)

---

## Lab 08 — Agent loop pattern (plan → act → reflect)

### Goal
Build a reusable looping graph pattern with a termination condition.

### State (suggested)
- `messages`
- `iteration`, `max_iters`
- `plan`, `next_action`
- `last_tool_output`
- `done: bool`

### Suggested graph
```
START -> planner -> executor -> reflector
                     ^            |
                     |            |
                     +----(not done)---
                          (done) -> END
```

### Deliverable
- `lab_08_agent_loop_pattern.py`

### Exercises
- Add `max_iters` stop
- Add “stop early” rule if confidence is high

---

## Lab 09 — Capstone: Full coding agent (problem + tests → PASS)

### Goal
Create an agent that:
1) reads a problem statement + tests
2) writes `solution.py`
3) runs tests (pytest)
4) if fail, uses errors to patch code
5) repeats until tests pass (or max iters)

### Workspace layout (suggested)
```
coding_agent_workspace/
  problem.md
  solution.py
  tests/
    test_solution.py
  run_log.jsonl
```

### Tools (suggested)
- `read_file(path)`
- `write_file(path, content)`
- `run_pytest(workdir)` → `{exit_code, stdout, stderr}`
- Optional: `py_compile(path)` for quick syntax checks

### Termination rules
- PASS when pytest exit_code == 0
- FAIL when:
  - `iteration >= max_iters`, or
  - tool returns fatal error (timeout, unsafe path)

### Deliverables
- `lab_09_coding_agent.py`
- `coding_agent_workspace/` template + sample problems/tests
- `run_log.jsonl` that captures each iteration

### Exercises
- Add “patch mode” (LLM returns a diff) vs full rewrite
- Add a “report” output: what changed each iteration and why

---

## Lab 10 — Hardening & production touches

### Goal
Make the agent safer and easier to debug.

### Improvements (choose 3–5)
- File allowlist enforcement (only workspace dir)
- Timeouts for tests
- Token budget per iteration
- Save artifacts: final solution, last failing output, trace log
- Optional human-in-the-loop: “approve before writing code”

### Deliverable
- `lab_10_agent_hardening.py` (or upgrades integrated into Lab 09)

---

## Wrap-up

Session 3 ends with a working, tool-evaluated agent loop.

From here, next natural topics are:
- multi-agent patterns (planner + executor separation)
- parallel tool execution / batching
- retrieval (RAG) nodes inside graphs
- deployment patterns and monitoring
