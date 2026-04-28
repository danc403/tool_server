# run_command.py
import asyncio
import os
import shlex
from typing import Optional, Dict

async def run_command(
    command: str, 
    cwd: Optional[str] = None, 
    timeout: int = 30,
    max_output_length: int = 5000
) -> dict:
    """
    Executes a system command in a shell-like environment and returns the output.
    
    This tool provides a direct interface to the host system's shell. It is intended 
    for local administrative tasks, system monitoring, and development utilities.
    
    **WARNING**: This tool allows for arbitrary code execution. It should ONLY be 
    used in secure, local, or firewalled environments.

    Args:
        command (str): The full shell command to execute. 
                       Example: "ls -la", "nvidia-smi", "df -h", "grep 'error' log.txt"
        cwd (str, optional): The working directory in which to run the command. 
                             Defaults to the tool_server's current directory.
        timeout (int, optional): Maximum time in seconds for the command to run 
                                 before being forcefully terminated. Defaults to 30.
        max_output_length (int, optional): Maximum number of characters from stdout/stderr 
                                            to return to the model. Defaults to 5000.

    Returns:
        dict: A dictionary representing the JSON response.

        On **success**:
        ```json
        {
          "status": "success",
          "data": {
            "stdout": "Command output here...",
            "stderr": "",
            "return_code": 0
          }
        }
        ```

        On **timeout**:
        ```json
        {
          "status": "error",
          "message": "Command timed out after 30 seconds."
        }
        ```

        On **failure**:
        ```json
        {
          "status": "error",
          "message": "A descriptive error message (e.g., Command not found)."
        }
        ```
    """
    try:
        # Use shlex to safely split the command string into a list
        args = shlex.split(command)
        
        # Create the subprocess asynchronously
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )

        try:
            # Wait for execution to complete within the timeout limit
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            # Decode output using 'replace' to handle non-UTF-8 characters gracefully
            out_decoded = stdout.decode('utf-8', errors='replace')
            err_decoded = stderr.decode('utf-8', errors='replace')

            # Truncate massive outputs to prevent context window saturation
            if len(out_decoded) > max_output_length:
                out_decoded = out_decoded[:max_output_length] + "\n...[Output Truncated]..."

            return {
                "status": "success",
                "data": {
                    "stdout": out_decoded,
                    "stderr": err_decoded,
                    "return_code": process.returncode
                }
            }

        except asyncio.TimeoutError:
            # Clean up the hanging process
            try:
                process.kill()
            except ProcessLookupError:
                pass
            return {
                "status": "error",
                "message": f"Command timed out after {timeout} seconds."
            }

    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Command not found: {command.split()[0] if command else 'Empty Command'}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }
