import ast


# -------------------------
# TOOL: Syntax Check
# -------------------------
def syntax_check(code: str):
    try:
        ast.parse(code)
        return {"status": "valid"}
    except Exception as e:
        return {"status": "invalid", "error": str(e)}


# -------------------------
# TOOL: Safe Exec
# -------------------------
def run_code(code: str):
    try:
        exec_globals = {}
        exec(code, exec_globals)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# -------------------------
# MCP ROUTER (simple)
# -------------------------
def run_mcp_tools(fixed_code: str):
    results = {}

    # syntax check
    results["syntax"] = syntax_check(fixed_code)

    # only run if syntax is valid
    if results["syntax"]["status"] == "valid":
        results["execution"] = run_code(fixed_code)

    return results