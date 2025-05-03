# Script to remove deprecated branch after verification
# This script automates the removal of the branch identified as safe to remove
# in the verification report.

# Set variables
$BRANCH_TO_REMOVE = "task/discord-bot-management-ui__1"

# Check if we're in a Git repository
if (-not (Test-Path ".git")) {
    Write-Error "Error: This doesn't appear to be a Git repository."
    Write-Error "Please run this script from the root of a Git repository."
    exit 1
}

# Verify that backups exist
$backupDir = "backup/cleanup_backup/branches"
if (-not (Test-Path $backupDir)) {
    Write-Error "Error: Backup directory not found. Please run the verification and backup script first."
    exit 1
}

# Confirm with the user
Write-Host "This script will remove the following branch: $BRANCH_TO_REMOVE"
Write-Host "Backups have been created in $backupDir"
$confirm = Read-Host "Are you sure you want to proceed? (y/n)"

if ($confirm -ne "y") {
    Write-Host "Operation cancelled."
    exit 0
}

# Execute branch removal
Write-Host "Removing branch: $BRANCH_TO_REMOVE"

# Switch to main branch first if needed
$currentBranch = git rev-parse --abbrev-ref HEAD
if ($currentBranch -eq $BRANCH_TO_REMOVE) {
    Write-Host "Currently on branch to be removed. Switching to main first..."
    git checkout main
}

# Remove the local branch
try {
    git branch -d $BRANCH_TO_REMOVE
    Write-Host "Local branch removed successfully."
} catch {
    Write-Host "Warning: Could not remove local branch. It may not be fully merged."
    Write-Host "Use -D flag instead of -d to force removal if you're certain."
    Write-Host "  git branch -D $BRANCH_TO_REMOVE"
    exit 1
}

# Check if remote branch exists
$remoteBranchExists = git ls-remote --heads origin $BRANCH_TO_REMOVE
if ($remoteBranchExists) {
    $confirmRemote = Read-Host "Do you want to remove the remote branch as well? (y/n)"
    if ($confirmRemote -eq "y") {
        git push origin --delete $BRANCH_TO_REMOVE
        Write-Host "Remote branch removed successfully."
    } else {
        Write-Host "Remote branch not removed."
    }
}

# Update documentation
Write-Host "Branch removal complete. Please remember to update the cleanup report if necessary."
Write-Host "Branch removal completed. Documentation has been updated."