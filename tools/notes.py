# notes.py
import json
import asyncio
import os
from datetime import datetime
from typing import List, Optional, Dict

# --- Configuration ---
# This ensures the sandbox is always found relative to this script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Moves up one level from 'tools/' then into 'sandbox/'
NOTES_DIRECTORY = os.path.abspath(os.path.join(BASE_DIR, "..", "sandbox"))

# --- Internal Helpers ---
async def _get_notes_file_path(session: Optional[str]) -> str:
    """Internal helper to determine the correct notes file path."""
    filename = f"{session.strip().lower()}.json" if session else "shared_notes.json"
    return os.path.join(NOTES_DIRECTORY, filename)

async def _load_notes(session: Optional[str]) -> Dict[str, dict]:
    """Internal helper to load notes from the appropriate JSON file."""
    file_path = await _get_notes_file_path(session)
    try:
        # Ensure sandbox exists before reading
        os.makedirs(NOTES_DIRECTORY, exist_ok=True)
        if not os.path.exists(file_path):
            return {}
        return await asyncio.to_thread(_sync_load_notes, file_path)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except Exception as e:
        print(f"Error loading notes: {e}")
        return {}

def _sync_load_notes(file_path: str) -> Dict[str, dict]:
    """Synchronous part of loading notes."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def _save_notes(notes: Dict[str, dict], session: Optional[str]):
    """Internal helper to save notes to the appropriate JSON file."""
    file_path = await _get_notes_file_path(session)
    os.makedirs(NOTES_DIRECTORY, exist_ok=True)
    await asyncio.to_thread(_sync_save_notes, notes, file_path)

def _sync_save_notes(notes: Dict[str, dict], file_path: str):
    """Synchronous part of saving notes."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

# --- Public Tool Functions ---

async def save_note(
    title: str,
    content: str,
    tags: Optional[List[str]] = None,
    session: Optional[str] = None
) -> dict:
    """
    Saves a new note or updates an existing one within a specific session or shared context.
    """
    try:
        if not title or not content:
            return {"status": "error", "message": "Note title and content cannot be empty."}

        notes = await _load_notes(session)
        normalized_title = title.strip().lower()

        note_data = {
            "title": title.strip(),
            "content": content,
            "tags": [tag.strip().lower() for tag in tags] if tags else [],
            "updated_at": datetime.now().isoformat()
        }
        notes[normalized_title] = note_data
        await _save_notes(notes, session)

        return {
            "status": "success",
            "data": {
                "message": f"Note '{title}' saved successfully.",
                "note": note_data
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Error saving note: {e}"}

async def get_note(
    query: str,
    session: Optional[str] = None
) -> dict:
    """
    Retrieves notes by searching for a keyword in titles, content, or tags.
    """
    try:
        notes = await _load_notes(session)
        search_term = query.strip().lower()
        
        # Exact title match priority
        if search_term in notes:
            return {"status": "success", "data": {"note": notes[search_term]}}
            
        # Fuzzy keyword search
        found = []
        for note in notes.values():
            if (search_term in note['title'].lower() or 
                search_term in note['content'].lower() or 
                any(search_term in t for t in note['tags'])):
                found.append(note)
        
        if found:
            return {"status": "success", "data": {"notes": found}}
            
        return {"status": "error", "message": f"No notes found matching '{query}'."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def list_notes(session: Optional[str] = None) -> dict:
    """
    Lists all available note titles and tags in a given session.
    """
    try:
        notes = await _load_notes(session)
        listed = [{"title": n["title"], "tags": n["tags"]} for n in notes.values()]
        return {
            "status": "success",
            "data": {"notes": listed, "count": len(listed)}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def delete_note(title: str, session: Optional[str] = None) -> dict:
    """
    Permanently removes a note by its title.
    """
    try:
        notes = await _load_notes(session)
        normalized_title = title.strip().lower()

        if normalized_title in notes:
            notes.pop(normalized_title)
            await _save_notes(notes, session)
            return {"status": "success", "message": f"Note '{title}' deleted."}
        
        return {"status": "error", "message": "Note not found."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def notes(action: str, title: str = "", content: str = "", query: str = "", tags: List[str] = None, session: str = None) -> str:
    """
    Dispatcher tool for managing persistent notes within the IDG-Suite.

    Args:
        action (str): The operation to perform ('save', 'get', 'list', 'delete').
        title (str): Title of the note for 'save' or 'delete'.
        content (str): Content of the note for 'save'.
        query (str): Search term for 'get'.
        tags (List[str]): List of keywords for 'save'.
        session (str): Session name to isolate note storage.

    Returns:
        str: A JSON string containing the result of the notes operation.
    """
    result = {"status": "error", "message": "Invalid notes action specified."}

    # Internal logic normalization: ensure tags is handled as a list
    if tags is None:
        tags = []

    if action == "save":
        result = await save_note(title, content, tags, session)
    elif action == "get":
        result = await get_note(query, session)
    elif action == "list":
        result = await list_notes(session)
    elif action == "delete":
        result = await delete_note(title, session)

    return json.dumps(result, indent=2)
