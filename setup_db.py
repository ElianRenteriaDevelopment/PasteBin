import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create the paste table (if not already created)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS paste (
        id INTEGER PRIMARY KEY,
        content TEXT NOT NULL,
        version INTEGER DEFAULT 1,
        last_updated TEXT
    )
''')

# Add version column if it doesn't exist (for existing databases)
try:
    cursor.execute('ALTER TABLE paste ADD COLUMN version INTEGER DEFAULT 1')
except sqlite3.OperationalError:
    pass  # Column already exists

# Add last_updated column if it doesn't exist (for existing databases)
try:
    cursor.execute('ALTER TABLE paste ADD COLUMN last_updated TEXT')
except sqlite3.OperationalError:
    pass  # Column already exists

conn.commit()
conn.close()
