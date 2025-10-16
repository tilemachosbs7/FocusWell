"""
features/planner/model.py
--------------------------
Data model for a single task within the Planner feature.
Represents a row in the `tasks` table of the SQLite database.
"""

from dataclasses import dataclass

@dataclass
class Task:
    id: int                 # Unique ID in the database
    title: str              # Task title or description
    done: bool              # True if completed
    created_at: str         # ISO timestamp of creation
    updated_at: str | None  # ISO timestamp of last update (nullable)
    due_date: str | None    # ISO format 'YYYY-MM-DD'
    due_time: str | None    # Format 'HH:MM'
