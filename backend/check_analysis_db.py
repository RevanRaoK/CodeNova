#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.analysis import DirectAnalysis
from sqlalchemy.orm import Session

# Get database session
db = SessionLocal()

try:
    # Check if the analysis ID exists
    analysis_id = '1a706e94-fa8b-4e3c-aa4f-ef32930bd990'
    analysis = db.query(DirectAnalysis).filter(DirectAnalysis.id == analysis_id).first()
    
    if analysis:
        print(f'Analysis found:')
        print(f'  ID: {analysis.id}')
        print(f'  User ID: {analysis.user_id}')
        print(f'  Status: {analysis.status}')
        print(f'  Filename: {analysis.filename}')
        print(f'  Created: {analysis.created_at}')
        print(f'  Results: {bool(analysis.results)}')
        if analysis.results:
            print(f'  Issues count: {len(analysis.results.get("issues", []))}')
    else:
        print(f'Analysis {analysis_id} not found')
        
    # Check all analyses for user 2
    user_analyses_2 = db.query(DirectAnalysis).filter(DirectAnalysis.user_id == 2).all()
    print(f'\nTotal analyses for user 2: {len(user_analyses_2)}')
    for a in user_analyses_2[:5]:  # Show first 5
        print(f'  {a.id} - {a.filename} - {a.status}')
        
    # Check all analyses for user 1
    user_analyses_1 = db.query(DirectAnalysis).filter(DirectAnalysis.user_id == 1).all()
    print(f'\nTotal analyses for user 1: {len(user_analyses_1)}')
    for a in user_analyses_1[:5]:  # Show first 5
        print(f'  {a.id} - {a.filename} - {a.status}')
        
finally:
    db.close()