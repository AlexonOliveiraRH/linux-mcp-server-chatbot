#!/usr/bin/env python3
"""Test if the model server is working."""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "http://localhost:8080")
MODEL_NAME = os.getenv("MODEL_NAME", "")

print(f"Testing model server at: {MODEL_ENDPOINT}")
print(f"Using model: {MODEL_NAME}")
print()

# Test 1: List models
print("Test 1: Listing models...")
try:
    response = requests.get(f"{MODEL_ENDPOINT}/v1/models", timeout=5)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Models: {json.dumps(data, indent=2)[:300]}")
    else:
        print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")

print()

# Test 2: Simple completion
print("Test 2: Simple chat completion...")
try:
    response = requests.post(
        f"{MODEL_ENDPOINT}/v1/chat/completions",
        json={
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": "Say 'test successful'"}],
            "max_tokens": 20,
        },
        timeout=30,
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"  Response: {content}")
    else:
        print(f"  Error response: {response.text[:500]}")
except Exception as e:
    print(f"  Error: {e}")

print()

# Test 3: Tool calling support
print("Test 3: Tool calling with tools parameter...")
try:
    response = requests.post(
        f"{MODEL_ENDPOINT}/v1/chat/completions",
        json={
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": "What's the weather?"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get weather",
                        "parameters": {"type": "object", "properties": {}}
                    }
                }
            ],
            "max_tokens": 50,
        },
        timeout=30,
    )
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"  Error response: {response.text[:500]}")
except Exception as e:
    print(f"  Error: {e}")
