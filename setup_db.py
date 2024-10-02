import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create the paste table (if not already created)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS paste (
        id INTEGER PRIMARY KEY,
        content TEXT NOT NULL
    )
''')

conn.commit()
conn.close()
