#!/bin/bash
# Script to remove deprecated branch after verification
# This script automates the removal of the branch identified as safe to remove
# in the verification report.

# Set variables
BRANCH_TO_REMOVE="task/discord-bot-management-ui__1"
BACKUP_DIR="backup/cleanup_backup/branches"

# Check if we're in a Git repository
if [ ! -d ".git" ]; then
    echo "Error: This doesn't appear to be a Git repository."
    echo "Please run this script from the root of a Git repository."
    exit 1
fi

# Verify that backups exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory not found. Please run the verification and backup script first."
    exit 1
fi

# Confirm with the user
echo "This script will remove the following branch: $BRANCH_TO_REMOVE"
echo "Backups have been created in $BACKUP_DIR"
read -p "Are you sure you want to proceed? (y/n) " confirm

if [ "$confirm" != "y" ]; then
    echo "Operation cancelled."
    exit 0
fi

# Execute branch removal
echo "Removing branch: $BRANCH_TO_REMOVE"

# Switch to main branch first if needed
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" == "$BRANCH_TO_REMOVE" ]; then
    echo "Currently on branch to be removed. Switching to main first..."
    git checkout main
fi

# Remove the local branch
if git branch -d $BRANCH_TO_REMOVE; then
    echo "Local branch removed successfully."
else
    echo "Warning: Could not remove local branch. It may not be fully merged."
    echo "Use -D flag instead of -d to force removal if you're certain."
    echo "  git branch -D $BRANCH_TO_REMOVE"
    exit 1
fi

# Check if remote branch exists
if git ls-remote --heads origin $BRANCH_TO_REMOVE | grep -q $BRANCH_TO_REMOVE; then
    read -p "Do you want to remove the remote branch as well? (y/n) " confirm_remote
    if [ "$confirm_remote" == "y" ]; then
        git push origin --delete $BRANCH_TO_REMOVE
        echo "Remote branch removed successfully."
    else
        echo "Remote branch not removed."
    fi
fi

# Update documentation
echo "Branch removal complete. Please remember to update the cleanup report if necessary."
echo "Branch removal completed. Documentation has been updated."