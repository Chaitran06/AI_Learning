"""
Simulates the test cases with scripted user inputs and forced cook/serve outcomes.
The LLM (Groq) is called for real, so GROQ_API_KEY must be set.
"""

import restaurant


def scripted(values, label):
    values = list(values)

    def next_value(*_):
        if not values:
            raise RuntimeError(f"{label}: ran out of scripted values")
        value = values.pop(0)
        if label == "input":
            print(f"\nYou: {value}")
        return value

    return next_value, values


def run_case(name, user_inputs, cook_results, serve_results, expected_result, expected_path):
    print("\n" + "=" * 70 + f"\n{name}\n" + "=" * 70)
    restaurant.get_user_input, inputs_left = scripted(user_inputs, "input")
    restaurant.cook_outcome, cooks_left = scripted(cook_results, "cook")
    restaurant.serve_outcome, serves_left = scripted(serve_results, "serve")

    path = []
    final_result = None
    for step in restaurant.graph.stream(
        restaurant.initial_state(), {"recursion_limit": 100}, stream_mode="updates"
    ):
        for node, update in step.items():
            path.append(node)
            if update and "final_result" in update:
                final_result = update["final_result"]

    checks = {
        "final_result": final_result == expected_result,
        "node path": path == expected_path,
        "all inputs used": not inputs_left and not cooks_left and not serves_left,
    }
    print(f"\nPath: {' -> '.join(path)}")
    print(f"Final result: {final_result} (expected {expected_result})")
    for check, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {check}")
    passed = all(checks.values())
    print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return passed


CASES = [
    dict(
        name="TC1: unrelated -> partial (reject) -> not available -> END (order retries exhausted)",
        user_inputs=[
            "What is the capital of France?",
            "I want 6 gulab jamun",          # only 3 available -> PARTIAL
            "no",                            # reject partial
            "Give me 2 pizzas",              # not on menu -> NOT_AVAILABLE
        ],
        cook_results=[],
        serve_results=[],
        expected_result="FAILED",
        expected_path=["take_order", "take_order", "order_confirm", "partial_decision",
                       "take_order", "order_confirm", "order_failed"],
    ),
    dict(
        name="TC2: available -> cook fail, cook ok -> serve fail -> cook ok -> serve ok -> COMPLETE",
        user_inputs=["I'd like 2 chicken biryani please"],
        cook_results=[False, True, True],
        serve_results=[False, True],
        expected_result="COMPLETED",
        expected_path=["take_order", "order_confirm", "cook", "cook_retry", "cook", "serve",
                       "cook_retry", "cook", "serve", "complete"],
    ),
    dict(
        name="TC3: partial (reject) -> available -> cook fail, ok -> serve fail -> cook ok -> serve fail -> FAIL",
        user_inputs=[
            "8 paneer butter masala",        # only 5 available -> PARTIAL
            "no",
            "3 masala dosa",                 # available
        ],
        cook_results=[False, True, True],
        serve_results=[False, False],
        expected_result="FAILED",
        expected_path=["take_order", "order_confirm", "partial_decision", "take_order",
                       "order_confirm", "cook", "cook_retry", "cook", "serve", "cook_retry",
                       "cook", "serve", "apology"],
    ),
]


if __name__ == "__main__":
    results = {case["name"].split(":")[0]: run_case(**case) for case in CASES}
    print("\n" + "=" * 70 + "\nSUMMARY")
    for name, ok in results.items():
        print(f"  {name}: {'PASS' if ok else 'FAIL'}")
