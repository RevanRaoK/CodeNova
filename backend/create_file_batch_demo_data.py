#!/usr/bin/env python3
"""
Create demo data for CodeNova file batches and analysis history
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.users import User
from app.models.file_batch import FileBatch, BatchFile, BatchStatus, FileStatus
from datetime import datetime, timedelta
import uuid
import random

def create_demo_file_batches():
    """Create demo file batches and files for testing analysis history"""
    db = SessionLocal()
    
    try:
        print("Creating demo file batch data...")
        
        # Get or create demo user
        demo_user = db.query(User).filter(User.email == "demo@codenova.com").first()
        if not demo_user:
            demo_user = User(
                email="demo@codenova.com",
                full_name="Demo User",
                hashed_password="demo_password_hash"  # This would be properly hashed in real app
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print(f"✅ Created demo user: {demo_user.email}")
        else:
            print(f"✅ Using existing demo user: {demo_user.email}")
        
        # Sample file data with realistic analysis results
        sample_files = [
            # Batch 1: JavaScript files
            [
                ("app.js", "javascript", 2456, 15, 3, 12, "Main application entry point"),
                ("utils.js", "javascript", 1834, 8, 1, 7, "Utility functions"),
                ("config.js", "javascript", 567, 2, 0, 2, "Configuration settings"),
                ("auth.js", "javascript", 2345, 9, 1, 8, "Authentication logic"),
                ("api.js", "javascript", 2987, 12, 2, 10, "API client functions")
            ],
            # Batch 2: Python files
            [
                ("main.py", "python", 3421, 12, 2, 10, "Main Python application"),
                ("models.py", "python", 2876, 13, 3, 10, "Database models"),
                ("views.py", "python", 1654, 5, 0, 5, "View functions"),
                ("utils.py", "python", 1987, 7, 1, 6, "Python utilities"),
                ("tests.py", "python", 2543, 10, 2, 8, "Unit tests"),
                ("config.py", "python", 876, 3, 0, 3, "Python configuration"),
                ("database.py", "python", 3456, 11, 2, 9, "Database connection")
            ],
            # Batch 3: Mixed web files
            [
                ("index.html", "html", 2890, 4, 1, 3, "Main HTML page"),
                ("styles.css", "css", 1234, 6, 0, 6, "Stylesheet"),
                ("script.js", "javascript", 4567, 18, 4, 14, "Main JavaScript"),
                ("components.jsx", "react", 3210, 14, 2, 12, "React components")
            ],
            # Batch 4: Backend services
            [
                ("server.js", "javascript", 4567, 18, 4, 14, "Express server"),
                ("routes.js", "javascript", 1987, 7, 1, 6, "API routes"),
                ("middleware.js", "javascript", 1765, 8, 1, 7, "Express middleware"),
                ("validation.js", "javascript", 2109, 9, 1, 8, "Input validation"),
                ("errors.js", "javascript", 1543, 7, 1, 6, "Error handling"),
                ("logger.js", "javascript", 987, 4, 0, 4, "Logging utilities")
            ]
        ]
        
        created_batches = []
        
        for batch_index, files_data in enumerate(sample_files):
            # Create batch
            batch_time = datetime.utcnow() - timedelta(days=batch_index + 1, hours=random.randint(1, 12))
            
            batch = FileBatch(
                user_id=demo_user.id,
                total_files=len(files_data),
                processed_files=len(files_data),
                successful_files=len(files_data),
                failed_files=0,
                status=BatchStatus.COMPLETED,
                created_at=batch_time,
                started_at=batch_time + timedelta(seconds=5),
                completed_at=batch_time + timedelta(minutes=random.randint(2, 8)),
                total_size_bytes=sum(file_data[2] for file_data in files_data),
                processing_time_seconds=random.uniform(30, 180)
            )
            
            db.add(batch)
            db.flush()  # Get the batch ID
            
            # Create files for this batch
            batch_files = []
            for file_index, (filename, language, size, issues, errors, warnings, description) in enumerate(files_data):
                # Generate realistic file content
                file_content = f"""// {description}
// File: {filename}
// Language: {language}
// Generated demo content for analysis

{'// JavaScript/React content' if language in ['javascript', 'react'] else ''}
{'# Python content' if language == 'python' else ''}
{'/* CSS content */' if language == 'css' else ''}
{'<!-- HTML content -->' if language == 'html' else ''}

// This is demo content with {issues} total issues
// Including {errors} errors and {warnings} warnings
// File size: {size} bytes

function exampleFunction() {{
    // Some demo code here
    console.log("Demo file: {filename}");
    return true;
}}

// End of demo content
"""
                
                # Create analysis results
                analysis_results = {
                    "issues": [
                        {
                            "type": "error" if i < errors else "warning" if i < errors + warnings else "suggestion",
                            "severity": "error" if i < errors else "warning" if i < errors + warnings else "info",
                            "message": f"Demo issue {i+1} in {filename}",
                            "line": random.randint(1, 50),
                            "column": random.randint(1, 80),
                            "rule": f"demo-rule-{i+1}",
                            "category": random.choice(["style", "performance", "security", "maintainability"])
                        }
                        for i in range(issues)
                    ],
                    "metrics": {
                        "lines_of_code": len(file_content.split('\n')),
                        "complexity": random.randint(1, 10),
                        "maintainability_index": random.randint(60, 95)
                    },
                    "summary": f"Analysis completed for {filename}. Found {issues} issues total."
                }
                
                batch_file = BatchFile(
                    batch_id=batch.id,
                    filename=filename,
                    original_filename=filename,
                    file_size_bytes=size,
                    content_type="text/plain",
                    language=language,
                    file_index=file_index,
                    status=FileStatus.COMPLETED,
                    file_content=file_content,
                    issues_count=issues,
                    errors_count=errors,
                    warnings_count=warnings,
                    suggestions_count=issues - errors - warnings,
                    analysis_results=analysis_results,
                    analysis_summary=f"Analysis of {filename} completed successfully. Found {issues} issues.",
                    created_at=batch_time + timedelta(seconds=file_index * 2),
                    started_processing_at=batch_time + timedelta(seconds=file_index * 2 + 1),
                    completed_at=batch_time + timedelta(seconds=file_index * 2 + random.randint(10, 60)),
                    processing_time_seconds=random.uniform(5, 30)
                )
                
                batch_files.append(batch_file)
                db.add(batch_file)
            
            batch.batch_files = batch_files
            created_batches.append(batch)
            
            print(f"✅ Created batch {batch_index + 1} with {len(files_data)} files")
        
        # Commit all changes
        db.commit()
        
        # Verify data
        total_batches = db.query(FileBatch).filter(FileBatch.user_id == demo_user.id).count()
        total_files = db.query(BatchFile).join(FileBatch).filter(FileBatch.user_id == demo_user.id).count()
        
        print(f"\n🎉 Demo data created successfully!")
        print(f"📊 Total batches: {total_batches}")
        print(f"📁 Total files: {total_files}")
        print(f"👤 Demo user: {demo_user.email}")
        print(f"\nYou can now test the analysis history page!")
        
        return created_batches
        
    except Exception as e:
        print(f"❌ Error creating demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_file_batches()