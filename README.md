# LM Studio Terminal Bridge

A production-ready Python tool bridge that allows a local LLM running in LM Studio to execute PowerShell commands on Windows.

## Features

- **Tool Calling Support**: Full OpenAI-compatible tool calling integration
- **PowerShell Execution**: Safe and controlled PowerShell command execution
- **Security Layer**: Built-in command filtering and sandbox rules
- **Interactive CLI**: User-friendly command-line interface
- **Structured Logging**: Comprehensive logging of all operations
- **Timeout Protection**: Commands auto-terminate after 15 seconds
- **Rich Output**: Beautiful formatted console output with the `rich` library

## System Architecture

```
LMSTUDIO_TERMINAL_BRIDGE/
├── main.py               # Entry point and CLI interface
├── llm_client.py         # LM Studio API communication
├── tool_router.py        # Tool call detection and routing
├── terminal_executor.py  # PowerShell command execution
├── security.py           # Command filtering and security
├── config.py             # Configuration variables
├── logger.py             # Logging system
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Installation

### Prerequisites

- Windows 10 or later
- Python 3.10 or higher
- LM Studio installed and running

### Setup Steps

1. **Clone or download this repository**

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start LM Studio**

   - Open LM Studio
   - Load your preferred model (any model with tool calling support)
   - Enable the API server:
     - Click the "Server" icon (⟠) in the left sidebar
     - Ensure "Enable Server" is checked
     - Note the port (default: 1234)

## Usage

### Starting the Bridge

Run the bridge in interactive mode:

```bash
python main.py
```

You should see the welcome banner:

```
╔═══════════════════════════════════════════════════════════╗
║           LM STUDIO TERMINAL BRIDGE v1.0.0               ║
║     PowerShell Tool Bridge for Local LLMs on Windows     ║
╚═══════════════════════════════════════════════════════════╝
```

### Interactive Commands

1. **Ask the LLM** (uses tool calling)

   ```
   bridge> ask: show running processes
   ```

   The LLM will respond by calling the `run_powershell_command` tool.

2. **Execute commands directly**

   ```
   bridge> Get-Process
   ```

3. **Exit**

   ```
   bridge> exit
   ```

### Command Line Options

```bash
# Test connection to LM Studio
python main.py --test

# Execute a single command
python main.py --execute "Get-Service | Where-Object {$_.Status -eq 'Running'}"

# Show version
python main.py --version
```

## Tool Calling

The bridge defines a single tool that the LLM can use:

### `run_powershell_command`

Executes a PowerShell command on the local system.

**Parameters:**
- `command` (string, required): The PowerShell command to execute

**Response:**
```json
{
  "command": "Get-Process",
  "stdout": "...",
  "stderr": "",
  "return_code": 0,
  "execution_time": 0.523,
  "success": true,
  "error": null
}
```

## Security

The security module implements a whitelist/blacklist system:

### Blocked Commands

The following commands are blocked for safety:

| Category | Commands |
|----------|----------|
| File Deletion | `Remove-Item`, `del`, `rmdir`, `rm -rf` |
| System Control | `Stop-Computer`, `Restart-Computer` |
| Disk Operations | `format`, `diskpart`, `fdisk` |
| System Settings | `Set-ExecutionPolicy` |

### Protected Paths

Commands targeting these paths are blocked:

- `C:\Windows`
- `C:\Program Files`
- `C:\Program Files (x86)`
- `System32`
- `SysWOW64`

### Allowed Commands

Common informational commands are explicitly allowed:

- `Get-*` (Get-Process, Get-Service, etc.)
- `Set-Location`, `cd`
- `ls`, `dir`
- `Test-Path`
- `Write-Host`, `Write-Output`

## Configuration

Edit `config.py` to customize:

- **API Endpoint**: Change LM Studio port
- **Timeout**: Command execution timeout (default: 15 seconds)
- **Security Rules**: Add/remove blocked commands
- **Logging**: Log level and file location

## Logging

All operations are logged to `logs/bridge.log`:

```
2024-01-15 10:30:15 | INFO     | bridge.executor | Command executed: Get-Process
2024-01-15 10:30:15 | DEBUG    | bridge.executor | Return code: 0
2024-01-15 10:30:15 | DEBUG    | bridge.executor | Execution time: 0.523s
```

## Example Session

```
bridge> ask: list the top 5 processes by memory usage

[Thinking...]

╭─ Assistant ───────────────────────────────────────╮
│ I'll get the top 5 processes by memory usage.    │
╜────────────────────────────────────────────────────╘

╭─ Command Output ───────────────────────────────────╮
│                                                       │
│ Handles  NPM(K)    PM(K)      WS(K)     CPU(s)     │
│ ------  ------    -----      -----     ------     │
│    784      45   128500     132456       2.34     │
│    ...                                           │
╜─────────────────────────────────────────────────────╘
```

## Troubleshooting

### "Cannot connect to LM Studio"

- Ensure LM Studio is running
- Check that the API server is enabled
- Verify the port is 1234 (or update `config.py`)

### "Command blocked by security"

- The command contains a blocked pattern or protected path
- Check `config.py` for security rules
- Use informational commands where possible

### Model not using tools

- Ensure your model supports tool calling/function calling
- Try a model known for good tool calling (like Llama 3.1+)
- The model must understand the tool schema format

## License

MIT License - Feel free to use and modify for your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Notes

- This tool is designed for **local use only**
- Always review commands before execution in production
- The security layer is a safeguard, not a replacement for caution
- Some models may hallucinate commands - supervision is recommended
