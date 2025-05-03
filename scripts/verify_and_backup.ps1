# Verification and Backup Script for Social Cube Project
# 
# This script verifies branch merge completeness and creates backups of branches
# and scripts identified for potential removal.

# Constants
$BACKUP_DIR = "backup/cleanup_backup"
$BRANCH_BACKUP_DIR = "$BACKUP_DIR/branches"
$SCRIPT_BACKUP_DIR = "$BACKUP_DIR/scripts"
$VERIFICATION_REPORT = "docs/verification_report.md"
$BRANCH_BUNDLE_DIR = "$BRANCH_BACKUP_DIR/bundles"
$BRANCH_PATCH_DIR = "$BRANCH_BACKUP_DIR/patches"
$STALE_THRESHOLD_DAYS = 90

# Set working directory to project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item $scriptDir).Parent.FullName
Set-Location $projectRoot

Write-Host "Running verification and backup from project root: $($PWD.Path)"

# Check if we're in a Git repository
if (-not (Test-Path ".git")) {
    Write-Error "Error: This doesn't appear to be a Git repository."
    Write-Error "Please run this script from the root of a Git repository."
    exit 1
}

# Create backup directories
function Setup-BackupDirectories {
    New-Item -ItemType Directory -Path $BRANCH_BACKUP_DIR -Force | Out-Null
    New-Item -ItemType Directory -Path $SCRIPT_BACKUP_DIR -Force | Out-Null
    New-Item -ItemType Directory -Path $BRANCH_BUNDLE_DIR -Force | Out-Null
    New-Item -ItemType Directory -Path $BRANCH_PATCH_DIR -Force | Out-Null
    Write-Host "Created backup directories in $BACKUP_DIR"
}

# Get list of all local branches
function Get-AllBranches {
    $branchesOutput = git branch --format="%(refname:short)" 2>$null
    return $branchesOutput | Where-Object { $_ -ne "" }
}

# Verify if a branch is completely merged into the target branch
function Verify-BranchMerge {
    param (
        [string]$branchName,
        [string]$targetBranch = "main"
    )
    
    Write-Host "`nVerifying merge status of branch: $branchName"
    
    # Check if branch exists
    $branches = Get-AllBranches
    if ($branchName -notin $branches) {
        Write-Host "Error: Branch $branchName not found"
        return @{
            name = $branchName
            merge_verified = $false
            target_branch = $targetBranch
            unique_commits = @()
            error = "Branch not found"
        }
    }
    
    # Get unique commits in the branch (not in target)
    $unmergedCommits = git log "$targetBranch..$branchName" --pretty=format:"%h: %s" --no-merges 2>$null
    
    $uniqueCommits = @()
    if ($unmergedCommits) {
        $uniqueCommits = $unmergedCommits | Where-Object { $_ -ne "" }
        Write-Host "  Found $($uniqueCommits.Count) commits in $branchName not in $targetBranch:"
        foreach ($commit in $uniqueCommits) {
            Write-Host "  - $commit"
        }
    } else {
        Write-Host "  Branch $branchName is fully merged into $targetBranch"
    }
    
    return @{
        name = $branchName
        merge_verified = $uniqueCommits.Count -eq 0
        target_branch = $targetBranch
        unique_commits = $uniqueCommits
        error = $null
    }
}

# Create a backup of a branch in bundle and patch format
function Backup-Branch {
    param (
        [string]$branchName
    )
    
    Write-Host "`nBacking up branch: $branchName"
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $bundleFile = "$BRANCH_BUNDLE_DIR/$($branchName.Replace('/', '_'))_$timestamp.bundle"
    $patchFile = "$BRANCH_PATCH_DIR/$($branchName.Replace('/', '_'))_$timestamp.patch"
    
    # Create a bundle (binary file with complete branch history)
    git bundle create $bundleFile $branchName 2>$null
    
    # Create a patch file (text-based diff)
    git format-patch --stdout main..$branchName > $patchFile 2>$null
    
    return @{
        name = $branchName
        bundle_file = $bundleFile
        patch_file = $patchFile
        timestamp = $timestamp
    }
}

# Find references to a script in the codebase
function Find-ScriptReferences {
    param (
        [string]$scriptPath
    )
    
    $scriptName = Split-Path -Leaf $scriptPath
    $moduleName = [System.IO.Path]::GetFileNameWithoutExtension($scriptName)
    
    # Search patterns based on file type
    $ext = [System.IO.Path]::GetExtension($scriptPath).ToLower()
    $patterns = @()
    
    if ($ext -eq ".py") {
        $patterns = @(
            "import\s+$moduleName",
            "from\s+$moduleName\s+import",
            "from\s+\.$moduleName\s+import",
            "__import__\(['\"]($moduleName|\.$moduleName)['\"]\\)"
        )
    } elseif ($ext -in @(".sh", ".bat", ".ps1")) {
        $escapedScriptName = [regex]::Escape($scriptName)
        $patterns = @(
            "subprocess\.\w+\(['\"].*$escapedScriptName",
            "os\.system\(['\"].*$escapedScriptName",
            "call\(['\"].*$escapedScriptName",
            "source\s+['\"]?.*$escapedScriptName",
            "\.\s*/.*$escapedScriptName",
            "\./.*$escapedScriptName",
            "sh\s+.*$escapedScriptName",
            "bash\s+.*$escapedScriptName",
            "cmd\s+.*$escapedScriptName"
        )
    } elseif ($ext -eq ".js") {
        $patterns = @(
            "require\(['\"].*$moduleName['\"]\\)",
            "import.*from\s+['\"].*$moduleName['\"]",
            "import\s+['\"].*$moduleName['\"]",
            "<script\s+src=['\"].*$scriptName['\"]>"
        )
    }
    
    # Files to search in
    $skipDirs = @('__pycache__', 'node_modules', 'venv', 'env', '.git', $BACKUP_DIR)
    $filesToSearch = @()
    
    Get-ChildItem -Recurse -File | Where-Object {
        $skip = $false
        foreach ($dir in $skipDirs) {
            if ($_.FullName -like "*$dir*") {
                $skip = $true
                break
            }
        }
        
        if (-not $skip -and $_.Extension -in @('.py', '.js', '.sh', '.bat', '.ps1', '.yml', '.yaml', '.json', '.md', '.html')) {
            return $_.FullName -ne $scriptPath
        }
        
        return $false
    } | ForEach-Object {
        $filesToSearch += $_.FullName
    }
    
    # Search for references
    $references = @()
    
    foreach ($filePath in $filesToSearch) {
        try {
            $content = Get-Content -Path $filePath -Raw -ErrorAction SilentlyContinue
            
            foreach ($pattern in $patterns) {
                if ($content -match $pattern) {
                    $references += @{
                        file = $filePath
                        pattern = $pattern
                    }
                    break
                }
            }
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Warning "Error reading $filePath: $errorMsg"
        }
    }
    
    return $references
}

# Create a backup of a script file
function Backup-Script {
    param (
        [string]$scriptPath
    )
    
    # Create target directory with same structure
    $targetDir = Join-Path -Path $SCRIPT_BACKUP_DIR -ChildPath (Split-Path -Parent $scriptPath)
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    
    # Copy the file
    $targetPath = Join-Path -Path $SCRIPT_BACKUP_DIR -ChildPath $scriptPath
    try {
        Copy-Item -Path $scriptPath -Destination $targetPath -Force
        return $true
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Host "Error backing up $scriptPath: $errorMsg"
        return $false
    }
}

# Get information about a script file
function Get-ScriptInfo {
    param (
        [string]$scriptPath
    )
    
    try {
        $fileInfo = Get-Item $scriptPath
        $modTime = $fileInfo.LastWriteTime
        $size = $fileInfo.Length
        
        # Try to extract purpose from file content
        $purpose = "Unknown"
        try {
            $firstLines = Get-Content -Path $scriptPath -TotalCount 10 -ErrorAction SilentlyContinue | Out-String
            
            if ($firstLines -match '"""(.+?)"""') {
                $purpose = $matches[1].Trim() -split "`n" | Select-Object -First 1
            } elseif ($firstLines -match '#\s*(.+)') {
                $purpose = $matches[1].Trim()
            }
        } catch {
            # Ignore errors in purpose extraction
        }
        
        return @{
            path = $scriptPath
            last_modified = $modTime.ToString("yyyy-MM-dd")
            size = $size
            purpose = $purpose
        }
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Host "Error getting info for $scriptPath: $errorMsg"
        return @{
            path = $scriptPath
            error = $errorMsg
        }
    }
}

# Create a detailed verification report
function Create-VerificationReport {
    param (
        [array]$branchResults,
        [array]$scriptResults
    )
    
    Write-Host "`nGenerating verification report: $VERIFICATION_REPORT"
    
    $report = @"
# Verification and Backup Report

Report generated on: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Branch Verification Results

| Branch | Merge Verified | Target Branch | Unique Commits | Backup Created |
|--------|---------------|--------------|----------------|----------------|
"@
    
    foreach ($branch in $branchResults) {
        $uniqueCommits = ($branch.unique_commits | Measure-Object).Count
        $mergeVerified = $branch.merge_verified
        $hasBackup = $null -ne $branch.bundle_file
        
        $report += "`n| $($branch.name) | $(if ($mergeVerified) { '✅' } else { '❌' }) | " +
                  "$($branch.target_branch) | $uniqueCommits | " +
                  "$(if ($hasBackup) { '✅' } else { '❌' }) |"
    }
    
    $report += "`n`n### Unmerged Commits`n"
    
    foreach ($branch in $branchResults) {
        $uniqueCommits = $branch.unique_commits
        if ($uniqueCommits -and $uniqueCommits.Count -gt 0) {
            $report += "`n#### $($branch.name)`n`n"
            foreach ($commit in $uniqueCommits) {
                $report += "- $commit`n"
            }
        }
    }
    
    $report += @"

## Script Verification Results

| Script | Referenced | Reference Count | Verified Safe | Backup Created |
|--------|------------|----------------|--------------|----------------|
"@
    
    foreach ($script in $scriptResults) {
        $references = $script.references
        $refCount = ($references | Measure-Object).Count
        $isReferenced = $refCount -gt 0
        $verifiedSafe = -not $isReferenced
        $backupCreated = $script.backup_success
        
        $report += "`n| $($script.path) | $(if ($isReferenced) { 'Yes' } else { 'No' }) | " +
                  "$refCount | $(if ($verifiedSafe) { '✅' } else { '❌' }) | " +
                  "$(if ($backupCreated) { '✅' } else { '❌' }) |"
    }
    
    $report += "`n`n### Script References`n"
    
    foreach ($script in $scriptResults) {
        $references = $script.references
        if ($references -and $references.Count -gt 0) {
            $report += "`n#### $($script.path)`n`n"
            foreach ($ref in $references) {
                $report += "- Referenced in: $($ref.file)`n"
            }
        }
    }
    
    $report += @"

## Backup Information

All backups are stored in the `$BACKUP_DIR` directory.

### Branch Backups

Branches have been backed up in two formats:

- **Bundle files**: `$BRANCH_BUNDLE_DIR/*.bundle` - Complete branch history in Git bundle format
- **Patch files**: `$BRANCH_PATCH_DIR/*.patch` - Text-based patches that can be applied to a repository

To restore a branch from a bundle:

```bash
# Create a new branch from the bundle
git bundle unbundle path/to/branch_name.bundle
git checkout -b restored_branch_name branch_name
```

To apply a patch:

```bash
# Apply the patch to the current branch
git apply path/to/branch_name.patch
```

### Script Backups

Scripts have been backed up to the `$SCRIPT_BACKUP_DIR` directory with their original directory structure preserved.

To restore a script:

```bash
# Simply copy the file back to its original location
cp backup/cleanup_backup/scripts/path/to/script.py path/to/script.py
```

## Recommendations

"@
    
    # Branch recommendations
    $safeToRemoveBranches = $branchResults | Where-Object { $_.merge_verified }
    $unsafeBranches = $branchResults | Where-Object { -not $_.merge_verified }
    
    if ($safeToRemoveBranches -and $safeToRemoveBranches.Count -gt 0) {
        $report += @"
### Branches Safe to Remove

The following branches have been verified as fully merged and can be safely removed:

"@
        foreach ($branch in $safeToRemoveBranches) {
            $report += "- $($branch.name)`n"
        }
        
        $report += "`n```bash`n"
        foreach ($branch in $safeToRemoveBranches) {
            $report += "git branch -d $($branch.name)  # Remove locally`n"
        }
        $report += "`n# Then to remove from remote:`n"
        foreach ($branch in $safeToRemoveBranches) {
            $report += "git push origin --delete $($branch.name)`n"
        }
        $report += "````n`n"
    }
    
    if ($unsafeBranches -and $unsafeBranches.Count -gt 0) {
        $report += @"
### Branches Requiring Further Review

The following branches have unique commits not present in the target branch:

"@
        foreach ($branch in $unsafeBranches) {
            $uniqueCommits = ($branch.unique_commits | Measure-Object).Count
            $report += "- $($branch.name) ($uniqueCommits unique commits)`n"
        }
        $report += "`nPlease review these branches carefully before removing.`n`n"
    }
    
    # Script recommendations
    $safeScripts = $scriptResults | Where-Object { ($_.references | Measure-Object).Count -eq 0 }
    $unsafeScripts = $scriptResults | Where-Object { ($_.references | Measure-Object).Count -gt 0 }
    
    if ($safeScripts -and $safeScripts.Count -gt 0) {
        $report += @"
### Scripts Safe to Remove

The following scripts have no detected references and can likely be safely removed:

"@
        foreach ($script in $safeScripts) {
            $report += "- $($script.path)`n"
        }
        
        $report += "`n```bash`n"
        foreach ($script in $safeScripts) {
            $report += "# rm $($script.path)`n"
        }
        $report += "````n`n"
        $report += "**Note:** The removal commands are commented out. Review each script and uncomment to remove.`n`n"
    }
    
    if ($unsafeScripts -and $unsafeScripts.Count -gt 0) {
        $report += @"
### Scripts Requiring Further Review

The following scripts have references in the codebase and should be reviewed carefully:

"@
        foreach ($script in $unsafeScripts) {
            $refCount = ($script.references | Measure-Object).Count
            $report += "- $($script.path) ($refCount references)`n"
        }
        $report += "`nConsider whether these references are essential or can be removed.`n`n"
    }
    
    # Write the report to the file
    $report | Out-File -FilePath $VERIFICATION_REPORT -Encoding utf8
}

# Create a zip archive of all backups
function Create-ZipBackup {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $zipFile = "$BACKUP_DIR/cleanup_backup_$timestamp.zip"
    
    Write-Host "`nCreating zip backup: $zipFile"
    
    if (-not (Test-Path $BACKUP_DIR)) {
        Write-Warning "Backup directory not found, cannot create zip."
        return $null
    }
    
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory($BACKUP_DIR, $zipFile)
        
        Write-Host "Zip backup created: $zipFile"
        return $zipFile
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Warning "Failed to create zip backup: $errorMsg"
        return $null
    }
}

# Main execution

# Create backup directories
Setup-BackupDirectories

# Get all branches to verify
$branches = Get-AllBranches
$branchResults = @()

# Verify and backup each branch except main
foreach ($branch in $branches) {
    if ($branch -eq "main") {
        continue
    }
    
    # Verify merge status
    $verification = Verify-BranchMerge -branchName $branch
    
    # Create backup
    $backup = Backup-Branch -branchName $branch
    
    # Combine results
    $result = $verification.Clone()
    $backup.Keys | ForEach-Object {
        $result[$_] = $backup[$_]
    }
    
    $branchResults += $result
}

# Find potential unused scripts (stale scripts)
Write-Host "`nSearching for potentially unused scripts..."
$scriptResults = @()

# Find old scripts
$now = Get-Date
$scriptExtensions = @(".py", ".sh", ".bat", ".ps1", ".js")

Get-ChildItem -Recurse -File | Where-Object {
    $scriptExtensions -contains $_.Extension.ToLower() -and
    $_.FullName -notmatch "[/\\]\." -and
    $_.FullName -notmatch "[/\\]__pycache__[/\\]" -and
    $_.FullName -notmatch "[/\\]node_modules[/\\]" -and
    $_.FullName -notmatch "[/\\]venv[/\\]" -and
    $_.FullName -notmatch "[/\\]env[/\\]" -and
    $_.FullName -notmatch "[/\\]\.git[/\\]" -and
    $_.FullName -notmatch "[/\\]$BACKUP_DIR[/\\]"
} | ForEach-Object {
    $scriptPath = $_.FullName
    $daysOld = ($now - $_.LastWriteTime).Days
    
    if ($daysOld -gt $STALE_THRESHOLD_DAYS) {
        # Get script info
        $scriptInfo = Get-ScriptInfo -scriptPath $scriptPath
        
        # Make path relative to project root
        $scriptInfo["path"] = $scriptPath.Replace("$projectRoot\", "").Replace("\", "/")
        
        # Check for references
        $references = Find-ScriptReferences -scriptPath $scriptPath
        $scriptInfo["references"] = $references
        
        # Backup the script
        $backupSuccess = Backup-Script -scriptPath $scriptPath
        $scriptInfo["backup_success"] = $backupSuccess
        
        $scriptResults += $scriptInfo
        
        # Print result
        $refStatus = if ($references.Count -gt 0) { "Found $($references.Count) references" } else { "No references found" }
        Write-Host "  $($scriptInfo.path) - $daysOld days old - $refStatus"
    }
}

# Create verification report
Create-VerificationReport -branchResults $branchResults -scriptResults $scriptResults

# Create a zip backup archive
$zipFile = Create-ZipBackup

Write-Host "`nVerification and backup process complete!"
Write-Host "Verification report: $(Resolve-Path $VERIFICATION_REPORT)"
Write-Host "Backup directory: $(Resolve-Path $BACKUP_DIR)"
if ($zipFile) {
    Write-Host "Backup archive: $(Resolve-Path $zipFile)"
}