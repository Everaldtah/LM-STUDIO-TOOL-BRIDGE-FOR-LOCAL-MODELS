"""
Terminal executor module for LM Studio Terminal Bridge.

Handles safe execution of PowerShell commands with proper timeout and output capture.
"""

import subprocess
import json
import time
from typing import Dict, Any, Optional

from logger import get_logger, BridgeLogger
from security import SecurityValidator, SecurityError
from config import (
    POWERSHELL_EXE,
    COMMAND_TIMEOUT,
    DEFAULT_ENCODING,
    RESPONSE_KEYS
)


class PowerShellExecutor:
    """
    Executes PowerShell commands safely with proper output capture.

    Provides secure command execution with timeout protection,
    structured output, and comprehensive error handling.
    """

    def __init__(self):
        """Initialize the PowerShell executor."""
        self.logger = get_logger("bridge.executor")
        self.security = SecurityValidator()

    def execute(self, command: str) -> Dict[str, Any]:
        """
        Execute a PowerShell command and return structured output.

        Args:
            command: The PowerShell command to execute

        Returns:
            Dictionary containing:
                - command: The executed command
                - stdout: Standard output
                - stderr: Standard error
                - return_code: Process exit code
                - execution_time: Time in seconds
                - success: Boolean indicating success
                - error: Error message if execution failed
        """
        # Validate command first
        is_valid, error_msg = self.security.validate_command(command)
        if not is_valid:
            self.logger.error(f"Command blocked by security: {error_msg}")
            return {
                RESPONSE_KEYS["command"]: command,
                RESPONSE_KEYS["stdout"]: "",
                RESPONSE_KEYS["stderr"]: error_msg,
                RESPONSE_KEYS["return_code"]: -1,
                RESPONSE_KEYS["execution_time"]: 0.0,
                RESPONSE_KEYS["success"]: False,
                RESPONSE_KEYS["error"]: error_msg
            }

        # Sanitize command
        command = self.security.sanitize_command(command)

        start_time = time.time()
        stdout_text = ""
        stderr_text = ""
        return_code = 0
        error_msg = None

        try:
            self.logger.info(f"Executing: {command}")

            # Execute the command
            result = subprocess.run(
                [POWERSHELL_EXE, "-Command", command],
                capture_output=True,
                text=True,
                encoding=DEFAULT_ENCODING,
                timeout=COMMAND_TIMEOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            stdout_text = result.stdout
            stderr_text = result.stderr
            return_code = result.returncode

        except subprocess.TimeoutExpired:
            return_code = -2
            error_msg = f"Command exceeded timeout of {COMMAND_TIMEOUT} seconds"
            self.logger.error(error_msg)

        except subprocess.CalledProcessError as e:
            return_code = e.returncode
            stderr_text = str(e.stderr) if e.stderr else "Process error occurred"
            error_msg = f"Process error: {stderr_text}"
            self.logger.error(error_msg)

        except FileNotFoundError:
            return_code = -3
            error_msg = f"PowerShell executable not found: {POWERSHELL_EXE}"
            self.logger.error(error_msg)

        except PermissionError:
            return_code = -4
            error_msg = "Permission denied executing command"
            self.logger.error(error_msg)

        except Exception as e:
            return_code = -99
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.exception(f"Unexpected error executing command: {e}")

        execution_time = time.time() - start_time

        # Log the execution
        BridgeLogger.log_command_execution(
            command=command,
            stdout=stdout_text,
            stderr=stderr_text,
            return_code=return_code,
            execution_time=execution_time
        )

        # Build response
        response = {
            RESPONSE_KEYS["command"]: command,
            RESPONSE_KEYS["stdout"]: stdout_text.strip() if stdout_text else "",
            RESPONSE_KEYS["stderr"]: stderr_text.strip() if stderr_text else "",
            RESPONSE_KEYS["return_code"]: return_code,
            RESPONSE_KEYS["execution_time"]: round(execution_time, 3),
            RESPONSE_KEYS["success"]: return_code == 0,
            RESPONSE_KEYS["error"]: error_msg
        }

        return response

    def execute_json(self, command: str) -> str:
        """
        Execute a command and return JSON string output.

        Args:
            command: The PowerShell command to execute

        Returns:
            JSON string containing the execution result
        """
        result = self.execute(command)
        return json.dumps(result, indent=2, ensure_ascii=False)

    @staticmethod
    def format_output(result: Dict[str, Any]) -> str:
        """
        Format execution result for display.

        Args:
            result: The execution result dictionary

        Returns:
            Formatted string for display
        """
        output = []

        if result.get(RESPONSE_KEYS["success"]):
            output.append(f"✓ Command executed in {result[RESPONSE_KEYS['execution_time']]}s")

            if result.get(RESPONSE_KEYS["stdout"]):
                output.append("\n--- Output ---")
                output.append(result[RESPONSE_KEYS["stdout"]])
        else:
            output.append("✗ Command failed")

            if result.get(RESPONSE_KEYS["error"]):
                output.append(f"Error: {result[RESPONSE_KEYS['error']]}")

            if result.get(RESPONSE_KEYS["stderr"]):
                output.append(f"\n--- Error Output ---")
                output.append(result[RESPONSE_KEYS["stderr"]])

        return "\n".join(output)


class CommandBuilder:
    """
    Builder class for constructing PowerShell commands.
    """

    @staticmethod
    def get_process_list() -> str:
        """Get command to list running processes."""
        return "Get-Process | Select-Object Id, ProcessName, CPU, WorkingSet | Format-Table"

    @staticmethod
    def get_services() -> str:
        """Get command to list system services."""
        return "Get-Service | Select-Object Status, Name, DisplayName | Format-Table"

    @staticmethod
    def get_directory_contents(path: str = ".") -> str:
        """
        Get command to list directory contents.

        Args:
            path: Directory path to list

        Returns:
            PowerShell command string
        """
        return f"Get-ChildItem -Path '{path}' | Format-Table Name, Length, LastWriteTime"

    @staticmethod
    def get_file_content(path: str) -> str:
        """
        Get command to read file content.

        Args:
            path: Path to the file

        Returns:
            PowerShell command string
        """
        return f"Get-Content -Path '{path}'"

    @staticmethod
    def get_system_info() -> str:
        """Get command to retrieve system information."""
        return "Get-ComputerInfo | Select-Object OsName, WindowsVersion, CsName, OsHardwareAbstractionLayer"

    @staticmethod
    def get_network_info() -> str:
        """Get command to retrieve network information."""
        return "Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress, InterfaceAlias"

    @staticmethod
    def get_disk_info() -> str:
        """Get command to retrieve disk information."""
        return "Get-Volume | Select-Object DriveLetter, FileSystemLabel, SizeRemaining, Size"

    @staticmethod
    def test_path(path: str) -> str:
        """
        Get command to test if a path exists.

        Args:
            path: Path to test

        Returns:
            PowerShell command string
        """
        return f"Test-Path '{path}'"
