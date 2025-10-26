#!/usr/bin/env python3
"""
Script to restart the background worker and clear Python cache.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clear_python_cache():
    """Clear Python bytecode cache files."""
    print("Clearing Python cache...")
    
    # Find and remove __pycache__ directories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            print(f"Removing {cache_dir}")
            shutil.rmtree(cache_dir, ignore_errors=True)
    
    # Remove .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                print(f"Removing {pyc_file}")
                os.remove(pyc_file)
    
    print("Python cache cleared.")

def restart_worker():
    """Instructions for restarting the worker."""
    print("\n" + "="*50)
    print("WORKER RESTART INSTRUCTIONS")
    print("="*50)
    print("1. Stop the current worker process (Ctrl+C if running in terminal)")
    print("2. Clear Python cache (done automatically by this script)")
    print("3. Restart the worker with:")
    print("   python -m app.core.hybrid_queue")
    print("   OR")
    print("   celery -A app.core.hybrid_queue worker --loglevel=info")
    print("="*50)

if __name__ == "__main__":
    print("Preparing to restart background worker...")
    
    # Clear Python cache
    clear_python_cache()
    
    # Show restart instructions
    restart_worker()
    
    print("\nAfter restarting the worker, try running the analysis again.")