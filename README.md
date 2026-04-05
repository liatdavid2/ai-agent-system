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
  "prompt": "def divide(a, b):\n    return a / b\n\nprint(divide(10, 0))"
}
```

---

###  Response (200 OK)

```json
{
  "result": {
    "bug": "Division by zero",
    "fixed_code": "def divide(a, b):\n    if b == 0:\n        raise ValueError(\"Cannot divide by zero\")\n    return a / b",
    "test": "try:\n    divide(10, 0)\n    assert False\nexcept ValueError:\n    assert True",
    "test_result": {
      "status": "PASS"
    },
    "mcp": {
      "syntax": {
        "status": "valid"
      },
      "execution": {
        "status": "success"
      }
    }
  }
}
```

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
## Agent Architecture
```
Client / Swagger
      │
      ▼
POST /fix
      │
      ▼
┌──────────────────────┐
│   Input Guard Agent  │
│  - validate input    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   LLM Fix Agent      │
│  - detect bug        │
│  - generate fix      │
│  - generate test     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  JSON Guard Agent    │
│  - enforce JSON      │
│  - parse output      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Structure Guard Agent│
│ - required fields    │
│ - bug/code/test      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Code Guard Agent     │
│ - safe Python only   │
│ - no unsafe patterns │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Test Guard Agent     │
│ - assert-only tests  │
│ - run + validate     │
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
  PASS         FAIL
     │           │
     ▼           ▼
 Return      Retry Agent
 Result      - increment attempt
                │
                └─────── back to LLM Fix Agent
```
---

# AI Agent System

Lightweight AI agent for detecting and fixing Python bugs with validation and MCP tools.

---

## Quick Start

### 1. Create virtual environment

```bash
py -m venv .venv
```

### 2. Activate environment

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

CPU-only PyTorch:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Project requirements:

```bash
pip install -r requirements.txt
```

---

### 4. Run the API

```bash
uvicorn main:app --reload
```

API will be available at:

```
http://127.0.0.1:8000
```

Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## MCP (Model Context Protocol)

Simple MCP layer for validating and safely executing generated code.

Location:

```
app/mcp.py
```

### Purpose

Add guardrails after LLM generation:

* Syntax validation
* Safe execution
* Controlled tool usage

---

### Available Tools

#### 1. Syntax Check

Validates Python code using AST parsing.

#### 2. Safe Execution

Runs code in isolated globals (basic sandbox).

---

### Usage

```python
from app.mcp import run_mcp_tools

results = run_mcp_tools(fixed_code)
```

---

### Example Output

```json
{
  "syntax": {
    "status": "valid"
  },
  "execution": {
    "status": "success"
  }
}
```
---

