"""
LM Studio Terminal Bridge - Main Entry Point.

A production-ready tool bridge that allows a local LLM running in LM Studio
to execute PowerShell commands on Windows.

Usage:
    python main.py                    # Start interactive CLI mode
    python main.py --test             # Test connection to LM Studio
    python main.py --execute "cmd"    # Execute a single command
"""

import sys
import json
import argparse
import io
from pathlib import Path
from typing import Optional

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from logger import get_logger, BridgeLogger
from config import (
    PROJECT_NAME,
    VERSION,
    LM_STUDIO_CHAT_ENDPOINT,
    CLI_PROMPT,
    CLI_ASK_PREFIX,
    CLI_EXIT_COMMANDS,
    TOOL_SCHEMA
)
from llm_client import LMStudioClient
from tool_router import ToolRouter
from terminal_executor import PowerShellExecutor
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table


class TerminalBridge:
    """
    Main application class for the LM Studio Terminal Bridge.

    Coordinates communication between the LLM and PowerShell executor.
    """

    def __init__(self):
        """Initialize the terminal bridge."""
        self.console = Console(force_terminal=True, legacy_windows=False)
        self.logger = get_logger("bridge.main")
        self.router = ToolRouter()
        self.executor = PowerShellExecutor()
        self.llm_client: Optional[LMStudioClient] = None

        # System prompt for the LLM
        self.system_prompt = """You are a helpful AI assistant with access to PowerShell commands on Windows.
When the user asks for system information, file operations, or other system tasks,
use the run_powershell_command tool to execute commands.

Guidelines:
- Be helpful and concise
- Explain what commands you're running
- Format command output clearly
- Warn about any potentially risky operations
- For file listings, use Get-ChildItem or dir
- For process info, use Get-Process
- For service info, use Get-Service
- Always show command output to the user"""

    def initialize_llm(self) -> bool:
        """
        Initialize the LM Studio client.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.llm_client = LMStudioClient(base_url=LM_STUDIO_CHAT_ENDPOINT)
            self.llm_client.set_system_prompt(self.system_prompt)

            if not self.llm_client.test_connection():
                self.console.print(
                    "[red]✗ Cannot connect to LM Studio at "
                    f"{LM_STUDIO_CHAT_ENDPOINT}[/red]"
                )
                self.console.print("\n[yellow]Please ensure:[/yellow]")
                self.console.print("  1. LM Studio is running")
                self.console.print("  2. A model is loaded")
                self.console.print("  3. The API server is enabled on port 1234")
                return False

            self.logger.info("LM Studio client initialized successfully")
            return True

        except Exception as e:
            self.console.print(f"[red]✗ Failed to initialize LLM client: {e}[/red]")
            return False

    def run_interactive(self) -> None:
        """Run the bridge in interactive CLI mode."""
        self.print_header()

        if not self.initialize_llm():
            return

        # Setup tool callbacks
        tool_callbacks = {
            "run_powershell_command": self._execute_powershell_tool
        }

        self.console.print("\n[green]✓ Bridge ready. Type your requests below.[/green]")
        self.console.print(f"[dim]Commands starting with '{CLI_ASK_PREFIX}' will be sent to the LLM.[/dim]")
        self.console.print(f"[dim]Type 'exit' or 'quit' to exit.[/dim]\n")

        while True:
            try:
                user_input = self.console.input(CLI_PROMPT).strip()

                if not user_input:
                    continue

                if user_input.lower() in CLI_EXIT_COMMANDS:
                    self.console.print("\n[yellow]Goodbye![/yellow]")
                    break

                # Check if this is an LLM request
                if user_input.lower().startswith(CLI_ASK_PREFIX):
                    # Extract the actual prompt
                    prompt = user_input[len(CLI_ASK_PREFIX):].strip()
                    if not prompt:
                        self.console.print("[yellow]Please provide a prompt after 'ask:'[/yellow]")
                        continue

                    self._handle_llm_request(prompt, tool_callbacks)

                else:
                    # Direct command execution
                    self.console.print(f"[dim]Executing: {user_input}[/dim]")
                    result = self.executor.execute(user_input)
                    self._display_execution_result(result)

            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                self.logger.exception(f"Unexpected error: {e}")

    def _handle_llm_request(
        self,
        prompt: str,
        tool_callbacks: dict
    ) -> None:
        """
        Handle a request to the LLM.

        Args:
            prompt: The user's prompt
            tool_callbacks: Dictionary of tool callbacks
        """
        with self.console.status("[dim]Thinking...", spinner="dots"):
            response = self.llm_client.send_message(
                message=prompt,
                tools=[TOOL_SCHEMA],
                tool_callbacks=tool_callbacks
            )

        if "error" in response:
            self.console.print(f"[red]Error: {response['error']}[/red]")
            return

        # Display the LLM's response
        content = response.get("content", "")
        if content:
            self.console.print(Panel(content, title="[bold blue]Assistant[/bold blue]", border_style="blue"))

        # Show tool results if any
        if "tool_results" in response:
            for tool_result in response["tool_results"]:
                try:
                    result_data = json.loads(tool_result.get("content", "{}"))
                    if result_data.get("success"):
                        output = result_data.get("stdout", "")
                        if output:
                            self.console.print(Panel(
                                output,
                                title="[bold green]Command Output[/bold green]",
                                border_style="green"
                            ))
                except json.JSONDecodeError:
                    pass

    def _execute_powershell_tool(self, command: str) -> dict:
        """
        Execute PowerShell command from tool call.

        Args:
            command: The PowerShell command to execute

        Returns:
            Execution result dictionary
        """
        return self.executor.execute(command)

    def _display_execution_result(self, result: dict) -> None:
        """
        Display the result of a command execution.

        Args:
            result: The execution result dictionary
        """
        if result.get("success"):
            exec_time = result.get("execution_time", 0)

            if result.get("stdout"):
                self.console.print(
                    Panel(
                        result["stdout"],
                        title=f"[bold green]Output[/bold green] "
                              f"({result['return_code']} | {exec_time}s)",
                        border_style="green"
                    )
                )
            else:
                self.console.print(f"[green]✓ Command completed in {exec_time}s[/green]")

            if result.get("stderr"):
                self.console.print(f"[yellow]Warning: {result['stderr']}[/yellow]")
        else:
            error = result.get("error", "Unknown error")
            stderr = result.get("stderr", "")
            self.console.print(
                Panel(
                    f"{error}\n\n{stderr}" if stderr else error,
                    title="[bold red]Error[/bold red]",
                    border_style="red"
                )
            )

    def execute_single_command(self, command: str) -> None:
        """
        Execute a single command and exit.

        Args:
            command: The command to execute
        """
        self.logger.info(f"Executing single command: {command}")

        result = self.executor.execute(command)

        # Print JSON output
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Exit with appropriate code
        sys.exit(0 if result.get("success") else 1)

    def test_connection(self) -> None:
        """Test the connection to LM Studio."""
        self.print_header()

        self.console.print("\n[dim]Testing connection to LM Studio...[/dim]")

        if self.initialize_llm():
            self.console.print("[green]✓ Connection successful![/green]")

            # Try a simple test
            self.console.print("\n[dim]Sending test message...[/dim]")
            response = self.llm_client.send_message("Hello! Please respond with 'OK'.")

            if "error" not in response:
                content = response.get("content", "")
                self.console.print(f"[green]✓ Model response: {content}[/green]")
            else:
                self.console.print(f"[red]✗ Error: {response['error']}[/red]")
        else:
            sys.exit(1)

    def print_header(self) -> None:
        """Print the application header."""
        # Use ASCII characters for better Windows compatibility
        header = f"""
[bold cyan]+===========================================================+
|           LM STUDIO TERMINAL BRIDGE v{VERSION}              |
|     PowerShell Tool Bridge for Local LLMs on Windows       |
+===========================================================+[/bold cyan]
"""

        self.console.print(header)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="LM Studio Terminal Bridge - Execute PowerShell commands via local LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  Start interactive CLI mode
  python main.py --test           Test connection to LM Studio
  python main.py --execute "Get-Process"   Execute single command

Interactive Mode Commands:
  ask: <prompt>    Send prompt to the LLM
  <command>        Execute PowerShell command directly
  exit/quit        Exit the bridge
        """
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test connection to LM Studio and exit"
    )

    parser.add_argument(
        "--execute",
        "-e",
        type=str,
        metavar="COMMAND",
        help="Execute a single PowerShell command and exit"
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"{PROJECT_NAME} v{VERSION}"
    )

    parser.add_argument(
        "--landing",
        "-l",
        action="store_true",
        help="Show the native CLI landing page"
    )

    parser.add_argument(
        "--chat",
        "-c",
        action="store_true",
        help="Start natural chat mode (no ask: prefix needed)"
    )

    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code
    """
    args = parse_arguments()

    # Handle --landing flag
    if args.landing:
        import subprocess
        landing_script = Path(__file__).parent / "cli_landing.py"
        subprocess.run([sys.executable, str(landing_script)])
        return 0

    # Handle --chat flag
    if args.chat:
        import subprocess
        chat_script = Path(__file__).parent / "chat.py"
        subprocess.run([sys.executable, str(chat_script)])
        return 0

    bridge = TerminalBridge()

    try:
        if args.test:
            bridge.test_connection()
        elif args.execute:
            bridge.execute_single_command(args.execute)
        else:
            bridge.run_interactive()

        return 0

    except Exception as e:
        bridge.console.print(f"[red]Fatal error: {e}[/red]")
        bridge.logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
