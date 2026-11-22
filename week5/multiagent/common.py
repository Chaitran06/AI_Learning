"""
Shared building blocks for both systems:
  - Groq client + token tracking
  - Tool 1: web search (Tavily)
  - Tool 2: python calculator (safe AST evaluator)
  - Tool schemas in OpenAI/Groq function-calling format
"""

import ast
import json
import math
import operator
import os
from collections import defaultdict

from dotenv import find_dotenv, load_dotenv
from groq import Groq
from tavily import TavilyClient

load_dotenv(find_dotenv(usecwd=True) or find_dotenv())

MODEL = "openai/gpt-oss-120b"
MAX_ATTEMPTS = 5

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# ----------------------------------------------------------------------------
# Token tracking
# ----------------------------------------------------------------------------
class TokenTracker:
    """Accumulates token usage per agent (e.g. 'single', 'manager', 'search', 'math')."""

    def __init__(self):
        self.usage = defaultdict(lambda: {"prompt": 0, "completion": 0, "total": 0, "calls": 0})

    def add(self, agent: str, usage) -> None:
        if usage is None:
            return
        u = self.usage[agent]
        u["prompt"] += usage.prompt_tokens
        u["completion"] += usage.completion_tokens
        u["total"] += usage.total_tokens
        u["calls"] += 1

    def total(self) -> dict:
        t = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}
        for u in self.usage.values():
            for k in t:
                t[k] += u[k]
        return t

    def report(self, title: str) -> None:
        print(f"\n--- Token usage: {title} ---")
        print(f"{'agent':<10}{'calls':>7}{'prompt':>10}{'completion':>12}{'total':>10}")
        for agent, u in self.usage.items():
            print(f"{agent:<10}{u['calls']:>7}{u['prompt']:>10}{u['completion']:>12}{u['total']:>10}")
        t = self.total()
        print(f"{'TOTAL':<10}{t['calls']:>7}{t['prompt']:>10}{t['completion']:>12}{t['total']:>10}")


def chat(messages, tracker: TokenTracker, agent: str, tools=None):
    """One call to the Groq LLM. Records token usage under `agent`."""
    kwargs = {"model": MODEL, "messages": messages, "temperature": 0}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    response = groq_client.chat.completions.create(**kwargs)
    tracker.add(agent, response.usage)
    return response.choices[0].message


def force_final_answer(messages, tracker: TokenTracker, agent: str, instruction: str) -> str:
    """
    Called when max attempts are used up. The history contains tool calls, and
    Groq rejects a no-tools request whose model still tries to call a tool, so we
    flatten the whole history to plain text and ask for a final answer.
    """
    system = messages[0]["content"]
    transcript = []
    for m in messages[1:]:
        if m["role"] == "assistant" and m.get("tool_calls"):
            for tc in m["tool_calls"]:
                transcript.append(f"CALLED {tc['function']['name']}({tc['function']['arguments']})")
        elif m["content"]:
            transcript.append(f"{m['role'].upper()}: {m['content']}")
    flat = [
        {"role": "system", "content": system + "\nYou can no longer use tools."},
        {"role": "user", "content": "\n".join(transcript) + f"\n\n{instruction}"},
    ]
    try:
        return chat(flat, tracker, agent).content
    except Exception as e:
        return f"(could not produce final answer: {e})"


def assistant_to_dict(msg) -> dict:
    """Convert a Groq assistant message into a plain dict for the history."""
    d = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    return d


# ----------------------------------------------------------------------------
# Tool 1: web search
# ----------------------------------------------------------------------------
def web_search(query: str) -> str:
    """Search the web with Tavily. Returns a short answer + trimmed sources."""
    try:
        res = tavily_client.search(query=query, max_results=3, include_answer=True)
    except Exception as e:
        return f"Search error: {e}"
    lines = []
    if res.get("answer"):
        lines.append(f"Answer: {res['answer']}")
    for r in res.get("results", []):
        lines.append(f"- {r.get('title')}: {r.get('content', '')[:300]}")
    return "\n".join(lines) or "No results."


# ----------------------------------------------------------------------------
# Tool 2: python calculator (safe - no arbitrary code execution)
# ----------------------------------------------------------------------------
_OPS = {
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
_FUNCS = {
    name: getattr(math, name)
    for name in ("sqrt", "log", "log10", "log2", "exp", "sin", "cos", "tan", "floor", "ceil", "factorial")
}
_FUNCS.update({"abs": abs, "round": round, "min": min, "max": max})
_CONSTS = {"pi": math.pi, "e": math.e}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Name) and node.id in _CONSTS:
        return _CONSTS[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def calculator(expression: str) -> str:
    """Evaluate a math expression like '(1.5e6 / 3) ** 0.5 + round(2.345, 2)'."""
    try:
        return str(_eval(ast.parse(expression, mode="eval")))
    except Exception as e:
        return f"Calculator error: {e}"


# ----------------------------------------------------------------------------
# Tool schemas + dispatcher
# ----------------------------------------------------------------------------
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for up-to-date facts (populations, prices, dates, statistics...).",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query."}},
            "required": ["query"],
        },
    },
}

CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluate a single Python math expression. Supports + - * / // % **, "
            "sqrt, log, log10, exp, sin, cos, tan, floor, ceil, abs, round, min, max, pi, e. "
            "Use plain numbers without commas, e.g. '1428000000 / 125000000'."
        ),
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "The math expression."}},
            "required": ["expression"],
        },
    },
}

TOOL_FUNCTIONS = {"web_search": web_search, "calculator": calculator}


def run_tool(tool_call) -> str:
    """Execute a tool call from the LLM and return its string output."""
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError:
        return f"Error: invalid JSON arguments for {name}"
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return f"Error: unknown tool {name}"
    try:
        return fn(**args)
    except TypeError as e:
        return f"Error: bad arguments for {name}: {e}"
