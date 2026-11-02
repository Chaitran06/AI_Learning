"""
Restaurant Order Management System using LangGraph.

Flow:
    START -> take_order -> (unrelated / order) -> order_confirm
          -> CONFIRMED      -> cook
          -> PARTIAL        -> partial_decision -> cook (accept) / take_order (reject)
          -> NOT_AVAILABLE  -> take_order
    cook  -> READY -> serve | COOK_FAILED -> cook (retry) / apology
    serve -> COMPLETE -> complete | SERVE_FAILED -> cook (retry) / apology
    complete / apology / order retries exhausted -> END
"""

import json
import os
import random
from typing import Annotated, Callable, TypedDict

from dotenv import load_dotenv
from groq import Groq
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()

MODEL = "openai/gpt-oss-120b"
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# dish name -> quantity available in the kitchen
MENU = {
    "chicken biryani": 10,
    "paneer butter masala": 5,
    "masala dosa": 8,
    "butter naan": 20,
    "gulab jamun": 3,
    "veg fried rice": 0,
}

COOK_SUCCESS_PROB = 0.6
SERVE_SUCCESS_PROB = 0.6

# Hooks so the test scenarios can script user input and cook/serve outcomes.
# get_user_input(prompt) -> str
# cook_outcome() / serve_outcome() -> True for success, False for failure
get_user_input: Callable[[str], str] = input
cook_outcome: Callable[[], bool] = lambda: random.random() < COOK_SUCCESS_PROB
serve_outcome: Callable[[], bool] = lambda: random.random() < SERVE_SUCCESS_PROB


class OrderState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    dish_name: str
    required_quantity: int
    available_quantity: int
    status: str  # UNRELATED, CONFIRMED, PARTIAL, NOT_AVAILABLE, READY, COOK_FAILED, SERVE_FAILED, COMPLETE, FAILED
    order_retry: int
    cook_retry: int
    serve_retry: int
    final_result: str  # "" while running, then "COMPLETED" or "FAILED"


# ---------------- helpers ----------------

def ask_llm(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        **kwargs,
    )
    return response.choices[0].message.content.strip()


def assistant_says(text: str) -> AIMessage:
    print(f"\nAssistant: {text}")
    return AIMessage(content=text)


def state_summary(state: OrderState) -> str:
    return (
        f"dish={state['dish_name']}, required_quantity={state['required_quantity']}, "
        f"available_quantity={state['available_quantity']}, status={state['status']}, "
        f"order_retry={state['order_retry']}, cook_retry={state['cook_retry']}, "
        f"serve_retry={state['serve_retry']}"
    )


def llm_message(instruction: str, state: OrderState) -> str:
    """Let the LLM write the customer-facing message after reading the state."""
    return ask_llm(
        "You are a polite restaurant ordering assistant. Write a short (1-3 sentence) "
        "message to the customer. Do not invent facts beyond the state given.",
        f"Current order state: {state_summary(state)}\n\nTask: {instruction}",
    )


# ---------------- nodes ----------------

def take_order(state: OrderState) -> dict:
    user_text = get_user_input("\nYou: ")

    raw = ask_llm(
        "You extract food orders for a restaurant. "
        f"The menu is: {', '.join(MENU)}.\n"
        "Return JSON with keys: is_food_order (bool), dish_name (str), quantity (int).\n"
        "- If the message is not about ordering food, set is_food_order=false.\n"
        "- If the dish clearly refers to a menu item, use the exact menu name; "
        "otherwise return the dish name as the user wrote it (lowercase).\n"
        "- If no quantity is mentioned, use 1.",
        user_text,
        json_mode=True,
    )
    data = json.loads(raw)

    if not data.get("is_food_order"):
        order_retry = state["order_retry"] - 1
        reply = (
            "Sorry, I am not a general purpose assistant - I can only help you order food. "
            f"Please place a food order. (order attempts left: {order_retry})"
        )
        return {
            "messages": [HumanMessage(content=user_text), assistant_says(reply)],
            "status": "UNRELATED",
            "order_retry": order_retry,
        }

    return {
        "messages": [HumanMessage(content=user_text)],
        "dish_name": str(data.get("dish_name", "")).strip().lower(),
        "required_quantity": int(data.get("quantity", 1)),
        "status": "ORDER_RECEIVED",
    }


def order_confirm(state: OrderState) -> dict:
    available = MENU.get(state["dish_name"], 0)
    required = state["required_quantity"]

    if available >= required:
        status = "CONFIRMED"
    elif available > 0:
        status = "PARTIAL"
    else:
        status = "NOT_AVAILABLE"

    print(f"[order_confirm] {state['dish_name']} x{required} -> available {available} -> {status}")
    update = {"available_quantity": available, "status": status}

    if status == "NOT_AVAILABLE":
        update["order_retry"] = state["order_retry"] - 1
        new_state = {**state, **update}
        update["messages"] = [assistant_says(llm_message(
            "The dish is not available. Apologise and, if order_retry > 0, ask them to place "
            "a different order; if order_retry is 0, tell them no attempts are left.",
            new_state,
        ))]
    elif status == "CONFIRMED":
        update["messages"] = [assistant_says(llm_message(
            "Confirm the order and say it is being sent to the kitchen.", {**state, **update}
        ))]
    return update


def partial_decision(state: OrderState) -> dict:
    question = llm_message(
        "Only available_quantity of the requested dish is available. Ask the customer "
        "whether they want to accept the partial quantity (yes) or place a new order (no).",
        state,
    )
    msg = assistant_says(question)
    answer = get_user_input("\nYou (yes/no): ")

    if answer.strip().lower() in ("y", "yes", "ok", "okay", "sure", "accept"):
        return {
            "messages": [msg, HumanMessage(content=answer),
                         assistant_says(f"Great, going ahead with {state['available_quantity']} x {state['dish_name']}.")],
            "required_quantity": state["available_quantity"],
            "status": "CONFIRMED",
        }

    order_retry = state["order_retry"] - 1
    note = (f"Okay, please place a new order. (order attempts left: {order_retry})"
            if order_retry > 0 else "Okay. No order attempts are left.")
    return {
        "messages": [msg, HumanMessage(content=answer), assistant_says(note)],
        "status": "PARTIAL_REJECTED",
        "order_retry": order_retry,
    }


def cook(state: OrderState) -> dict:
    if cook_outcome():
        print("[cook] success -> READY")
        return {"status": "READY"}
    print(f"[cook] failed (cook retries left before this failure: {state['cook_retry']})")
    return {"status": "COOK_FAILED"}


def cook_retry(state: OrderState) -> dict:
    """Uses one cook retry (after a cook failure or a serve failure)."""
    print(f"[cook_retry] retrying cook, cook_retry {state['cook_retry']} -> {state['cook_retry'] - 1}")
    return {"cook_retry": state["cook_retry"] - 1}


def serve(state: OrderState) -> dict:
    if serve_outcome():
        print("[serve] success -> COMPLETE")
        return {"status": "COMPLETE"}
    serve_retry = state["serve_retry"] - 1
    print(f"[serve] failed, serve_retry {state['serve_retry']} -> {serve_retry}")
    return {"status": "SERVE_FAILED", "serve_retry": serve_retry}


def complete(state: OrderState) -> dict:
    text = llm_message("The order has been served. Tell the customer their order is complete.", state)
    return {"messages": [assistant_says(text)], "final_result": "COMPLETED"}


def apology(state: OrderState) -> dict:
    text = llm_message(
        "The order could not be fulfilled because the retries (cook_retry / serve_retry) are "
        "exhausted. Issue a sincere apology to the customer.",
        state,
    )
    return {"messages": [assistant_says(text)], "status": "FAILED", "final_result": "FAILED"}


def order_failed(state: OrderState) -> dict:
    print("[order_failed] order retries exhausted")
    return {"status": "FAILED", "final_result": "FAILED"}


# ---------------- routers (conditional edges) ----------------

def route_after_take_order(state: OrderState) -> str:
    if state["status"] == "UNRELATED":
        return "take_order" if state["order_retry"] > 0 else "order_failed"
    return "order_confirm"


def route_after_order_confirm(state: OrderState) -> str:
    if state["status"] == "CONFIRMED":
        return "cook"
    if state["status"] == "PARTIAL":
        return "partial_decision"
    return "take_order" if state["order_retry"] > 0 else "order_failed"


def route_after_partial(state: OrderState) -> str:
    if state["status"] == "CONFIRMED":
        return "cook"
    return "take_order" if state["order_retry"] > 0 else "order_failed"


def route_after_cook(state: OrderState) -> str:
    if state["status"] == "READY":
        return "serve"
    return "cook_retry" if state["cook_retry"] > 0 else "apology"


def route_after_serve(state: OrderState) -> str:
    if state["status"] == "COMPLETE":
        return "complete"
    if state["serve_retry"] <= 0:
        return "apology"
    # serve failed -> food must be cooked again, only if cook retries remain
    return "cook_retry" if state["cook_retry"] > 0 else "apology"


# ---------------- graph ----------------

def build_graph():
    builder = StateGraph(OrderState)
    builder.add_node("take_order", take_order)
    builder.add_node("order_confirm", order_confirm)
    builder.add_node("partial_decision", partial_decision)
    builder.add_node("cook", cook)
    builder.add_node("cook_retry", cook_retry)
    builder.add_node("serve", serve)
    builder.add_node("complete", complete)
    builder.add_node("apology", apology)
    builder.add_node("order_failed", order_failed)

    builder.add_edge(START, "take_order")
    builder.add_conditional_edges(
        "take_order", route_after_take_order,
        {"take_order": "take_order", "order_confirm": "order_confirm", "order_failed": "order_failed"},
    )
    builder.add_conditional_edges(
        "order_confirm", route_after_order_confirm,
        {"cook": "cook", "partial_decision": "partial_decision",
         "take_order": "take_order", "order_failed": "order_failed"},
    )
    builder.add_conditional_edges(
        "partial_decision", route_after_partial,
        {"cook": "cook", "take_order": "take_order", "order_failed": "order_failed"},
    )
    builder.add_conditional_edges(
        "cook", route_after_cook, {"serve": "serve", "cook_retry": "cook_retry", "apology": "apology"}
    )
    builder.add_edge("cook_retry", "cook")
    builder.add_conditional_edges(
        "serve", route_after_serve,
        {"complete": "complete", "cook_retry": "cook_retry", "apology": "apology"},
    )
    builder.add_edge("complete", END)
    builder.add_edge("apology", END)
    builder.add_edge("order_failed", END)
    return builder.compile()


def initial_state() -> OrderState:
    return {
        "messages": [],
        "dish_name": "",
        "required_quantity": 0,
        "available_quantity": 0,
        "status": "NEW",
        "order_retry": 3,
        "cook_retry": 2,
        "serve_retry": 2,
        "final_result": "",
    }


graph = build_graph()


if __name__ == "__main__":
    print("Welcome! Menu:")
    for dish, qty in MENU.items():
        print(f"  - {dish} (available: {qty})")
    print("Place your order (one dish + quantity).")

    result = graph.invoke(initial_state(), {"recursion_limit": 100})
    print(f"\nFINAL RESULT: {result['final_result']}  (status={result['status']})")
