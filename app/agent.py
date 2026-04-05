# app/agent.py

import os
from typing import TypedDict
from openai import OpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from app.mcp import run_mcp_tools

from app.guardrails import (
    guard_input,
    guard_llm_output,
    guard_structure,
    guard_code_safety,
    guard_test_result,
    guard_test_format   
)
from app.mcp import run_mcp_tools

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------
# STATE
# -------------------------
class AgentState(TypedDict):
    user_input: str
    response: str
    parsed: dict
    test_result: dict
    attempt: int
    error: str


# -------------------------
# LLM
# -------------------------
def build_messages(prompt: str):
    return [
        {
            "role": "system",
            "content": (
                "You are an expert Python debugging assistant.\n"
                "Return ONLY valid JSON (no text before/after).\n\n"

                "Format:\n"
                "{\n"
                '  "bug": "<short explanation>",\n'
                '  "fixed_code": "<corrected Python code>",\n'
                '  "test": "<unit test code>"\n'
                "}\n\n"

                "Rules:\n"
                "- Fix the root cause (not try/except)\n"
                "- Keep original behavior and function signature\n"
                "- Do NOT change return types\n"
                "- Return clean, runnable Python code\n"
                "- Ensure valid Python syntax\n"
                "- Return only the function (no print statements)\n\n"

                "Test Rules:\n"
                "- Use ONLY plain assert statements\n"
                "- Do NOT use unittest\n"
                "- Do NOT use pytest\n"
                "- Do NOT define classes\n"
                "- Do NOT call main()\n"
                "- The test must run with exec()\n"
                "- The test must FAIL if the fix is incorrect\n\n"

                "Example:\n"
                "Input:\n"
                "def f(): return 1/0\n\n"
                "Output:\n"
                "{\n"
                '  "bug": "Division by zero",\n'
                '  "fixed_code": "def f():\\n    raise ValueError(\\"invalid\\")",\n'
                '  "test": "try:\\n    f()\\n    assert False\\nexcept ValueError:\\n    assert True"\n'
                "}\n"
            )
        },
        {"role": "user", "content": prompt}
    ]


def generate_response(prompt: str):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=build_messages(prompt),
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM Error: {str(e)}"


# -------------------------
# EXECUTION
# -------------------------
def run_test(fixed_code: str, test_code: str):
    try:
        exec_globals = {}
        exec(fixed_code + "\n\n" + test_code, exec_globals)
        return {"status": "PASS"}
    except AssertionError:
        return {"status": "FAIL", "error": "Assertion failed"}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


# -------------------------
# NODES
# -------------------------

def input_node(state: AgentState):
    valid, error = guard_input(state["user_input"])
    if not valid:
        return {"error": error}
    return {}


def llm_node(state: AgentState):
    response = generate_response(state["user_input"])
    return {"response": response}


def parse_node(state: AgentState):
    ok, parsed = guard_llm_output(state["response"])
    if not ok:
        return {"error": "Invalid JSON"}
    return {"parsed": parsed}


def structure_node(state: AgentState):
    ok, error = guard_structure(state["parsed"])
    if not ok:
        return {"error": error}
    return {}


def code_node(state: AgentState):
    code = state["parsed"]["fixed_code"]

    ok, error = guard_code_safety(code)
    if not ok:
        return {"error": error}

    # MCP tools
    mcp_results = run_mcp_tools(code)

    # optional: fail if syntax invalid
    if mcp_results["syntax"]["status"] != "valid":
        return {
            "test_result": {
                "status": "FAIL",
                "error": "Invalid syntax"
            }
        }

    return {"mcp": mcp_results}


def test_node(state: AgentState):

    ok, error = guard_test_format(state["parsed"]["test"])
    if not ok:
        return {
            "test_result": {
                "status": "FAIL",
                "error": error
            }
        }

    test_result = run_test(
        state["parsed"]["fixed_code"],
        state["parsed"]["test"]
    )

    state["parsed"]["test_result"] = test_result
    return {"test_result": test_result}


def increment_node(state: AgentState):
    return {"attempt": state["attempt"] + 1}


# -------------------------
# ROUTER (retry logic)
# -------------------------
def router(state: AgentState):

    # max attempts FIRST (important!)
    if state.get("attempt", 0) >= 2:
        return "fail"

    if "test_result" not in state:
        return "retry"

    ok, _ = guard_test_result(state["test_result"])

    if ok:
        return "success"

    return "retry"


# -------------------------
# GRAPH
# -------------------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("input", input_node)
    graph.add_node("llm", llm_node)
    graph.add_node("parse", parse_node)
    graph.add_node("structure", structure_node)
    graph.add_node("code", code_node)
    graph.add_node("test", test_node)
    graph.add_node("increment", increment_node)

    graph.set_entry_point("input")

    graph.add_edge("input", "llm")
    graph.add_edge("llm", "parse")
    graph.add_edge("parse", "structure")
    graph.add_edge("structure", "code")
    graph.add_edge("code", "test")

    graph.add_conditional_edges(
        "test",
        router,
        {
            "success": END,
            "retry": "increment",
            "fail": END
        }
    )

    graph.add_edge("increment", "llm")

    return graph.compile()


graph = build_graph()


# -------------------------
# PUBLIC API (same name)
# -------------------------
def run_agent_pipeline(user_input: str):
    print("[LOG] Running agent pipeline...")

    result = graph.invoke({
        "user_input": user_input,
        "attempt": 0
    })

    if "parsed" in result:
        print("[LOG] Success")

        parsed = result["parsed"]

        # -------------------------
        # MCP validation
        # -------------------------
        if "fixed_code" in parsed:
            mcp_result = run_mcp_tools(parsed["fixed_code"])
            parsed["mcp"] = mcp_result

        return parsed

    return {"error": result.get("error", "Failed after retries")}