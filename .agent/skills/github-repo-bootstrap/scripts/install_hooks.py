#!/usr/bin/env python3
"""
Pre-commit hook installer
Installs the pre-commit hook to automatically run commit_check.py
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    # Find git root
    git_dir = Path(".git")
    if not git_dir.exists():
        print("Error: Not a git repository")
        sys.exit(1)
    
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    # Determine hook content based on OS
    if os.name == 'nt':  # Windows
        hook_content = """#!/usr/bin/env python3
import sys
import subprocess

# Run commit_check.py
result = subprocess.run(
    ["python", ".agent/skills/github-repo-bootstrap/scripts/commit_check.py"],
    capture_output=False
)

sys.exit(result.returncode)
"""
    else:  # Unix-like
        hook_content = """#!/bin/sh
# Pre-commit hook to run commit_check.py

python3 .agent/skills/github-repo-bootstrap/scripts/commit_check.py
exit $?
"""
    
    # Write hook file
    hook_file = hooks_dir / "pre-commit"
    
    if hook_file.exists():
        print(f"Warning: {hook_file} already exists")
        response = input("Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Installation cancelled")
            sys.exit(0)
    
    with open(hook_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(hook_content)
    
    # Make executable on Unix
    if os.name != 'nt':
        os.chmod(hook_file, 0o755)
    
    print(f"✓ Pre-commit hook installed at {hook_file}")
    print("\nThe hook will automatically run commit_check.py before each commit.")
    print("To bypass the hook, use: git commit --no-verify")

if __name__ == "__main__":
    main()
