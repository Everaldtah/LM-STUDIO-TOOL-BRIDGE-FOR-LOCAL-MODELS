"""
LLM client module for LM Studio Terminal Bridge.

Handles communication with the LM Studio OpenAI-compatible API.
"""

import json
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

import requests

from logger import get_logger
from config import (
    LM_STUDIO_CHAT_ENDPOINT,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    TOOL_SCHEMA
)


class LMStudioClient:
    """
    Client for communicating with LM Studio's OpenAI-compatible API.

    Supports chat completions with tool calling functionality.
    """

    def __init__(
        self,
        base_url: str = LM_STUDIO_CHAT_ENDPOINT,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ):
        """
        Initialize the LM Studio client.

        Args:
            base_url: The API endpoint URL
            model: The model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = get_logger("bridge.llm_client")
        self.conversation_history: List[Dict[str, Any]] = []

    def send_message(
        self,
        message: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_callbacks: Optional[Dict[str, Callable]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to the model and handle tool calls.

        Args:
            message: The user message to send
            tools: List of tool schemas available to the model
            tool_callbacks: Dictionary mapping tool names to handler functions

        Returns:
            Dictionary containing the model's response and any tool results
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Default tools if not provided
        if tools is None:
            tools = [TOOL_SCHEMA]

        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": self.conversation_history,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": tools,
            "tool_choice": "auto"  # Let the model decide when to use tools
        }

        try:
            self.logger.info(f"Sending request to LM Studio: {message[:100]}...")

            response = requests.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            # Extract the assistant's response
            if "choices" not in data or not data["choices"]:
                self.logger.error("Invalid response format: no choices")
                return {"error": "Invalid response from model"}

            choice = data["choices"][0]
            message_obj = choice.get("message", {})

            # Add assistant response to history
            self.conversation_history.append(message_obj)

            # Check for tool calls
            tool_calls = message_obj.get("tool_calls")
            if tool_calls and tool_callbacks:
                return self._handle_tool_calls(tool_calls, tool_callbacks, tools)

            # Return text response
            return {
                "content": message_obj.get("content", ""),
                "role": "assistant",
                "finish_reason": choice.get("finish_reason", "unknown")
            }

        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to LM Studio. Ensure it's running on the configured port."
            self.logger.error(error_msg)
            return {"error": error_msg}

        except requests.exceptions.Timeout:
            error_msg = "Request to LM Studio timed out"
            self.logger.error(error_msg)
            return {"error": error_msg}

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
            self.logger.error(error_msg)
            return {"error": error_msg}

        except json.JSONDecodeError:
            error_msg = "Invalid JSON response from LM Studio"
            self.logger.error(error_msg)
            return {"error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.exception(error_msg)
            return {"error": error_msg}

    def _handle_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        tool_callbacks: Dict[str, Callable],
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Handle tool calls from the model.

        Args:
            tool_calls: List of tool call objects from the model
            tool_callbacks: Dictionary of tool name to handler function
            tools: Tool schemas for re-sending to model

        Returns:
            Response after executing tool calls
        """
        tool_responses = []

        for tool_call in tool_calls:
            function_name = tool_call.get("function", {}).get("name")
            function_args = tool_call.get("function", {}).get("arguments", "{}")

            self.logger.info(f"Tool call: {function_name} with args: {function_args}")

            # Parse arguments
            try:
                arguments = json.loads(function_args) if isinstance(function_args, str) else function_args
            except json.JSONDecodeError:
                arguments = {"raw": function_args}

            # Execute tool callback
            if function_name in tool_callbacks:
                try:
                    result = tool_callbacks[function_name](**arguments)

                    # Add tool response message
                    tool_response_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", ""),
                        "content": json.dumps(result) if not isinstance(result, str) else result
                    }
                    tool_responses.append(tool_response_message)
                    self.conversation_history.append(tool_response_message)

                except Exception as e:
                    error_msg = f"Error executing {function_name}: {str(e)}"
                    self.logger.error(error_msg)
                    tool_responses.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", ""),
                        "content": json.dumps({"error": error_msg})
                    })
            else:
                self.logger.warning(f"No callback found for tool: {function_name}")

        # Get final response from model after tool execution
        if tool_responses:
            payload = {
                "model": self.model,
                "messages": self.conversation_history,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "tools": tools
            }

            try:
                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()

                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    message_obj = choice.get("message", {})
                    self.conversation_history.append(message_obj)

                    return {
                        "content": message_obj.get("content", ""),
                        "role": "assistant",
                        "tool_results": tool_responses,
                        "finish_reason": choice.get("finish_reason", "unknown")
                    }

            except Exception as e:
                self.logger.error(f"Error getting final response: {e}")
                return {"error": f"Error after tool execution: {str(e)}"}

        return {"error": "Tool calls processed but no response received"}

    def reset_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get the current conversation history.

        Returns:
            List of message objects
        """
        return self.conversation_history.copy()

    def set_system_prompt(self, prompt: str) -> None:
        """
        Set or update the system prompt.

        Args:
            prompt: The system prompt to set
        """
        # Remove existing system message if present
        self.conversation_history = [
            msg for msg in self.conversation_history
            if msg.get("role") != "system"
        ]

        # Add new system message at the beginning
        self.conversation_history.insert(0, {
            "role": "system",
            "content": prompt
        })
        self.logger.info("System prompt updated")

    def test_connection(self) -> bool:
        """
        Test the connection to LM Studio.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = requests.get(
                self.base_url.replace("/chat/completions", "/models"),
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.debug(f"Connection test failed: {e}")
            return False
