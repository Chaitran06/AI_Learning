"""Run both systems on the same query and compare token usage."""

from common import TokenTracker
from multi_agent import NOTES_FILE, ask_manager_llm
from single_agent import ask_llm
from test_query import TEST_QUERY


def main():
    print(f"QUERY:\n{TEST_QUERY}\n")

    print("=" * 70 + "\nSINGLE AGENT\n" + "=" * 70)
    single = TokenTracker()
    print("\nFINAL ANSWER:\n" + ask_llm(TEST_QUERY, single))
    single.report("single agent")

    print("\n" + "=" * 70 + "\nMULTI AGENT\n" + "=" * 70)
    multi = TokenTracker()
    print("\nFINAL ANSWER:\n" + ask_manager_llm(TEST_QUERY, multi))
    multi.report("multi agent")
    print(f"(manager notes: {NOTES_FILE.name})")

    s, m = single.total(), multi.total()
    print("\n" + "=" * 70 + "\nCOMPARISON\n" + "=" * 70)
    print(f"{'':<14}{'LLM calls':>10}{'prompt':>10}{'completion':>12}{'total':>10}")
    for name, t in (("single agent", s), ("multi agent", m)):
        print(f"{name:<14}{t['calls']:>10}{t['prompt']:>10}{t['completion']:>12}{t['total']:>10}")
    if s["total"] and m["total"]:
        more, less = ("multi", "single") if m["total"] > s["total"] else ("single", "multi")
        ratio = max(s["total"], m["total"]) / min(s["total"], m["total"])
        print(f"\n=> The {more}-agent system used {ratio:.2f}x the tokens of the {less}-agent system.")


if __name__ == "__main__":
    main()
