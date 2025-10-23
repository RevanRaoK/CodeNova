#!/usr/bin/env python3
"""
Create demo data in PostgreSQL database
"""
import psycopg2
import json
from datetime import datetime, timedelta
import uuid

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'codenova_db',
    'user': 'postgres',
    'password': 'codenova_secure_password'
}

def create_demo_data():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Connected to PostgreSQL database")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Available tables: {tables}")
        
        # Get or create a user (assuming user ID 1 exists)
        cursor.execute("SELECT id FROM users LIMIT 1")
        user_result = cursor.fetchone()
        
        if not user_result:
            print("No users found. Creating demo user...")
            cursor.execute("""
                INSERT INTO users (email, full_name, hashed_password, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, ('demo@codenova.com', 'Demo User', 'hashed_password', True, datetime.now()))
            user_id = cursor.fetchone()[0]
        else:
            user_id = user_result[0]
        
        print(f"Using user ID: {user_id}")
        
        # Create demo files and analyses
        file_names = [
            'app.js', 'utils.py', 'main.java', 'config.json', 'styles.css',
            'index.html', 'server.js', 'database.py', 'auth.js', 'routes.js',
            'models.py', 'views.py', 'components.jsx', 'services.js', 'helpers.js',
            'constants.js', 'api.js', 'middleware.js', 'validation.js', 'errors.js',
            'logger.js', 'cache.js', 'security.js', 'performance.js', 'analytics.js',
            'notifications.js', 'email.js', 'upload.js', 'download.js'
        ]
        
        # First create a file batch
        batch_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO file_batches (
                id, user_id, status, total_files, processed_files, 
                successful_files, failed_files, created_at, completed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            batch_id, user_id, 'completed', len(file_names), len(file_names),
            len(file_names), 0, datetime.now() - timedelta(hours=24), datetime.now() - timedelta(hours=23)
        ))
        
        for i, filename in enumerate(file_names):
            # Create batch file (this is what the API queries)
            file_id = str(uuid.uuid4())
            language = 'python' if filename.endswith('.py') else 'java' if filename.endswith('.java') else 'javascript'
            
            cursor.execute("""
                INSERT INTO batch_files (
                    id, batch_id, filename, original_filename, language, 
                    file_size_bytes, file_index, status, issues_count, 
                    errors_count, warnings_count, suggestions_count, created_at, completed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                file_id, batch_id, filename, filename, language,
                1024 * (i + 1), i, 'completed', (i % 10) + 5,
                (i % 3) + 1, (i % 5) + 2, (i % 4) + 1,
                datetime.now() - timedelta(hours=i), datetime.now() - timedelta(hours=i) + timedelta(minutes=2)
            ))
            
            # Create analysis (optional - link to analyses table if needed)
            analysis_id = str(uuid.uuid4())
            # Update the batch_file with analysis_id
            cursor.execute("""
                UPDATE batch_files SET analysis_id = %s WHERE id = %s
            """, (analysis_id, file_id))
            
            # Create issues for this analysis
            issue_count = (i % 10) + 5  # 5-14 issues per file
            for j in range(issue_count):
                issue_id = str(uuid.uuid4())
                severity = 'error' if j % 3 == 0 else 'warning'
                
                cursor.execute("""
                    INSERT INTO issues (
                        id, analysis_id, type, severity, message, 
                        line_number, column_number, rule_id, category
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    issue_id, analysis_id, severity, severity,
                    f'Issue {j+1} in {filename}: Sample code issue detected',
                    (j % 50) + 1, (j % 20) + 1, f'rule_{j}', 'Code Quality'
                ))
        
        # Commit all changes
        conn.commit()
        print(f"✅ Created {len(file_names)} files with analyses and issues")
        
        # Verify data was created
        cursor.execute("SELECT COUNT(*) FROM stored_files")
        file_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analysis")
        analysis_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM issues")
        issue_count = cursor.fetchone()[0]
        
        print(f"✅ Database now contains:")
        print(f"   - {file_count} files")
        print(f"   - {analysis_count} analyses")
        print(f"   - {issue_count} issues")
        
        conn.close()
        print("✅ Demo data created successfully in PostgreSQL!")
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    create_demo_data()