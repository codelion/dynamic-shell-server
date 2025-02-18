# Dynamic Shell Command MCP Server

A Model Context Protocol (MCP) server that enables secure execution of shell commands with a dynamic approval system. This server allows running arbitrary commands while maintaining security through user approval and audit logging.

## Features

- 🔐 Dynamic command approval system
- 📝 Persistent storage of approved commands
- 📊 Comprehensive audit logging
- ⏱️ Command timeout protection
- 🔄 Command revocation capability

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd dynamic-shell-server
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Standalone Mode

Run the server directly:

```bash
python dynamic_shell_server.py
```

### Claude Desktop Integration

1. Open your Claude Desktop configuration:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the server configuration:
```json
{
    "mcpServers": {
        "shell": {
            "command": "/absolute/path/to/.venv/bin/python",
            "args": ["/absolute/path/to/dynamic_shell_server.py"]
        }
    }
}
```

3. Restart Claude Desktop

### Command Approval Process

When running a command for the first time, you'll be prompted with:
```
Command Approval Required

Command: <command>
Arguments: <args>

This command has not been previously approved. Do you want to:
1. Allow this command once
2. Allow this command and remember for future use
3. Deny execution

Please choose an option (1-3):
```

### Available Tools

1. `execute_command`: Execute a shell command
   - Parameters:
     - `command`: The command to execute
     - `args`: Optional list of command arguments

2. `revoke_command_approval`: Revoke approval for a previously approved command
   - Parameters:
     - `command`: The command to revoke approval for

### Available Resources

1. `commands://approved`: Lists all approved commands with their approval dates

## Data Storage

The server stores its data in `~/.config/mcp-shell-server/`:
- `approved_commands.json`: List of approved commands and their approval dates
- `audit.log`: Detailed execution history of all commands

## Security Features

- User approval required for first-time command execution
- Persistent storage of approved commands
- Comprehensive audit logging
- 5-minute command timeout
- No shell execution (prevents injection attacks)
- Command revocation capability

## Example Usage

Through Claude Desktop:

```
Human: Run 'npm install' in my project directory
Assistant: I'll help you run that command. Since this is the first time running 'npm install', you'll need to approve it.
[Command approval prompt appears]
