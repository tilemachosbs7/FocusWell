"""
features/planner/controller.py
------------------------------
Task management logic for FocusWell.

Handles CRUD operations and sorting for tasks stored in SQLite
via core/db.py, including filtering by date and listing upcoming tasks.
"""

from typing import List, Optional
from core import db
from features.planner.model import Task

# ------------------------------------------------------------
# Initialization
# ------------------------------------------------------------
def init_storage() -> None:
    """Ensure the tasks table exists."""
    db.init_db()

# ------------------------------------------------------------
# CRUD operations
# ------------------------------------------------------------
def add_task(title: str, due_date: Optional[str] = None, due_time: Optional[str] = None) -> int:
    """
    Add a new task.
    Optionally include due_date ('YYYY-MM-DD') and due_time ('HH:MM').
    """
    title = title.strip()
    if not title:
        return 0

    if due_date and due_time:
        sql = "INSERT INTO tasks (title, due_date, due_time) VALUES (?, ?, ?)"
        return db.execute(sql, (title, due_date, due_time))
    elif due_date:
        sql = "INSERT INTO tasks (title, due_date) VALUES (?, ?)"
        return db.execute(sql, (title, due_date))
    else:
        sql = "INSERT INTO tasks (title) VALUES (?)"
        return db.execute(sql, (title,))

def list_tasks(show_done: bool = True) -> List[Task]:
    """Return all tasks, sorted by date/time."""
    base = (
        "SELECT id, title, done, created_at, IFNULL(updated_at,''), "
        "IFNULL(due_date,''), IFNULL(due_time,'') FROM tasks "
    )
    if show_done:
        sql = base + (
            "ORDER BY CASE WHEN due_date='' THEN 1 ELSE 0 END, due_date ASC, "
            "CASE WHEN due_time='' THEN 1 ELSE 0 END, due_time ASC, id DESC"
        )
    else:
        sql = base + (
            "WHERE done=0 "
            "ORDER BY CASE WHEN due_date='' THEN 1 ELSE 0 END, due_date ASC, "
            "CASE WHEN due_time='' THEN 1 ELSE 0 END, due_time ASC, id DESC"
        )
    return _rows_to_tasks(db.query_all(sql))

def list_tasks_by_date(date_iso: str) -> List[Task]:
    """Return all tasks with due_date = date_iso ('YYYY-MM-DD')."""
    rows = db.query_all(
        "SELECT id, title, done, created_at, IFNULL(updated_at,''), IFNULL(due_date,''), IFNULL(due_time,'') "
        "FROM tasks WHERE due_date = ? "
        "ORDER BY CASE WHEN due_time='' THEN 1 ELSE 0 END, due_time ASC, id DESC",
        (date_iso,),
    )
    return _rows_to_tasks(rows)

def list_tasks_after_date(date_iso: str, limit: int = 50) -> List[Task]:
    """Return upcoming tasks after given date, ordered chronologically."""
    rows = db.query_all(
        "SELECT id, title, done, created_at, IFNULL(updated_at,''), IFNULL(due_date,''), IFNULL(due_time,'') "
        "FROM tasks "
        "WHERE due_date IS NOT NULL AND due_date <> '' AND due_date > ? "
        "ORDER BY due_date ASC, CASE WHEN due_time='' THEN 1 ELSE 0 END, due_time ASC, id DESC "
        f"LIMIT {int(limit)}",
        (date_iso,),
    )
    return _rows_to_tasks(rows)

def toggle_done(task_id: int, done: bool) -> None:
    """Mark a task as done or not done."""
    sql = "UPDATE tasks SET done=?, updated_at=datetime('now') WHERE id=?"
    db.execute(sql, (1 if done else 0, task_id))

def delete_task(task_id: int) -> None:
    """Delete a task by ID."""
    sql = "DELETE FROM tasks WHERE id=?"
    db.execute(sql, (task_id,))

def update_task_time(task_id: int, due_time: Optional[str]) -> None:
    """Set or clear the time for a task ('HH:MM' or None)."""
    if due_time:
        sql = "UPDATE tasks SET due_time=?, updated_at=datetime('now') WHERE id=?"
        db.execute(sql, (due_time, task_id))
    else:
        sql = "UPDATE tasks SET due_time=NULL, updated_at=datetime('now') WHERE id=?"
        db.execute(sql, (task_id,))

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _rows_to_tasks(rows: list[tuple]) -> List[Task]:
    """Convert raw database rows into Task objects."""
    def _norm(v: str) -> Optional[str]:
        v = v or ""
        return v if v.strip() else None

    return [
        Task(
            id=row[0],
            title=row[1],
            done=bool(row[2]),
            created_at=row[3],
            updated_at=_norm(row[4]),
            due_date=_norm(row[5]),
            due_time=_norm(row[6]),
        )
        for row in rows
    ]
