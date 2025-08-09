#!/usr/bin/env python3
"""
Fix all relative imports to absolute imports for Railway deployment
"""

import os
import re

def fix_imports_in_file(filepath):
    """Fix relative imports in a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace relative imports with absolute imports
    original_content = content
    
    # Pattern to match relative imports
    patterns = [
        (r'from \.\.utils\.', 'from src.utils.'),
        (r'from \.\.models\.', 'from src.models.'),
        (r'from \.\.services\.', 'from src.services.'),
        (r'from \.\.config\.', 'from src.config.'),
        (r'from \.\.core\.', 'from src.core.'),
        (r'from \.\.api\.', 'from src.api.'),
        (r'from \.([a-zA-Z_]+)', r'from src.core.\1'),  # Single dot imports in core
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed imports in: {filepath}")
        return True
    return False

def main():
    """Fix all Python files in src directory"""
    src_dir = '/Users/ryanyin/united-voice-agent/src'
    fixed_count = 0
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_imports_in_file(filepath):
                    fixed_count += 1
    
    print(f"\n✅ Fixed imports in {fixed_count} files")

if __name__ == "__main__":
    main()