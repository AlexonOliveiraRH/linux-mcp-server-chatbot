"""
Wrapper for Claude via Vertex AI to work with LangChain agents.
Uses the exact same authentication as Claude Code CLI!
"""
from typing import Any, List, Optional, Sequence, Union, Dict, Callable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable, RunnableConfig
from anthropic import AnthropicVertex
from anthropic.types import ToolUseBlock, TextBlock
from pydantic import PrivateAttr
import json


def _convert_tool_to_anthropic_format(tool: Union[Dict, BaseTool, Callable]) -> dict:
    """Convert LangChain tool to Anthropic format."""
    if isinstance(tool, dict):
        # Already in dict format
        return {
            "name": tool.get("name", ""),
            "description": tool.get("description", ""),
            "input_schema": tool.get("parameters", {"type": "object", "properties": {}})
        }
    elif hasattr(tool, 'name') and hasattr(tool, 'description'):
        # BaseTool or similar
        schema = {"type": "object", "properties": {}}
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema.schema() if hasattr(tool.args_schema, 'schema') else schema
        return {
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": schema
        }
    else:
        raise ValueError(f"Unsupported tool type: {type(tool)}")


class ClaudeVertexChat(BaseChatModel):
    """Claude via Vertex AI chat model (same auth as Claude Code CLI)."""

    project_id: str
    region: str
    model: str = "claude-sonnet-4-5@20250929"
    temperature: float = 0
    max_tokens: int = 4096
    timeout: float = 120

    # Use PrivateAttr for proper Pydantic handling
    _tools: Optional[List[dict]] = PrivateAttr(default=None)
    _client: Optional[AnthropicVertex] = PrivateAttr(default=None)

    def __init__(self, tools: Optional[List[dict]] = None, **kwargs):
        super().__init__(**kwargs)
        self._client = AnthropicVertex(
            project_id=self.project_id,
            region=self.region,
        )
        self._tools = tools

    def bind_tools(
        self,
        tools: Sequence[Union[Dict[str, Any], type, Callable, BaseTool]],
        **kwargs: Any,
    ) -> Runnable:
        """Bind tools to the model."""
        # Convert tools to Anthropic format
        anthropic_tools = [_convert_tool_to_anthropic_format(tool) for tool in tools]

        # Create a new instance with tools bound
        return self.__class__(
            project_id=self.project_id,
            region=self.region,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            tools=anthropic_tools,  # Pass as 'tools' parameter, not '_tools'
        )

    def _convert_messages(self, messages: List[BaseMessage]) -> tuple:
        """Convert LangChain messages to Anthropic format."""
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_message = msg.content
            elif isinstance(msg, HumanMessage):
                anthropic_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif isinstance(msg, ToolMessage):
                # Tool results go back to the user
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content
                    }]
                })
            elif isinstance(msg, AIMessage):
                # Handle tool calls in AI messages
                content = msg.content
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # Convert tool calls to Anthropic format
                    tool_use_content = []
                    if content:
                        tool_use_content.append({"type": "text", "text": content})
                    for tool_call in msg.tool_calls:
                        tool_use_content.append({
                            "type": "tool_use",
                            "id": tool_call.get("id", ""),
                            "name": tool_call.get("name", ""),
                            "input": tool_call.get("args", {})
                        })
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": tool_use_content
                    })
                else:
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": content
                    })

        return system_message, anthropic_messages

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response from Claude via Vertex AI."""
        system_message, anthropic_messages = self._convert_messages(messages)

        # Prepare request parameters
        request_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": anthropic_messages,
            "temperature": self.temperature,
        }

        if system_message:
            request_params["system"] = system_message

        # Add tools if bound
        if self._tools:
            request_params["tools"] = self._tools

        # Make API call
        response = self._client.messages.create(**request_params)

        # Convert response to LangChain format
        content = ""
        tool_calls = []

        for block in response.content:
            if isinstance(block, TextBlock) or hasattr(block, 'text'):
                content += block.text
            elif isinstance(block, ToolUseBlock) or (hasattr(block, 'type') and block.type == 'tool_use'):
                # Extract tool call
                tool_calls.append({
                    "name": block.name,
                    "args": block.input,
                    "id": block.id,
                })

        message = AIMessage(content=content)
        if tool_calls:
            message.tool_calls = tool_calls

        generation = ChatGeneration(message=message)

        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "claude-vertex"

    @property
    def _identifying_params(self) -> dict:
        """Return identifying parameters."""
        return {
            "model": self.model,
            "project_id": self.project_id,
            "region": self.region,
        }
