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
        self.mode = "local"  # New: default to local (ollama)
        self.api_key = None  # New: for API services
        self.api_provider = None  # New: which API provider

    def set_mode(self, mode, api_key=None):
        """
        Set the mode for the library.
        
        Args:
            mode (str): "local" for Ollama, or API provider name like "google", "openai", "anthropic"
            api_key (str): API key for the service (required for non-local modes)
        """
        valid_modes = ["local", "google", "openai", "anthropic", "groq"]
        
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Choose from: {', '.join(valid_modes)}")
        
        if mode != "local" and not api_key:
            raise ValueError(f"API key required for mode '{mode}'")
        
        self.mode = mode
        self.api_provider = mode if mode != "local" else None
        self.api_key = api_key


    def set_model(self, modelname):
        if self.mode == "local":
            start_ollama_quietly()
        self.model = modelname
        self.history = []

    def set_system_prompt(self, prompt):
        if self.mode == "local":
            start_ollama_quietly()
        self.system_prompt = prompt

    def _chat_google(self, message):
        """Handle Google AI Studio (Gemini) API calls"""
        url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent?key={self.api_key}"
        
        # Build contents array
        contents = []
        for msg in self.history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": message}]})
        
        payload = {"contents": contents}
        
        # Add system instruction if set
        if self.system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": self.system_prompt}]}
        
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": content})
        return content

    def _chat_openai(self, message):
        """Handle OpenAI API calls"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages += self.history
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages
        }
        
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        content = data["choices"][0]["message"]["content"]
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": content})
        return content

    def _chat_anthropic(self, message):
        """Handle Anthropic (Claude) API calls"""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        messages = self.history.copy()
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096
        }
        
        if self.system_prompt:
            payload["system"] = self.system_prompt
        
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        content = data["content"][0]["text"]
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": content})
        return content

    def _chat_groq(self, message):
        """Handle Groq API calls"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages += self.history
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages
        }
        
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        content = data["choices"][0]["message"]["content"]
        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": content})
        return content

    def chat(self, message, stream=False):
        if self.mode == "local":
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
        
        # API mode routing
        if not self.model:
            raise ValueError("Model not set. Use set_model('modelname') first.")
        
        if stream:
            print("Warning: Streaming not yet supported for API modes, using regular chat.")
        
        if self.mode == "google":
            return self._chat_google(message)
        elif self.mode == "openai":
            return self._chat_openai(message)
        elif self.mode == "anthropic":
            return self._chat_anthropic(message)
        elif self.mode == "groq":
            return self._chat_groq(message)

    def list_models(self):
        if self.mode != "local":
            print(f"list_models() only works in 'local' mode (Ollama). Current mode: {self.mode}")
            return []
        
        start_ollama_quietly()
        resp = requests.get(f"{self.api_url}/api/tags")
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]

    def reset_history(self):
        if self.mode == "local":
            start_ollama_quietly()
        self.history = []

    def text_to_speech(self, text):
        if self.mode == "local":
            start_ollama_quietly()
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    def pull_model(self, modelname):
        if self.mode != "local":
            print(f"pull_model() only works in 'local' mode (Ollama). Current mode: {self.mode}")
            return
        
        start_ollama_quietly()
        if sys.platform == "win32":
            exit_code = os.system(f"ollama pull {modelname}")
        else:
            exit_code = os.system(f"ollama pull {modelname}")
        if exit_code != 0:
            print(f"{modelname} not found!")
        else:
            print(f"Pulled model: {modelname}")

ez = EzOllama()
