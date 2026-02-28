import os
import requests
import json
from dotenv import load_dotenv

load_dotenv(override=True)

def test_gemini_native():
    key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": "hi"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return f"Gemini Native: {res.status_code} - {res.text[:100]}"
    except Exception as e:
        return f"Gemini Native: {e}"

def test_groq():
    key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "hi"}]}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        return f"Groq: {res.status_code} - {res.text[:100]}"
    except Exception as e:
        return f"Groq: {e}"

def test_hf():
    token = os.getenv("HF_API_TOKEN")
    url = "https://router.huggingface.co/v1/chat/completions"
    payload = {"model": "meta-llama/Llama-3.1-8B-Instruct", "messages": [{"role": "user", "content": "hi"}]}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        return f"HF: {res.status_code} - {res.text[:100]}"
    except Exception as e:
        return f"HF: {e}"

def test_nvidia():
    key = os.getenv("NVIDIA_API_KEY")
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    payload = {"model": "meta/llama-3.1-405b-instruct", "messages": [{"role": "user", "content": "hi"}]}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        return f"NVIDIA: {res.status_code} - {res.text[:100]}"
    except Exception as e:
        return f"NVIDIA: {e}"

if __name__ == "__main__":
    print(test_gemini_native())
    print(test_groq())
    print(test_hf())
    print(test_nvidia())
