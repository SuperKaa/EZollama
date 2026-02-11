import requests
import subprocess
import sys
import shutil
import os
import json
import base64
import mimetypes

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

    def set_history(self, history):
        self.history = history

    def get_history(self):
        return self.history

    def _encode_image(self, image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"
            
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        return encoded_string, mime_type

    def _chat_google(self, message, image=None):
        """Handle Google AI Studio (Gemini) API calls"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        # Build contents array
        contents = []
        for turn in self.history:
            contents.append({"role": "user", "parts": [{"text": turn["user"]}]})
            if "ai" in turn:
                contents.append({"role": "model", "parts": [{"text": turn["ai"]}]})
        
        user_parts = [{"text": message}]
        if image:
            b64_img, mime = self._encode_image(image)
            user_parts.append({
                "inline_data": {
                    "mime_type": mime,
                    "data": b64_img
                }
            })
        contents.append({"role": "user", "parts": user_parts})
        
        payload = {"contents": contents}
        
        # Add system instruction if set
        if self.system_prompt:
            payload["system_instruction"] = {"parts": [{"text": self.system_prompt}]}
        
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        self.history.append({"user": message, "ai": content})
        return content

    def _chat_openai(self, message, image=None):
        """Handle OpenAI API calls"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        for turn in self.history:
            messages.append({"role": "user", "content": turn["user"]})
            if "ai" in turn:
                messages.append({"role": "assistant", "content": turn["ai"]})
        
        if image:
            b64_img, mime = self._encode_image(image)
            content = [
                {"type": "text", "text": message},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64_img}"}
                }
            ]
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages
        }
        
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        content = data["choices"][0]["message"]["content"]
        self.history.append({"user": message, "ai": content})
        return content

    def _chat_anthropic(self, message, image=None):
        """Handle Anthropic (Claude) API calls"""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        messages = []
        for turn in self.history:
            messages.append({"role": "user", "content": turn["user"]})
            if "ai" in turn:
                messages.append({"role": "assistant", "content": turn["ai"]})
        
        if image:
            b64_img, mime = self._encode_image(image)
            content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime,
                        "data": b64_img
                    }
                },
                {"type": "text", "text": message}
            ]
            messages.append({"role": "user", "content": content})
        else:
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
        self.history.append({"user": message, "ai": content})
        return content

    def _chat_groq(self, message, image=None):
        """Handle Groq API calls"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        for turn in self.history:
            messages.append({"role": "user", "content": turn["user"]})
            if "ai" in turn:
                messages.append({"role": "assistant", "content": turn["ai"]})
        
        if image:
            b64_img, mime = self._encode_image(image)
            content = [
                {"type": "text", "text": message},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64_img}"}
                }
            ]
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages
        }
        
        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        content = data["choices"][0]["message"]["content"]
        self.history.append({"user": message, "ai": content})
        return content

    def chat(self, message, image=None, stream=False):
        if self.mode == "local":
            start_ollama_quietly()
            if not self.model:
                raise ValueError("Model not set. Use set_model('modelname') first.")

            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            for turn in self.history:
                messages.append({"role": "user", "content": turn["user"]})
                if "ai" in turn:
                    messages.append({"role": "assistant", "content": turn["ai"]})
            
            current_msg = {"role": "user", "content": message}
            if image:
                b64_img, _ = self._encode_image(image)
                current_msg["images"] = [b64_img]
            messages.append(current_msg)

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
                        try:
                            data = json.loads(line.decode("utf-8"))
                            response_text += data.get("message", {}).get("content", "")
                        except json.JSONDecodeError:
                            pass
                self.history.append({"user": message, "ai": response_text})
                return response_text
            else:
                resp.raise_for_status()
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                self.history.append({"user": message, "ai": content})
                return content
        
        # API mode routing
        if not self.model:
            raise ValueError("Model not set. Use set_model('modelname') first.")
        
        if stream:
            print("Warning: Streaming not yet supported for API modes, using regular chat.")
        
        if self.mode == "google":
            return self._chat_google(message, image)
        elif self.mode == "openai":
            return self._chat_openai(message, image)
        elif self.mode == "anthropic":
            return self._chat_anthropic(message, image)
        elif self.mode == "groq":
            return self._chat_groq(message, image)

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
