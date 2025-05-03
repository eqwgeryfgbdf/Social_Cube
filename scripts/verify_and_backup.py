#!/usr/bin/env python3
"""
Verification and Backup Script for Social Cube Project

This script verifies branch merge completeness and creates backups of branches
and scripts identified for potential removal.
"""

import os
import subprocess
import datetime
import json
import shutil
import zipfile
import re
import sys
from pathlib import Path

# Constants
BACKUP_DIR = 'backup/cleanup_backup'
BRANCH_BACKUP_DIR = f'{BACKUP_DIR}/branches'
SCRIPT_BACKUP_DIR = f'{BACKUP_DIR}/scripts'
VERIFICATION_REPORT = 'docs/verification_report.md'
INVENTORY_FILE = 'docs/branch_script_inventory.md'
BRANCH_BUNDLE_DIR = f'{BRANCH_BACKUP_DIR}/bundles'
BRANCH_PATCH_DIR = f'{BRANCH_BACKUP_DIR}/patches'

def run_command(cmd, show_output=True):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True)
        if show_output and result.stdout.strip():
            print(result.stdout.strip())
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}")
        print(f"Error message: {e.stderr}")
        return ""

def setup_backup_directories():
    """Create backup directories if they don't exist"""
    os.makedirs(BRANCH_BACKUP_DIR, exist_ok=True)
    os.makedirs(SCRIPT_BACKUP_DIR, exist_ok=True)
    os.makedirs(BRANCH_BUNDLE_DIR, exist_ok=True)
    os.makedirs(BRANCH_PATCH_DIR, exist_ok=True)
    print(f"Created backup directories in {BACKUP_DIR}")

def get_all_branches():
    """Get list of all local branches"""
    branches_cmd = 'git branch --format="%(refname:short)"'
    branches_output = run_command(branches_cmd, show_output=False)
    return [b.strip() for b in branches_output.split('\n') if b.strip()]

def verify_branch_merge(branch_name, target_branch='main'):
    """Verify if a branch is completely merged into the target branch"""
    print(f"\nVerifying merge status of branch: {branch_name}")
    
    # Check if branch exists
    branches = get_all_branches()
    if branch_name not in branches:
        print(f"Error: Branch {branch_name} not found")
        return {
            'name': branch_name,
            'merge_verified': False,
            'target_branch': target_branch,
            'unique_commits': [],
            'error': 'Branch not found'
        }
    
    # Get unique commits in the branch (not in target)
    unmerged_cmd = f'git log {target_branch}..{branch_name} --pretty=format:"%h: %s" --no-merges'
    unmerged_commits = run_command(unmerged_cmd, show_output=False)
    
    unique_commits = []
    if unmerged_commits:
        unique_commits = [commit.strip() for commit in unmerged_commits.split('\n') if commit.strip()]
        print(f"  Found {len(unique_commits)} commits in {branch_name} not in {target_branch}:")
        for commit in unique_commits:
            print(f"  - {commit}")
    else:
        print(f"  Branch {branch_name} is fully merged into {target_branch}")
    
    return {
        'name': branch_name,
        'merge_verified': len(unique_commits) == 0,
        'target_branch': target_branch,
        'unique_commits': unique_commits,
        'error': None
    }

def backup_branch(branch_name):
    """Create a backup of a branch in bundle and patch format"""
    print(f"\nBacking up branch: {branch_name}")
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bundle_file = f"{BRANCH_BUNDLE_DIR}/{branch_name.replace('/', '_')}_{timestamp}.bundle"
    patch_file = f"{BRANCH_PATCH_DIR}/{branch_name.replace('/', '_')}_{timestamp}.patch"
    
    # Create a bundle (binary file with complete branch history)
    bundle_cmd = f'git bundle create "{bundle_file}" {branch_name}'
    run_command(bundle_cmd)
    
    # Create a patch file (text-based diff)
    patch_cmd = f'git format-patch --stdout main..{branch_name} > "{patch_file}"'
    run_command(patch_cmd, show_output=False)
    
    return {
        'name': branch_name,
        'bundle_file': bundle_file,
        'patch_file': patch_file,
        'timestamp': timestamp
    }

def find_script_references(script_path):
    """Find references to a script in the codebase"""
    script_name = os.path.basename(script_path)
    module_name = os.path.splitext(script_name)[0]
    
    # Search patterns based on file type
    _, ext = os.path.splitext(script_path)
    patterns = []
    
    if ext.lower() == '.py':
        patterns = [
            f"import\\s+{module_name}",
            f"from\\s+{module_name}\\s+import",
            f"from\\s+\\.{module_name}\\s+import",
            f"__import__\\(['\"]({module_name}|\\.{module_name})['\"]\\)"
        ]
    elif ext.lower() in ['.sh', '.bat', '.ps1']:
        patterns = [
            f"subprocess\\.\\w+\\(['\"].*{re.escape(script_name)}",
            f"os\\.system\\(['\"].*{re.escape(script_name)}",
            f"call\\(['\"].*{re.escape(script_name)}",
            f"source\\s+['\"]?.*{re.escape(script_name)}",
            f"\\.\\s*/.*{re.escape(script_name)}",
            f"\\./.*{re.escape(script_name)}",
            f"sh\\s+.*{re.escape(script_name)}",
            f"bash\\s+.*{re.escape(script_name)}",
            f"cmd\\s+.*{re.escape(script_name)}"
        ]
    elif ext.lower() == '.js':
        patterns = [
            f"require\\(['\"].*{module_name}['\"]\\)",
            f"import.*from\\s+['\"].*{module_name}['\"]",
            f"import\\s+['\"].*{module_name}['\"]",
            f"<script\\s+src=['\"].*{script_name}['\"]>"
        ]
    
    # Files to search in
    skip_dirs = ['__pycache__', 'node_modules', 'venv', 'env', '.git', BACKUP_DIR]
    files_to_search = []
    
    for root, dirs, files in os.walk('.'):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        
        for file in files:
            if not file.endswith(('.py', '.js', '.sh', '.bat', '.ps1', '.yml', '.yaml', '.json', '.md', '.html')):
                continue
            
            file_path = os.path.join(root, file)
            if file_path != script_path:  # Don't check the script itself
                files_to_search.append(file_path)
    
    # Search for references
    references = []
    
    for file_path in files_to_search:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        references.append({
                            'file': file_path,
                            'matches': matches,
                            'pattern': pattern
                        })
                        break  # Only need to know that there is at least one reference
        except Exception as e:
            print(f"Warning: Error reading {file_path}: {e}")
    
    return references

def backup_script(script_path):
    """Create a backup of a script file"""
    # Create target directory with same structure
    target_dir = os.path.join(SCRIPT_BACKUP_DIR, os.path.dirname(script_path))
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy the file
    target_path = os.path.join(SCRIPT_BACKUP_DIR, script_path)
    try:
        shutil.copy2(script_path, target_path)
        return True
    except Exception as e:
        print(f"Error backing up {script_path}: {e}")
        return False

def get_script_info(script_path):
    """Get information about a script file"""
    try:
        stat_info = os.stat(script_path)
        mod_time = datetime.datetime.fromtimestamp(stat_info.st_mtime)
        size = stat_info.st_size
        
        # Try to extract purpose from file content
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
        except Exception:
            pass
        
        return {
            'path': script_path,
            'last_modified': mod_time.strftime('%Y-%m-%d'),
            'size': size,
            'purpose': purpose
        }
    except Exception as e:
        print(f"Error getting info for {script_path}: {e}")
        return {
            'path': script_path,
            'error': str(e)
        }

def create_verification_report(branch_results, script_results):
    """Create a detailed verification report"""
    print(f"\nGenerating verification report: {VERIFICATION_REPORT}")
    
    with open(VERIFICATION_REPORT, 'w') as f:
        f.write("# Verification and Backup Report\n\n")
        f.write(f"Report generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Branch verification results
        f.write("## Branch Verification Results\n\n")
        f.write("| Branch | Merge Verified | Target Branch | Unique Commits | Backup Created |\n")
        f.write("|--------|---------------|--------------|----------------|----------------|\n")
        
        for branch in branch_results:
            unique_commits = len(branch.get('unique_commits', []))
            merge_verified = branch.get('merge_verified', False)
            has_backup = 'bundle_file' in branch
            
            f.write(f"| {branch['name']} | {'✅' if merge_verified else '❌'} | " +
                   f"{branch.get('target_branch', 'N/A')} | {unique_commits} | " +
                   f"{'✅' if has_backup else '❌'} |\n")
        
        f.write("\n")
        
        # List all unique commits that are not merged
        f.write("### Unmerged Commits\n\n")
        for branch in branch_results:
            unique_commits = branch.get('unique_commits', [])
            if unique_commits:
                f.write(f"#### {branch['name']}\n\n")
                for commit in unique_commits:
                    f.write(f"- {commit}\n")
                f.write("\n")
        
        # Script verification results
        f.write("## Script Verification Results\n\n")
        f.write("| Script | Referenced | Reference Count | Verified Safe | Backup Created |\n")
        f.write("|--------|------------|----------------|--------------|----------------|\n")
        
        for script in script_results:
            references = script.get('references', [])
            ref_count = len(references)
            is_referenced = ref_count > 0
            verified_safe = not is_referenced
            backup_created = script.get('backup_success', False)
            
            f.write(f"| {script['path']} | {'Yes' if is_referenced else 'No'} | " +
                   f"{ref_count} | {'❌' if is_referenced else '✅'} | " +
                   f"{'✅' if backup_created else '❌'} |\n")
        
        f.write("\n")
        
        # List all references found for each script
        f.write("### Script References\n\n")
        for script in script_results:
            references = script.get('references', [])
            if references:
                f.write(f"#### {script['path']}\n\n")
                for ref in references:
                    f.write(f"- Referenced in: {ref['file']}\n")
                f.write("\n")
        
        # Backup details
        f.write("## Backup Information\n\n")
        f.write(f"All backups are stored in the `{BACKUP_DIR}` directory.\n\n")
        
        f.write("### Branch Backups\n\n")
        f.write("Branches have been backed up in two formats:\n\n")
        f.write(f"- **Bundle files**: `{BRANCH_BUNDLE_DIR}/*.bundle` - Complete branch history in Git bundle format\n")
        f.write(f"- **Patch files**: `{BRANCH_PATCH_DIR}/*.patch` - Text-based patches that can be applied to a repository\n\n")
        
        f.write("To restore a branch from a bundle:\n\n")
        f.write("```bash\n")
        f.write("# Create a new branch from the bundle\n")
        f.write("git bundle unbundle path/to/branch_name.bundle\n")
        f.write("git checkout -b restored_branch_name branch_name\n")
        f.write("```\n\n")
        
        f.write("To apply a patch:\n\n")
        f.write("```bash\n")
        f.write("# Apply the patch to the current branch\n")
        f.write("git apply path/to/branch_name.patch\n")
        f.write("```\n\n")
        
        f.write("### Script Backups\n\n")
        f.write(f"Scripts have been backed up to the `{SCRIPT_BACKUP_DIR}` directory with their original directory structure preserved.\n\n")
        
        f.write("To restore a script:\n\n")
        f.write("```bash\n")
        f.write("# Simply copy the file back to its original location\n")
        f.write("cp backup/cleanup_backup/scripts/path/to/script.py path/to/script.py\n")
        f.write("```\n\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        
        # Branch recommendations
        safe_to_remove_branches = [b for b in branch_results if b.get('merge_verified', False)]
        unsafe_branches = [b for b in branch_results if not b.get('merge_verified', False)]
        
        if safe_to_remove_branches:
            f.write("### Branches Safe to Remove\n\n")
            f.write("The following branches have been verified as fully merged and can be safely removed:\n\n")
            for branch in safe_to_remove_branches:
                f.write(f"- {branch['name']}\n")
            
            f.write("\n```bash\n")
            for branch in safe_to_remove_branches:
                f.write(f"git branch -d {branch['name']}  # Remove locally\n")
            f.write("\n# Then to remove from remote:\n")
            for branch in safe_to_remove_branches:
                f.write(f"git push origin --delete {branch['name']}\n")
            f.write("```\n\n")
        
        if unsafe_branches:
            f.write("### Branches Requiring Further Review\n\n")
            f.write("The following branches have unique commits not present in the target branch:\n\n")
            for branch in unsafe_branches:
                f.write(f"- {branch['name']} ({len(branch.get('unique_commits', []))} unique commits)\n")
            f.write("\nPlease review these branches carefully before removing.\n\n")
        
        # Script recommendations
        safe_scripts = [s for s in script_results if not s.get('references')]
        unsafe_scripts = [s for s in script_results if s.get('references')]
        
        if safe_scripts:
            f.write("### Scripts Safe to Remove\n\n")
            f.write("The following scripts have no detected references and can likely be safely removed:\n\n")
            for script in safe_scripts:
                f.write(f"- {script['path']}\n")
            
            f.write("\n```bash\n")
            for script in safe_scripts:
                f.write(f"# rm {script['path']}\n")
            f.write("```\n\n")
            f.write("**Note:** The removal commands are commented out. Review each script and uncomment to remove.\n\n")
        
        if unsafe_scripts:
            f.write("### Scripts Requiring Further Review\n\n")
            f.write("The following scripts have references in the codebase and should be reviewed carefully:\n\n")
            for script in unsafe_scripts:
                ref_count = len(script.get('references', []))
                f.write(f"- {script['path']} ({ref_count} references)\n")
            f.write("\nConsider whether these references are essential or can be removed.\n\n")

def create_zip_backup():
    """Create a zip archive of all backups"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_file = f"{BACKUP_DIR}/cleanup_backup_{timestamp}.zip"
    
    print(f"\nCreating zip backup: {zip_file}")
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(BACKUP_DIR):
            for file in files:
                if file.endswith('.zip'):  # Skip other zip files
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, BACKUP_DIR)
                zipf.write(file_path, arcname)
    
    print(f"Zip backup created: {zip_file}")
    return zip_file

def main():
    """Main function to verify and backup branches and scripts"""
    # Set working directory to project root if not already there
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    os.chdir(project_root)
    
    print(f"Running verification and backup from project root: {os.getcwd()}")
    
    # Check if we're in a Git repository
    if not os.path.exists('.git'):
        print("Error: This doesn't appear to be a Git repository.")
        print("Please run this script from the root of a Git repository.")
        sys.exit(1)
    
    # Create backup directories
    setup_backup_directories()
    
    # Get all branches to verify
    branches = get_all_branches()
    branch_results = []
    
    # Verify and backup each branch except main
    for branch in branches:
        if branch == 'main':
            continue
        
        # Verify merge status
        verification = verify_branch_merge(branch)
        
        # Create backup
        backup = backup_branch(branch)
        
        # Combine results
        result = {**verification, **backup}
        branch_results.append(result)
    
    # Find potential unused scripts (stale scripts)
    print("\nSearching for potentially unused scripts...")
    stale_threshold = 90  # days
    now = datetime.datetime.now()
    
    script_extensions = ['.py', '.sh', '.bat', '.ps1', '.js']
    script_results = []
    
    # Find old scripts
    for root, dirs, files in os.walk('.'):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and 
                  d not in ['__pycache__', 'node_modules', 'venv', 'env', '.git', BACKUP_DIR]]
        
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in script_extensions:
                script_path = os.path.join(root, file)
                
                # Check file age
                try:
                    mod_time = os.path.getmtime(script_path)
                    mod_date = datetime.datetime.fromtimestamp(mod_time)
                    days_old = (now - mod_date).days
                    
                    if days_old > stale_threshold:
                        # Get script info
                        script_info = get_script_info(script_path)
                        
                        # Check for references
                        references = find_script_references(script_path)
                        script_info['references'] = references
                        
                        # Backup the script
                        backup_success = backup_script(script_path)
                        script_info['backup_success'] = backup_success
                        
                        script_results.append(script_info)
                        
                        # Print result
                        ref_status = f"Found {len(references)} references" if references else "No references found"
                        print(f"  {script_path} - {days_old} days old - {ref_status}")
                except Exception as e:
                    print(f"Error processing {script_path}: {e}")
    
    # Create verification report
    create_verification_report(branch_results, script_results)
    
    # Create a zip backup archive
    zip_file = create_zip_backup()
    
    print("\nVerification and backup process complete!")
    print(f"Verification report: {os.path.abspath(VERIFICATION_REPORT)}")
    print(f"Backup directory: {os.path.abspath(BACKUP_DIR)}")
    print(f"Backup archive: {os.path.abspath(zip_file)}")

if __name__ == "__main__":
    main()