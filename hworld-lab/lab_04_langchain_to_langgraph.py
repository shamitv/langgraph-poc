"""
lab_04_langchain_to_langgraph.py — Component 4: LangChain → LangGraph (Single-node Graph)

Goal
----
Show that a LangGraph workflow is just "Python functions (nodes) + edges + state",
and that the *same* LLM call you used in Lab 1 becomes a node inside a graph.

What you’ll do in this script
-----------------------------
1) Call the model once using the Lab 1 (LangChain) style: llm.invoke(messages)
2) Call the model again using a single-node LangGraph:
   - State contains messages
   - Node calls llm.invoke(state["messages"])
   - Graph returns updated state

Prereqs (install once)
----------------------
pip install langgraph langchain-openai langchain-core

Run
---
python lab_04_langchain_to_langgraph.py

Optional env vars (same as Lab 1)
---------------------------------
MODEL      : model name (default: "Ministral-3B-Instruct")
BASE_URL   : OpenAI-compatible endpoint (default: "http://localhost:8090/v1")
API_KEY    : API key for local server (default: "NONE")
OPENAI_API_KEY : OpenAI key (fallback if API_KEY not set)
TEMP       : temperature (default: 0)

Tip
---
- For OpenAI, you can set:
    OPENAI_API_KEY=...
    BASE_URL=https://api.openai.com/v1
- For local servers, API_KEY can often be "NONE".
"""

from __future__ import annotations

import os
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

# LangGraph imports:
# - StateGraph builds a directed graph around a typed state object
# - END is the special terminal marker for the end of a run
from langgraph.graph import END, StateGraph

# add_messages is a reducer: it appends new messages returned by a node
# into the state's message list (rather than replacing it).
from langgraph.graph.message import add_messages


# ----------------------------
# 1) Define graph "state"
# ----------------------------
class GraphState(TypedDict):
    """
    The state that flows through the graph.

    We store a message history under the key "messages".
    The add_messages reducer means:
      - If a node returns {"messages": [<new_message>]}
      - LangGraph will append that to the existing state["messages"] list.
    """
    messages: Annotated[list[BaseMessage], add_messages]


def read_config() -> tuple[str, str | None, str, float]:
    """
    Reads env-driven config (same idea as Lab 1).
    Returns: (model, base_url_or_none, api_key, temperature)
    """
    model = os.getenv("MODEL", "Ministral-3B-Instruct")

    # Allow BASE_URL to be omitted/empty (useful if someone wants SDK defaults)
    base_url_env = os.getenv("BASE_URL", "http://localhost:8090/v1").strip()
    base_url = base_url_env or None

    # Support both API_KEY (local) and OPENAI_API_KEY (OpenAI)
    api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or "NONE"

    try:
        temperature = float(os.getenv("TEMP", "0"))
    except ValueError:
        temperature = 0.0

    return model, base_url, api_key, temperature


def make_llm(model: str, base_url: str | None, api_key: str, temperature: float) -> ChatOpenAI:
    """
    Create the chat model wrapper.

    Note: We pass base_url + api_key to keep things consistent with earlier labs.
    If base_url is None, we omit it so ChatOpenAI can use its default endpoint.
    """
    kwargs: dict[str, object] = {
        "model": model,
        "temperature": temperature,
        "timeout": 120,
    }
    if base_url is not None:
        kwargs["base_url"] = base_url
    if api_key is not None:
        kwargs["api_key"] = api_key

    return ChatOpenAI(**kwargs)


def build_messages() -> list[BaseMessage]:
    """
    Build the same kind of system + user messages as Lab 1.
    """
    system_prompt = (
        "You are a helpful assistant. "
        "Keep answers short and clear unless asked for more detail."
    )
    user_prompt = (
        "Hello! In one sentence, explain what an LLM is, then give one practical example."
    )

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]


# ----------------------------
# 2) LangChain-style call (baseline)
# ----------------------------
def run_langchain(llm: ChatOpenAI, messages: list[BaseMessage]) -> str:
    """
    This is the Lab 1 call pattern: directly invoke the model with messages.
    """
    response = llm.invoke(messages)
    return response.content


# ----------------------------
# 3) LangGraph-style call (single-node graph)
# ----------------------------
def build_single_node_graph(llm: ChatOpenAI):
    """
    Create a single-node LangGraph workflow that calls the LLM.

    Node contract:
      - input: GraphState (has "messages")
      - output: partial GraphState update (returns {"messages": [assistant_message]})
    """

    def llm_node(state: GraphState) -> GraphState:
        # The node receives the current state (including message history).
        # We call the LLM using that history and return the assistant message.
        assistant_msg = llm.invoke(state["messages"])
        return {"messages": [assistant_msg]}

    builder = StateGraph(GraphState)

    # Add exactly one node.
    builder.add_node("call_llm", llm_node)

    # Start the graph at that node and end immediately after.
    builder.set_entry_point("call_llm")
    builder.add_edge("call_llm", END)

    return builder.compile()


def run_langgraph(llm: ChatOpenAI, messages: list[BaseMessage]) -> str:
    """
    Run the single-node graph and return the assistant response text.
    """
    graph = build_single_node_graph(llm)

    # Graph input must match the state schema (GraphState).
    result_state: GraphState = graph.invoke({"messages": messages})

    # After the run, result_state["messages"] includes:
    # [SystemMessage, HumanMessage, AIMessage]
    final_msg = result_state["messages"][-1]
    return getattr(final_msg, "content", str(final_msg))


def main() -> None:
    # 1) Read config and create LLM client
    model, base_url, api_key, temperature = read_config()
    llm = make_llm(model=model, base_url=base_url, api_key=api_key, temperature=temperature)

    # 2) Build prompts/messages (same as Lab 1)
    messages = build_messages()
    user_prompt = messages[-1].content  # last message is the HumanMessage

    print("\n=== CONFIG ===")
    print(f"model     : {model}")
    print(f"base_url  : {base_url if base_url else '(default)'}")
    print(f"temp      : {temperature}")
    # We intentionally do NOT print api_key for security

    print("\n=== PROMPT ===")
    print(user_prompt)

    # 3) Run LangChain baseline
    print("\n=== LANGCHAIN (Lab 1 style) ===")
    try:
        lc_text = run_langchain(llm, messages)
        print(lc_text)
    except Exception as e:
        print("ERROR: LangChain call failed.")
        print(f"details: {e}")

    # 4) Run LangGraph single-node
    print("\n=== LANGGRAPH (Single-node graph) ===")
    try:
        lg_text = run_langgraph(llm, messages)
        print(lg_text)
    except Exception as e:
        print("ERROR: LangGraph run failed.")
        print("Common causes: missing 'langgraph' install, import errors, or endpoint issues.")
        print(f"details: {e}")

    print("\nDone. Next step: turn this into a multi-node graph (routing, tools, retries).")


if __name__ == "__main__":
    main()
