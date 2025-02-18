from mcp.server.fastmcp import FastMCP, Context
import asyncio
from typing import List, Optional, Dict, Union
import os

# Initialize the MCP server
mcp = FastMCP("Shell Commander")

@mcp.tool()
async def execute_command(command: str, args: Optional[List[str]] = None, shell: bool = True, timeout: Optional[int] = None) -> Dict[str, List[Dict[str, str]]]:
    """
    Execute a shell command asynchronously and return its output.
    
    Args:
        command: The command to execute
        args: Optional list of command arguments
        shell: Whether to use shell execution (default: True)
        timeout: Optional timeout in seconds (default: None, meaning no timeout)
    """
    try:
        # Handle both string and list commands
        if args:
            if shell:
                cmd = f"{command} {' '.join(args)}"
            else:
                cmd = [command] + args
        else:
            cmd = command

        # Create and run the process asynchronously
        if shell:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            process = await asyncio.create_subprocess_exec(
                command,
                *args if args else [],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

        try:
            # Wait for the process to complete with optional timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            # Decode output
            stdout_str = stdout.decode('utf-8') if stdout else ""
            stderr_str = stderr.decode('utf-8') if stderr else ""
            
            # Check return code
            if process.returncode == 0:
                return {
                    "content": [{
                        "type": "text",
                        "text": stdout_str if stdout_str else "Command completed successfully"
                    }],
                    "isError": False
                }
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": f"Error: {stderr_str}" if stderr_str else "Command failed with no error message"
                    }],
                    "isError": True
                }
                
        except asyncio.TimeoutError:
            # Try to terminate the process if it times out
            try:
                process.terminate()
                await asyncio.sleep(0.1)
                process.kill()
            except:
                pass
                
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Command timed out after {timeout} seconds"
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
    # Use the full path to activate script
    activation_command = f"source {os.path.join(venv_path, 'bin', 'activate')} && {command}"
    
    return await execute_command("/bin/bash", ["-c", activation_command], timeout=timeout)

@mcp.resource("process://status")
def get_process_status() -> str:
    """Resource that provides status of currently running processes."""
    return "Process status information"

if __name__ == "__main__":
    mcp.run()