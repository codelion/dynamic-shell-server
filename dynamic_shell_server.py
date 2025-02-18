from mcp.server.fastmcp import FastMCP, Context
import subprocess
from typing import List, Optional, Dict, Union

# Initialize the MCP server
mcp = FastMCP("Shell Commander")

@mcp.tool()
async def execute_command(command: str, args: Optional[List[str]] = None, shell: bool = True, timeout: Optional[int] = None) -> Dict[str, List[Dict[str, str]]]:
    """
    Execute a shell command and return its output.
    
    Args:
        command: The command to execute
        args: Optional list of command arguments
        shell: Whether to use shell execution (default: True)
        timeout: Optional timeout in seconds (default: None, meaning no timeout)
    
    Returns:
        Command output or error message
    """
    try:
        # Handle both string and list commands
        if args:
            if shell:
                # Join command and args into a shell command string
                cmd = f"{command} {' '.join(args)}"
            else:
                # Use command and args as a list
                cmd = [command] + args
        else:
            cmd = command
            
        # Execute command with shell interpretation
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,  # No default timeout
            shell=shell,   # Allow shell interpretation
            executable='/bin/bash' if shell else None  # Use bash for shell commands
        )
        
        # Prepare the response
        if result.returncode == 0:
            output = result.stdout if result.stdout else "Command completed successfully"
            return {
                "content": [{
                    "type": "text",
                    "text": output
                }],
                "isError": False
            }
        else:
            error_msg = f"Error: {result.stderr}" if result.stderr else "Command failed with no error message"
            return {
                "content": [{
                    "type": "text",
                    "text": error_msg
                }],
                "isError": True
            }
            
    except subprocess.TimeoutExpired:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: Command timed out after {timeout} seconds"
            }],
            "isError": True
        }
    except subprocess.SubprocessError as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Execution Error: {str(e)}"
            }],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Unexpected Error: {str(e)}"
            }],
            "isError": True
        }

@mcp.tool()
async def run_in_venv(venv_path: str, command: str, timeout: Optional[int] = None) -> Dict[str, List[Dict[str, str]]]:
    """
    Run a command in a specific virtual environment.
    
    Args:
        venv_path: Path to the virtual environment
        command: Command to execute in the venv
        timeout: Optional timeout in seconds (default: None, meaning no timeout)
    """
    # Construct the command to activate venv and run command
    activation_command = f"source {venv_path}/bin/activate && {command}"
    
    return await execute_command("/bin/bash", ["-c", activation_command], timeout=timeout)

if __name__ == "__main__":
    mcp.run()