"""
Multi-agent system (no LangGraph), three LLM roles:

  manager LLM      -> only decides which helper to use (and what to ask it).
                      Keeps a notes file with every helper response; the notes
                      are its only memory between rounds.
  ask_search_llm   -> helper with access to ONLY the web_search tool.
  ask_math_llm     -> helper with access to ONLY the calculator tool.
"""

import json
from datetime import datetime
from pathlib import Path

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

NOTES_FILE = Path(__file__).parent / "manager_notes.md"

# ----------------------------------------------------------------------------
# System prompts (the role of each LLM)
# ----------------------------------------------------------------------------
MANAGER_PROMPT = """You are a MANAGER. You never search or calculate yourself.
Your only job is to decide which helper to delegate the next step to:
- ask_search_llm: finds facts on the web (one clear fact-finding task per call).
- ask_math_llm: does arithmetic. Always include the exact numbers it needs in the task.
You are given the user's question and your NOTES (everything helpers have told you so far).
Read the notes, then delegate the next missing piece. Do not repeat work already in the notes.
You have at most 5 rounds: when tasks are independent, delegate them in the same turn.
When the notes contain everything needed, do NOT call a helper - write the final answer,
showing the key facts and computed numbers."""

SEARCH_PROMPT = """You are a SEARCH specialist. You have only the web_search tool.
Find the requested facts and reply with a short, precise summary: the numbers, their
units, the year/date and the source. Do not do any calculations."""

MATH_PROMPT = """You are a MATH specialist. You have only the calculator tool.
Use the calculator for every computation (never compute in your head) and reply with
the results and the expressions you evaluated. Do not look up facts."""

# Tools the manager can "call" = the helper LLMs
DELEGATE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": {"task": {"type": "string", "description": "Self-contained task for the helper."}},
                "required": ["task"],
            },
        },
    }
    for name, desc in [
        ("ask_search_llm", "Delegate a fact-finding / web search task to the search helper."),
        ("ask_math_llm", "Delegate a calculation to the math helper. Include all numbers needed."),
    ]
]


# ----------------------------------------------------------------------------
# Notes file
# ----------------------------------------------------------------------------
def init_notes(query: str) -> None:
    NOTES_FILE.write_text(f"# Manager notes\nStarted: {datetime.now():%Y-%m-%d %H:%M:%S}\nQuery: {query}\n", encoding="utf-8")


def append_note(helper: str, task: str, response: str) -> None:
    with NOTES_FILE.open("a", encoding="utf-8") as f:
        f.write(f"\n## {helper}\n**Task:** {task}\n**Response:** {response}\n")


def read_notes() -> str:
    text = NOTES_FILE.read_text(encoding="utf-8")
    # skip the header; only the helper entries matter to the manager
    entries = text.split("\n## ", 1)
    return ("## " + entries[1]) if len(entries) > 1 else "(no notes yet)"


# ----------------------------------------------------------------------------
# Helper LLMs - each is a small tool loop with its own restricted toolset
# ----------------------------------------------------------------------------
def _helper_loop(agent: str, system_prompt: str, tools: list, task: str, tracker: TokenTracker, verbose: bool) -> str:
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": task}]
    allowed = {t["function"]["name"] for t in tools}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        msg = chat(messages, tracker, agent=agent, tools=tools)
        messages.append(assistant_to_dict(msg))
        if not msg.tool_calls:
            return msg.content

        for tc in msg.tool_calls:
            if tc.function.name not in allowed:
                result = f"Error: you do not have access to {tc.function.name}."
            else:
                result = run_tool(tc)
            if verbose:
                print(f"      [{agent} {attempt}] {tc.function.name}({tc.function.arguments}) -> {result[:100]!r}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return force_final_answer(messages, tracker, agent, "Max attempts reached. Report what you have now.")


def ask_search_llm(task: str, tracker: TokenTracker, verbose: bool = True) -> str:
    return _helper_loop("search", SEARCH_PROMPT, [SEARCH_TOOL], task, tracker, verbose)


def ask_math_llm(task: str, tracker: TokenTracker, verbose: bool = True) -> str:
    return _helper_loop("math", MATH_PROMPT, [CALCULATOR_TOOL], task, tracker, verbose)


HELPERS = {"ask_search_llm": ask_search_llm, "ask_math_llm": ask_math_llm}


# ----------------------------------------------------------------------------
# Manager LLM
# ----------------------------------------------------------------------------
def ask_manager_llm(query: str, tracker: TokenTracker, verbose: bool = True) -> str:
    init_notes(query)

    def manager_messages():
        # Manager is stateless between rounds: its memory is the notes file.
        return [
            {"role": "system", "content": MANAGER_PROMPT},
            {"role": "user", "content": f"QUESTION:\n{query}\n\nNOTES:\n{read_notes()}"},
        ]

    for round_no in range(1, MAX_ATTEMPTS + 1):
        msg = chat(manager_messages(), tracker, agent="manager", tools=DELEGATE_TOOLS)
        if not msg.tool_calls:
            return msg.content

        for tc in msg.tool_calls:
            try:
                task = json.loads(tc.function.arguments or "{}").get("task", "")
            except json.JSONDecodeError:
                task = tc.function.arguments
            helper = HELPERS.get(tc.function.name)
            if verbose:
                print(f"  [manager {round_no}] -> {tc.function.name}: {task}")
            response = helper(task, tracker, verbose) if helper else f"Unknown helper {tc.function.name}"
            append_note(tc.function.name, task, response)

    # Out of rounds: final answer from notes, no more delegation.
    messages = manager_messages()
    messages.append({"role": "user", "content": "Max rounds reached. Give the final answer from your notes now."})
    return chat(messages, tracker, agent="manager").content


if __name__ == "__main__":
    from test_query import TEST_QUERY

    tracker = TokenTracker()
    print(f"QUERY: {TEST_QUERY}\n")
    print("FINAL ANSWER:\n" + ask_manager_llm(TEST_QUERY, tracker))
    tracker.report("multi agent")
    print(f"\nNotes saved to {NOTES_FILE}")
