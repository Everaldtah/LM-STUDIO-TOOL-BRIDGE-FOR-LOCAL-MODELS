#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LM Bridge - Voice-First Natural Interface
Speak naturally to LM Studio without typing anything
"""

import sys
import os
import io
import json
import time
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
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[38;5;141m'
    GREEN = '\033[38;5;82m'
    BLUE = '\033[38;5;75m'
    CYAN = '\033[38;5;43m'
    WHITE = '\033[37m'
    GRAY = '\033[38;5;245m'


class VoiceBridge:
    """Voice-first natural interface for LM Studio"""

    def __init__(self):
        self.listening = False
        self.conversation_history = []

    def print_header(self):
        """Print the voice interface header"""
        width = 58
        print()
        print(C.ORANGE + '╭' + '─' * width + '╮' + C.RESET)
        print(C.ORANGE + '│' + C.RESET + ' ' * width + C.ORANGE + '│' + C.RESET)
        print(C.ORANGE + '│' + C.RESET + C.BOLD + C.ORANGE + '     LMBRIDGE VOICE MODE' + C.RESET + '              v1.0.0   ' + C.ORANGE + '│' + C.RESET)
        print(C.ORANGE + '│' + C.RESET + ' ' * width + C.ORANGE + '│' + C.RESET)
        print(C.ORANGE + '╰' + '─' * width + '╯' + C.RESET)
        print()
        print(C.WHITE + '    ' + C.CYAN + '●' + C.RESET + C.WHITE + ' Speak naturally - no typing required' + C.RESET)
        print(C.WHITE + '    ' + C.GREEN + '●' + C.RESET + C.WHITE + ' AI detects commands vs conversations' + C.RESET)
        print(C.WHITE + '    ' + C.PURPLE + '●' + C.RESET + C.WHITE + ' Responses spoken aloud' + C.RESET)
        print()
        print(C.GRAY + '    Commands: ' + C.CYAN + '/listen' + C.GRAY + ' | ' + C.CYAN + '/stop' + C.GRAY + ' | ' + C.CYAN + '/type' + C.GRAY + ' | ' + C.CYAN + '/exit' + C.RESET)
        print()

    def execute_powershell(self, command):
        """Execute PowerShell command and return result"""
        try:
            result = subprocess.run(
                [POWERSHELL_EXE, "-Command", command],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=COMMAND_TIMEOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "return_code": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_to_model(self, user_input, tool_results=None):
        """Send input to LM Studio and get response"""
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # Add previous tool results if any
        if tool_results:
            for result in tool_results:
                self.conversation_history.append({
                    "role": "tool",
                    "content": json.dumps(result)
                })

        payload = {
            "model": "local-model",
            "messages": self.conversation_history,
            "temperature": 0.7,
            "max_tokens": 1024,
            "tools": [TOOL_SCHEMA],
            "tool_choice": "auto"
        }

        try:
            response = requests.post(
                LM_STUDIO_CHAT_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            if "choices" in data and data["choices"]:
                message = data["choices"][0].get("message", {})
                self.conversation_history.append(message)

                # Check for tool calls
                tool_calls = message.get("tool_calls")
                if tool_calls:
                    return self.handle_tool_calls(tool_calls)

                return message.get("content", "")

        except Exception as e:
            return f"Error: {str(e)}"

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

                result = self.execute_powershell(command)
                tool_results.append({
                    "role": "tool",
                    "content": json.dumps(result)
                })

                if result.get("success") and result.get("stdout"):
                    print(C.GREEN + '  ✓ ' + C.RESET + C.WHITE + 'Output:' + C.RESET)
                    for line in result["stdout"].split('\n')[:10]:
                        print(f'    {C.GRAY}{line}{C.RESET}')

        # Get final response after tool execution
        return self.send_to_model("", tool_results)

    def speak(self, text):
        """Speak text using Windows speech synthesis"""
        if not text or text.startswith("Error"):
            return

        # Clean up text for speech
        clean_text = text
        for prefix in ["Here's the output:", "Output:", "The result is:", "✓"]:
            clean_text = clean_text.replace(prefix, "").strip()

        try:
            # Remove ANSI codes
            import re
            clean_text = re.sub(r'\033\[[0-9;]*m', '', clean_text)

            # Use PowerShell to speak
            ps_cmd = f'Add-Type -AssemblyName System.Speech; ' \
                     f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; ' \
                     f'$speak.Speak("{clean_text[:300]}")'
            subprocess.run(["powershell", "-Command", ps_cmd],
                          creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

    def listen_once(self):
        """Listen for voice input once"""
        print()
        print(C.CYAN + '  🎙 Listening...' + C.RESET)

        try:
            # Use Windows Speech Recognition
            ps_script = '''
            Add-Type -AssemblyName System.Speech
            $recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
            $recognizer.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
            $recognizer.SetInputToDefaultAudioDevice()

            $result = $recognizer.Recognize()
            $result.Text
            '''

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=10
            )

            if result.stdout and result.stdout.strip():
                return result.stdout.strip()
            else:
                return None

        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(C.RED + f'  ⚠ Speech recognition error: {e}' + C.RESET)
            return None

    def get_console_input(self):
        """Get input from console with natural feel"""
        print()
        user_input = input(C.GREEN + 'you> ' + C.RESET).strip()
        return user_input if user_input else None

    def run_voice_mode(self):
        """Run the voice-first interface"""
        self.print_header()

        print(C.WHITE + '    Press ' + C.CYAN + 'Enter' + C.WHITE + ' to start listening, or type to input directly' + C.RESET)
        print()

        # Check for speech recognition
        try:
            subprocess.run(["powershell", "-Command", "Add-Type -AssemblyName System.Speech"],
                          capture_output=True, timeout=2)
            has_speech = True
        except:
            has_speech = False

        if has_speech:
            print(C.GREEN + '    ✓ Speech recognition available' + C.RESET)
        else:
            print(C.YELLOW + '    ⚠ Speech not available, using text input' + C.RESET)

        print()

        while True:
            try:
                print(C.ORANGE + '────────────────────────────────────────────────' + C.RESET)

                # Get input
                if has_speech:
                    print(C.CYAN + '🎙 Press Enter to listen... ' + C.RESET, end='', flush=True)
                    input()

                    print('\r' + ' ' * 50 + '\r', end='', flush=True)

                    voice_input = self.listen_once()

                    if voice_input:
                        user_input = voice_input
                        print(C.GREEN + 'you> ' + C.RESET + C.WHITE + voice_input + C.RESET)
                    else:
                        print(C.YELLOW + '  (No speech detected, type instead)' + C.RESET)
                        user_input = self.get_console_input()
                        if not user_input:
                            continue
                else:
                    user_input = self.get_console_input()
                    if not user_input:
                        continue

                # Handle commands
                if user_input.lower() in ['/exit', 'exit', 'quit']:
                    print(C.YELLOW + '\n    Goodbye!\n' + C.RESET)
                    break

                if user_input.lower() == '/stop':
                    print(C.YELLOW + '    Stopping...\n' + C.RESET)
                    break

                if user_input.lower() == '/listen':
                    self.listening = not self.listening
                    print(C.CYAN + f'    Continuous listening: {"ON" if self.listening else "OFF"}' + C.RESET)
                    continue

                if user_input.lower() == '/type':
                    # Manual input mode
                    manual_input = input(C.GREEN + 'you> ' + C.RESET)
                    if manual_input:
                        user_input = manual_input
                    else:
                        continue

                # Send to model
                print()
                print(C.PURPLE + '🤖 ' + C.RESET + C.WHITE + 'Thinking...' + C.RESET)

                response = self.send_to_model(user_input)

                if response:
                    print()
                    print(C.PURPLE + 'ai> ' + C.RESET + C.WHITE + response + C.RESET)
                    print()

                    # Speak the response
                    self.speak(response)

                print(C.ORANGE + '────────────────────────────────────────────────' + C.RESET)

            except KeyboardInterrupt:
                print(C.YELLOW + '\n\n    Use /exit to quit\n' + C.RESET)
            except EOFError:
                break


def main():
    """Main entry point"""
    bridge = VoiceBridge()
    bridge.run_voice_mode()


if __name__ == '__main__':
    main()
