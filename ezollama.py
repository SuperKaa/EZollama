import requests
import subprocess
import sys
import shutil
import os

try:
    import pyttsx3
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyttsx3"])
    import pyttsx3

def start_ollama_quietly():
    if shutil.which("ollama") is None:
        print("[ezollama] Warning: Ollama CLI not found in PATH. Please install Ollama from https://ollama.com/download.")
    if sys.platform == "win32":
        os.system("ollama list >nul 2>&1")
    else:
        os.system("ollama list >/dev/null 2>&1")

class EzOllama:
    def __init__(self, api_url="http://localhost:11434"):
        self.api_url = api_url.rstrip("/")
        self.model = None
        self.history = []
        self.system_prompt = None

    def set_model(self, modelname):
        start_ollama_quietly()
        self.model = modelname
        self.history = []

    def set_system_prompt(self, prompt):
        start_ollama_quietly()
        self.system_prompt = prompt

    def chat(self, message, stream=False):
        start_ollama_quietly()
        if not self.model:
            raise ValueError("Model not set. Use set_model('modelname') first.")

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages += self.history
        messages.append({"role": "user", "content": message})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        resp = requests.post(f"{self.api_url}/api/chat", json=payload, stream=stream)
        if stream:
            response_text = ""
            for line in resp.iter_lines():
                if line:
                    data = line.decode("utf-8")
                    response_text += data
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": response_text})
            return response_text
        else:
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": content})
            return content

    def list_models(self):
        start_ollama_quietly()
        resp = requests.get(f"{self.api_url}/api/tags")
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]

    def reset_history(self):
        start_ollama_quietly()
        self.history = []

    def text_to_speech(self, text):
        start_ollama_quietly()
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    def pull_model(self, modelname):
        start_ollama_quietly()
        resp = requests.get(f"{self.api_url}/api/tags")
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        if modelname not in models:
            print(f"{modelname} not found!")
            return
        pull_resp = requests.post(f"{self.api_url}/api/pull", json={"name": modelname})
        pull_resp.raise_for_status()
        print(f"Pulled model: {modelname}")

ez = EzOllama()
