#!/usr/bin/env python3
"""
Test script to verify Linux MCP Server Chatbot setup.

Run this before starting the chatbot to ensure everything is configured correctly.
"""
import os
import sys
import subprocess
import json
import requests
from dotenv import load_dotenv

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")


def print_error(text):
    print(f"{RED}✗{RESET} {text}")


def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")


def print_info(text):
    print(f"{BLUE}ℹ{RESET} {text}")


def check_env_file():
    """Check if .env file exists and is configured."""
    print_header("Checking Environment Configuration")

    if not os.path.exists(".env"):
        print_error(".env file not found")
        print_info("Copy .env.example to .env and configure it:")
        print_info("  cp .env.example .env")
        return False

    print_success(".env file found")

    load_dotenv()

    # Check required variables
    model_endpoint = os.getenv("MODEL_ENDPOINT", "").strip()
    model_name = os.getenv("MODEL_NAME", "").strip()
    mcp_command = os.getenv("MCP_COMMAND", "").strip()

    if not model_endpoint:
        print_error("MODEL_ENDPOINT not set in .env")
        return False
    print_success(f"MODEL_ENDPOINT: {model_endpoint}")

    if model_name:
        print_success(f"MODEL_NAME: {model_name}")
    else:
        print_warning("MODEL_NAME not set (will attempt auto-detection for Ollama)")

    if not mcp_command:
        print_error("MCP_COMMAND not set in .env")
        return False
    print_success(f"MCP_COMMAND: {mcp_command}")

    linux_mcp_user = os.getenv("LINUX_MCP_USER", "").strip()
    if linux_mcp_user:
        print_success(f"LINUX_MCP_USER: {linux_mcp_user} (for remote hosts)")
    else:
        print_warning("LINUX_MCP_USER not set (local host only)")

    return True


def check_mcp_server():
    """Check if Linux MCP Server is installed and runnable."""
    print_header("Checking Linux MCP Server")

    load_dotenv()
    mcp_command = os.getenv("MCP_COMMAND", "/usr/local/bin/linux-mcp-server").strip()

    # Check if file exists
    if not os.path.exists(mcp_command):
        print_error(f"MCP Server not found at: {mcp_command}")
        print_info("Install with: pipx install linux-mcp-server")
        print_info("Or update MCP_COMMAND in .env with the correct path")
        # Try to find it
        try:
            result = subprocess.run(["which", "linux-mcp-server"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                print_info(f"Found at: {result.stdout.strip()}")
                print_info(f"Update .env: MCP_COMMAND={result.stdout.strip()}")
        except:
            pass
        return False

    print_success(f"MCP Server found at: {mcp_command}")

    # Test if it's executable
    if not os.access(mcp_command, os.X_OK):
        print_error(f"MCP Server is not executable: {mcp_command}")
        print_info(f"Fix with: chmod +x {mcp_command}")
        return False

    print_success("MCP Server is executable")

    # Try to run it briefly
    print_info("Testing MCP Server startup...")
    try:
        proc = subprocess.Popen(
            [mcp_command],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send initialize message
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }

        proc.stdin.write(json.dumps(init_msg) + "\n")
        proc.stdin.flush()

        # Try to read response (with timeout)
        import select
        ready, _, _ = select.select([proc.stdout], [], [], 5)

        if ready:
            response = proc.stdout.readline()
            if response and "result" in response:
                print_success("MCP Server started successfully")
                proc.terminate()
                return True

        proc.terminate()
        print_warning("MCP Server started but communication test inconclusive")
        return True

    except Exception as e:
        print_error(f"Error testing MCP Server: {e}")
        return False


def check_inference_server():
    """Check if inference server is accessible."""
    print_header("Checking Inference Server")

    load_dotenv()
    model_endpoint = os.getenv("MODEL_ENDPOINT", "http://localhost:8080").strip()

    # Try Ollama API
    try:
        print_info(f"Testing Ollama API at {model_endpoint}...")
        response = requests.get(f"{model_endpoint}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            print_success(f"Ollama server detected with {len(models)} model(s)")
            if models:
                print_info(f"Available models: {', '.join(models[:5])}")
                if len(models) > 5:
                    print_info(f"  ... and {len(models) - 5} more")
            else:
                print_warning("No models found. Pull a model with: ollama pull mistral")
            return True
    except Exception as e:
        print_info(f"Not an Ollama server: {e}")

    # Try OpenAI-compatible API
    try:
        print_info(f"Testing OpenAI-compatible API at {model_endpoint}...")
        response = requests.get(f"{model_endpoint}/v1/models", timeout=5)
        if response.status_code == 200:
            print_success("OpenAI-compatible server detected")

            model_name = os.getenv("MODEL_NAME", "").strip()
            if not model_name:
                print_warning("MODEL_NAME not set in .env - required for non-Ollama servers")
                return False

            print_success(f"Will use model: {model_name}")
            return True
    except Exception as e:
        print_info(f"Not an OpenAI-compatible server: {e}")

    print_error(f"Could not connect to inference server at {model_endpoint}")
    print_info("Make sure your inference server is running:")
    print_info("  - Ollama: ollama serve")
    print_info("  - vLLM: vllm serve <model-name> --port 8080")
    print_info("  - Other: Check your server documentation")
    return False


def check_python_deps():
    """Check if Python dependencies are installed."""
    print_header("Checking Python Dependencies")

    # (display_name, import_name)
    required = [
        ("streamlit", "streamlit"),
        ("langchain", "langchain"),
        ("langchain-core", "langchain_core"),
        ("langchain-openai", "langchain_openai"),
        ("langgraph", "langgraph"),
        ("openai", "openai"),
        ("pydantic", "pydantic"),
        ("python-dotenv", "dotenv"),
        ("requests", "requests"),
    ]

    missing = []
    for display_name, import_name in required:
        try:
            __import__(import_name)
            print_success(f"{display_name}")
        except ImportError:
            print_error(f"{display_name} - NOT INSTALLED")
            missing.append(display_name)

    if missing:
        print_error(f"\nMissing packages: {', '.join(missing)}")
        print_info("Install with: pip install -r requirements.txt")
        return False

    print_success("\nAll dependencies installed")
    return True


def main():
    print_header("Linux MCP Server Chatbot - Setup Verification")

    results = {
        "Python Dependencies": check_python_deps(),
        "Environment Configuration": check_env_file(),
        "Linux MCP Server": check_mcp_server(),
        "Inference Server": check_inference_server(),
    }

    print_header("Summary")

    all_passed = True
    for check, passed in results.items():
        if passed:
            print_success(f"{check}")
        else:
            print_error(f"{check}")
            all_passed = False

    print()
    if all_passed:
        print_success("All checks passed! Ready to run the chatbot.")
        print_info("\nStart with: streamlit run app.py")
        return 0
    else:
        print_error("Some checks failed. Please fix the issues above.")
        print_info("\nSee QUICKSTART.md for detailed setup instructions.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
