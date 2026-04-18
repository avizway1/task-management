# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
pip install flask
python3 app.py
```

App runs at `http://localhost:5000` with Flask's built-in debug server (auto-reloads on code changes).

No build step, no package manager, no test suite.

## Architecture

**Stack:** Python/Flask backend + SQLite + Jinja2 templates + vanilla CSS. No JavaScript framework, no Node.js, no ORM.

**Two-module backend:**
- `database.py` — all SQLite operations (`init_db`, `get_all_tasks`, `add_task`, `complete_task`, `delete_task`). DB file path hardcoded as `tasks.db`.
- `app.py` — 4 Flask routes that call into `database.py`, then redirect back to `/` or render `index.html`.

**Request cycle:** Every form submission (add/complete/delete) POSTs to its route → database write → `redirect('/')`. No AJAX, no JSON API — pure server-side rendering via Jinja2.

**Database schema** (single table, auto-created on first run):
```sql
tasks(id INTEGER PK, title TEXT, done INTEGER DEFAULT 0, created_at TEXT)
```
`done` is `0` (pending) or `1` (complete).

**Frontend:** `templates/index.html` is the only template; `static/style.css` is hand-written with no framework.

## Code Style
- Python: PEP 8 compliant, 4-space indentation, snake_case.
- HTML: Indented with 2 spaces, no trailing whitespace.
- CSS: Indented with 2 spaces, no trailing whitespace.

## Testing

### Setup

Tests use **pytest** and Flask's built-in test client. No extra libraries required beyond pytest.

```bash
pip install pytest
pytest tests/ -v
```

### Test Database Isolation Rule

Tests must **never** touch the real `tasks.db`. Patch `database.DB_FILE` to a temp path in every test using pytest's `tmp_path` + `monkeypatch`:

```python
import database

def test_something(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_FILE", str(tmp_path / "test.db"))
    database.init_db()
    # ... test body
```

For route tests, also call `database.init_db()` inside the fixture before using the Flask test client.

### Test File Location

```
tests/
└── test_app.py
```

---

### Recommended Test Scenarios

#### Database Unit Tests — test `database.py` directly, no Flask involved

| Test name | What to assert |
|---|---|
| `test_db_init_creates_table` | `init_db()` creates the `tasks` table without error |
| `test_db_init_is_idempotent` | Calling `init_db()` twice does not raise or duplicate the table |
| `test_db_add_task_inserts_row` | `add_task("Buy milk")` → `get_all_tasks()` returns 1 task with that exact title |
| `test_db_add_task_defaults` | New task has `done == 0` and a non-empty `created_at` |
| `test_db_get_all_tasks_empty` | Returns `[]` when no tasks exist |
| `test_db_get_all_tasks_order` | Multiple tasks are returned newest-first |
| `test_db_complete_task` | `complete_task(id)` sets `done == 1` for that task only |
| `test_db_complete_does_not_affect_others` | Completing task A leaves task B's `done` unchanged |
| `test_db_complete_task_nonexistent` | `complete_task(9999)` does not raise an exception |
| `test_db_delete_task` | After `delete_task(id)`, that task is gone from `get_all_tasks()` |
| `test_db_delete_task_nonexistent` | `delete_task(9999)` does not raise an exception |

#### Route Integration Tests — use `app.test_client()` to test HTTP behaviour

| Test name | What to assert |
|---|---|
| `test_route_index_200` | `GET /` returns HTTP 200 |
| `test_route_index_shows_task` | Task title added to DB appears in the rendered HTML |
| `test_route_index_empty_state` | `GET /` shows "No tasks" message when DB is empty |
| `test_route_add_valid_task` | `POST /add` with a valid title returns 302 and task appears on `GET /` |
| `test_route_add_empty_title` | `POST /add` with `title=` does **not** insert a task |
| `test_route_add_whitespace_title` | `POST /add` with `title=   ` (spaces only) does **not** insert a task |
| `test_route_complete_task` | `POST /complete/<id>` returns 302 and task shows as completed on next `GET /` |
| `test_route_delete_task` | `POST /delete/<id>` returns 302 and task no longer appears on `GET /` |
| `test_route_complete_nonexistent` | `POST /complete/9999` does not return a 500 |
| `test_route_delete_nonexistent` | `POST /delete/9999` does not return a 500 |

#### What NOT to Test

- Flask or SQLite internals (trust the frameworks)
- Visual appearance of HTML/CSS
- That `tasks.db` is created on disk (verified by running the app manually)