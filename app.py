import os
import json
import time
import requests
import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

from mcp_client import LinuxMCPClient

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------
load_dotenv()

MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "http://localhost:8080") + "/v1"
MODEL_NAME = os.getenv("MODEL_NAME", "")
MODEL_BEARER = os.getenv("MODEL_ENDPOINT_BEARER")

MCP_REMOTE_HOST = os.getenv("MCP_REMOTE_HOST")

REQUEST_KWARGS = {}
if MODEL_BEARER:
    REQUEST_KWARGS = {
        "headers": {"Authorization": f"Bearer {MODEL_BEARER}"}
    }

# -----------------------------------------------------------------------------
# MCP Tool
# -----------------------------------------------------------------------------
mcp = LinuxMCPClient(host=MCP_REMOTE_HOST)

def linux_mcp_tool_runner(input: str) -> str:
    """
    Expected JSON:
    {
      "tool": "cpu_info | disk_usage | memory | journal_errors | ps",
      "args": {}
    }
    """
    data = json.loads(input)
    return mcp.run(
        tool=data["tool"],
        args=data.get("args", {})
    )

linux_mcp_tool = Tool(
    name="linux_mcp",
    description=(
        "Run safe diagnostic commands on a remote RHEL system "
        "using Linux MCP Server. Use only when system data is required."
    ),
    func=linux_mcp_tool_runner
)

# -----------------------------------------------------------------------------
# Model availability check
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def checking_model_service():
    while True:
        try:
            r = requests.get(f"{MODEL_ENDPOINT}/models", **REQUEST_KWARGS)
            if r.status_code == 200:
                return "OpenAI-Compatible"
        except:
            pass
        time.sleep(1)

# -----------------------------------------------------------------------------
# Streamlit UI
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Linux MCP Server Chatbot")
st.title("💬 Linux MCP Server Chatbot (Lightspeed-style)")

with st.spinner("Checking model service..."):
    server = checking_model_service()

# -----------------------------------------------------------------------------
# Memory
# -----------------------------------------------------------------------------
@st.cache_resource
def memory():
    return ConversationBufferWindowMemory(
        return_messages=True,
        k=4
    )

# -----------------------------------------------------------------------------
# LLM
# -----------------------------------------------------------------------------
llm = ChatOpenAI(
    base_url=MODEL_ENDPOINT,
    api_key="sk-no-key-required" if not MODEL_BEARER else MODEL_BEARER,
    model=MODEL_NAME,
    streaming=True
)

# -----------------------------------------------------------------------------
# Prompt
# -----------------------------------------------------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system",
     """You are a world-class Linux and Kubernetes technical advisor.

You may use tools to retrieve real system information.
Only use tools when necessary.
When calling a tool, respond ONLY with valid JSON.

Example:
{
  "tool": "linux_mcp",
  "args": {
    "tool": "disk_usage",
    "args": {}
  }
}
"""),
    MessagesPlaceholder(variable_name="history"),
    ("user", "{input}")
])

# -----------------------------------------------------------------------------
# Agent
# -----------------------------------------------------------------------------
agent = initialize_agent(
    tools=[linux_mcp_tool],
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    memory=memory(),
    verbose=True
)

# -----------------------------------------------------------------------------
# Chat state
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you today?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------------------------------------------------------
# Input
# -----------------------------------------------------------------------------
if user_input := st.chat_input("Ask about your RHEL system…"):
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )
    st.chat_message("user").write(user_input)

    with st.spinner("Thinking…"):
        result = agent.invoke({"input": user_input})
        answer = result["output"]

    st.chat_message("assistant").write(answer)
    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

