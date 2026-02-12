#!/usr/bin/env python3
"""Test Claude via Vertex AI using Anthropic SDK directly."""
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "your-gcp-project-id")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

print("=" * 60)
print("Claude via Vertex AI - Direct SDK Test")
print("=" * 60)
print()
print(f"Project: {GOOGLE_PROJECT_ID}")
print(f"Region: {GOOGLE_LOCATION}")
print()

# Import Anthropic Vertex client
from anthropic import AnthropicVertex

print("Creating AnthropicVertex client...")
client = AnthropicVertex(
    project_id=GOOGLE_PROJECT_ID,
    region=GOOGLE_LOCATION,
)

print("✓ Client created")
print()

print("Sending test message...")
try:
    message = client.messages.create(
        model="claude-sonnet-4-5@20250929",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Say 'It works!' in exactly 2 words"}
        ]
    )

    print(f"✓ Response: {message.content[0].text}")
    print()
    print("=" * 60)
    print("✅ SUCCESS! Claude via Vertex AI works!")
    print("=" * 60)
    print()
    print("This uses the EXACT same authentication as Claude Code CLI!")

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    if "403" in str(e):
        print("Permission denied - may need to enable Claude in Vertex AI")
    elif "404" in str(e):
        print("Model not found - try a different region or model")
    exit(1)
