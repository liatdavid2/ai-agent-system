# app/agent.py

import os
from openai import OpenAI
from dotenv import load_dotenv
from app.guardrails import (
    guard_input,
    guard_llm_output,
    guard_structure,
    guard_code_safety,
    guard_test_result
)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
                "- Prefer raising proper Python exceptions over returning error strings\n"
                "- Replace incorrect logic instead of only adding code\n"
                "- Return clean, runnable Python code\n"
                "- Use proper formatting and indentation\n"
                "- If code is one line, expand it into multiple lines\n"
                "- Do NOT include explanations inside fixed_code\n"
                "- Ensure the code is syntactically valid Python\n"
                "- Return only the function (no print statements)\n\n"

                "Test Rules:\n"
                "- Generate a minimal unit test using assert\n"
                "- The test must validate the fix\n"
                "- The test must FAIL if the fix is incorrect\n"
                "- Ensure exception tests assert failure if exception is not raised\n"
                "- Do NOT include explanations inside test\n\n"

                "Example:\n"
                "Input:\n"
                "def f(): return 1/0\n\n"
                "Output:\n"
                "{\n"
                '  "bug": "Division by zero error",\n'
                '  "fixed_code": "def f():\\n    raise ValueError(\\"invalid\\")",\n'
                '  "test": "try:\\n    f()\\n    assert False\\nexcept ValueError:\\n    assert True"\n'
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


def run_test(fixed_code: str, test_code: str):
    try:
        # combine code + test
        full_code = fixed_code + "\n\n" + test_code

        # run in isolated scope
        exec_globals = {}
        exec(full_code, exec_globals)

        return {"status": "PASS"}

    except AssertionError:
        return {"status": "FAIL", "error": "Assertion failed"}

    except Exception as e:
        return {"status": "ERROR", "error": str(e)}
    
def run_agent_pipeline(user_input: str):
    print("[LOG] Running agent pipeline...")

    valid, error = guard_input(user_input)
    if not valid:
        return {"error": error}

    for attempt in range(3):
        print(f"[LOG] Attempt {attempt+1}")

        response = generate_response(user_input)

        ok, parsed = guard_llm_output(response)
        if not ok:
            print("[LOG] Invalid JSON → retrying...")
            continue

        ok, error = guard_structure(parsed)
        if not ok:
            print("[LOG] Invalid structure → retrying...")
            continue

        ok, error = guard_code_safety(parsed["fixed_code"])
        if not ok:
            print("[LOG] Unsafe code → retrying...")
            continue

        test_result = run_test(parsed["fixed_code"], parsed["test"])
        parsed["test_result"] = test_result

        ok, error = guard_test_result(test_result)
        if ok:
            print("[LOG] Success")
            return parsed

        print("[LOG] Test failed → retrying...")

    return {"error": "Failed after retries"}