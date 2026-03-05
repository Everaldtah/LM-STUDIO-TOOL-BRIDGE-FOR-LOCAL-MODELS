"""
Test script for LM Studio Terminal Bridge.

Demonstrates the core functionality without requiring interactive input.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_client import LMStudioClient
from tool_router import ToolRouter, ToolCall
from terminal_executor import PowerShellExecutor
from config import TOOL_SCHEMA, LM_STUDIO_CHAT_ENDPOINT


def test_direct_execution():
    """Test direct PowerShell command execution."""
    print("=" * 60)
    print("TEST 1: Direct PowerShell Execution")
    print("=" * 60)

    executor = PowerShellExecutor()

    commands = [
        "Get-Process | Select-Object -First 5 | Format-Table Name, Id, CPU",
        "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object -First 5 | Format-Table Name, Status",
        "Get-Location",
    ]

    for cmd in commands:
        print(f"\n[CMD] {cmd}")
        print("-" * 40)
        result = executor.execute(cmd)
        if result["success"]:
            print(f"[OK] Return Code: {result['return_code']}, Time: {result['execution_time']}s")
            if result["stdout"]:
                print(result["stdout"][:500])
        else:
            print(f"[FAIL] {result.get('error', 'Unknown error')}")


def test_llm_with_tools():
    """Test LLM communication with tool calling."""
    print("\n" + "=" * 60)
    print("TEST 2: LLM with Tool Calling")
    print("=" * 60)

    client = LMStudioClient(base_url=LM_STUDIO_CHAT_ENDPOINT)
    router = ToolRouter()

    # Set up system prompt
    client.set_system_prompt(
        "You are a helpful assistant with access to PowerShell commands. "
        "Use the run_powershell_command tool to execute commands."
    )

    # Test prompts
    test_prompts = [
        "List the top 3 running processes by CPU usage",
        "Show me the current directory and what's in it",
    ]

    for prompt in test_prompts:
        print(f"\n[PROMPT] {prompt}")
        print("-" * 40)

        tool_callbacks = {
            "run_powershell_command": lambda command: router.route(
                ToolCall("run_powershell_command", {"command": command})
            )
        }

        response = client.send_message(
            message=prompt,
            tools=[TOOL_SCHEMA],
            tool_callbacks=tool_callbacks
        )

        if "error" in response:
            print(f"[ERROR] {response['error']}")
        else:
            content = response.get("content", "")
            print(f"[ASSISTANT] {content[:300]}...")

            if "tool_results" in response:
                for tool_result in response["tool_results"]:
                    try:
                        result_data = json.loads(tool_result.get("content", "{}"))
                        if result_data.get("success") and result_data.get("stdout"):
                            print(f"[TOOL OUTPUT]\n{result_data['stdout'][:300]}...")
                    except json.JSONDecodeError:
                        pass


def test_security():
    """Test security filtering."""
    print("\n" + "=" * 60)
    print("TEST 3: Security Layer")
    print("=" * 60)

    executor = PowerShellExecutor()

    # Dangerous commands that should be blocked
    dangerous_commands = [
        "Remove-Item C:\\test.txt",
        "format C:",
        "shutdown /s",
        "Stop-Computer",
    ]

    # Safe commands that should pass
    safe_commands = [
        "Get-Process",
        "Get-Location",
        "Format-Table",  # Should pass - it's a formatting cmdlet
    ]

    print("\n[Dangerous Commands (should be blocked)]:")
    for cmd in dangerous_commands:
        result = executor.execute(cmd)
        status = "BLOCKED" if not result["success"] else "ALLOWED"
        print(f"  [{status}] {cmd}")

    print("\n[Safe Commands (should be allowed)]:")
    for cmd in safe_commands:
        result = executor.execute(cmd)
        status = "OK" if result["success"] else "BLOCKED"
        print(f"  [{status}] {cmd}")


def test_tool_router():
    """Test the tool router."""
    print("\n" + "=" * 60)
    print("TEST 4: Tool Router")
    print("=" * 60)

    router = ToolRouter()

    print(f"Registered tools: {router.get_registered_tools()}")

    # Test a valid tool call
    tool_call = ToolCall(
        "run_powershell_command",
        {"command": "Get-Date"}
    )

    print(f"\nExecuting tool: {tool_call.name}")
    result = router.route(tool_call)
    print(f"Success: {result.get('success')}")
    if result.get("stdout"):
        print(f"Output: {result['stdout'].strip()}")


if __name__ == "__main__":
    try:
        test_direct_execution()
        test_llm_with_tools()
        test_security()
        test_tool_router()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
