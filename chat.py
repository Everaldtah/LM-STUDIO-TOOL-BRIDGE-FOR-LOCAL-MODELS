#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LM Bridge - Natural Chat Interface
Type naturally without any prefix - AI handles everything
"""

import sys
import os
import io
import json
import subprocess
import threading
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import requests
from config import LM_STUDIO_CHAT_ENDPOINT, TOOL_SCHEMA, POWERSHELL_EXE, COMMAND_TIMEOUT

# ANSI Colors
class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[38;5;141m'
    GREEN = '\033[38;5;82m'
    BLUE = '\033[38;5;75m'
    CYAN = '\033[38;5;43m'
    WHITE = '\033[37m'
    GRAY = '\033[38;5;245m'
    YELLOW = '\033[38;5;226m'
    RED = '\033[38;5;203m'


class NaturalChatBridge:
    """Natural chat interface - no prefixes needed"""

    def __init__(self):
        self.conversation_history = []
        self.running = True
        self.request_timeout = 120  # Increased from 60 to 120 seconds

        # Set system prompt
        self.conversation_history.append({
            "role": "system",
            "content": """You are a helpful AI assistant with access to PowerShell commands on Windows.

IMPORTANT RULES:
1. Keep responses concise and helpful
2. When users ask about WiFi, networks, or system info, ALWAYS use the run_powershell_command tool
3. For WiFi networks: use "netsh wlan show networks mode=bssid" (not "show network profiles")
4. Show command output clearly - format it for readability
5. If a command fails, explain why and suggest alternatives
6. The user types naturally - just respond helpfully

Available tool: run_powershell_command - Execute PowerShell commands with parameter "command""""
        })

    def print_header(self):
        """Print the chat interface header"""
        width = 58
        print()
        print(C.ORANGE + '╭' + '─' * width + '╮' + C.RESET)
        print(C.ORANGE + '│' + C.RESET + ' ' * width + C.ORANGE + '│' + C.RESET)
        print(C.ORANGE + '│' + C.RESET + C.BOLD + C.ORANGE + '     LMBRIDGE NATURAL CHAT' + C.RESET + '           v1.0.0   ' + C.ORANGE + '│' + C.RESET)
        print(C.ORANGE + '│' + C.RESET + ' ' * width + C.ORANGE + '│' + C.RESET)
        print(C.ORANGE + '╰' + '─' * width + '╯' + C.RESET)
        print()
        print(C.WHITE + '    ' + C.CYAN + '●' + C.RESET + C.WHITE + ' Type naturally - no prefixes needed' + C.RESET)
        print(C.WHITE + '    ' + C.GREEN + '●' + C.RESET + C.WHITE + ' AI handles PowerShell commands automatically' + C.RESET)
        print(C.WHITE + '    ' + C.PURPLE + '●' + C.RESET + C.WHITE + ' Just ask, like you would ChatGPT' + C.RESET)
        print()
        print(C.GRAY + '    Type ' + C.CYAN + '/exit' + C.GRAY + ' or ' + C.CYAN + '/quit' + C.GRAY + ' to leave' + C.RESET)
        print(C.ORANGE + '────────────────────────────────────────────────' + C.RESET)
        print()

    def execute_powershell(self, command):
        """Execute PowerShell command and return result"""
        try:
            # For certain commands, we might need longer timeout
            timeout = COMMAND_TIMEOUT
            if 'netsh' in command.lower() or 'scan' in command.lower():
                timeout = 30  # Longer timeout for network commands

            result = subprocess.run(
                [POWERSHELL_EXE, "-Command", command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_to_model(self, user_input, tool_results=None):
        """Send input to LM Studio and get response"""
        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Add tool results if any
        if tool_results:
            for result in tool_results:
                self.conversation_history.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": result.get("tool_call_id", "")
                })

        # Build request
        payload = {
            "model": "local-model",
            "messages": self.conversation_history,
            "temperature": 0.7,
            "max_tokens": 2048,
            "tools": [TOOL_SCHEMA],
            "tool_choice": "auto"
        }

        try:
            response = requests.post(
                LM_STUDIO_CHAT_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.request_timeout
            )
            response.raise_for_status()
            data = response.json()

            if "choices" not in data or not data["choices"]:
                return "Error: No response from model"

            message = data["choices"][0].get("message", {})
            self.conversation_history.append(message)

            # Check for tool calls
            tool_calls = message.get("tool_calls")
            if tool_calls:
                return self.handle_tool_calls(tool_calls)

            # Return text content
            content = message.get("content", "")
            if content:
                return content
            return "I'm sorry, I couldn't generate a response."

        except requests.exceptions.Timeout:
            return C.RED + "Request timed out. The model took too long to respond. Try a shorter prompt or use a faster model." + C.RESET
        except requests.exceptions.ConnectionError:
            return C.RED + "Cannot connect to LM Studio. Make sure it's running with the API server enabled on port 1234." + C.RESET
        except Exception as e:
            return f"{C.RED}Error:{C.RESET} {str(e)}"

    def handle_tool_calls(self, tool_calls):
        """Handle tool calls from the model"""
        tool_results = []

        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            function_name = function.get("name")
            arguments = json.loads(function.get("arguments", "{}"))

            if function_name == "run_powershell_command":
                command = arguments.get("command", "")

                print()
                print(C.BLUE + '  ⚙ ' + C.RESET + C.WHITE + f'Executing: {command}' + C.RESET)
                print(C.GRAY + '  ' + '─' * 50 + C.RESET)

                result = self.execute_powershell(command)

                # Store tool call ID for response
                result["tool_call_id"] = tool_call.get("id", "")
                tool_results.append(result)

                if result.get("success"):
                    if result.get("stdout"):
                        output_lines = result["stdout"].split('\n')
                        # Show first 20 lines
                        for line in output_lines[:20]:
                            print(f'    {C.GRAY}{line}{C.RESET}')
                        if len(output_lines) > 20:
                            print(f'    {C.DIM}... ({len(output_lines) - 20} more lines){C.RESET}')
                else:
                    error = result.get("error", result.get("stderr", "Unknown error"))
                    print(C.YELLOW + f'  ⚠ Error: {error}' + C.RESET)

                print()

        # Get final response from model after tool execution
        print(C.PURPLE + 'ai>  ' + C.RESET + C.GRAY + 'Processing results...' + C.RESET, end='', flush=True)
        return self.send_to_model("", tool_results)

    def run(self):
        """Run the natural chat interface"""
        self.print_header()

        # Test connection
        print(C.CYAN + '  Checking connection to LM Studio...' + C.RESET, end='', flush=True)
        try:
            response = requests.get(
                LM_STUDIO_CHAT_ENDPOINT.replace("/chat/completions", "/models"),
                timeout=5
            )
            if response.status_code == 200:
                print(C.GREEN + ' ✓ Connected' + C.RESET)
            else:
                print(C.YELLOW + f ' ⚠ API returned status {response.status_code}' + C.RESET)
        except Exception as e:
            print(C.YELLOW + f ' ⚠ Could not connect: {e}' + C.RESET)
            print()
            print(C.WHITE + '  Make sure LM Studio is running:' + C.RESET)
            print(C.WHITE + '  1. Open LM Studio' + C.RESET)
            print(C.WHITE + '  2. Click the Server icon (⟠)' + C.RESET)
            print(C.WHITE + '  3. Enable "Enable Server"' + C.RESET)
            print(C.WHITE + '  4. Port should be 1234' + C.RESET)

        print()
        print(C.ORANGE + '────────────────────────────────────────────────' + C.RESET)

        while self.running:
            try:
                # Get user input
                user_input = input(C.GREEN + 'you> ' + C.RESET).strip()

                if not user_input:
                    continue

                # Handle exit commands
                if user_input.lower() in ['/exit', '/quit', 'exit', 'quit']:
                    print()
                    print(C.YELLOW + '    Goodbye!' + C.RESET)
                    print()
                    break

                # Clear screen command
                if user_input.lower() in ['/clear', 'clear']:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.print_header()
                    continue

                # Direct command mode (start with !)
                if user_input.startswith('!'):
                    direct_command = user_input[1:].strip()
                    print()
                    print(C.BLUE + '  ⚙ ' + C.RESET + C.WHITE + f'Direct: {direct_command}' + C.RESET)
                    result = self.execute_powershell(direct_command)
                    if result.get("success"):
                        if result.get("stdout"):
                            for line in result["stdout"].split('\n')[:20]:
                                print(f'    {C.GRAY}{line}{C.RESET}')
                    else:
                        print(C.YELLOW + f'  ⚠ {result.get("error", "Unknown error")}' + C.RESET)
                    print()
                    print(C.ORANGE + '────────────────────────────────────────────────' + C.RESET)
                    continue

                # Show thinking indicator
                print()
                print(C.PURPLE + 'ai>  ' + C.RESET + C.GRAY + 'Thinking...' + C.RESET, end='', flush=True)

                # Get response from model
                response = self.send_to_model(user_input)

                # Clear thinking line and show response
                print('\r' + ' ' * 60 + '\r', end='')
                print(C.PURPLE + 'ai>  ' + C.RESET + C.WHITE + response + C.RESET)
                print()
                print(C.ORANGE + '────────────────────────────────────────────────' + C.RESET)

            except KeyboardInterrupt:
                print()
                print(C.YELLOW + '    Use /exit to quit' + C.RESET)
                print(C.ORANGE + '────────────────────────────────────────────────' + C.RESET)
            except EOFError:
                break


def main():
    """Main entry point"""
    bridge = NaturalChatBridge()
    bridge.run()


if __name__ == '__main__':
    main()
