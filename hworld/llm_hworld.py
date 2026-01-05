from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

local_llm = ChatOpenAI(
    model="Ministral-3B-Instruct",  # Replace with your desired model
    base_url="http://localhost:8090/v1",  # Replace with your custom URL
    api_key="NONE",  # You can also pass the API key here
    timeout=10,
)


HELLO_PROMPT = "Hello, world! Please respond with a friendly greeting."


def run_prompt(prompt: str) -> str:
    """Send the prompt to the configured ChatOpenAI instance and return the text."""

    response = local_llm.invoke([HumanMessage(content=prompt)])
    if not response.text:
        raise RuntimeError("LLM returned no generations")
    return response.text


def main() -> None:
    """Emit the hello prompt and print the LLM response."""

    print("Prompt:", HELLO_PROMPT)
    try:
        reply = run_prompt(HELLO_PROMPT)
    except Exception as exc:  # pragma: no cover - best effort script
        print("Failed to get a response from the LLM:", exc)
        return
    print("Response:", reply)


if __name__ == "__main__":
    main()

