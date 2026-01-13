from flask import Flask, request, render_template, redirect, url_for, Response, jsonify
import sqlite3
import time
import json
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# Database helper function to get the current text and version
def get_current_text():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM paste LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else ""

def get_current_version():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT version FROM paste LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_paste_data():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT content, version, last_updated FROM paste LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"content": result[0], "version": result[1], "last_updated": result[2] or ""}
    return {"content": "", "version": 0, "last_updated": ""}

# Function to either update or insert the new text
def save_text(content):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Get current time in PST
    pst = timezone(timedelta(hours=-8))
    now_pst = datetime.now(pst).strftime('%B %d, %Y at %I:%M %p PST')

    # Check if there is already a text in the database
    cursor.execute('SELECT COUNT(*), COALESCE(MAX(version), 0) FROM paste')
    row = cursor.fetchone()
    count = row[0]
    current_version = row[1]

    if count > 0:
        # Update the existing row and increment version
        cursor.execute('UPDATE paste SET content = ?, version = ?, last_updated = ? WHERE id = 1', (content, current_version + 1, now_pst))
    else:
        # Insert the first row
        cursor.execute('INSERT INTO paste (id, content, version, last_updated) VALUES (1, ?, 1, ?)', (content, now_pst))

    conn.commit()
    conn.close()

# Route for the main page
@app.route('/pastebin', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        new_content = request.form['content']
        if new_content.strip():  # Ensure it's not empty
            save_text(new_content)
        return redirect(url_for('index'))  # Reload the page after submitting

    data = get_paste_data()
    return render_template('index.html', current_text=data["content"], current_version=data["version"], last_updated=data["last_updated"])

# API endpoint to get current paste data
@app.route('/pastebin/api/data')
def get_data():
    data = get_paste_data()
    return jsonify(data)

# SSE endpoint for real-time updates
@app.route('/pastebin/stream')
def stream():
    def event_stream():
        last_version = get_current_version()
        while True:
            time.sleep(1)  # Check for updates every second
            current_version = get_current_version()
            if current_version != last_version:
                last_version = current_version
                data = get_paste_data()
                yield f"data: {json.dumps(data)}\n\n"

    return Response(event_stream(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    })

if __name__ == '__main__':
    app.run(debug=False, port=8000)
