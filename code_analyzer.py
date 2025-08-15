from typing import Dict
ANALYZE_SYSTEM = (
    "You are a code reviewer. Compare legacy vs modern code, verify functional equivalence, "
    "flag missing logic, risky changes, and suggest improvements. Return concise JSON."
)

def analyze_legacy_vs_modern(client, provider: str, legacy_code: str, modern_code: str, max_tokens: int = 2048) -> Dict:
    messages = [
        {"role":"system","content":ANALYZE_SYSTEM},
        {"role":"user","content":f"LEGACY:\n{legacy_code}\n\nMODERN:\n{modern_code}\n\nReturn JSON with keys: summary, risks, diffs, suggestions"}
    ]
    provider = provider.lower()
    if provider == "openai":
        resp = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type":"json_object"},
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1
        )
        return {"report": resp.choices[0].message.content}
    else:
        resp = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1
        )
        return {"report": resp.choices[0].message["content"]}
