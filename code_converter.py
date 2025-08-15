import json, time
from typing import Dict, List, Any
from ai_providers import ProviderError

SYSTEM = (
    "You are a senior Mainframe Modernization architect. "
    "You convert COBOL/JCL to modern stacks with clean architecture, explicit data models, "
    "defensive error handling, and clear comments for assumptions. "
    "Always return STRICT JSON."
)

def _prompt(legacy_code: str, target_stack: str, mode: str, extra_artifacts: List[str], user_instructions: str) -> List[Dict[str,str]]:
    artifacts = ", ".join(extra_artifacts) if extra_artifacts else "Unit Tests, OpenAPI, Dockerfile, Migration Notes"
    mode_note = {
        "convert": "Perform faithful conversion.",
        "optimize": "Refactor for readability/performance.",
        "explain": "Explain logic step-by-step for new devs.",
        "debug": "Fix issues given error messages or unclear logic.",
    }.get(mode, "Perform faithful conversion.")

    user = f"""
=== LEGACY CODE START ===
{legacy_code}
=== LEGACY CODE END ===

Target stack: {target_stack}
Mode: {mode} -> {mode_note}
Requested artifacts: {artifacts}
Additional instructions: {user_instructions}

Return STRICT JSON:
{{
  "files": [{{"path": "relative/path.ext", "content": "file content"}}],
  "notes_markdown": "short markdown notes"
}}
"""
    return [{"role":"system","content":SYSTEM},{"role":"user","content":user}]

def convert_legacy(client, provider: str, legacy_code: str, target_stack: str, mode: str,
                   extra_artifacts: List[str], user_instructions: str, temperature: float, max_tokens: int):
    messages = _prompt(legacy_code, target_stack, mode, extra_artifacts, user_instructions)
    provider = provider.lower()

    if provider == "openai":
        resp = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type":"json_object"},
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        txt = resp.choices[0].message.content
        data = json.loads(_extract_json(txt))
        usage = getattr(resp, "usage", None)
        return {"files": data.get("files", []), "notes_markdown": data.get("notes_markdown",""), "usage": _usage_to_dict(usage)}
    elif provider == "groq":
        # Groq models don't enforce JSON; ask strictly and then salvage JSON if needed
        resp = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        txt = resp.choices[0].message["content"]
        data = json.loads(_extract_json(txt))
        return {"files": data.get("files", []), "notes_markdown": data.get("notes_markdown",""), "usage": {}}
    else:
        raise ProviderError("Unknown provider")

def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model did not return JSON.")
    return text[start:end+1]

def _usage_to_dict(usage):
    if not usage: return {}
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }
