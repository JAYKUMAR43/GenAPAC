import json
import asyncio
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

# Import FastMCP to create the local MCP Server
from mcp.server.fastmcp import FastMCP

# Import Database dependencies natively
from backend.database import SessionLocal
from backend.models import Task, Note, Event

# Initialize FastMCP Server
mcp_server = FastMCP("GenAPAC Assistant MCP Server")

# Helper function to get DB sessions reliably in MCP
def get_db_session() -> Session:
    return SessionLocal()

@mcp_server.tool()
def get_tasks() -> str:
    """Retrieve all tasks from the GenAPAC database."""
    db = get_db_session()
    try:
        tasks = db.query(Task).all()
        result = [{"id": t.id, "title": t.title, "status": t.status} for t in tasks]
        return json.dumps(result, indent=2)
    finally:
        db.close()

@mcp_server.tool()
def add_task(title: str) -> str:
    """Add a new task to the database.
    Args:
        title: The description/title of the task.
    """
    db = get_db_session()
    try:
        new_task = Task(title=title, status="pending")
        db.add(new_task)
        db.commit()
        return f"Task '{title}' added successfully with ID {new_task.id}."
    finally:
        db.close()

@mcp_server.tool()
def get_notes() -> str:
    """Retrieve all saved notes from the GenAPAC database."""
    db = get_db_session()
    try:
        notes = db.query(Note).all()
        result = [{"id": n.id, "content": n.content} for n in notes]
        return json.dumps(result, indent=2)
    finally:
        db.close()

@mcp_server.tool()
def add_note(content: str) -> str:
    """Add a new note to the database.
    Args:
        content: The text content of the note.
    """
    db = get_db_session()
    try:
        new_note = Note(content=content)
        db.add(new_note)
        db.commit()
        return f"Note added successfully with ID {new_note.id}."
    finally:
        db.close()

@mcp_server.tool()
def get_events() -> str:
    """Retrieve all scheduled events from the GenAPAC database."""
    db = get_db_session()
    try:
        events = db.query(Event).all()
        result = [{"id": e.id, "title": e.title, "datetime": e.datetime} for e in events]
        return json.dumps(result, indent=2)
    finally:
        db.close()

@mcp_server.tool()
def add_event(title: str, datetime_str: str) -> str:
    """Schedule a new event in the database.
    Args:
        title: The name/title of the event.
        datetime_str: The ISO format date and time string (e.g. '2026-04-06 14:00').
    """
    db = get_db_session()
    try:
        new_event = Event(title=title, datetime=datetime_str)
        db.add(new_event)
        db.commit()
        return f"Event '{title}' scheduled successfully with ID {new_event.id}."
    finally:
        db.close()

# Expose the Starlette application suitable for SSE mounting
# or standalone startup.
pass
