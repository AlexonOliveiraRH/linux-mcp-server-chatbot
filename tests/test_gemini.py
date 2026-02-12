#!/usr/bin/env python3
"""Quick test for Google Gemini / Vertex AI setup."""
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")

print("=" * 60)
print("Claude via Vertex AI Setup Test")
print("(Same authentication as Claude Code CLI!)")
print("=" * 60)
print()

# Check project ID
if not GOOGLE_PROJECT_ID:
    print("❌ GOOGLE_PROJECT_ID not set in .env")
    print("   Add: GOOGLE_PROJECT_ID=your-project-id")
    exit(1)
else:
    print(f"✓ Project ID: {GOOGLE_PROJECT_ID}")

# Check credentials
import os.path
creds_file = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
if os.path.exists(creds_file):
    print(f"✓ Credentials found: {creds_file}")
else:
    print("❌ Application default credentials not found")
    print("   Run: gcloud auth application-default login")
    exit(1)

# Try to import Vertex AI
try:
    from langchain_google_vertexai import ChatVertexAI
    print("✓ langchain-google-vertexai installed")
except ImportError:
    print("❌ langchain-google-vertexai not installed")
    print("   Run: pip install langchain-google-vertexai google-cloud-aiplatform")
    exit(1)

# Try to create a ChatVertexAI instance
print()
print("Testing Vertex AI connection...")
try:
    # Test with Claude via Vertex AI (same as Claude Code CLI!)
    llm = ChatVertexAI(
        model="claude-sonnet-4-5@20250929",
        project=GOOGLE_PROJECT_ID,
        location="us-central1",
        timeout=30,
    )
    print("✓ ChatVertexAI instance created")
except Exception as e:
    print(f"❌ Failed to create ChatVertexAI: {e}")
    print()
    print("Common fixes:")
    print("  1. Enable Vertex AI API:")
    print(f"     gcloud services enable aiplatform.googleapis.com --project={GOOGLE_PROJECT_ID}")
    print("  2. Re-authenticate:")
    print("     gcloud auth application-default login")
    exit(1)

# Try a simple inference
print()
print("Testing simple query (this may take 5-10 seconds)...")
try:
    response = llm.invoke("Say 'Gemini is working!' in exactly 3 words")
    print(f"✓ Response: {response.content}")
    print()
    print("=" * 60)
    print("✅ All tests passed! Gemini is ready to use.")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run: ./start-chatbot.sh")
    print("  2. Visit: http://localhost:8501")
    print("  3. Ask: 'Check health status of demo.example.local'")
except Exception as e:
    print(f"❌ Query failed: {e}")
    print()
    if "403" in str(e):
        print("Permission error - you may need Vertex AI permissions:")
        print(f"  gcloud projects add-iam-policy-binding {GOOGLE_PROJECT_ID} \\")
        print("    --member=\"user:$(gcloud config get-value account)\" \\")
        print("    --role=\"roles/aiplatform.user\"")
    elif "API" in str(e) and "not enabled" in str(e):
        print("Vertex AI API not enabled. Run:")
        print(f"  gcloud services enable aiplatform.googleapis.com --project={GOOGLE_PROJECT_ID}")
    else:
        print("Check the error above and refer to GOOGLE_GEMINI_SETUP.md")
    exit(1)
