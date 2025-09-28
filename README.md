# EZollama

A simple Python library for interacting with [Ollama](https://ollama.com/) models via their local API.  
Supports model selection, chatting, persistent system prompts, listing models, downloading models, resetting chat history, and text-to-speech.

---

## Installation

1. **Install Ollama:**  
   Download and install Ollama from [https://ollama.com/download](https://ollama.com/download).  
   The library will prompt to install Ollama if not found.

2. **Python dependencies:**  
   The library auto-installs `pyttsx3` for text-to-speech if missing.

---

## Usage

### Import

```python
from ezollama import EzOllama
ez = EzOllama()
```

### Set Model

```python
ez.setmodel("llama2")
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
ez.text_to_speech("Hello, this is Ollama speaking.")
```

---

## Example

```python
from ezollama import EzOllama

ez = EzOllama()

ez.setmodel("llama3.2:3b")
ez.set_system_prompt("You are a friendly assistant.")

while True:
    user_input = input("- ")
    resp = ez.chat(user_input)
    print(resp)
    ez.text_to_speech(resp)
```

---

## Notes

- The library checks and quietly starts the Ollama server before each API call.
- If the model does not exist, `pull_model` will print a message.
- Text-to-speech uses `pyttsx3` and works cross-platform.
