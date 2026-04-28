# file_manager.py
import json
import asyncio
import os

from typing import List, Optional

# --- Configuration ---
# Restrict file operations to the 'sandbox' directory relative to the tool script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_FILE_DIRECTORY = os.path.abspath(os.path.join(BASE_DIR, "..", "sandbox"))

async def _get_absolute_path(relative_path: str) -> str:
    """
    Internal helper to get the absolute path within the sandbox directory.
    
    This enforces security by ensuring no path traversal can access files outside
     of the designated sandbox.
    """
    # Join and normalize the path
    abs_path = os.path.abspath(os.path.join(BASE_FILE_DIRECTORY, relative_path))
    
    # Security check: Ensure the path doesn't escape the BASE_FILE_DIRECTORY
    if not abs_path.startswith(os.path.abspath(BASE_FILE_DIRECTORY)):
        raise ValueError("Security Violation: Attempted to access path outside of the allowed sandbox.")
    
    return abs_path

async def read_file_content(file_path: str) -> dict:
    """
    Reads the plain text content of a specified file.

    Args:
        file_path (str): The path to the text file to read, relative to the sandbox.
                         Example: "my_document.txt" or "data/logs/log_01.txt"

    Returns:
        dict: A dictionary representing the JSON response.

        On **success**:
        ```json
        {
          "status": "success",
          "data": {
            "file_path": "my_document.txt",
            "content": "This is the content of my document."
          }
        }
        ```

        On **failure**:
        ```json
        {
          "status": "error",
          "message": "A descriptive error message."
        }
        ```
    """
    try:
        # Ensure sandbox exists
        os.makedirs(BASE_FILE_DIRECTORY, exist_ok=True)
        
        abs_path = await _get_absolute_path(file_path)
        
        if not await asyncio.to_thread(os.path.isfile, abs_path):
            return {"status": "error", "message": f"File not found or is not a file: '{file_path}'"}
        
        # Read file content in a separate thread to prevent blocking the async loop
        content = await asyncio.to_thread(_sync_read_file, abs_path)

        return {
            "status": "success",
            "data": {
                "file_path": file_path,
                "content": content
            }
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Error reading file '{file_path}': {e}"}

def _sync_read_file(abs_path: str) -> str:
    """Synchronous part of reading a file."""
    with open(abs_path, 'r', encoding='utf-8') as f:
        return f.read()

async def write_file_content(file_path: str, content: str, append: bool = False) -> dict:
    """
    Writes content to a specified file. If the file exists, it will be overwritten
    unless `append` is set to True. If the file does not exist, it will be created.

    Args:
        file_path (str): The path to the file to write to, relative to the sandbox.
                         Directories in the path will be created if they don't exist.
                         Example: "new_report.txt" or "output/results.log"
        content (str): The text content to write to the file.
        append (bool, optional): If True, content will be appended to the end of the file.
                                 If False (default), the file will be truncated first.

    Returns:
        dict: A dictionary representing the JSON response.
    """
    try:
        # Ensure sandbox exists
        os.makedirs(BASE_FILE_DIRECTORY, exist_ok=True)
        
        abs_path = await _get_absolute_path(file_path)
        
        # Ensure the sub-directory for the file exists within the sandbox
        dir_name = os.path.dirname(abs_path)
        if dir_name:
            await asyncio.to_thread(os.makedirs, dir_name, exist_ok=True)
        
        # Write file content in a separate thread to prevent blocking
        await asyncio.to_thread(_sync_write_file, abs_path, content, append)

        mode_msg = "appended to" if append else "written to"
        return {
            "status": "success",
            "data": {
                "file_path": file_path,
                "message": f"Content successfully {mode_msg} '{file_path}'."
            }
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Error writing to file '{file_path}': {e}"}

def _sync_write_file(abs_path: str, content: str, append: bool):
    """Synchronous part of writing a file."""
    mode = 'a' if append else 'w'
    with open(abs_path, mode, encoding='utf-8') as f:
        f.write(content)

async def list_directory_contents(path: str = ".") -> dict:
    """
    Lists the files and subdirectories within a specified directory in the sandbox.

    Args:
        path (str, optional): The path to the directory to list, relative to the sandbox.
                              Defaults to the sandbox root (".").
                              Example: "data/logs"

    Returns:
        dict: A dictionary representing the JSON response.
    """
    try:
        # Ensure sandbox exists
        os.makedirs(BASE_FILE_DIRECTORY, exist_ok=True)
        
        abs_path = await _get_absolute_path(path)
        
        if not await asyncio.to_thread(os.path.isdir, abs_path):
            return {"status": "error", "message": f"Directory not found: '{path}'"}

        # List contents in a separate thread
        contents = await asyncio.to_thread(os.listdir, abs_path)
        
        files = []
        directories = []
        for item in contents:
            item_abs_path = os.path.join(abs_path, item)
            if await asyncio.to_thread(os.path.isfile, item_abs_path):
                files.append(item)
            elif await asyncio.to_thread(os.path.isdir, item_abs_path):
                directories.append(item)

        return {
            "status": "success",
            "data": {
                "directory_path": path,
                "contents": {
                    "files": files,
                    "directories": directories
                }
            }
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Error listing directory '{path}': {e}"}

async def create_directory(path: str) -> dict:
    """
    Creates a new directory within the sandbox. Supports nested directories.

    Args:
        path (str): The path of the directory to create, relative to the sandbox.
                    Example: "my_new_folder" or "projects/docs"

    Returns:
        dict: A dictionary representing the JSON response.
    """
    try:
        # Ensure sandbox exists
        os.makedirs(BASE_FILE_DIRECTORY, exist_ok=True)
        
        abs_path = await _get_absolute_path(path)
        
        if await asyncio.to_thread(os.path.exists, abs_path):
            return {"status": "error", "message": f"Path already exists at '{path}'."}

        # Create directory in a separate thread
        await asyncio.to_thread(os.makedirs, abs_path, exist_ok=True)

        return {
            "status": "success",
            "data": {
                "directory_path": path,
                "message": f"Directory '{path}' created successfully."
            }
        }
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Error creating directory '{path}': {e}"}

async def file_manager(action: str, file_path: str = ".", content: str = "", append: bool = False) -> str:
    """
    Dispatcher tool for managing files and directories within the secure sandbox.
    
    Supported actions:
    - 'read': Returns the content of a file.
    - 'write': Writes content to a file.
    - 'list': Lists the contents of a directory.
    - 'create_dir': Creates a new directory.

    Args:
        action (str): The operation to perform ('read', 'write', 'list', 'create_dir').
        file_path (str): The relative path to the file or directory.
        content (str): The text content to write (only used for 'write' action).
        append (bool): Whether to append content (only used for 'write' action).

    Returns:
        str: A JSON string containing the result of the operation.
    """
    result = {"status": "error", "message": "Invalid action specified."}

    if action == "read":
        result = await read_file_content(file_path)
    elif action == "write":
        result = await write_file_content(file_path, content, append)
    elif action == "list":
        result = await list_directory_contents(file_path)
    elif action == "create_dir":
        result = await create_directory(file_path)

    return json.dumps(result, indent=2)
