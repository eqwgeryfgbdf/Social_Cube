#!/usr/bin/env python3
"""
Branch and Script Analyzer for Social Cube Project

This script performs two main functions:
1. Analyzes Git branches to identify stale or merged branches
2. Scans the codebase for potentially unused scripts

The results are compiled into a structured report.
"""

import os
import subprocess
import datetime
import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

# Constants
STALE_THRESHOLD_DAYS = 90  # Consider branches stale if no commits for 90 days
OUTPUT_CSV = 'branch_inventory.csv'
SCRIPT_INVENTORY_CSV = 'script_inventory.csv'
FINAL_REPORT = 'cleanup_inventory.md'

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
    """Analyze Git branches and return data about them"""
    print("Analyzing Git branches...")
    
    # Get all branches with their last commit date, author, and subject
    branches_cmd = 'git for-each-ref --sort=-committerdate refs/heads/ ' + \
                 '--format="%(refname:short),%(authordate),%(authorname),%(subject)"'
    branches_output = run_command(branches_cmd)
    
    branch_data = []
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
        
        # Check if branch is merged into main
        merged_cmd = f'git branch --merged main | grep -E "\\b{branch_name}\\b"'
        is_merged = bool(run_command(merged_cmd))
        
        branch_data.append({
            'name': branch_name,
            'last_commit_date': date_obj.strftime('%Y-%m-%d'),
            'days_since_commit': days_since_commit,
            'author': author,
            'subject': subject,
            'is_stale': is_stale,
            'is_merged': is_merged,
            'status': 'merged' if is_merged else ('stale' if is_stale else 'active')
        })
    
    return branch_data

def find_all_scripts():
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

def analyze_script_usage(script_files):
    """Analyze script usage patterns to identify potentially unused scripts"""
    print("Analyzing script usage patterns...")
    
    # Build a dict of all scripts
    script_data = []
    import_patterns = {}
    
    # First get all script paths and their modified dates
    for script_path in script_files:
        try:
            mod_time = os.path.getmtime(script_path)
            mod_date = datetime.datetime.fromtimestamp(mod_time)
            
            # Read first 10 lines to try to determine purpose
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = ''.join([next(f, '') for _ in range(10)])
            
            # Try to extract purpose from docstring or comments
            purpose = "Unknown"
            docstring_match = re.search(r'"""(.+?)"""', first_lines, re.DOTALL)
            if docstring_match:
                purpose = docstring_match.group(1).strip().split('\n')[0]
            else:
                # Look for comments
                comment_match = re.search(r'#\s*(.+)', first_lines)
                if comment_match:
                    purpose = comment_match.group(1).strip()
            
            script_data.append({
                'path': script_path,
                'last_modified': mod_date.strftime('%Y-%m-%d'),
                'days_since_modified': (datetime.datetime.now() - mod_date).days,
                'purpose': purpose,
                'referenced_count': 0,
                'status': 'unknown'
            })
            
            # Determine import pattern based on script type
            _, ext = os.path.splitext(script_path)
            basename = os.path.basename(script_path)
            module_name = os.path.splitext(basename)[0]
            
            if ext.lower() == '.py':
                # Create patterns to find imports of this Python module
                import_patterns[script_path] = [
                    f"import\\s+{module_name}",
                    f"from\\s+{module_name}\\s+import",
                    f"from\\s+\\.{module_name}\\s+import",  # Relative import
                    f"__import__\\(['\"]({module_name}|\\.{module_name})['\"]\\)"
                ]
            elif ext.lower() in ['.sh', '.bat', '.ps1']:
                # Shell/batch scripts usually executed directly or via system calls
                import_patterns[script_path] = [
                    f"subprocess\\.\\w+\\(['\"].*{re.escape(basename)}",
                    f"os\\.system\\(['\"].*{re.escape(basename)}",
                    f"call\\(['\"].*{re.escape(basename)}",
                    f"source\\s+['\"]?.*{re.escape(basename)}",
                    f"\\.\\s*/.*{re.escape(basename)}",
                    f"\\./.*{re.escape(basename)}",
                    f"sh\\s+.*{re.escape(basename)}",
                    f"bash\\s+.*{re.escape(basename)}",
                    f"cmd\\s+.*{re.escape(basename)}"
                ]
            elif ext.lower() == '.js':
                # JavaScript imports
                import_patterns[script_path] = [
                    f"require\\(['\"].*{module_name}['\"]\\)",
                    f"import.*from\\s+['\"].*{module_name}['\"]",
                    f"import\\s+['\"].*{module_name}['\"]",
                    f"<script\\s+src=['\"].*{basename}['\"]>"
                ]
    
    # Search for references to each script
    for target_script in script_data:
        for search_script in script_files:
            # Don't search within the script itself
            if search_script == target_script['path']:
                continue
                
            try:
                with open(search_script, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Check for imports/references to the target script
                    patterns = import_patterns.get(target_script['path'], [])
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                            target_script['referenced_count'] += 1
                            break
            except Exception as e:
                print(f"Warning: Error reading {search_script}: {e}")
    
    # Also check if the script is referenced in Docker/compose files
    docker_files = ['Dockerfile', 'docker-compose.yml', 'docker-compose.override.yml']
    for docker_file in docker_files:
        if os.path.exists(docker_file):
            try:
                with open(docker_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for script in script_data:
                        basename = os.path.basename(script['path'])
                        if basename in content:
                            script['referenced_count'] += 1
            except Exception as e:
                print(f"Warning: Error reading {docker_file}: {e}")
    
    # Set status based on reference count
    for script in script_data:
        if script['referenced_count'] == 0:
            if script['days_since_modified'] > STALE_THRESHOLD_DAYS:
                script['status'] = 'likely unused (stale)'
            else:
                script['status'] = 'potentially unused (recent)'
        else:
            script['status'] = 'in use'
    
    return script_data

def write_branch_inventory(branch_data):
    """Write branch data to a CSV file"""
    print(f"Writing branch inventory to {OUTPUT_CSV}...")
    
    with open(OUTPUT_CSV, 'w', newline='') as csvfile:
        fieldnames = ['name', 'last_commit_date', 'days_since_commit', 
                     'author', 'subject', 'is_stale', 'is_merged', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for branch in branch_data:
            writer.writerow(branch)

def write_script_inventory(script_data):
    """Write script analysis data to a CSV file"""
    print(f"Writing script inventory to {SCRIPT_INVENTORY_CSV}...")
    
    with open(SCRIPT_INVENTORY_CSV, 'w', newline='') as csvfile:
        fieldnames = ['path', 'last_modified', 'days_since_modified', 
                     'purpose', 'referenced_count', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for script in script_data:
            writer.writerow(script)

def generate_final_report(branch_data, script_data):
    """Generate a final Markdown report with cleanup recommendations"""
    print(f"Generating final report to {FINAL_REPORT}...")
    
    with open(FINAL_REPORT, 'w') as f:
        f.write("# Branch and Script Cleanup Inventory\n\n")
        f.write(f"Report generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Add branch summary
        f.write("## Branch Inventory Summary\n\n")
        stale_branches = [b for b in branch_data if b['is_stale']]
        merged_branches = [b for b in branch_data if b['is_merged']]
        safe_to_remove = [b for b in branch_data if b['is_stale'] and b['is_merged']]
        
        f.write(f"- Total branches: {len(branch_data)}\n")
        f.write(f"- Stale branches (no activity for {STALE_THRESHOLD_DAYS}+ days): {len(stale_branches)}\n")
        f.write(f"- Merged branches: {len(merged_branches)}\n")
        f.write(f"- Safe to remove (stale and merged): {len(safe_to_remove)}\n\n")
        
        # Branch categories
        f.write("### Branches Safe to Remove\n\n")
        f.write("| Branch | Last Commit | Days Since | Author |\n")
        f.write("|--------|-------------|------------|--------|\n")
        for branch in safe_to_remove:
            f.write(f"| {branch['name']} | {branch['last_commit_date']} | {branch['days_since_commit']} | {branch['author']} |\n")
        f.write("\n")
        
        f.write("### Active Branches\n\n")
        f.write("| Branch | Last Commit | Days Since | Author |\n")
        f.write("|--------|-------------|------------|--------|\n")
        for branch in branch_data:
            if not branch['is_stale'] and not branch['is_merged']:
                f.write(f"| {branch['name']} | {branch['last_commit_date']} | {branch['days_since_commit']} | {branch['author']} |\n")
        f.write("\n")
        
        # Add script summary
        f.write("## Script Inventory Summary\n\n")
        unused_scripts = [s for s in script_data if s['referenced_count'] == 0]
        stale_unused = [s for s in unused_scripts if s['days_since_modified'] > STALE_THRESHOLD_DAYS]
        recent_unused = [s for s in unused_scripts if s['days_since_modified'] <= STALE_THRESHOLD_DAYS]
        
        f.write(f"- Total scripts analyzed: {len(script_data)}\n")
        f.write(f"- Potentially unused scripts: {len(unused_scripts)}\n")
        f.write(f"- Stale unused scripts (no modification for {STALE_THRESHOLD_DAYS}+ days): {len(stale_unused)}\n")
        f.write(f"- Recent unused scripts: {len(recent_unused)}\n\n")
        
        # Script categories
        f.write("### Scripts Likely Safe to Remove\n\n")
        f.write("| Script Path | Last Modified | Days Since | Purpose |\n")
        f.write("|-------------|---------------|------------|--------|\n")
        for script in stale_unused:
            purpose = script['purpose'].replace('\n', ' ')[:50]  # Truncate for table readability
            f.write(f"| {script['path']} | {script['last_modified']} | {script['days_since_modified']} | {purpose} |\n")
        f.write("\n")
        
        f.write("### Recently Modified Unused Scripts (Needs Investigation)\n\n")
        f.write("| Script Path | Last Modified | Days Since | Purpose |\n")
        f.write("|-------------|---------------|------------|--------|\n")
        for script in recent_unused:
            purpose = script['purpose'].replace('\n', ' ')[:50]  # Truncate for table readability
            f.write(f"| {script['path']} | {script['last_modified']} | {script['days_since_modified']} | {purpose} |\n")
        f.write("\n")
        
        # Recommended actions
        f.write("## Recommended Actions\n\n")
        
        f.write("### Git Branch Cleanup\n\n")
        f.write("Run the following commands to remove stale and merged branches:\n\n")
        f.write("```bash\n")
        for branch in safe_to_remove:
            f.write(f"git branch -d {branch['name']}  # Remove locally\n")
        f.write("\n# Then to remove remote branches (if needed):\n")
        for branch in safe_to_remove:
            f.write(f"git push origin --delete {branch['name']}\n")
        f.write("```\n\n")
        
        f.write("### Script Backup and Removal Process\n\n")
        f.write("1. Create a backup archive of scripts before removal:\n\n")
        f.write("```bash\n")
        f.write("mkdir -p backup/obsolete_scripts\n")
        for script in stale_unused:
            dir_name = os.path.dirname(script['path'])
            f.write(f"mkdir -p backup/obsolete_scripts/{dir_name}\n")
            f.write(f"cp {script['path']} backup/obsolete_scripts/{script['path']}\n")
        f.write("```\n\n")
        
        f.write("2. Remove scripts after verification:\n\n")
        f.write("```bash\n")
        for script in stale_unused:
            f.write(f"# rm {script['path']}\n")
        f.write("```\n\n")
        
        f.write("**Note:** Before executing removal commands, verify each item thoroughly. " + 
                "The commented 'rm' commands require manual review and uncommented execution.\n")

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
        sys.exit(1)
    
    # Analyze Git branches
    branch_data = analyze_branches()
    write_branch_inventory(branch_data)
    
    # Find and analyze all scripts
    script_files = find_all_scripts()
    script_data = analyze_script_usage(script_files)
    write_script_inventory(script_data)
    
    # Generate final report
    generate_final_report(branch_data, script_data)
    
    print("Analysis complete!")
    print(f"Branch inventory: {os.path.abspath(OUTPUT_CSV)}")
    print(f"Script inventory: {os.path.abspath(SCRIPT_INVENTORY_CSV)}")
    print(f"Final report: {os.path.abspath(FINAL_REPORT)}")

if __name__ == "__main__":
    main()