#!/usr/bin/env python3
"""
Create demo data for CodeNova analysis history
"""
import sqlite3
import json
from datetime import datetime, timedelta
import uuid
import random

# Connect to database
conn = sqlite3.connect('test.db')
cursor = conn.cursor()

print("Creating demo data for CodeNova...")

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS stored_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    filename TEXT NOT NULL,
    original_filename TEXT,
    file_path TEXT,
    file_size INTEGER,
    language TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    file_id INTEGER,
    status TEXT DEFAULT 'completed',
    issues_count INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (file_id) REFERENCES stored_files (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS file_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    batch_id TEXT UNIQUE,
    total_files INTEGER,
    processed_files INTEGER,
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Create demo user
cursor.execute('INSERT OR IGNORE INTO users (email, full_name) VALUES (?, ?)', 
               ('demo@codenova.com', 'Demo User'))
user_id = cursor.lastrowid or 1

# Create realistic file data
files_data = [
    ('app.js', 'javascript', 2456, 15, 3, 12),
    ('utils.py', 'python', 1834, 8, 1, 7),
    ('main.java', 'java', 3421, 12, 2, 10),
    ('config.json', 'json', 567, 2, 0, 2),
    ('styles.css', 'css', 1234, 6, 0, 6),
    ('index.html', 'html', 2890, 4, 1, 3),
    ('server.js', 'javascript', 4567, 18, 4, 14),
    ('database.py', 'python', 3456, 11, 2, 9),
    ('auth.js', 'javascript', 2345, 9, 1, 8),
    ('routes.js', 'javascript', 1987, 7, 1, 6),
    ('models.py', 'python', 2876, 13, 3, 10),
    ('views.py', 'python', 1654, 5, 0, 5),
    ('components.jsx', 'react', 3210, 14, 2, 12),
    ('services.js', 'javascript', 2543, 10, 2, 8),
    ('helpers.js', 'javascript', 1432, 6, 1, 5),
    ('constants.js', 'javascript', 876, 3, 0, 3),
    ('api.js', 'javascript', 2987, 12, 2, 10),
    ('middleware.js', 'javascript', 1765, 8, 1, 7),
    ('validation.js', 'javascript', 2109, 9, 1, 8),
    ('errors.js', 'javascript', 1543, 7, 1, 6),
    ('logger.js', 'javascript', 987, 4, 0, 4),
    ('cache.js', 'javascript', 1876, 8, 1, 7),
    ('security.js', 'javascript', 2345, 11, 2, 9),
    ('performance.js', 'javascript', 1654, 6, 1, 5),
    ('analytics.js', 'javascript', 2876, 13, 3, 10),
    ('notifications.js', 'javascript', 1987, 9, 1, 8),
    ('email.js', 'javascript', 1432, 5, 0, 5),
    ('upload.js', 'javascript', 2543, 10, 2, 8),
    ('download.js', 'javascript', 1765, 7, 1, 6)
]

print(f"Creating {len(files_data)} files...")

# Insert files and analyses
for i, (filename, language, size, issues, errors, warnings) in enumerate(files_data):
    # Create file record
    created_time = datetime.now() - timedelta(hours=i*2)
    cursor.execute('''
        INSERT INTO stored_files (user_id, filename, original_filename, file_path, file_size, language, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, filename, filename, f'/uploads/{filename}', size, language, created_time))
    
    file_id = cursor.lastrowid
    
    # Create analysis record
    completed_time = created_time + timedelta(seconds=random.randint(30, 180))
    cursor.execute('''
        INSERT INTO analysis (user_id, file_id, status, issues_count, errors_count, warnings_count, created_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, file_id, 'completed', issues, errors, warnings, created_time, completed_time))

# Create some batch records
batch_sizes = [5, 8, 12, 4]
for i, batch_size in enumerate(batch_sizes):
    batch_id = str(uuid.uuid4())
    batch_time = datetime.now() - timedelta(days=i+1)
    
    cursor.execute('''
        INSERT INTO file_batches (user_id, batch_id, total_files, processed_files, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, batch_id, batch_size, batch_size, 'completed', batch_time))

# Commit changes
conn.commit()

# Verify data
cursor.execute('SELECT COUNT(*) FROM stored_files')
file_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM analysis')
analysis_count = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM file_batches')
batch_count = cursor.fetchone()[0]

print(f"✅ Created {file_count} files")
print(f"✅ Created {analysis_count} analyses") 
print(f"✅ Created {batch_count} batches")
print(f"✅ Demo data created successfully!")

conn.close()