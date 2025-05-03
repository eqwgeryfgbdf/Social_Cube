#!/usr/bin/env python3
"""
Simple Branch and Script Analyzer for Social Cube Project

This script analyzes Git branches and script files to identify candidates for cleanup.
"""

import os
import subprocess
import datetime
import re
from pathlib import Path

# Constants
STALE_THRESHOLD_DAYS = 90  # Consider branches stale if no commits for 90 days

def run_command(cmd):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}")
        print(f"Error message: {e.stderr}")
        return ""

def analyze_branches():
    """Analyze Git branches and print information about them"""
    print("\n=== BRANCH ANALYSIS ===\n")
    
    # Get all branches with their last commit date, author, and subject
    branches_cmd = 'git for-each-ref --sort=-committerdate refs/heads/ ' + \
                 '--format="%(refname:short),%(authordate),%(authorname),%(subject)"'
    branches_output = run_command(branches_cmd)
    
    branches = []
    now = datetime.datetime.now()
    
    for line in branches_output.split('\n'):
        if not line.strip():
            continue
            
        parts = line.split(',', 3)
        if len(parts) < 4:
            continue
            
        branch_name, date_str, author, subject = parts
        
        # Parse the date (format may vary depending on Git config)
        try:
            # Try common Git date format
            date_obj = datetime.datetime.strptime(date_str.split(' +')[0], '%a %b %d %H:%M:%S %Y')
        except ValueError:
            try:
                # Try ISO format
                date_obj = datetime.datetime.fromisoformat(date_str.split('+')[0].strip())
            except ValueError:
                print(f"Warning: Could not parse date: {date_str} for branch {branch_name}")
                date_obj = datetime.datetime(1970, 1, 1)  # Default to epoch
        
        # Calculate days since last commit
        days_since_commit = (now - date_obj).days
        
        # Determine if branch is stale
        is_stale = days_since_commit > STALE_THRESHOLD_DAYS
        
        # Check if branch is merged into main - using different approach for Windows
        # First get the list of merged branches
        merged_branches_cmd = 'git branch --merged main'
        merged_branches_output = run_command(merged_branches_cmd)
        # Then check if current branch is in the list
        is_merged = any(line.strip() == branch_name or line.strip() == '* ' + branch_name 
                        for line in merged_branches_output.split('\n') if line.strip())
        
        branches.append({
            'name': branch_name,
            'last_commit_date': date_obj.strftime('%Y-%m-%d'),
            'days_since_commit': days_since_commit,
            'author': author,
            'subject': subject,
            'is_stale': is_stale,
            'is_merged': is_merged,
            'status': 'merged' if is_merged else ('stale' if is_stale else 'active')
        })
    
    # Print summary
    print(f"Total branches: {len(branches)}")
    stale_branches = [b for b in branches if b['is_stale']]
    merged_branches = [b for b in branches if b['is_merged']]
    safe_to_remove = [b for b in branches if b['is_stale'] and b['is_merged']]
    
    print(f"Stale branches (no activity for {STALE_THRESHOLD_DAYS}+ days): {len(stale_branches)}")
    print(f"Merged branches: {len(merged_branches)}")
    print(f"Safe to remove (stale and merged): {len(safe_to_remove)}")
    print("\nBranches safe to remove:")
    
    for branch in safe_to_remove:
        print(f"  - {branch['name']} (last active: {branch['last_commit_date']}, {branch['days_since_commit']} days ago)")
    
    print("\nActive branches:")
    for branch in branches:
        if not branch['is_stale'] and not branch['is_merged']:
            print(f"  - {branch['name']} (last active: {branch['last_commit_date']}, {branch['days_since_commit']} days ago)")
    
    return branches

def find_script_files():
    """Find all script files in the project"""
    script_extensions = ['.py', '.sh', '.bat', '.ps1', '.js']
    script_files = []
    
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and common build/env directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and 
                  d not in ['__pycache__', 'node_modules', 'venv', 'env', '.git']]
        
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in script_extensions:
                full_path = os.path.join(root, file)
                script_files.append(full_path)
    
    return script_files

def analyze_scripts():
    """Find potentially unused scripts based on file age"""
    print("\n=== SCRIPT ANALYSIS ===\n")
    
    script_files = find_script_files()
    print(f"Total script files found: {len(script_files)}")
    
    unused_scripts = []
    now = datetime.datetime.now()
    
    for script_path in script_files:
        try:
            # Get file modification time
            mod_time = os.path.getmtime(script_path)
            mod_date = datetime.datetime.fromtimestamp(mod_time)
            days_since_modified = (now - mod_date).days
            
            # Consider stale if not modified for the threshold period
            if days_since_modified > STALE_THRESHOLD_DAYS:
                # Try to determine purpose from file content
                purpose = "Unknown"
                try:
                    with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                        first_lines = ''.join([next(f, '') for _ in range(10)])
                        # Look for docstrings or comments
                        docstring_match = re.search(r'"""(.+?)"""', first_lines, re.DOTALL)
                        if docstring_match:
                            purpose = docstring_match.group(1).strip().split('\n')[0]
                        else:
                            comment_match = re.search(r'#\s*(.+)', first_lines)
                            if comment_match:
                                purpose = comment_match.group(1).strip()
                except Exception as e:
                    purpose = f"Could not read file: {e}"
                
                unused_scripts.append({
                    'path': script_path,
                    'last_modified': mod_date.strftime('%Y-%m-%d'),
                    'days_since_modified': days_since_modified,
                    'purpose': purpose
                })
        except Exception as e:
            print(f"Error processing {script_path}: {e}")
    
    # Sort by age (oldest first)
    unused_scripts.sort(key=lambda x: x['days_since_modified'], reverse=True)
    
    print(f"Potentially stale scripts (not modified for {STALE_THRESHOLD_DAYS}+ days): {len(unused_scripts)}")
    
    print("\nTop 20 oldest scripts:")
    for i, script in enumerate(unused_scripts[:20]):
        print(f"  {i+1}. {script['path']} (last modified: {script['last_modified']}, {script['days_since_modified']} days ago)")
        print(f"     Purpose: {script['purpose'][:80]}{'...' if len(script['purpose']) > 80 else ''}")
    
    return unused_scripts

def main():
    # Set working directory to project root if not already there
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    os.chdir(project_root)
    
    print(f"Running analysis from project root: {os.getcwd()}")
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        print("Error: This doesn't appear to be a Git repository.")
        print("Please run this script from the root of a Git repository.")
        return
    
    # Analyze Git branches
    branches = analyze_branches()
    
    # Analyze scripts
    unused_scripts = analyze_scripts()
    
    # Generate simple recommendations
    print("\n=== RECOMMENDATIONS ===\n")
    
    safe_to_remove_branches = [b for b in branches if b['is_stale'] and b['is_merged']]
    if safe_to_remove_branches:
        print("Git branches that can be safely removed:")
        for branch in safe_to_remove_branches:
            print(f"  git branch -d {branch['name']}  # Remove locally")
        print("\n  # Then to remove from remote:")
        for branch in safe_to_remove_branches:
            print(f"  git push origin --delete {branch['name']}")
    else:
        print("No Git branches identified as safe to remove.")
    
    print("\nBefore removing any scripts, create backups:")
    print("  mkdir -p backup/obsolete_scripts")
    
    for script in unused_scripts[:10]:  # Just show top 10 for brevity
        dir_name = os.path.dirname(script['path'])
        if dir_name:
            print(f"  mkdir -p backup/obsolete_scripts/{dir_name}")
        print(f"  copy \"{script['path']}\" \"backup/obsolete_scripts/{script['path']}\"")
    
    print("\nAnalysis complete! For a full inventory, consider using a more comprehensive tool.")

if __name__ == "__main__":
    main()