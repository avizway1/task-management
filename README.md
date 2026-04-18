# Task Manager

A minimal task management web app built with Python, Flask, and SQLite. No external CSS frameworks, no authentication — just a clean, simple tool that runs locally with a single command.

---

## Features

- Add tasks with a title
- View all tasks on a single dashboard
- Mark tasks as complete
- Delete tasks
- Data persists in a local SQLite database (`tasks.db`)

---

## Prerequisites

- Python 3.7+
- pip

---

## Setup & Run

**1. Install Flask**

```bash
pip install flask
```

**2. Start the app**

```bash
python3 app.py
```

**3. Open your browser**

```
http://localhost:5000
```

That's it. The database file (`tasks.db`) is created automatically on first run.

---

## Project Structure

```
task-management/
├── app.py          # Flask routes and app entry point
├── database.py     # SQLite connection, table setup, and queries
├── templates/
│   └── index.html  # Single-page Jinja2 dashboard template
├── static/
│   └── style.css   # Plain hand-written CSS (no frameworks)
├── tasks.db        # Auto-created SQLite database (gitignored)
└── README.md       # This file
```

---

## How It Works

| File | Responsibility |
|---|---|
| `app.py` | Defines 4 routes: `GET /`, `POST /add`, `POST /complete/<id>`, `POST /delete/<id>` |
| `database.py` | Creates the DB/table on startup; exposes `add_task`, `get_all_tasks`, `complete_task`, `delete_task` |
| `index.html` | Renders the task list using Jinja2 templating |
| `style.css` | Styles the layout with plain CSS — no Bootstrap or Tailwind |

---

## Notes

- All data is stored locally in `tasks.db` — nothing is sent to any server.
- Restarting the app preserves all tasks.
- The app runs in debug mode by default (suitable for local development).
