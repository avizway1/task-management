"""
app.py - Main entry point for the Task Manager web application.

Run with:  python3 app.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template, request, redirect, url_for
import database

# Create the Flask application instance
app = Flask(__name__)


@app.route("/")
def index():
    """Show the main dashboard with all tasks."""
    tasks = database.get_all_tasks()
    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["POST"])
def add():
    """Add a new task from the form submission."""
    title = request.form.get("title", "").strip()
    if title:  # Only add if the title is not empty
        database.add_task(title)
    return redirect(url_for("index"))


@app.route("/complete/<int:task_id>", methods=["POST"])
def complete(task_id):
    """Mark a task as complete."""
    database.complete_task(task_id)
    return redirect(url_for("index"))


@app.route("/reopen/<int:task_id>", methods=["POST"])
def reopen(task_id):
    """Re-open a completed task, setting it back to pending."""
    database.reopen_task(task_id)
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    """Delete a task permanently."""
    database.delete_task(task_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Initialize the database (creates tasks.db and the table if needed)
    database.init_db()
    print("Database ready.")
    print("Starting server at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
