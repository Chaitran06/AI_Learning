"""
Simple coding agent that fixes small bugs in the files under ./playground.

Flow:
  1. Ask the user to describe the bug in plain English.
  2. The LLM (Groq) calls tools in a loop:
       - search_files   -> which files are related to the bug
       - search_in_file -> which line numbers are related to the bug
       - replace_line   -> replace one line with a new line
  3. When the LLM says it is done, we check the result (it must have edited
     something, and C++ files must still compile if g++ is available).
  4. If the attempt failed, we retry (max 3 attempts). After that we print
     "Cannot solve the bug".

No LangGraph - just a plain Python loop.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from groq import Groq

load_dotenv(find_dotenv(usecwd=True) or find_dotenv())

MODEL = "openai/gpt-oss-120b"
MAX_ATTEMPTS = 3          # max retries for solving the bug
MAX_STEPS_PER_ATTEMPT = 10  # max LLM calls inside a single attempt
CONTEXT_LINES = 3         # lines shown around each match in search_in_file

BASE_DIR = Path(__file__).parent
WORKSPACE = BASE_DIR / "playground"
SOURCE_EXTENSIONS = {".cpp", ".cc", ".c", ".h", ".hpp"}

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ----------------------------------------------------------------------------
# Pretty printing helpers
# ----------------------------------------------------------------------------
def banner(text: str) -> None:
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def log(tag: str, text: str) -> None:
    print(f"[{tag}] {text}")


# ----------------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------------
def list_source_files() -> list[Path]:
    return sorted(p for p in WORKSPACE.rglob("*") if p.is_file() and p.suffix in SOURCE_EXTENSIONS)


def resolve_path(path: str) -> Path | None:
    """Turn a path given by the LLM into a real file inside the workspace."""
    candidate = (WORKSPACE / path).resolve()
    if not candidate.is_file():
        # The LLM may pass just the file name
        matches = [p for p in list_source_files() if p.name == Path(path).name]
        if not matches:
            return None
        candidate = matches[0].resolve()
    if WORKSPACE.resolve() not in candidate.parents:
        return None  # never touch files outside the workspace
    return candidate


def search_files(keywords: list[str]) -> str:
    """List files whose name or content contains any of the keywords."""
    files = list_source_files()
    if not files:
        return "No source files found in the workspace."

    results = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore").lower()
        hits = {k: text.count(k.lower()) + f.name.lower().count(k.lower()) for k in keywords}
        hits = {k: n for k, n in hits.items() if n > 0}
        if hits:
            results.append(f"{f.relative_to(WORKSPACE).as_posix()}  (matches: {hits})")

    all_files = ", ".join(f.relative_to(WORKSPACE).as_posix() for f in files)
    if not results:
        return f"No file matched {keywords}. All source files: {all_files}"
    return "Related files:\n" + "\n".join(results)


def search_in_file(path: str, keyword: str) -> str:
    """Return line numbers (with surrounding context) where keyword appears."""
    f = resolve_path(path)
    if f is None:
        return f"File '{path}' not found in workspace."

    lines = f.read_text(encoding="utf-8").splitlines()
    match_idx = [i for i, line in enumerate(lines) if keyword.lower() in line.lower()]
    if not match_idx:
        return f"'{keyword}' not found in {path}."

    # Collect matches plus some context so the LLM can see the surrounding code
    show = set()
    for i in match_idx:
        show.update(range(max(0, i - CONTEXT_LINES), min(len(lines), i + CONTEXT_LINES + 1)))

    out, prev = [], None
    for i in sorted(show):
        if prev is not None and i != prev + 1:
            out.append("   ...")
        marker = ">>" if i in match_idx else "  "
        out.append(f"{marker} {i + 1:4d}: {lines[i]}")
        prev = i
    return f"Matches for '{keyword}' in {path} (>> = matching line):\n" + "\n".join(out)


def replace_line(path: str, line_number: int, new_line: str) -> str:
    """Replace a single line (1-based) with new_line."""
    f = resolve_path(path)
    if f is None:
        return f"File '{path}' not found in workspace."

    lines = f.read_text(encoding="utf-8").splitlines(keepends=True)
    if not 1 <= line_number <= len(lines):
        return f"Line {line_number} is out of range (file has {len(lines)} lines)."

    old = lines[line_number - 1]
    old_stripped = old.rstrip("\r\n")
    newline_char = old[len(old_stripped):] or "\n"

    # Keep original indentation if the LLM didn't provide any
    if new_line and not new_line[0].isspace():
        indent = old_stripped[: len(old_stripped) - len(old_stripped.lstrip())]
        new_line = indent + new_line

    lines[line_number - 1] = new_line.rstrip("\r\n") + newline_char
    f.write_text("".join(lines), encoding="utf-8")
    return f"Replaced line {line_number} in {path}.\n  old: {old_stripped}\n  new: {new_line.rstrip()}"


TOOL_FUNCTIONS = {
    "search_files": search_files,
    "search_in_file": search_in_file,
    "replace_line": replace_line,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Find source files in the project related to the bug. "
                           "Returns file paths whose name or content contains any of the keywords.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords related to the bug, e.g. function names or identifiers.",
                    }
                },
                "required": ["keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Search inside one file. Returns the line numbers where the keyword appears, "
                           "with a few lines of surrounding code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path as returned by search_files."},
                    "keyword": {"type": "string", "description": "Text to search for (case-insensitive)."},
                },
                "required": ["path", "keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "replace_line",
            "description": "Replace exactly one line in a file with a new line.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path as returned by search_files."},
                    "line_number": {"type": "integer", "description": "1-based line number to replace."},
                    "new_line": {"type": "string", "description": "The full new content of that line."},
                },
                "required": ["path", "line_number", "new_line"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a coding agent that fixes small bugs in C++ code.

You have three tools:
1. search_files(keywords)              -> find files related to the bug
2. search_in_file(path, keyword)       -> get line numbers + nearby code for a keyword
3. replace_line(path, line_number, new_line) -> replace one line with a corrected line

Work step by step:
- First use search_files to locate the relevant file(s).
- Then use search_in_file to find the exact buggy line(s) and read the surrounding code.
- Then use replace_line to fix each buggy line. Only change what is needed.
- Always check line numbers with search_in_file before replacing.

When you are finished, reply WITHOUT calling any tool, starting with exactly one of:
  STATUS: FIXED      - followed by a short explanation of the fix
  STATUS: NOT_FIXED  - followed by why you could not fix it
"""


# ----------------------------------------------------------------------------
# Verification
# ----------------------------------------------------------------------------
def compile_check() -> tuple[bool, str]:
    """Compile every .cpp file with g++ (if installed). Returns (ok, message)."""
    gpp = shutil.which("g++")
    if gpp is None:
        return True, "g++ not found, skipping compile check."
    for f in list_source_files():
        if f.suffix not in {".cpp", ".cc"}:
            continue
        proc = subprocess.run(
            [gpp, "-fsyntax-only", str(f)], capture_output=True, text=True
        )
        if proc.returncode != 0:
            return False, f"Compilation failed for {f.name}:\n{proc.stderr.strip()[:1500]}"
    return True, "All C++ files compile successfully."


# ----------------------------------------------------------------------------
# Agent loop
# ----------------------------------------------------------------------------
def run_attempt(messages: list, attempt: int) -> tuple[bool, str]:
    """Run one attempt. Returns (success, reason). Mutates messages."""
    edits_made = 0

    for step in range(1, MAX_STEPS_PER_ATTEMPT + 1):
        log(f"Attempt {attempt} | Step {step}", "Asking the LLM what to do next...")
        try:
            response = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto"
            )
        except Exception as e:
            return False, f"LLM call failed: {e}"

        msg = response.choices[0].message

        # ---- LLM wants to call tools ----
        if msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                print(f"\n  >>> TOOL CALLED: {name}")
                print(f"      arguments : {json.dumps(args)}")

                func = TOOL_FUNCTIONS.get(name)
                if func is None:
                    result = f"Unknown tool '{name}'."
                else:
                    try:
                        result = func(**args)
                    except Exception as e:
                        result = f"Tool error: {e}"
                if name == "replace_line" and result.startswith("Replaced"):
                    edits_made += 1

                print("      result    :")
                for line in result.splitlines():
                    print(f"        {line}")
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        # ---- LLM gave its final answer ----
        answer = (msg.content or "").strip()
        messages.append({"role": "assistant", "content": answer})
        print(f"\n[LLM final answer]\n{answer}\n")

        if "STATUS: FIXED" not in answer:
            return False, "The LLM reported that it could not fix the bug."
        if edits_made == 0:
            return False, "The LLM said FIXED but did not change any line."

        log("Verify", "Running compile check...")
        ok, info = compile_check()
        log("Verify", info)
        if not ok:
            return False, info
        return True, answer

    return False, f"Reached max steps ({MAX_STEPS_PER_ATTEMPT}) without finishing."


def solve(bug: str) -> None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Bug report: {bug}"},
    ]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        banner(f"ATTEMPT {attempt} of {MAX_ATTEMPTS}")
        success, reason = run_attempt(messages, attempt)
        if success:
            banner(f"Bug solved in attempt {attempt}")
            return
        log("Attempt failed", reason)
        # Give the LLM feedback for the next attempt (same conversation)
        messages.append({
            "role": "user",
            "content": f"Your previous attempt failed: {reason}\n"
                       "Re-check the code with the tools and try again.",
        })

    banner("Cannot solve the bug")


def main():
    banner("Simple Coding Agent")
    print(f"Model     : {MODEL}")
    print(f"Workspace : {WORKSPACE}")
    print("Files     : " + ", ".join(p.name for p in list_source_files()))
    bug = input("\nDescribe your bug: ").strip()
    if not bug:
        print("No bug given. Exiting.")
        return
    solve(bug)


if __name__ == "__main__":
    main()
