from mcp.server.fastmcp import FastMCP, Context
import subprocess
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime

# Initialize the MCP server
mcp = FastMCP("Dynamic Shell Commander")

# Paths for persistent storage
CONFIG_DIR = Path.home() / ".config" / "mcp-shell-server"
APPROVED_COMMANDS_FILE = CONFIG_DIR / "approved_commands.json"
AUDIT_LOG_FILE = CONFIG_DIR / "audit.log"

# Ensure config directory exists
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Load previously approved commands
def load_approved_commands() -> Dict[str, datetime]:
    try:
        if APPROVED_COMMANDS_FILE.exists():
            with open(APPROVED_COMMANDS_FILE) as f:
                return {cmd: datetime.fromisoformat(date) for cmd, date in json.load(f).items()}
    except Exception as e:
        print(f"Error loading approved commands: {e}")
    return {}

# Save approved commands
def save_approved_commands(commands: Dict[str, datetime]):
    try:
        with open(APPROVED_COMMANDS_FILE, 'w') as f:
            json.dump({cmd: date.isoformat() for cmd, date in commands.items()}, f, indent=2)
    except Exception as e:
        print(f"Error saving approved commands: {e}")

# Initialize approved commands
APPROVED_COMMANDS = load_approved_commands()

def log_command_execution(command: str, args: List[str], result: str, success: bool):
    """Log command execution to audit file."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "arguments": args,
        "success": success,
        "result_summary": result[:100] + "..." if len(result) > 100 else result
    }
    
    try:
        with open(AUDIT_LOG_FILE, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')
    except Exception as e:
        print(f"Error writing to audit log: {e}")

@mcp.tool()
async def execute_command(command: str, args: Optional[List[str]] = None, ctx: Context = None) -> str:
    """
    Execute a shell command with dynamic approval system.
    
    Args:
        command: The command to execute
        args: Optional list of command arguments
        ctx: MCP context for approval handling
    
    Returns:
        The command output as a string
    """
    if args is None:
        args = []
        
    # Create a unique identifier for this command
    command_key = f"{command} {' '.join(args)}".strip()
    
    # Check if command needs approval
    if command_key not in APPROVED_COMMANDS:
        # Request user approval
        approval_prompt = f"""
Command Approval Required

Command: {command}
Arguments: {' '.join(args)}

This command has not been previously approved. Do you want to:
1. Allow this command once
2. Allow this command and remember for future use
3. Deny execution

Please choose an option (1-3):
"""
        ctx.info(approval_prompt)
        
        # Wait for user response
        while True:
            try:
                response = input().strip()
                if response in ['1', '2', '3']:
                    break
                print("Invalid response. Please enter 1, 2, or 3.")
            except Exception:
                return "Command approval interrupted"
        
        if response == '3':
            return "Command execution denied by user"
        elif response == '2':
            # Add to approved commands
            APPROVED_COMMANDS[command_key] = datetime.now()
            save_approved_commands(APPROVED_COMMANDS)
    
    try:
        # Execute command
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            shell=False  # Prevent shell injection
        )
        
        # Prepare output
        if result.returncode == 0:
            output = result.stdout
            success = True
        else:
            output = f"Error: {result.stderr}"
            success = False
            
        # Log execution
        log_command_execution(command, args, output, success)
        
        return output
        
    except subprocess.TimeoutExpired:
        error_msg = "Error: Command timed out after 5 minutes"
        log_command_execution(command, args, error_msg, False)
        return error_msg
    except subprocess.SubprocessError as e:
        error_msg = f"Execution Error: {str(e)}"
        log_command_execution(command, args, error_msg, False)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        log_command_execution(command, args, error_msg, False)
        return error_msg

@mcp.resource("commands://approved")
def list_approved_commands() -> str:
    """Resource that lists all approved commands with their approval dates."""
    if not APPROVED_COMMANDS:
        return "No commands have been approved yet."
        
    command_list = []
    for cmd, approval_date in APPROVED_COMMANDS.items():
        command_list.append(f"{cmd}\nApproved: {approval_date.isoformat()}\n")
    return "\n".join(command_list)

@mcp.tool()
async def revoke_command_approval(command: str) -> str:
    """
    Revoke approval for a previously approved command.
    
    Args:
        command: The command to revoke approval for
    """
    if command in APPROVED_COMMANDS:
        del APPROVED_COMMANDS[command]
        save_approved_commands(APPROVED_COMMANDS)
        return f"Approval revoked for: {command}"
    return f"Command not found in approved list: {command}"

if __name__ == "__main__":
    mcp.run()
