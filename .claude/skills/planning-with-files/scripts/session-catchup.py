#!/usr/bin/env python3
"""
Session Catchup Script for planning-with-files
Detects unsynced context after /clear or session restart
"""

import os
import sys
import subprocess
from pathlib import Path

def run_git_diff(directory):
    """Run git diff to see what changed"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--stat'],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    return None

def read_planning_files(directory):
    """Read current planning files"""
    files = {}
    for filename in ['task_plan.md', 'findings.md', 'progress.md']:
        filepath = Path(directory) / filename
        if filepath.exists():
            files[filename] = filepath.read_text(encoding='utf-8')
    return files

def main():
    if len(sys.argv) < 2:
        print("Usage: session-catchup.py <project-directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    print("=" * 60)
    print("SESSION CATCHUP REPORT")
    print("=" * 60)
    
    # Check git status
    git_diff = run_git_diff(directory)
    if git_diff:
        print("\n📊 Git Changes:")
        print(git_diff)
    else:
        print("\n📊 No git changes detected (or not a git repository)")
    
    # Read planning files
    files = read_planning_files(directory)
    
    if not files:
        print("\n⚠️  No planning files found in this directory")
        print("   Run: cp ~/.cursor/skills/planning-with-files/templates/*.md .")
        return
    
    print(f"\n📁 Planning Files Found: {len(files)}")
    
    for filename, content in files.items():
        print(f"\n{'='*40}")
        print(f"📄 {filename}")
        print(f"{'='*40}")
        # Show first 30 lines
        lines = content.split('\n')[:30]
        print('\n'.join(lines))
        if len(content.split('\n')) > 30:
            print(f"\n... ({len(content.split(chr(10))) - 30} more lines)")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATION:")
    print("=" * 60)
    print("1. Review the planning files above")
    print("2. Update progress.md with current status")
    print("3. Check if current phase is still accurate")
    print("4. Continue work based on task_plan.md")

if __name__ == '__main__':
    main()
