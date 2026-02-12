#!/usr/bin/env python3
"""Test Claude via Vertex AI (same as Claude Code CLI)."""
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-5@20250929")

print("=" * 60)
print("Claude via Vertex AI Test")
print("(EXACT same setup as Claude Code CLI!)")
print("=" * 60)
print()

# Check project ID
if not GOOGLE_PROJECT_ID:
    print("❌ GOOGLE_PROJECT_ID not set in .env")
    exit(1)
else:
    print(f"✓ Project ID: {GOOGLE_PROJECT_ID}")
    print(f"✓ Region: {GOOGLE_LOCATION}")
    print(f"✓ Model: {MODEL_NAME}")

# Check credentials
import os.path
creds_file = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
if os.path.exists(creds_file):
    print(f"✓ Credentials found: {creds_file}")
else:
    print("❌ Application default credentials not found")
    print("   Run: gcloud auth application-default login")
    exit(1)

# Try to import ChatAnthropicVertex
print()
print("Checking langchain-anthropic...")
try:
    from langchain_anthropic import ChatAnthropicVertex
    print("✓ ChatAnthropicVertex available")
except ImportError:
    print("❌ ChatAnthropicVertex not available")
    print("   Updating langchain-anthropic...")
    import subprocess
    subprocess.run(["pip", "install", "-U", "langchain-anthropic"], check=True)
    from langchain_anthropic import ChatAnthropicVertex
    print("✓ ChatAnthropicVertex installed")

# Create client
print()
print("Creating Claude via Vertex AI client...")
try:
    llm = ChatAnthropicVertex(
        model=MODEL_NAME,
        project_id=GOOGLE_PROJECT_ID,
        region=GOOGLE_LOCATION,
        temperature=0,
        timeout=30,
    )
    print("✓ Client created successfully")
except Exception as e:
    print(f"❌ Failed to create client: {e}")
    exit(1)

# Test query
print()
print("Testing simple query (may take 5-10 seconds)...")
print()
try:
    response = llm.invoke("Say 'Claude via Vertex AI is working!' in exactly 6 words")
    print(f"✓ Response: {response.content}")
    print()
    print("=" * 60)
    print("✅ SUCCESS! Claude via Vertex AI is working!")
    print("=" * 60)
    print()
    print("Your chatbot is configured to use the EXACT same")
    print("authentication and model as Claude Code CLI!")
    print()
    print("Next steps:")
    print("  1. Run: ./start-chatbot.sh")
    print("  2. Visit: http://localhost:8501")
    print("  3. Ask: 'Check health status of demo.example.local'")
    print()
    print("Expected: 5-10 second response (same as Claude Code!)")
except Exception as e:
    print(f"❌ Query failed: {e}")
    print()
    if "403" in str(e) or "PERMISSION_DENIED" in str(e):
        print("Permission error:")
        print("  Your GCP account may not have Vertex AI permissions.")
        print("  Since Claude Code works, this shouldn't happen.")
        print()
        print("  Try refreshing your credentials:")
        print("    gcloud auth application-default login")
    elif "404" in str(e) or "not found" in str(e).lower():
        print("Model not found:")
        print(f"  The model '{MODEL_NAME}' is not available in {GOOGLE_LOCATION}")
        print()
        print("  Try a different region:")
        print("    GOOGLE_LOCATION=us-east5")
        print()
        print("  Or check available models:")
        print(f"    gcloud ai models list --region={GOOGLE_LOCATION}")
    else:
        print("Unexpected error. Full details above.")
    exit(1)
