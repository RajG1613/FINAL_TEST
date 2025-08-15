import os, time
from typing import Dict, Any, List

# OpenAI (official SDK v1+)
from openai import OpenAI as OpenAIClient
from openai._exceptions import APIError, APIConnectionError, RateLimitError

# Groq
try:
    from groq import Groq as GroqClient
except Exception:
    GroqClient = None  # optional dependency

OPENAI_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("MY_NEW_APP_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

class ProviderError(Exception):
    pass

def choose_client(provider: str):
    p = provider.lower()
    if p == "openai":
        if not OPENAI_KEY:
            raise ProviderError("Missing OPENAI_API_KEY (or MY_NEW_APP_KEY).")
        return OpenAIClient(api_key=OPENAI_KEY)
    elif p == "groq":
        if not GROQ_KEY:
            raise ProviderError("Missing GROQ_API_KEY.")
        if GroqClient is None:
            raise ProviderError("Groq SDK not installed. pip install groq")
        return GroqClient(api_key=GROQ_KEY)
    else:
        raise ProviderError(f"Unknown provider: {provider}")

def test_providers():
    status = {}
    for p in ["openai", "groq"]:
        try:
            client = choose_client(p)
            status[p] = True
        except Exception as e:
            status[p] = f"unavailable: {e}"
    return status

def chat_complete(client, provider: str, messages: List[Dict[str,str]], temperature: float, max_tokens: int):
    provider = provider.lower()
    if provider == "openai":
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {"content": resp.choices[0].message.content, "usage": getattr(resp, "usage", None)}
    elif provider == "groq":
        # Use LLaMA-3 or Mixtral; pick a solid default
        resp = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {"content": resp.choices[0].message["content"], "usage": None}
    else:
        raise ProviderError(f"Unsupported provider: {provider}")
