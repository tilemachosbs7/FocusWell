# tests/test_planner_controller.py
from features.planner import controller as pc

def test_add_and_list_tasks_by_date():
    pc.init_storage()

    date = "2025-10-16"
    id1 = pc.add_task("Task A", due_date=date, due_time="09:00")
    id2 = pc.add_task("Task B", due_date=date, due_time="08:30")
    id3 = pc.add_task("Task C")  # no due date/time

    assert id1 > 0 and id2 > 0 and id3 > 0

    items = pc.list_tasks_by_date(date)
    titles = [t.title for t in items]
    assert titles == ["Task B", "Task A"]  # sorted by due_time ascending

def test_toggle_update_delete_and_upcoming():
    pc.init_storage()

    d0 = "2025-10-16"
    d1 = "2025-10-17"
    id_a = pc.add_task("Do X", due_date=d0, due_time="10:00")
    id_b = pc.add_task("Do Y", due_date=d1)
    id_c = pc.add_task("Do Z")  # no date

    # Toggle done
    pc.toggle_done(id_a, True)
    day_items = pc.list_tasks_by_date(d0)
    assert day_items[0].done is True

    # Update time
    pc.update_task_time(id_b, "08:45")
    upcoming = pc.list_tasks_after_date(d0)
    assert any(t.id == id_b and t.due_time == "08:45" for t in upcoming)

    # Clear time
    pc.update_task_time(id_b, None)
    upcoming = pc.list_tasks_after_date(d0)
    assert any(t.id == id_b and t.due_time is None for t in upcoming)

    # Delete
    pc.delete_task(id_a)
    day_items = pc.list_tasks_by_date(d0)
    assert all(t.id != id_a for t in day_items)
