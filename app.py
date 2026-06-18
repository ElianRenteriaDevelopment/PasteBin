from gevent import monkey
monkey.patch_all()

from gevent.event import Event

from flask import Flask, request, render_template, redirect, url_for, Response, jsonify
import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

DATABASE = 'database.db'
PACIFIC = ZoneInfo('America/Los_Angeles')

# Reject pastes larger than 1 MB (also caps the size of each SSE payload).
MAX_CONTENT_BYTES = 1 * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_BYTES + 64 * 1024  # form overhead

# In-process broadcast primitive. Writers bump the version and wake every
# connected SSE listener at once, so listeners never have to poll the DB.
_update_event = Event()
_current_version = 0


def get_connection():
    conn = sqlite3.connect(DATABASE)
    # WAL lets the single writer proceed without blocking concurrent readers.
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


# Initialize/migrate database on startup
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paste (
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            last_updated TEXT
        )
    ''')

    # Add columns if they don't exist (migration for older databases)
    for column, ddl in (
        ('version', 'ALTER TABLE paste ADD COLUMN version INTEGER DEFAULT 1'),
        ('last_updated', 'ALTER TABLE paste ADD COLUMN last_updated TEXT'),
    ):
        try:
            cursor.execute(ddl)
        except sqlite3.OperationalError:
            pass  # Column already exists

    conn.commit()
    conn.close()


def get_paste_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content, version, last_updated FROM paste LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"content": result[0], "version": result[1], "last_updated": result[2] or ""}
    return {"content": "", "version": 0, "last_updated": ""}


def notify_update():
    """Wake all SSE listeners that are currently blocked on the event."""
    _update_event.set()
    _update_event.clear()


# Function to either update or insert the new text
def save_text(content):
    global _current_version
    conn = get_connection()
    cursor = conn.cursor()

    now_pacific = datetime.now(PACIFIC).strftime('%B %d, %Y at %I:%M %p %Z')

    # Check if there is already a text in the database
    cursor.execute('SELECT COUNT(*), COALESCE(MAX(version), 0) FROM paste')
    count, current_version = cursor.fetchone()

    new_version = current_version + 1
    if count > 0:
        cursor.execute(
            'UPDATE paste SET content = ?, version = ?, last_updated = ? WHERE id = 1',
            (content, new_version, now_pacific),
        )
    else:
        cursor.execute(
            'INSERT INTO paste (id, content, version, last_updated) VALUES (1, ?, ?, ?)',
            (content, new_version, now_pacific),
        )

    conn.commit()
    conn.close()

    _current_version = new_version
    notify_update()


# Route for the main page
@app.route('/pastebin', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # content may be intentionally blank to clear the paste.
        new_content = request.form.get('content', '')
        save_text(new_content)
        return redirect(url_for('index'))  # Reload the page after submitting

    data = get_paste_data()
    return render_template(
        'index.html',
        current_text=data["content"],
        current_version=data["version"],
        last_updated=data["last_updated"],
    )


# API endpoint to get current paste data
@app.route('/pastebin/api/data')
def get_data():
    return jsonify(get_paste_data())


# SSE endpoint for real-time updates
@app.route('/pastebin/stream')
def stream():
    def event_stream():
        last_version = _current_version
        while True:
            # Wake instantly on an in-process write, or fall through every 30s.
            # We re-read the DB on each wake (rather than trusting the in-memory
            # counter) so that writes served by another process are still seen
            # — degrading gracefully to a 30s lag if ever run multi-worker.
            _update_event.wait(timeout=30)
            data = get_paste_data()
            if data["version"] != last_version:
                last_version = data["version"]
                yield f"data: {json.dumps(data)}\n\n"
            else:
                yield ": keepalive\n\n"

    return Response(event_stream(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    })


# Run migration and load the current version into memory on startup
init_db()
_current_version = get_paste_data()["version"]


if __name__ == '__main__':
    app.run(debug=False, port=8000)
