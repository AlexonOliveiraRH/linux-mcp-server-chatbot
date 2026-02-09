# Linux MCP Server Chatbot (Lightspeed-style)

This project demonstrates how to combine:

- vLLM / OpenAI-compatible models
- LangChain agents
- Linux MCP Server
- Streamlit UI

to build an **enterprise-grade AI assistant** similar to Red Hat Lightspeed.

## Architecture

LLM = reasoning  
MCP Server = action  
Human = decision maker  

The LLM never executes shell commands directly.

## How to run

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```
