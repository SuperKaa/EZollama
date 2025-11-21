# EZollama

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/ezollama.svg)](https://pypi.org/project/ezollama/)

A simple Python library for interacting with [Ollama](https://ollama.com/) models via their local API and cloud models through Google, Groq, OpenAI and Anthropic.  
Supports model selection, chatting, persistent system prompts, listing models, downloading models, resetting chat history, and text-to-speech.

---

## Installation

1. **Install Ollama:**  
   Download and install Ollama from [https://ollama.com/download](https://ollama.com/download).  
   The library will prompt to install Ollama if not found.

2. **Python dependencies:**  
   The library auto-installs `pyttsx3` for text-to-speech if missing.

---

## Usage for local

### Import

```python
from ezollama import EzOllama
ez = EzOllama()
```

### Set Model

```python
ez.set_model("llama2")
```

### Set Persistent System Prompt

```python
ez.set_system_prompt("You are a helpful assistant.")
```

### Chat

```python
response = ez.chat("Hello!")
print(response)
```

### List Available Models

```python
models = ez.list_models()
print(models)
```

### Pull (Download) a Model

```python
ez.pull_model("llama2")
```

### Reset Chat History

```python
ez.reset_history()
```

### Text-to-Speech

```python
ez.text_to_speech("Hello, this is AI speaking.")
```

---

## Usage for cloud

### Import

```python
from ezollama import EzOllama
ez = EzOllama()
```

### Set mode

```python
ez.set_mode("mode", "api-key") # choosable from groq, google, anthropic and openai
```

### Set model

```python
ez.set_model("model") # for example 'gemini-2.5-flash
```

### Set Persistent System Prompt

```python
ez.set_system_prompt("You are a helpful assistant.")
```

---

## Example for local

```python
from ezollama import EzOllama

ez = EzOllama()

ez.set_model("llama3.2:3b")
ez.set_system_prompt("You are a friendly assistant.")

while True:
    user_input = input("- ")
    resp = ez.chat(user_input)
    print(resp)
    ez.text_to_speech(resp)
```

---

## Example for cloud
```python
from ezollama import EzOllama

ez = EzOllama()

ez.set_mode("google" "API-KEY")
ez.set_model("gemini-2.5-flash")
ez.set_system_prompt("You are a friendly assistant.")

while True:
    user_input = input("- ")
    resp = ez.chat(user_input)
    print(resp)
```
## Notes

- The library checks and quietly starts the Ollama server before each API call.
- If Ollama is not installed, you will be prompted to install it.
- If the model does not exist, `pull_model` will print a message.
- Text-to-speech uses `pyttsx3` and works cross-platform.
