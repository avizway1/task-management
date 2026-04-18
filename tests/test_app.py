"""
tests/test_app.py — Test suite for the Task Manager app.

Run with:  pytest tests/ -v

All tests use a temporary database (via tmp_path + monkeypatch) so they
never touch the real tasks.db file.
"""

import sys
import os
import pytest

# Make sure the project root is on the path so we can import app and database
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database
from app import app as flask_app


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """
    Redirect database.DB_FILE to a fresh temp file before each test.
    Creates the table automatically so every test starts with an empty,
    ready-to-use database.
    """
    monkeypatch.setattr(database, "DB_FILE", str(tmp_path / "test.db"))
    database.init_db()


@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Flask test client wired to an isolated temp database.
    Use this fixture for all route tests.
    """
    monkeypatch.setattr(database, "DB_FILE", str(tmp_path / "test.db"))
    database.init_db()

    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Database unit tests
# ---------------------------------------------------------------------------

class TestDbInit:
    def test_init_creates_table(self, isolated_db):
        """init_db() should create the tasks table without raising."""
        conn = database.get_connection()
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
        ).fetchone()
        conn.close()
        assert result is not None, "tasks table was not created"

    def test_init_is_idempotent(self, isolated_db):
        """Calling init_db() a second time must not raise or duplicate the table."""
        database.init_db()  # second call — should be a no-op
        conn = database.get_connection()
        count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='tasks'"
        ).fetchone()[0]
        conn.close()
        assert count == 1


class TestDbAddAndGet:
    def test_add_task_inserts_row(self, isolated_db):
        """add_task() should store a task that get_all_tasks() can retrieve."""
        database.add_task("Buy milk")
        tasks = database.get_all_tasks()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Buy milk"

    def test_new_task_done_is_false(self, isolated_db):
        """A newly added task must have done = 0 (pending)."""
        database.add_task("Walk the dog")
        tasks = database.get_all_tasks()
        assert tasks[0]["done"] == 0

    def test_new_task_created_at_is_set(self, isolated_db):
        """created_at must be non-empty after inserting a task."""
        database.add_task("Read a book")
        tasks = database.get_all_tasks()
        assert tasks[0]["created_at"] not in (None, "")

    def test_get_all_tasks_empty(self, isolated_db):
        """get_all_tasks() returns an empty list when there are no tasks."""
        tasks = database.get_all_tasks()
        assert tasks == []

    def test_get_all_tasks_newest_first(self, isolated_db):
        """
        Tasks should come back ordered newest-first.
        We insert with a small sleep to guarantee different timestamps.
        """
        import time
        database.add_task("First task")
        time.sleep(1.1)  # ensure different created_at second
        database.add_task("Second task")
        tasks = database.get_all_tasks()
        assert tasks[0]["title"] == "Second task"
        assert tasks[1]["title"] == "First task"


class TestDbCompleteTask:
    def test_complete_task_sets_done(self, isolated_db):
        """complete_task() must flip done from 0 to 1."""
        database.add_task("Exercise")
        task_id = database.get_all_tasks()[0]["id"]
        database.complete_task(task_id)
        tasks = database.get_all_tasks()
        assert tasks[0]["done"] == 1

    def test_complete_does_not_affect_other_tasks(self, isolated_db):
        """Completing one task must leave others unchanged."""
        database.add_task("Task A")
        database.add_task("Task B")
        all_tasks = database.get_all_tasks()
        # all_tasks[0] is "Task B" (newest first), all_tasks[1] is "Task A"
        database.complete_task(all_tasks[0]["id"])  # complete Task B only

        refreshed = {t["title"]: t["done"] for t in database.get_all_tasks()}
        assert refreshed["Task B"] == 1
        assert refreshed["Task A"] == 0

    def test_complete_nonexistent_task_no_error(self, isolated_db):
        """complete_task() on a non-existent id must not raise."""
        database.complete_task(9999)  # should silently do nothing


class TestDbDeleteTask:
    def test_delete_task_removes_row(self, isolated_db):
        """After delete_task(), the task must no longer appear in get_all_tasks()."""
        database.add_task("Buy groceries")
        task_id = database.get_all_tasks()[0]["id"]
        database.delete_task(task_id)
        tasks = database.get_all_tasks()
        assert len(tasks) == 0

    def test_delete_nonexistent_task_no_error(self, isolated_db):
        """delete_task() on a non-existent id must not raise."""
        database.delete_task(9999)  # should silently do nothing


# ---------------------------------------------------------------------------
# Route integration tests
# ---------------------------------------------------------------------------

class TestIndexRoute:
    def test_index_returns_200(self, client):
        """GET / must respond with HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_shows_task_title(self, client):
        """A task stored in the DB must appear in the rendered HTML."""
        database.add_task("Learn Flask")
        response = client.get("/")
        assert b"Learn Flask" in response.data

    def test_index_empty_state_message(self, client):
        """When there are no tasks, the empty-state message must be visible."""
        response = client.get("/")
        assert b"No tasks" in response.data


class TestAddRoute:
    def test_add_valid_task_redirects(self, client):
        """POST /add with a valid title must return a 302 redirect."""
        response = client.post("/add", data={"title": "Write tests"})
        assert response.status_code == 302

    def test_add_valid_task_appears_in_list(self, client):
        """After POST /add, the task title must appear on GET /."""
        client.post("/add", data={"title": "Write tests"})
        response = client.get("/")
        assert b"Write tests" in response.data

    def test_add_empty_title_ignored(self, client):
        """POST /add with an empty title must NOT insert a task."""
        client.post("/add", data={"title": ""})
        assert len(database.get_all_tasks()) == 0

    def test_add_whitespace_title_ignored(self, client):
        """POST /add with a whitespace-only title must NOT insert a task."""
        client.post("/add", data={"title": "   "})
        assert len(database.get_all_tasks()) == 0


class TestCompleteRoute:
    def test_complete_task_redirects(self, client):
        """POST /complete/<id> must return a 302 redirect."""
        database.add_task("Drink water")
        task_id = database.get_all_tasks()[0]["id"]
        response = client.post(f"/complete/{task_id}")
        assert response.status_code == 302

    def test_complete_task_marks_done(self, client):
        """After POST /complete/<id>, the task's done flag must be 1."""
        database.add_task("Stretch")
        task_id = database.get_all_tasks()[0]["id"]
        client.post(f"/complete/{task_id}")
        assert database.get_all_tasks()[0]["done"] == 1

    def test_complete_nonexistent_no_500(self, client):
        """POST /complete/9999 must not return a server error (500)."""
        response = client.post("/complete/9999")
        assert response.status_code != 500


class TestReopenRoute:
    def test_reopen_task_redirects(self, client):
        """POST /reopen/<id> must return a 302 redirect."""
        database.add_task("Meditate")
        task_id = database.get_all_tasks()[0]["id"]
        database.complete_task(task_id)
        response = client.post(f"/reopen/{task_id}")
        assert response.status_code == 302

    def test_reopen_task_marks_pending(self, client):
        """After POST /reopen/<id>, the task's done flag must be 0."""
        database.add_task("Meditate")
        task_id = database.get_all_tasks()[0]["id"]
        database.complete_task(task_id)
        client.post(f"/reopen/{task_id}")
        assert database.get_all_tasks()[0]["done"] == 0

    def test_reopen_nonexistent_no_500(self, client):
        """POST /reopen/9999 must not return a server error (500)."""
        response = client.post("/reopen/9999")
        assert response.status_code != 500


class TestDbReopenTask:
    def test_reopen_task_sets_pending(self, isolated_db):
        """reopen_task() must flip done from 1 back to 0."""
        database.add_task("Go for a run")
        task_id = database.get_all_tasks()[0]["id"]
        database.complete_task(task_id)
        database.reopen_task(task_id)
        assert database.get_all_tasks()[0]["done"] == 0

    def test_reopen_does_not_affect_other_tasks(self, isolated_db):
        """Reopening one task must leave others unchanged."""
        database.add_task("Task A")
        database.add_task("Task B")
        all_tasks = database.get_all_tasks()
        database.complete_task(all_tasks[0]["id"])
        database.complete_task(all_tasks[1]["id"])
        database.reopen_task(all_tasks[0]["id"])  # reopen Task B only

        refreshed = {t["title"]: t["done"] for t in database.get_all_tasks()}
        assert refreshed["Task B"] == 0
        assert refreshed["Task A"] == 1

    def test_reopen_nonexistent_task_no_error(self, isolated_db):
        """reopen_task() on a non-existent id must not raise."""
        database.reopen_task(9999)


class TestDeleteRoute:
    def test_delete_task_redirects(self, client):
        """POST /delete/<id> must return a 302 redirect."""
        database.add_task("Clean desk")
        task_id = database.get_all_tasks()[0]["id"]
        response = client.post(f"/delete/{task_id}")
        assert response.status_code == 302

    def test_delete_task_removes_it(self, client):
        """After POST /delete/<id>, the task must be gone from the DB."""
        database.add_task("Take out trash")
        task_id = database.get_all_tasks()[0]["id"]
        client.post(f"/delete/{task_id}")
        assert len(database.get_all_tasks()) == 0

    def test_delete_nonexistent_no_500(self, client):
        """POST /delete/9999 must not return a server error (500)."""
        response = client.post("/delete/9999")
        assert response.status_code != 500
