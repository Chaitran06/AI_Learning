import os
import sys
import ast
import json
import operator

from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

MODEL = "openai/gpt-oss-120b"

groq_client = Groq(api_key=GROQ_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


# ---------------- Tool 1: Web Search ----------------
def web_search(query: str) -> str:
    """Search the web using Tavily and return a short answer with sources."""
    try:
        response = tavily_client.search(query=query, include_answer=True, max_results=3)
    except Exception as e:
        return f"Web search failed: {e}"

    answer = response.get("answer") or "No direct answer found."
    sources = "\n".join(
        f"- {r['title']}: {r['content'][:300]} ({r['url']})"
        for r in response.get("results", [])
    )
    return f"Answer: {answer}\n\nSources:\n{sources}"


# ---------------- Tool 2: Calculator ----------------
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("Unsupported expression")


def calculate(expression: str) -> str:
    """Safely evaluate a basic math expression like '2*2' or '(10+5)/3'."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_evaluate(tree.body))
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


# ---------------- Tools schema ----------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information, facts, news, or anything the model does not know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, e.g. 'Who won the latest cricket world cup?'",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a basic math expression using +, -, *, /, //, %, ** and parentheses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The math expression to evaluate, e.g. '2*2' or '(15+5)/4'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]

available_functions = {
    "web_search": web_search,
    "calculate": calculate,
}


# ---------------- Agent ----------------
def run_agent(user_input: str, max_steps: int = 5) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use the web_search tool for questions that need "
                "up-to-date or factual information, and the calculate tool for any math. "
                "Answer directly if no tool is needed."
            ),
        },
        {"role": "user", "content": user_input},
    ]

    for _ in range(max_steps):
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        message = response.choices[0].message

        # No tool call -> final answer
        if not message.tool_calls:
            return message.content

        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message.tool_calls
                ],
            }
        )

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")
            print(f"[Tool call] {name}({args})")

            func = available_functions.get(name)
            result = func(**args) if func else f"Unknown tool: {name}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return "Stopped: reached the maximum number of steps."


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # avoid UnicodeEncodeError on Windows consoles
    user_input = input("Ask me anything: ")
    print("\n" + run_agent(user_input))
