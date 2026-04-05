# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from app.agent import run_agent_pipeline

app = FastAPI(
    title="AI Agent System",
    description="Bug Fixing Agent",
    version="1.0.0"
)


class InputRequest(BaseModel):
    prompt: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/fix")
def fix_code(request: InputRequest):
    result = run_agent_pipeline(request.prompt)
    return {"result": result}