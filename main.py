import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -----------------------------
# Guardrails
# -----------------------------
def input_guard(user_input: str):
    blocked_keywords = ["hack", "exploit", "attack"]

    for word in blocked_keywords:
        if word in user_input.lower():
            return False, f"Blocked keyword detected: {word}"

    return True, None


def output_guard(output: str):
    if len(output) > 1500:
        return False, "Output too long"

    return True, None


# -----------------------------
# LLM Call
# -----------------------------
def call_llm(prompt: str):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant. Answer clearly and concisely."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=300
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"LLM Error: {str(e)}"


# -----------------------------
# Agent Pipeline
# -----------------------------
def run_agent(user_input: str):
    print("[LOG] Running agent pipeline...")

    # Step 1: Input Guard
    valid, error = input_guard(user_input)
    if not valid:
        return f"[BLOCKED] {error}"

    # Step 2: Reasoning (LLM)
    response = call_llm(user_input)

    # Step 3: Output Guard
    valid, error = output_guard(response)
    if not valid:
        return f"[BLOCKED OUTPUT] {error}"

    return response


# -----------------------------
# Main
# -----------------------------
def read_multiline():
    print("Paste your input. Type 'END' on a new line to finish:\n")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)

def main():
    print("=== AI Agent System ===")

    user_input = read_multiline()

    print("\n[DEBUG] Received input:\n", user_input)

    result = run_agent(user_input)

    print("\n=== Final Response ===")
    print(result)


if __name__ == "__main__":
    main()