#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.analysis import DirectAnalysis

# Get database session
db = SessionLocal()

try:
    # Get all analyses for user 2 (from JWT token)
    user_analyses = db.query(DirectAnalysis).filter(DirectAnalysis.user_id == 2).all()
    print(f'Found {len(user_analyses)} analyses for user 2:')
    
    for analysis in user_analyses:
        print(f'ID: {analysis.id}')
        print(f'  Filename: {analysis.filename}')
        print(f'  Status: {analysis.status}')
        print(f'  Created: {analysis.created_at}')
        if analysis.results:
            issues_count = len(analysis.results.get("issues", []))
            print(f'  Issues: {issues_count}')
        print('---')
        
finally:
    db.close()