from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from ai_providers import choose_client, ProviderError, test_providers
from code_converter import convert_legacy
from code_analyzer import analyze_legacy_vs_modern
from data_insights import insights_from_excel
from github_push import push_files_to_github
from db import init_db, save_history

app = FastAPI(title="AI Modernizer Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ---------- Models ----------
class ConvertRequest(BaseModel):
    legacy_code: str
    target_stack: str = "Python (FastAPI)"  # or "Java (Spring Boot)" etc
    mode: str = "convert"  # convert | optimize | explain | debug
    extra_artifacts: List[str] = ["Unit Tests", "OpenAPI Spec", "Dockerfile"]
    model_choice: str = "openai"  # openai | groq
    temperature: float = 0.2
    max_tokens: int = 4096
    user_instructions: Optional[str] = None

class ConvertResponse(BaseModel):
    files: List[Dict[str, str]]
    notes_markdown: Optional[str] = ""
    usage: Dict[str, Any] = {}

class AnalyzeRequest(BaseModel):
    legacy_code: str
    modern_code: str
    model_choice: str = "openai"
    max_tokens: int = 2048

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]  # [{role: system|user|assistant, content: "..."}]
    model_choice: str = "openai"
    temperature: float = 0.2
    max_tokens: int = 1024

class GitFile(BaseModel):
    path: str
    content: str

class GitPushRequest(BaseModel):
    repo: str                # e.g. "username/repo"
    branch: str = "main"
    commit_message: str = "Add converted code"
    files: List[GitFile]

# ---------- Health ----------
@app.get("/health")
def health():
    ok = test_providers()
    return {"status": "ok", "providers": ok}

# ---------- Convert ----------
@app.post("/convert", response_model=ConvertResponse)
def convert(req: ConvertRequest):
    try:
        client = choose_client(req.model_choice)
        bundle = convert_legacy(
            client=client,
            provider=req.model_choice,
            legacy_code=req.legacy_code,
            target_stack=req.target_stack,
            mode=req.mode,
            extra_artifacts=req.extra_artifacts,
            user_instructions=req.user_instructions or "",
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        save_history("convert", req.model_choice, req.legacy_code[:500], bundle)
        return bundle
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")

# ---------- Analyze (legacy vs modern) ----------
@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        client = choose_client(req.model_choice)
        report = analyze_legacy_vs_modern(client, req.model_choice, req.legacy_code, req.modern_code, req.max_tokens)
        save_history("analyze", req.model_choice, req.legacy_code[:500], report)
        return report
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analyze failed: {e}")

# ---------- Chat (interactive console) ----------
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        client = choose_client(req.model_choice)
        from ai_providers import chat_complete
        out = chat_complete(client, req.model_choice, req.messages, req.temperature, req.max_tokens)
        save_history("chat", req.model_choice, str(req.messages)[:500], out)
        return out
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")

# ---------- Data insights (Excel) ----------
@app.post("/data/insights")
async def data_insights(file: UploadFile = File(...), query: str = Form("Show recursive incidents for the last 1 month")):
    try:
        content = await file.read()
        result = insights_from_excel(content, query)
        save_history("insights", "local", query, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insights failed: {e}")

# ---------- Push to GitHub ----------
@app.post("/github/push")
def github_push(req: GitPushRequest):
    try:
        r = push_files_to_github(repo=req.repo, branch=req.branch, commit_message=req.commit_message,
                                 files=[{"path": f.path, "content": f.content} for f in req.files])
        return r
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git push failed: {e}")

if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)



