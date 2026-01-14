import os
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def ask_llm(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        return "⚠️ API key non configurata."

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Sei un AI advisor per consulenti assicurativi."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        },
        timeout=30
    )

    if response.status_code != 200:
        return f"⚠️ Errore AI: {response.text}"

    return response.json()["choices"][0]["message"]["content"]


