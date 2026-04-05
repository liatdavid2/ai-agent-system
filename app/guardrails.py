# app/guardrails.py

import json
import ast

# ----------------------
# INPUT GUARDRAIL
# ----------------------
def guard_input(user_input: str):
    blocked_keywords = ["hack", "exploit", "attack"]

    for word in blocked_keywords:
        if word in user_input.lower():
            return False, f"Blocked keyword: {word}"

    if len(user_input) > 2000:
        return False, "Input too long"

    return True, None


# ----------------------
# OUTPUT GUARDRAIL (RAW LLM)
# ----------------------
def guard_llm_output(raw_output: str):
    try:
        data = json.loads(raw_output)
        return True, data
    except Exception:
        return False, "Invalid JSON"


# ----------------------
# STRUCTURE GUARDRAIL
# ----------------------
def guard_structure(data: dict):
    required_fields = ["bug", "fixed_code", "test"]

    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"

    return True, None


# ----------------------
# CODE SAFETY GUARDRAIL
# ----------------------
def guard_code_safety(code: str):
    forbidden = ["import os", "import sys", "__import__", "eval", "exec"]

    for f in forbidden:
        if f in code:
            return False, f"Forbidden code detected: {f}"

    try:
        ast.parse(code)
    except Exception:
        return False, "Invalid Python syntax"

    return True, None


# ----------------------
# TEST RESULT GUARDRAIL
# ----------------------
def guard_test_result(test_result: dict):
    if test_result.get("status") != "PASS":
        return False, "Test failed"

    return True, None