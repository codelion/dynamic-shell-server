from mcp.server.fastmcp import FastMCP, Context
import subprocess
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime

# Initialize the MCP server with proper capabilities
mcp = FastMCP("Dynamic Shell Commander", capabilities={
    'prompts': True,
    'resources': True,
    'tools': True
})

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
        print(f"Error loading approved commands: {e}", file=os.sys.stderr)
    return {}

# Save approved commands
def save_approved_commands(commands: Dict[str, datetime]):
    try:
        with open(APPROVED_COMMANDS_FILE, 'w') as f:
            json.dump({cmd: date.isoformat() for cmd, date in commands.items()}, f, indent=2)
    except Exception as e:
        print(f"Error saving approved commands: {e}", file=os.sys.stderr)

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
        print(f"Error writing to audit log: {e}", file=os.sys.stderr)

@mcp.tool()
async def execute_command(command: str, args: Optional[List[str]] = None, ctx: Context = None) -> Dict[str, List[Dict[str, str]]]:
    """
    Execute a shell command with dynamic approval system.
    """
    if args is None:
        args = []
        
    # Create a unique identifier for this command
    command_key = f"{command} {' '.join(args)}".strip()
    
    # Check if command needs approval
    if command_key not in APPROVED_COMMANDS:
        # Request user approval using proper MCP notification
        approval_message = (
            f"Command Approval Required\n\n"
            f"Command: {command}\n"
            f"Arguments: {' '.join(args)}\n\n"
            f"This command has not been previously approved. Do you want to:\n"
            f"1. Allow this command once\n"
            f"2. Allow this command and remember for future use\n"
            f"3. Deny execution\n\n"
            f"Please choose an option (1-3):"
        )
        
        if ctx:
            ctx.info(approval_message)
        
        # Wait for user response
        while True:
            try:
                response = input().strip()
                if response in ['1', '2', '3']:
                    break
                print("Invalid response. Please enter 1, 2, or 3.", file=os.sys.stderr)
            except Exception:
                return {
                    "content": [{
                        "type": "text",
                        "text": "Command approval interrupted"
                    }],
                    "isError": True
                }
        
        if response == '3':
            return {
                "content": [{
                    "type": "text",
                    "text": "Command execution denied by user"
                }],
                "isError": True
            }
        elif response == '2':
            APPROVED_COMMANDS[command_key] = datetime.now()
            save_approved_commands(APPROVED_COMMANDS)
    
    try:
        # Execute command with timeout
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            timeout=300,
            shell=False
        )
        
        if result.returncode == 0:
            output = result.stdout if result.stdout else "Command completed successfully"
            success = True
        else:
            output = f"Error: {result.stderr}" if result.stderr else "Command failed with no error message"
            success = False
            
        # Log execution
        log_command_execution(command, args, output, success)
        
        return {
            "content": [{
                "type": "text",
                "text": output
            }],
            "isError": not success
        }
        
    except subprocess.TimeoutExpired:
        error_msg = "Error: Command timed out after 5 minutes"
        log_command_execution(command, args, error_msg, False)
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }],
            "isError": True
        }
    except subprocess.SubprocessError as e:
        error_msg = f"Execution Error: {str(e)}"
        log_command_execution(command, args, error_msg, False)
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }],
            "isError": True
        }
    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        log_command_execution(command, args, error_msg, False)
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }],
            "isError": True
        }

@mcp.resource("commands://approved")
def list_approved_commands() -> Dict[str, List[Dict[str, str]]]:
    """Resource that lists all approved commands with their approval dates."""
    if not APPROVED_COMMANDS:
        return {
            "content": [{
                "type": "text",
                "text": "No commands have been approved yet."
            }]
        }
        
    command_list = []
    for cmd, approval_date in APPROVED_COMMANDS.items():
        command_list.append(f"{cmd}\nApproved: {approval_date.isoformat()}\n")
    
    return {
        "content": [{
            "type": "text",
            "text": "\n".join(command_list)
        }]
    }

@mcp.tool()
async def revoke_command_approval(command: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Revoke approval for a previously approved command.
    """
    if command in APPROVED_COMMANDS:
        del APPROVED_COMMANDS[command]
        save_approved_commands(APPROVED_COMMANDS)
        return {
            "content": [{
                "type": "text",
                "text": f"Approval revoked for: {command}"
            }],
            "isError": False
        }
    
    return {
        "content": [{
            "type": "text",
            "text": f"Command not found in approved list: {command}"
        }],
        "isError": True
    }

if __name__ == "__main__":
    mcp.run()