#!/usr/bin/env python3
"""
Test the complete upload and analysis flow
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.users import User
from app.models.file_batch import FileBatch, BatchFile
from app.services.batch_processing_service import BatchProcessingService
from app.services.ai_service import AIService
from fastapi import UploadFile
from io import BytesIO
import tempfile

def test_upload_flow():
    """Test the complete upload and analysis flow"""
    db = SessionLocal()
    
    try:
        print("🧪 Testing upload and analysis flow...")
        
        # Get or create test user
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                full_name="Test User",
                hashed_password="test_password_hash"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Created test user: {test_user.email}")
        else:
            print(f"✅ Using existing test user: {test_user.email}")
        
        # Create test files
        test_files_content = [
            ("test1.js", "javascript", """
// Test JavaScript file
function calculateSum(a, b) {
    return a + b;
}

// This has some issues
var x = 1;
console.log(x);
"""),
            ("test2.py", "python", """
# Test Python file
def calculate_sum(a, b):
    return a + b

# This has some issues
x = 1
print(x)
""")
        ]
        
        # Create UploadFile objects
        upload_files = []
        for filename, language, content in test_files_content:
            file_bytes = content.encode('utf-8')
            upload_file = UploadFile(
                filename=filename,
                file=BytesIO(file_bytes),
                size=len(file_bytes),
                headers={"content-type": "text/plain"}
            )
            upload_files.append(upload_file)
        
        print(f"📁 Created {len(upload_files)} test files")
        
        # Test batch processing service
        batch_service = BatchProcessingService()
        
        print("🚀 Creating batch...")
        batch = await batch_service.create_batch(
            files=upload_files,
            user=test_user,
            db=db,
            auto_analyze=True
        )
        
        print(f"✅ Batch created: {batch.id}")
        print(f"   Status: {batch.status}")
        print(f"   Total files: {batch.total_files}")
        print(f"   Processed files: {batch.processed_files}")
        
        # Check batch files
        batch_files = db.query(BatchFile).filter(BatchFile.batch_id == batch.id).all()
        print(f"📄 Batch files in database: {len(batch_files)}")
        
        for bf in batch_files:
            print(f"   - {bf.filename}: {bf.status} ({bf.issues_count} issues)")
            if bf.analysis_results:
                print(f"     Analysis: {len(bf.analysis_results)} issues found")
        
        # Test AI service directly
        print("\n🤖 Testing AI service directly...")
        ai_service = AIService()
        
        test_code = """
function badFunction() {
    var x = 1;
    console.log(x);
    return x;
}
"""
        
        analysis_result = ai_service.analyze_code(
            code=test_code,
            language="javascript",
            filename="test_direct.js"
        )
        
        print(f"✅ Direct AI analysis result:")
        print(f"   Issues: {len(analysis_result.get('issues', []))}")
        print(f"   Summary: {analysis_result.get('summary', 'No summary')}")
        
        # Test files endpoint
        print("\n📊 Testing files endpoint...")
        from app.api.v1.endpoints.files import get_user_files
        from app.api.v1.endpoints.auth import get_current_active_user
        
        # Mock the current user dependency
        async def mock_get_current_user():
            return test_user
        
        try:
            files_result = await get_user_files(
                page=1,
                page_size=20,
                language=None,
                status=None,
                current_user=test_user,
                db=db
            )
            
            print(f"✅ Files endpoint result:")
            print(f"   Total files: {files_result.get('total', 0)}")
            print(f"   Files returned: {len(files_result.get('files', []))}")
            
            for file_data in files_result.get('files', []):
                print(f"   - {file_data['filename']}: {file_data['status']} ({file_data['issues_count']} issues)")
        
        except Exception as e:
            print(f"❌ Files endpoint error: {e}")
        
        print("\n🎉 Upload flow test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_upload_flow())