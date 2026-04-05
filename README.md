#  AI Bug Fixing Agent API

Automatically detect and fix Python bugs using an LLM-powered agent with execution-based validation.

---

##  Input / Output

###  Endpoint

```http
POST /fix
```

---

###  Request Body

```json
{
  "code": "def divide(a, b):\n    return a / b\n\nprint(divide(10, 0))"
}
```

---

###  Response (200 OK)

```json
{
  "result": {
    "bug": "Division by zero error",
    "fixed_code": "def divide(a, b):\n    if b == 0:\n        raise ValueError(\"Cannot divide by zero\")\n    return a / b",
    "test": "try:\n    divide(10, 0)\n    assert False\nexcept ValueError:\n    assert True",
    "test_result": {
      "status": "PASS"
    }
  }
}
```

---

### 🔹 Response Fields

| Field                | Type   | Description                  |
| -------------------- | ------ | ---------------------------- |
| `bug`                | string | Short explanation of the bug |
| `fixed_code`         | string | Corrected Python code        |
| `test`               | string | Generated unit test          |
| `test_result.status` | string | `PASS` or `FAIL`             |

---

### Error Response

```json
{
  "error": "Failed after max attempts"
}
```
---

##  Guardrails

The system uses a dedicated guardrails module to ensure safe and reliable LLM behavior.

Guardrails are applied at multiple stages:

* **Input validation** – blocks unsafe or malicious prompts
* **Output validation** – ensures valid JSON format
* **Structure validation** – verifies required fields (`bug`, `fixed_code`, `test`)
* **Code safety checks** – prevents execution of unsafe code (e.g. `eval`, `exec`, `os`)
* **Execution validation** – runs generated code and tests to verify correctness

This separation keeps safety logic independent from the agent pipeline and allows easy extension.

---

## Agentic Retry Loop

The system uses an agentic retry loop to improve reliability.

Instead of trusting a single LLM response, the agent:

1. Generates a fix and test
2. Validates structure and safety
3. Executes the code and test
4. Retries if validation fails

```text
Generate → Validate → Execute → PASS / RETRY
```

The loop continues until:

* a valid solution passes execution, or
* the maximum number of attempts is reached

This approach ensures that outputs are **functionally correct**, not just syntactically valid.

---
