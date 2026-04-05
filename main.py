import os
import ast
from openai import OpenAI
from dotenv import load_dotenv

# -----------------------------
# Setup
# -----------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -----------------------------
# Guardrails
# -----------------------------
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


# -----------------------------
# LLM Layer
# -----------------------------
def build_messages(prompt: str):
    return [
        {
            "role": "system",
            "content": (
                "You are an expert Python debugging assistant.\n"
                "When given buggy code:\n"
                "1. Identify the bug\n"
                "2. Fix the root cause (not try/except)\n"
                "3. Return in this format:\n\n"
                "BUG:\n<short explanation>\n\n"
                "FIX:\n<corrected code>\n\n"
                "Do NOT use markdown or ``` blocks.\n"
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


# -----------------------------
# Post-processing
# -----------------------------
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


# -----------------------------
# Agent Pipeline
# -----------------------------
def run_agent_pipeline(user_input: str):
    print("[LOG] Running agent pipeline...")

    # Step 1: Input validation
    valid, error = validate_input(user_input)
    if not valid:
        return f"[BLOCKED INPUT] {error}"

    # Step 2: LLM reasoning
    response = generate_response(user_input)

    # Step 3: Extract + validate code
    code = extract_fixed_code(response)
    if code:
        if not is_valid_python(code):
            print("[LOG] Invalid code detected → retrying...")
            response = generate_response(user_input + "\nFix the code correctly.")

    # Step 4: Output validation
    valid, error = validate_output(response)
    if not valid:
        return f"[BLOCKED OUTPUT] {error}"

    return response


# -----------------------------
# CLI Input
# -----------------------------
def read_multiline_input():
    print("Paste your input. Type 'END' on a new line to finish:\n")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    return "\n".join(lines)


# -----------------------------
# Main
# -----------------------------
def main():
    print("=== AI Agent System ===")

    user_input = read_multiline_input()

    print("\n[DEBUG] Received input:\n", user_input)

    result = run_agent_pipeline(user_input)

    print("\n=== Final Response ===")
    print(result)


if __name__ == "__main__":
    main()