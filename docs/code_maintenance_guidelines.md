# Code Maintenance Guidelines

This document outlines the best practices and procedures for maintaining code quality and cleanliness in the Social Cube project, with a specific focus on branch management and script lifecycle.

## Git Branch Management

### Branch Naming Conventions

All branches should follow this naming pattern:

```
<type>/<feature-description>_<YYYY-MM-DD>
```

Where:
- `<type>` is one of: `feature`, `bugfix`, `hotfix`, `refactor`, `task`
- `<feature-description>` is a brief, hyphenated description of the work
- `<YYYY-MM-DD>` is the creation date of the branch

Examples:
- `feature/user-authentication_2025-04-12`
- `bugfix/login-redirect_2025-05-03`
- `refactor/api-endpoints_2025-04-28`

### Branch Lifecycle Policy

- **Maximum Branch Age**: 3 months
- **Stale Branch Definition**: No commits for 1 month
- **Merged Branch Retention**: 2 weeks after merge

### Regular Cleanup Process

1. **Bi-weekly Cleanup**:
   - Run `scripts/branch_script_analyzer.py` to identify candidates for cleanup
   - Review the results with the team
   - Remove merged branches after approval

2. **Quarterly Deep Cleanup**:
   - Run full verification and analysis
   - Address stale branches (merge, update, or remove)
   - Document cleanup actions

3. **Emergency Cleanup**:
   - Run when approaching disk space or performance issues
   - Focus only on fully merged branches
   - Document emergency actions taken

### Branch Archiving Process

Before removing branches with unique work:

1. Create a backup bundle: `git bundle create archives/branch-name.bundle branch-name`
2. Document the archived branch in `docs/archived_branches.md`
3. Remove the branch only after verification of the backup

## Script Management

### Script Documentation Requirements

All scripts must include:

1. **Header Comment Block**:
   ```python
   #!/usr/bin/env python3
   """
   Script Name: example_script.py
   
   Purpose:
   Detailed description of what this script does.
   
   Usage:
   python example_script.py [args]
   
   Created: YYYY-MM-DD
   Last Modified: YYYY-MM-DD
   Author: Developer Name
   """
   ```

2. **Function Documentation**:
   ```python
   def example_function(param1, param2):
       """
       Brief description of function purpose.
       
       Args:
           param1: Description of parameter 1
           param2: Description of parameter 2
           
       Returns:
           Description of return value
       """
       # Implementation
   ```

3. **Usage Examples** (for utility scripts):
   ```python
   if __name__ == "__main__":
       # Example usage
       print("Example usage:")
       print("python example_script.py --arg1 value1 --arg2 value2")
   ```

### Script Lifecycle Management

1. **Creation**:
   - Create with proper documentation
   - Place in appropriate directory (e.g., `scripts/` for utility scripts)
   - Add entry to `docs/script_inventory.md` if applicable

2. **Maintenance**:
   - Update the "Last Modified" date when making changes
   - Ensure documentation remains accurate
   - Add comments for complex logic

3. **Deprecation**:
   - Mark as deprecated in documentation
   - Move to `deprecated/` directory
   - Update documentation to point to replacement
   - Set timeline for removal

4. **Removal**:
   - Backup the script to `backup/` directory
   - Remove from codebase
   - Update documentation to reflect removal
   - Provide recovery instructions if needed

### Quarterly Script Audit

Every quarter:

1. Run `scripts/branch_script_analyzer.py` to identify unused scripts
2. Review usage patterns and identify candidates for cleanup
3. Follow deprecation and removal process for unused scripts
4. Update the script inventory documentation

## CI/CD Considerations

### Pipeline Configuration Maintenance

1. **Regular Validation**:
   - Before removing any scripts or branches, validate all CI/CD configurations
   - Test relevant pipelines with simulated removals before actual deletion

2. **Configuration Updates**:
   - When scripts are deprecated, update CI/CD configurations immediately
   - Use the transitional period to ensure all pipelines function properly

### Documentation References

1. **Keep Documentation Current**:
   - Update all documentation references when scripts are moved or removed
   - Ensure README files are updated with current information

## Backup and Recovery

### Backup Strategy

1. **Regular Backups**:
   - Maintain archives of all removed branches and scripts
   - Use the backup tools provided in `scripts/verify_and_backup.py`

2. **Backup Location**:
   - Store all backups in the `backup/cleanup_backup/` directory
   - Create dated archives for each cleanup session

### Recovery Process

1. **Branch Recovery**:
   - Use bundle files to restore branches: `git bundle unbundle backup/path/to/branch.bundle`
   - Or apply patches for specific changes: `git apply backup/path/to/branch.patch`

2. **Script Recovery**:
   - Copy script from backup directory: `cp backup/cleanup_backup/scripts/path/to/script.py path/to/script.py`
   - Update any dependencies or references as needed

## Implementation Tools

The following tools are available to assist with branch and script management:

1. **Analysis Tools**:
   - `scripts/branch_script_analyzer.py` - Comprehensive analysis of branches and scripts
   - `scripts/simple_branch_analyzer.py` - Quick analysis focused on branches

2. **Verification Tools**:
   - `scripts/verify_and_backup.py` - Verification and backup of branches and scripts
   - `scripts/run_verification.bat` - Windows wrapper for verification scripts

3. **Cleanup Tools**:
   - `scripts/run_branch_analyzer.bat` - Windows wrapper for branch analysis

## Conclusion

Following these guidelines will help maintain a clean, efficient codebase and prevent accumulation of unused or deprecated code. Regular maintenance reduces technical debt and improves project sustainability.