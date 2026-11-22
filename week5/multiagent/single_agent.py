"""
Single-agent system: one LLM with two tools (web_search + calculator).
The LLM decides which tools to call and how many times, up to MAX_ATTEMPTS rounds.
"""

from common import (
    CALCULATOR_TOOL,
    MAX_ATTEMPTS,
    SEARCH_TOOL,
    TokenTracker,
    assistant_to_dict,
    chat,
    force_final_answer,
    run_tool,
)

SYSTEM_PROMPT = """You are a helpful research assistant with two tools:
- web_search: look up facts you don't know or that may have changed.
- calculator: do ALL arithmetic with this tool, never compute in your head.
Call tools as many times as needed. You have at most 5 rounds, so when several lookups or
calculations are independent, request them together in the same turn. When you have everything, give a concise final answer
that shows the key facts (with sources/years) and the computed numbers."""


def ask_llm(query: str, tracker: TokenTracker, verbose: bool = True) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    tools = [SEARCH_TOOL, CALCULATOR_TOOL]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        msg = chat(messages, tracker, agent="single", tools=tools)
        messages.append(assistant_to_dict(msg))

        if not msg.tool_calls:
            return msg.content

        for tc in msg.tool_calls:
            result = run_tool(tc)
            if verbose:
                print(f"  [attempt {attempt}] {tc.function.name}({tc.function.arguments}) -> {result[:120]!r}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    # Out of attempts: ask for a final answer with no tools.
    return force_final_answer(messages, tracker, "single", "Max attempts reached. Give your best final answer now.")


if __name__ == "__main__":
    from test_query import TEST_QUERY

    tracker = TokenTracker()
    print(f"QUERY: {TEST_QUERY}\n")
    print("FINAL ANSWER:\n" + ask_llm(TEST_QUERY, tracker))
    tracker.report("single agent")
