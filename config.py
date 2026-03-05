"""
Configuration module for LM Studio Terminal Bridge.

Contains all configuration variables and constants used throughout the application.
"""

from pathlib import Path
from typing import List

# Project Information
PROJECT_NAME = "LMSTUDIO_TERMINAL_BRIDGE"
VERSION = "1.0.0"

# LM Studio API Configuration
LM_STUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
LM_STUDIO_CHAT_ENDPOINT = f"{LM_STUDIO_BASE_URL}/chat/completions"

# Model Configuration
DEFAULT_MODEL = "local-model"  # LM Studio typically uses this or the actual model name
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048

# Tool Definition
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_powershell_command",
        "description": "Execute a PowerShell command on the local system. "
                      "Use this tool when you need to run PowerShell commands, "
                      "get system information, or perform system operations.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The PowerShell command to execute"
                }
            },
            "required": ["command"]
        }
    }
}

# PowerShell Execution Configuration
POWERSHELL_EXE = "powershell.exe"
COMMAND_TIMEOUT = 15  # seconds
DEFAULT_ENCODING = "utf-8"

# Security Configuration
# Dangerous commands that are completely blocked
BLOCKED_COMMANDS = [
    # PowerShell dangerous commands
    "Remove-Item",
    "Remove-ItemProperty",
    "Remove-Module",
    "Remove-PSDrive",
    "Remove-Variable",
    "Remove-Function",
    "Stop-Computer",
    "Restart-Computer",
    "Set-ExecutionPolicy",
    "Disable-SecurityRule",
    "Uninstall-Module",
    "Uninstall-Package",

    # Command prompt dangerous commands
    "del ",
    "delete ",
    "rmdir ",
    "rd ",
    "shutdown",
    "format ",  # format with a space (disk format command)
    " diskpart",
    "fdisk",

    # Additional dangerous patterns
    "rm -rf",
    "rm -r",
    "rm -f",
]

# Protected paths that cannot be targeted
PROTECTED_PATHS = [
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
    "System32",
    "SysWOW64",
]

# Commands that are explicitly allowed (override blocks if needed)
ALLOWED_COMMANDS = [
    "Get-",
    "Set-Location",
    "cd ",
    "ls",
    "dir",
    "Write-Host",
    "Write-Output",
    "Select-Object",
    "Where-Object",
    "ForEach-Object",
    "Get-ChildItem",
    "Get-Process",
    "Get-Service",
    "Get-Content",
    "Test-Path",
    "New-Item",
    "New-Object",
    "Measure-Object",
    "Sort-Object",
    "Group-Object",
    "Format-Table",
    "Format-List",
    "Out-File",
    "Out-String",
    "Export-Csv",
    "ConvertTo-Json",
    "ConvertFrom-Json",
]

# Logging Configuration
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "bridge.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# CLI Configuration
CLI_PROMPT = "bridge> "
CLI_ASK_PREFIX = "ask:"
CLI_EXIT_COMMANDS = ["exit", "quit", "q"]

# Response Structure Keys
RESPONSE_KEYS = {
    "command": "command",
    "stdout": "stdout",
    "stderr": "stderr",
    "return_code": "return_code",
    "execution_time": "execution_time",
    "success": "success",
    "error": "error"
}
