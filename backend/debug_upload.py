"""
Debug script for file upload issues.
"""

import asyncio
from datetime import datetime

async def test_mock_file():
    """Test the mock file implementation."""
    
    test_content = f"""
# Test File for Digital Ocean Spaces Upload
# Generated at: {datetime.now().isoformat()}

def hello_world():
    print("Hello from Digital Ocean Spaces!")
    return "Upload test successful"

if __name__ == "__main__":
    hello_world()
"""
    
    # Create a mock UploadFile
    test_filename = f"test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    file_bytes = test_content.encode('utf-8')
    
    class MockUploadFile:
        def __init__(self, filename, content_bytes, content_type="text/plain"):
            self.filename = filename
            self.content_type = content_type
            self._content = content_bytes
            self.size = len(content_bytes)
            print(f"DEBUG: MockUploadFile created with content type: {type(content_bytes)}")
        
        async def read(self):
            print(f"DEBUG: MockUploadFile.read() returning type: {type(self._content)}")
            return self._content
    
    mock_file = MockUploadFile(test_filename, file_bytes, "text/x-python")
    
    print(f"Mock file created:")
    print(f"  - Filename: {mock_file.filename}")
    print(f"  - Content type: {mock_file.content_type}")
    print(f"  - Size: {mock_file.size}")
    
    # Test reading
    content = await mock_file.read()
    print(f"  - Read content type: {type(content)}")
    print(f"  - Read content length: {len(content)}")
    print(f"  - Content preview: {content[:50]}...")
    
    # Test hash calculation
    import hashlib
    file_hash = hashlib.sha256(content).hexdigest()
    print(f"  - File hash: {file_hash}")

if __name__ == "__main__":
    asyncio.run(test_mock_file())