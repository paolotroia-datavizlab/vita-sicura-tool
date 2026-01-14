import os
import requests
import streamlit as st

def get_api_key():
    """
    Priorità:
    1) Streamlit Secrets (Cloud / demo)
    2) Variabili d'ambiente (locale)
    """
    return st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")

def ask_llm(prompt: str) -> str:
    api_key = get_api_key()

    if not api_key:
        return "⚠️ API key non configurata."

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "Sei un AI advisor per consulenti assicurativi. Spiega le decisioni in modo chiaro, operativo e professionale."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.4
        },
        timeout=30
    )

    if response.status_code != 200:
        return f"⚠️ Errore AI: {response.text}"

    data = response.json()

    # 🔐 protezione extra (evita crash live)
    if "choices" not in data:
        return f"⚠️ Risposta AI inattesa: {data}"

    return data["choices"][0]["message"]["content"]



