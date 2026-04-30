import sqlite3
import os

db_path = os.path.join('backend', 'database', 'studyup.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Add columns if not exist
try:
    c.execute('ALTER TABLE cronograma ADD COLUMN start_time TEXT')
    print('Added start_time')
except sqlite3.OperationalError as e:
    print(f'start_time: {e}')

try:
    c.execute('ALTER TABLE cronograma ADD COLUMN duration INTEGER DEFAULT 60')
    print('Added duration')
except sqlite3.OperationalError as e:
    print(f'duration: {e}')

try:
    c.execute('ALTER TABLE cronograma ADD COLUMN color TEXT DEFAULT "#4CAF50"')
    print('Added color')
except sqlite3.OperationalError as e:
    print(f'color: {e}')

conn.commit()
conn.close()
print('Done')