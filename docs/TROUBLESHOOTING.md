# Troubleshooting Guide

## Issue: Chatbot Says "I don't have the necessary tools"

### Root Cause Found ✓

The chatbot and MCP integration are **working perfectly**. The issue is:

**Your `llama-server` is running a 24B parameter model on CPU (no GPU) and timing out on every request.**

```bash
# Your current server (from ps aux):
llama-server --model /models/Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf \
  --host 0.0.0.0 --port 8000 --gpu_layers 0  # ← NO GPU!
```

**What happens:**
1. Chatbot sends request to model
2. Model takes 30+ seconds to respond (CPU is too slow for 24B model)
3. Request times out before completion
4. Model never gets to call the tools

**Evidence:**
- ✓ MCP Server: Working (19 tools loaded)
- ✓ MCP Client: Working (can call tools directly)
- ✓ LangChain Agent: Working (created with tools)
- ✗ Model Server: **Timing out on all inference requests**

---

## Solutions (Choose One)

### Solution 1: Enable GPU Acceleration ⚡ (Best if you have an NVIDIA GPU)

Check if you have a GPU:
```bash
nvidia-smi
```

If you see GPU info, restart llama-server with GPU:

```bash
# Stop current server
pkill -f llama-server

# Restart with GPU offloading
llama-server \
  --model /models/Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu_layers 99 \
  --n_ctx 4096
```

**Then test:**
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/models/Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}'
```

Should respond in <5 seconds.

---

### Solution 2: Use a Much Smaller Model 🚀 (Best for CPU-only)

For CPU inference, you need a **2B-3B model**, not 24B!

#### Option A: Download Granite 3.3 2B (Recommended)

```bash
# Download small model
cd /models
wget https://huggingface.co/lmstudio-community/granite-3.3-2b-instruct-GGUF/resolve/main/granite-3.3-2b-instruct-Q4_K_M.gguf

# Stop current server
pkill -f llama-server

# Start with small model
llama-server \
  --model /models/granite-3.3-2b-instruct-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu_layers 0 \
  --n_ctx 4096
```

**Update `.env`:**
```bash
MODEL_NAME=/models/granite-3.3-2b-instruct-Q4_K_M.gguf
```

#### Option B: Download Gemma 2 2B

```bash
cd /models
wget https://huggingface.co/lmstudio-community/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf

pkill -f llama-server

llama-server \
  --model /models/gemma-2-2b-it-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu_layers 0 \
  --n_ctx 4096
```

**Update `.env`:**
```bash
MODEL_NAME=/models/gemma-2-2b-it-Q4_K_M.gguf
```

---

### Solution 3: Use Ollama 🦙 (Easiest)

Ollama automatically manages model loading and is easier to use:

```bash
# Stop llama-server
pkill -f llama-server

# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve &

# Pull a small model
ollama pull granite3.1:2b
# or: ollama pull gemma2:2b
# or: ollama pull qwen2.5:3b
```

**Update `.env`:**
```bash
MODEL_ENDPOINT=http://localhost:11434
MODEL_NAME=  # Leave empty - will auto-detect!
```

**Benefits:**
- Auto model management
- Faster startup
- Model selection UI in chatbot
- Better memory management

---

## Model Size Recommendations

| Hardware | Recommended Model Size | Examples |
|----------|----------------------|----------|
| **CPU only** | 2B-3B parameters | Granite 3.3 2B, Gemma 2 2B, Qwen 2.5 3B |
| **8GB VRAM GPU** | 7B-8B parameters | Granite 3.3 8B, Llama 3.3 8B |
| **16GB VRAM GPU** | 13B-24B parameters | Mistral 24B, Qwen 2.5 14B |
| **24GB+ VRAM GPU** | 70B+ parameters | Llama 3.3 70B |

**Your current setup:**
- Model: 24B parameters (Mistral-Small)
- Hardware: CPU only (--gpu_layers 0)
- **Mismatch!** → Timeouts

**Fix:** Use 2B-3B model OR enable GPU

---

## Testing After Fix

### 1. Test Model Server

```bash
cd /path/to/linux-mcp-server-chatbot
source .venv/bin/activate
python test_model_server.py
```

**Expected output:**
```
Test 2: Simple chat completion...
  Status: 200
  Response: test successful
```

Should complete in <10 seconds.

### 2. Test Agent

```bash
python test_tool_call.py
```

**Expected:** Should see tool calls happening.

### 3. Test Chatbot

```bash
pkill -f streamlit  # Stop old instance
./start-chatbot.sh
```

Visit http://localhost:8501 and ask:
```
What is the system hostname?
```

**Expected:** Chatbot calls `get_system_information` and responds with your hostname.

---

## Verification Checklist

Before running the chatbot:

- [ ] Model server responding in <10 seconds
  ```bash
  python test_model_server.py
  ```

- [ ] MCP tools loading successfully
  ```bash
  python debug_mcp.py
  ```

- [ ] MODEL_NAME in `.env` matches your model

- [ ] No Streamlit processes running
  ```bash
  pkill -f streamlit
  ```

- [ ] Streamlit cache cleared
  ```bash
  rm -rf .streamlit
  ```

---

## Quick Fix Summary

**Fastest fix for you:**

1. **Stop current server:**
   ```bash
   pkill -f llama-server
   ```

2. **Install Ollama:**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama serve &
   ```

3. **Pull small model:**
   ```bash
   ollama pull granite3.1:2b
   ```

4. **Update `.env`:**
   ```bash
   MODEL_ENDPOINT=http://localhost:11434
   MODEL_NAME=granite3.1:2b
   ```

5. **Test:**
   ```bash
   python test_model_server.py
   ```

6. **Run chatbot:**
   ```bash
   ./start-chatbot.sh
   ```

**Done!** Should work in <5 minutes.

---

## Common Errors

### "Read timed out after 30 seconds"
- **Cause:** Model too large for CPU
- **Fix:** Use 2B-3B model or enable GPU

### "I don't have the necessary tools"
- **Cause:** Model server timing out, never responds
- **Fix:** Fix model server timeouts first

### "No response from model"
- **Cause:** Model server not running or wrong port
- **Fix:** Check `ps aux | grep llama-server` and verify port

### "Model not found"
- **Cause:** MODEL_NAME in .env doesn't match actual model name
- **Fix:** Run `curl http://localhost:8000/v1/models` and use exact name

---

## Your Current Configuration

From analysis:

```
✓ MCP Server: ~/.local/bin/linux-mcp-server (working)
✓ MCP Client: Working (19 tools loaded)
✓ Python Dependencies: All installed
✓ Chatbot Code: Working perfectly
✗ Model Server: llama-server on port 8000
  ├─ Model: 24B parameters (TOO LARGE for CPU)
  ├─ GPU: Disabled (--gpu_layers 0)
  └─ Result: Timeouts on every request
```

**Action needed:** Change model or enable GPU.

---

## Need Help?

Run diagnostics:
```bash
python test_model_server.py  # Shows if model responds
python debug_mcp.py          # Shows if MCP works
python test_setup.py         # Full setup check
```

All files are in: `/path/to/linux-mcp-server-chatbot/`
