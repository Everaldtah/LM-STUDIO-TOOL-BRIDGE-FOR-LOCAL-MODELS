"""
Tool router module for LM Studio Terminal Bridge.

Detects, validates, and routes tool calls from the LLM to appropriate handlers.
"""

import json
from typing import Dict, Any, Callable, Optional, List
from enum import Enum

from logger import get_logger, BridgeLogger
from terminal_executor import PowerShellExecutor
from config import TOOL_SCHEMA, RESPONSE_KEYS


class ToolType(Enum):
    """Enumeration of available tool types."""
    POWERSHELL = "run_powershell_command"


class ToolCall:
    """
    Represents a tool call from the LLM.

    Encapsulates the tool name, arguments, and metadata.
    """

    def __init__(self, name: str, arguments: Dict[str, Any], call_id: str = ""):
        """
        Initialize a tool call.

        Args:
            name: The name of the tool being called
            arguments: Dictionary of arguments passed to the tool
            call_id: Unique identifier for the tool call
        """
        self.name = name
        self.arguments = arguments
        self.call_id = call_id
        self.logger = get_logger("bridge.router")

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the tool call parameters.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.name:
            return False, "Tool name is required"

        if self.name == ToolType.POWERSHELL.value:
            if "command" not in self.arguments:
                return False, "PowerShell tool requires 'command' parameter"

            command = self.arguments.get("command", "")
            if not command or not command.strip():
                return False, "Command cannot be empty"

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool call to dictionary representation."""
        return {
            "name": self.name,
            "arguments": self.arguments,
            "call_id": self.call_id
        }


class ToolRouter:
    """
    Routes tool calls to appropriate handlers.

    Manages tool registration, validation, and execution routing.
    """

    def __init__(self):
        """Initialize the tool router."""
        self.logger = get_logger("bridge.router")
        self.executor = PowerShellExecutor()
        self._tools: Dict[str, Callable] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the default tool handlers."""
        self.register_tool(
            ToolType.POWERSHELL.value,
            self._execute_powershell
        )
        self.logger.info(f"Registered {len(self._tools)} tools")

    def register_tool(self, name: str, handler: Callable) -> None:
        """
        Register a tool handler.

        Args:
            name: The tool name
            handler: The function to handle the tool call
        """
        self._tools[name] = handler
        self.logger.debug(f"Registered tool: {name}")

    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool handler.

        Args:
            name: The tool name to unregister

        Returns:
            True if tool was unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            self.logger.debug(f"Unregistered tool: {name}")
            return True
        return False

    def route(self, tool_call: ToolCall) -> Dict[str, Any]:
        """
        Route a tool call to its handler.

        Args:
            tool_call: The tool call to route

        Returns:
            Dictionary result from the tool execution
        """
        # Log the tool call
        BridgeLogger.log_tool_call(
            tool_call.name,
            tool_call.arguments
        )

        # Validate the tool call
        is_valid, error_msg = tool_call.validate()
        if not is_valid:
            self.logger.error(f"Invalid tool call: {error_msg}")
            return {
                RESPONSE_KEYS["success"]: False,
                RESPONSE_KEYS["error"]: f"Validation error: {error_msg}"
            }

        # Route to handler
        if tool_call.name not in self._tools:
            self.logger.error(f"Unknown tool: {tool_call.name}")
            return {
                RESPONSE_KEYS["success"]: False,
                RESPONSE_KEYS["error"]: f"Unknown tool: {tool_call.name}"
            }

        try:
            handler = self._tools[tool_call.name]
            result = handler(**tool_call.arguments)
            return result

        except Exception as e:
            self.logger.exception(f"Error executing tool {tool_call.name}: {e}")
            return {
                RESPONSE_KEYS["success"]: False,
                RESPONSE_KEYS["error"]: f"Execution error: {str(e)}"
            }

    def route_from_json(self, json_data: str) -> Dict[str, Any]:
        """
        Route a tool call from JSON string.

        Args:
            json_data: JSON string containing tool call data

        Returns:
            Dictionary result from the tool execution
        """
        try:
            data = json.loads(json_data)
            tool_name = data.get("name", "")
            arguments = data.get("arguments", {})
            call_id = data.get("call_id", "")

            tool_call = ToolCall(tool_name, arguments, call_id)
            return self.route(tool_call)

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in tool call: {e}")
            return {
                RESPONSE_KEYS["success"]: False,
                RESPONSE_KEYS["error"]: f"Invalid JSON: {str(e)}"
            }

    def route_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a tool call from dictionary.

        Args:
            data: Dictionary containing tool call data

        Returns:
            Dictionary result from the tool execution
        """
        tool_name = data.get("name", "")
        arguments = data.get("arguments", {})
        call_id = data.get("call_id", "")

        tool_call = ToolCall(tool_name, arguments, call_id)
        return self.route(tool_call)

    def get_registered_tools(self) -> List[str]:
        """
        Get list of registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get the tool schemas for the LLM.

        Returns:
            List of tool schema dictionaries
        """
        return [TOOL_SCHEMA]

    def _execute_powershell(self, command: str) -> Dict[str, Any]:
        """
        Execute a PowerShell command.

        Args:
            command: The PowerShell command to execute

        Returns:
            Execution result dictionary
        """
        return self.executor.execute(command)


class ToolResult:
    """
    Represents the result of a tool execution.

    Provides structured result formatting and serialization.
    """

    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Initialize a tool result.

        Args:
            success: Whether the tool execution was successful
            data: Result data from the tool
            error: Error message if execution failed
        """
        self.success = success
        self.data = data or {}
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {
            RESPONSE_KEYS["success"]: self.success
        }

        if self.data:
            result.update(self.data)

        if self.error:
            result[RESPONSE_KEYS["error"]] = self.error

        return result

    def to_json(self) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self) -> str:
        """String representation of the result."""
        return f"ToolResult(success={self.success}, error={self.error})"
