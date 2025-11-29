# Hackaton Minecraft – Python Backend (AI Mentor Server) 🤖💬

This repository is the **backend server** for the Hackathon “AI-Mentor in Minecraft” project.  
It provides an HTTP API that the Minecraft mod uses to query an LLM (Large Language Model, e.g. via Google Gemini API) and returns natural-language responses to be displayed in-game.  

The backend handles requests from the Minecraft client mod, sends them to the LLM, and returns answers — decoupling game logic (in Java / Forge) from AI logic (in Python).

---

## Features

- **AI Chat API**  
  - Exposes a simple HTTP interface for chat requests (e.g. POST with a “message”).  
  - Forwards the message to a LLM and returns the reply.  
- **Stateless / Lightweight Server**  
  - Easy to run locally or host externally.  
  - Minimal dependencies.  
- **Automated Tests**  
  - Includes basic test scripts to validate API functionality and memory schema logic (if applicable).  
- **Configurable via environment variables**  
  - LLM API key (e.g. in `.env` or via environment variable) — see "Setup" below.  

---

## Tech Stack

- **Language**: Python 3.x  
- **Dependencies**: see `requirements.txt`  
- **LLM backend**: via LLM API (e.g. Google Gemini, or other provider)  
- **Server**: simple HTTP server (e.g. using Flask / FastAPI / similar — depending on your `app.py`)  
- **Testing**: Python test scripts (`test_*.py`)  

---

## Quick Start

```bash
git clone https://github.com/simo-br91/Hackaton_Minecraft_Python.git
cd Hackaton_Minecraft_Python

# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your API key for the LLM
# For example (Linux / macOS shell):
export GEMINI_API_KEY="your_key_here"
# Or create a .env file containing:
# GEMINI_API_KEY=your_key_here

# 3. Run the server
python app.py
