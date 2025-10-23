#!/usr/bin/env python3
"""
Simple script to get user files from database and serve via HTTP
"""
import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

class FileHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/v1/files':
            self.handle_files_request()
        elif parsed_path.path.startswith('/api/v1/files/') and parsed_path.path.endswith('/analysis'):
            file_id = parsed_path.path.split('/')[-2]
            self.handle_analysis_request(file_id)
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def handle_files_request(self):
        try:
            conn = sqlite3.connect('test.db')
            cursor = conn.cursor()
            
            # Get all files with their analysis data
            cursor.execute('''
                SELECT 
                    sf.id,
                    sf.filename,
                    sf.original_filename,
                    sf.language,
                    sf.created_at,
                    a.id as analysis_id,
                    a.status,
                    a.completed_at,
                    a.processing_time_seconds,
                    COUNT(i.id) as issues_count,
                    SUM(CASE WHEN i.severity = 'error' THEN 1 ELSE 0 END) as errors_count,
                    SUM(CASE WHEN i.severity = 'warning' THEN 1 ELSE 0 END) as warnings_count
                FROM stored_files sf
                LEFT JOIN analysis a ON sf.id = a.file_id
                LEFT JOIN issues i ON a.id = i.analysis_id
                GROUP BY sf.id, a.id
                ORDER BY sf.created_at DESC
                LIMIT 50
            ''')
            
            rows = cursor.fetchall()
            
            files = []
            for row in rows:
                files.append({
                    'id': row[0],
                    'filename': row[1] or row[2],
                    'original_filename': row[2],
                    'language': row[3],
                    'created_at': row[4],
                    'analysis_id': row[5],
                    'status': row[6] or 'completed',
                    'analyzed_at': row[7],
                    'processing_time': row[8] or 0,
                    'issues_count': row[9] or 0,
                    'errors_count': row[10] or 0,
                    'warnings_count': row[11] or 0
                })
            
            response_data = {
                'files': files,
                'total': len(files),
                'page': 1,
                'page_size': 50,
                'has_next': False,
                'has_previous': False
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
            conn.close()
            
        except Exception as e:
            print(f"Error: {e}")
            self.send_error(500)
    
    def handle_analysis_request(self, file_id):
        try:
            conn = sqlite3.connect('test.db')
            cursor = conn.cursor()
            
            # Get analysis and issues for this file
            cursor.execute('''
                SELECT 
                    a.id,
                    sf.filename,
                    sf.language,
                    a.status,
                    a.created_at,
                    a.completed_at,
                    a.processing_time_seconds
                FROM analysis a
                JOIN stored_files sf ON a.file_id = sf.id
                WHERE sf.id = ?
            ''', (file_id,))
            
            analysis_row = cursor.fetchone()
            if not analysis_row:
                self.send_error(404)
                return
            
            # Get issues for this analysis
            cursor.execute('''
                SELECT 
                    id,
                    type,
                    severity,
                    message,
                    line_number,
                    column_number,
                    rule_id,
                    category
                FROM issues
                WHERE analysis_id = ?
                ORDER BY line_number, column_number
            ''', (analysis_row[0],))
            
            issue_rows = cursor.fetchall()
            
            issues = []
            for issue in issue_rows:
                issues.append({
                    'id': issue[0],
                    'type': issue[1],
                    'severity': issue[2],
                    'message': issue[3],
                    'line': issue[4],
                    'column': issue[5],
                    'rule': issue[6],
                    'category': issue[7]
                })
            
            response_data = {
                'id': analysis_row[0],
                'filename': analysis_row[1],
                'language': analysis_row[2],
                'status': analysis_row[3],
                'created_at': analysis_row[4],
                'completed_at': analysis_row[5],
                'processing_time': analysis_row[6],
                'issues': issues,
                'metrics': {
                    'total_issues': len(issues),
                    'errors': len([i for i in issues if i['severity'] == 'error']),
                    'warnings': len([i for i in issues if i['severity'] == 'warning']),
                    'complexity': 5,
                    'maintainability': 75
                }
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
            conn.close()
            
        except Exception as e:
            print(f"Error: {e}")
            self.send_error(500)

def run_server():
    server = HTTPServer(('localhost', 8001), FileHandler)
    print("Starting file server on http://localhost:8001")
    server.serve_forever()

if __name__ == '__main__':
    run_server()