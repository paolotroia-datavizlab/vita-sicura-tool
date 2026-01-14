import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

print("OPENROUTER_API_KEY =", OPENROUTER_API_KEY)


def ask_llm(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "Generali AI Control Room"
    }

    payload = {
        "model": "meta-llama/llama-3.1-70b-instruct",
        "messages": [
            {"role": "system", "content": "You are a senior insurance AI advisor."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    data = response.json()

    # ✅ GESTIONE SICURA
    if "choices" not in data:
        return f"⚠️ Errore AI:\n{data}"

    return data["choices"][0]["message"]["content"]

