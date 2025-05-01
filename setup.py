#!/usr/bin/env python3
"""
Setup script for the Cognitive Email Ecosystem with Ingestion Agent.
This script creates necessary directories and ensures the project structure is correct.
"""

import os
import sys

def ensure_directories():
    """Create all necessary directories for the project."""
    directories = [
        'src',
        'data',
        'tests',
        'src/tests'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Ensured directory exists: {directory}")

def check_files():
    """Check if key files exist."""
    required_files = [
        'cognitive_email_ecosystem.py',
        'data/syntheticEmails.json',
        'src/ingestionAgent.py',
        'src/cognitive_email_adapter.py',
        'tests/ingestionAgent_test.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("\nWarning: The following required files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease make sure these files are created before running the tests.")
    else:
        print("\n✓ All required files exist")

def create_init_files():
    """Create __init__.py files in directories to make imports work properly."""
    init_dirs = ['src', 'tests']
    
    for directory in init_dirs:
        init_file = os.path.join(directory, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# This file is intentionally empty to make the directory a Python package\n')
            print(f"✓ Created {init_file}")

if __name__ == "__main__":
    print("Setting up Cognitive Email Ecosystem...")
    ensure_directories()
    create_init_files()
    check_files()
    
    print("\nSetup complete. You can now run the ingestion agent:")
    print("  python src/ingestionAgent.py")
    print("\nOr run the tests:")
    print("  python tests/ingestionAgent_test.py")
    print("\nOr try the adapter to connect ingestion with the cognitive system:")
    print("  python src/cognitive_email_adapter.py") 