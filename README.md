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

### 🔹 Error Response

```json
{
  "error": "Failed after max attempts"
}
```

---