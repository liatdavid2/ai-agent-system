# app/agent.py

import os
import ast
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def validate_input(user_input: str):
    blocked_keywords = ["hack", "exploit", "attack"]
    for word in blocked_keywords:
        if word in user_input.lower():
            return False, f"Blocked keyword detected: {word}"
    return True, None


def validate_output(output: str):
    if len(output) > 1500:
        return False, "Output too long"
    return True, None


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
                '  "fixed_code": "<corrected Python code>"\n'
                "}\n\n"

                "Rules:\n"
                "- Fix the root cause (not try/except)\n"
                "- Keep original behavior and function signature\n"
                "- Do NOT change return types\n"
                "- Prefer raising proper Python exceptions over returning error strings\n"
                "- Replace incorrect logic instead of only adding code\n"
                "- Return clean, runnable Python code\n"
                "- Use proper formatting and indentation\n"
                "- If code is one line, expand it into multiple lines\n"
                "- Do NOT include explanations inside fixed_code\n"
                "- Ensure the code is syntactically valid Python\n\n"

                "Example:\n"
                "Input:\n"
                "def f(): return 1/0\n\n"
                "Output:\n"
                "{\n"
                '  "bug": "Division by zero error",\n'
                '  "fixed_code": "def f():\\n    raise ValueError(\\"invalid\\")"\n'
                "}\n"
            )
        },
        {
            "role": "user",
            "content": prompt
        }
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


def extract_fixed_code(response: str):
    if "FIX:" in response:
        return response.split("FIX:")[-1].strip()
    return ""


def is_valid_python(code: str):
    try:
        ast.parse(code)
        return True
    except Exception:
        return False

def is_valid_response(data):
    return (
        isinstance(data, dict)
        and isinstance(data.get("bug"), str)
        and isinstance(data.get("fixed_code"), str)
        and "def " in data["fixed_code"]
    )

def run_agent_pipeline(user_input: str):
    print("[LOG] Running agent pipeline...")

    valid, error = validate_input(user_input)
    if not valid:
        return {"error": error}

    response = generate_response(user_input)

    try:
        parsed = json.loads(response)
    except Exception:
        print("[LOG] Invalid JSON → retrying...")
        response = generate_response(user_input + "\nReturn ONLY valid JSON.")
        parsed = json.loads(response)

    if not is_valid_response(parsed):
        print("[LOG] Invalid structure → retrying...")
        response = generate_response(user_input + "\nEnsure keys: bug, patch")
        parsed = json.loads(response)

    if not is_valid_python(parsed["fixed_code"]):
        print("[LOG] Invalid code → retrying...")

    return parsed