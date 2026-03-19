import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS parking(
id INTEGER PRIMARY KEY AUTOINCREMENT,
vehicle TEXT NOT NULL,
slot TEXT NOT NULL,
entry_time TEXT,
exit_time TEXT,
fee INTEGER
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")