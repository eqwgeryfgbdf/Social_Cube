# Branch and Script Analyzer for Social Cube Project
# 
# This script performs two main functions:
# 1. Analyzes Git branches to identify stale or merged branches
# 2. Scans the codebase for potentially unused scripts
#
# The results are compiled into a structured report.

# Constants
$STALE_THRESHOLD_DAYS = 90  # Consider branches stale if no commits for 90 days
$OUTPUT_CSV = "branch_inventory.csv"
$SCRIPT_INVENTORY_CSV = "script_inventory.csv"
$FINAL_REPORT = "cleanup_inventory.md"

# Set working directory to project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Get-Item $scriptDir).Parent.FullName
Set-Location $projectRoot

Write-Host "Running analysis from project root: $($PWD.Path)"

# Check if we're in a Git repository
if (-not (Test-Path ".git")) {
    Write-Error "Error: This doesn't appear to be a Git repository."
    Write-Error "Please run this script from the root of a Git repository."
    exit 1
}

# Analyze Git branches
Write-Host "Analyzing Git branches..."

# Get all branches with their last commit date, author, and subject
$branches = (git for-each-ref --sort=-committerdate refs/heads/ --format="%(refname:short),%(authordate),%(authorname),%(subject)") | 
    Where-Object { $_ -ne "" } | 
    ForEach-Object {
        $parts = $_ -split ',', 4
        if ($parts.Length -ge 4) {
            $branchName, $dateStr, $author, $subject = $parts
            
            # Parse the date
            try {
                $dateObj = [DateTime]::Parse($dateStr)
            } catch {
                Write-Warning "Could not parse date: $dateStr for branch $branchName"
                $dateObj = [DateTime]::new(1970, 1, 1)
            }
            
            # Calculate days since last commit
            $daysSinceCommit = ([DateTime]::Now - $dateObj).Days
            
            # Determine if branch is stale
            $isStale = $daysSinceCommit -gt $STALE_THRESHOLD_DAYS
            
            # Check if branch is merged into main
            $isMerged = (git branch --merged main) -match "\b$branchName\b"
            
            [PSCustomObject]@{
                name = $branchName
                last_commit_date = $dateObj.ToString("yyyy-MM-dd")
                days_since_commit = $daysSinceCommit
                author = $author
                subject = $subject
                is_stale = $isStale
                is_merged = $isMerged
                status = if ($isMerged) { "merged" } elseif ($isStale) { "stale" } else { "active" }
            }
        }
    }

# Write branch inventory to CSV
Write-Host "Writing branch inventory to $OUTPUT_CSV..."
$branches | Export-Csv -Path $OUTPUT_CSV -NoTypeInformation

# Find all script files in the project
Write-Host "Finding all script files..."
$scriptExtensions = @(".py", ".sh", ".bat", ".ps1", ".js")
$scriptFiles = Get-ChildItem -Path . -Recurse -File | 
    Where-Object { 
        $scriptExtensions -contains $_.Extension.ToLower() -and 
        $_.FullName -notmatch "[\\/]\.git[\\/]" -and
        $_.FullName -notmatch "[\\/]__pycache__[\\/]" -and
        $_.FullName -notmatch "[\\/]node_modules[\\/]" -and
        $_.FullName -notmatch "[\\/]venv[\\/]" -and
        $_.FullName -notmatch "[\\/]env[\\/]"
    }

Write-Host "Found $($scriptFiles.Count) script files"

# Analyze script usage patterns
Write-Host "Analyzing script usage patterns..."
$scriptData = @()
$importPatterns = @{}

# First get all script paths and their modified dates
foreach ($scriptFile in $scriptFiles) {
    $modTime = $scriptFile.LastWriteTime
    $daysSinceModified = ([DateTime]::Now - $modTime).Days
    
    # Read first 10 lines to try to determine purpose
    $firstLines = ""
    try {
        $firstLines = Get-Content -Path $scriptFile.FullName -TotalCount 10 -ErrorAction SilentlyContinue | Out-String
    } catch {
        Write-Warning "Could not read file: $($scriptFile.FullName)"
    }
    
    # Try to extract purpose from docstring or comments
    $purpose = "Unknown"
    if ($firstLines -match '"""(.+?)"""') {
        $purpose = $matches[1].Trim() -split "`n" | Select-Object -First 1
    } elseif ($firstLines -match '#\s*(.+)') {
        $purpose = $matches[1].Trim()
    }
    
    $scriptInfo = [PSCustomObject]@{
        path = $scriptFile.FullName.Replace("$projectRoot\", "")
        last_modified = $modTime.ToString("yyyy-MM-dd")
        days_since_modified = $daysSinceModified
        purpose = $purpose
        referenced_count = 0
        status = "unknown"
    }
    
    $scriptData += $scriptInfo
    
    # Determine import pattern based on script type
    $ext = $scriptFile.Extension.ToLower()
    $basename = $scriptFile.Name
    $moduleName = $scriptFile.BaseName
    
    if ($ext -eq ".py") {
        # Create patterns to find imports of this Python module
        $importPatterns[$scriptFile.FullName] = @(
            "import\s+$moduleName",
            "from\s+$moduleName\s+import",
            "from\s+\.$moduleName\s+import",  # Relative import
            "__import__\(['\""]($moduleName|\.$moduleName)['\""]\\)"
        )
    } elseif ($ext -in @(".sh", ".bat", ".ps1")) {
        # Shell/batch scripts usually executed directly or via system calls
        $escapedBasename = [regex]::Escape($basename)
        $importPatterns[$scriptFile.FullName] = @(
            "subprocess\.\w+\(['\""].*$escapedBasename",
            "os\.system\(['\""].*$escapedBasename",
            "call\(['\""].*$escapedBasename",
            "source\s+['\""]?.*$escapedBasename",
            "\.\s*/.*$escapedBasename",
            "\./.*$escapedBasename",
            "sh\s+.*$escapedBasename",
            "bash\s+.*$escapedBasename",
            "cmd\s+.*$escapedBasename"
        )
    } elseif ($ext -eq ".js") {
        # JavaScript imports
        $importPatterns[$scriptFile.FullName] = @(
            "require\(['\""].*$moduleName['\""]\\)",
            "import.*from\s+['\""].*$moduleName['\""]",
            "import\s+['\""].*$moduleName['\""]",
            "<script\s+src=['\""].*$basename['\""]>"
        )
    }
}

# Search for references to each script
foreach ($targetScript in $scriptData) {
    foreach ($searchScript in $scriptFiles) {
        # Don't search within the script itself
        if ($searchScript.FullName -eq $targetScript.path) {
            continue
        }
        
        try {
            $content = Get-Content -Path $searchScript.FullName -Raw -ErrorAction SilentlyContinue
            
            # Check for imports/references to the target script
            $patterns = $importPatterns[$targetScript.path]
            if ($patterns) {
                foreach ($pattern in $patterns) {
                    if ($content -match $pattern) {
                        $targetScript.referenced_count++
                        break
                    }
                }
            }
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Warning "Error reading $($searchScript.FullName): ${errorMsg}"
        }
    }
    
    # Also check if the script is referenced in Docker/compose files
    $dockerFiles = @("Dockerfile", "docker-compose.yml", "docker-compose.override.yml")
    foreach ($dockerFile in $dockerFiles) {
        if (Test-Path $dockerFile) {
            try {
                $content = Get-Content -Path $dockerFile -Raw -ErrorAction SilentlyContinue
                $basename = Split-Path -Leaf $targetScript.path
                if ($content -match $basename) {
                    $targetScript.referenced_count++
                }
            } catch {
                $errorMsg = $_.Exception.Message
                Write-Warning "Error reading ${dockerFile}: ${errorMsg}"
            }
        }
    }
    
    # Set status based on reference count
    if ($targetScript.referenced_count -eq 0) {
        if ($targetScript.days_since_modified -gt $STALE_THRESHOLD_DAYS) {
            $targetScript.status = "likely unused (stale)"
        } else {
            $targetScript.status = "potentially unused (recent)"
        }
    } else {
        $targetScript.status = "in use"
    }
}

# Write script inventory to CSV
Write-Host "Writing script inventory to $SCRIPT_INVENTORY_CSV..."
$scriptData | Export-Csv -Path $SCRIPT_INVENTORY_CSV -NoTypeInformation

# Generate final Markdown report
Write-Host "Generating final report to $FINAL_REPORT..."
$reportContent = @"
# Branch and Script Cleanup Inventory

Report generated on: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Branch Inventory Summary

- Total branches: $($branches.Count)
- Stale branches (no activity for $STALE_THRESHOLD_DAYS+ days): $($branches | Where-Object { $_.is_stale } | Measure-Object | Select-Object -ExpandProperty Count)
- Merged branches: $($branches | Where-Object { $_.is_merged } | Measure-Object | Select-Object -ExpandProperty Count)
- Safe to remove (stale and merged): $($branches | Where-Object { $_.is_stale -and $_.is_merged } | Measure-Object | Select-Object -ExpandProperty Count)

### Branches Safe to Remove

| Branch | Last Commit | Days Since | Author |
|--------|-------------|------------|--------|
"@

foreach ($branch in ($branches | Where-Object { $_.is_stale -and $_.is_merged })) {
    $reportContent += "| $($branch.name) | $($branch.last_commit_date) | $($branch.days_since_commit) | $($branch.author) |`n"
}

$reportContent += @"

### Active Branches

| Branch | Last Commit | Days Since | Author |
|--------|-------------|------------|--------|
"@

foreach ($branch in ($branches | Where-Object { -not $_.is_stale -and -not $_.is_merged })) {
    $reportContent += "| $($branch.name) | $($branch.last_commit_date) | $($branch.days_since_commit) | $($branch.author) |`n"
}

$unusedScripts = $scriptData | Where-Object { $_.referenced_count -eq 0 }
$staleUnused = $unusedScripts | Where-Object { $_.days_since_modified -gt $STALE_THRESHOLD_DAYS }
$recentUnused = $unusedScripts | Where-Object { $_.days_since_modified -le $STALE_THRESHOLD_DAYS }

$reportContent += @"

## Script Inventory Summary

- Total scripts analyzed: $($scriptData.Count)
- Potentially unused scripts: $($unusedScripts.Count)
- Stale unused scripts (no modification for $STALE_THRESHOLD_DAYS+ days): $($staleUnused.Count)
- Recent unused scripts: $($recentUnused.Count)

### Scripts Likely Safe to Remove

| Script Path | Last Modified | Days Since | Purpose |
|-------------|---------------|------------|---------|
"@

foreach ($script in $staleUnused) {
    $purpose = $script.purpose -replace "`n", " "
    if ($purpose.Length -gt 50) {
        $purpose = $purpose.Substring(0, 50)
    }
    $reportContent += "| $($script.path) | $($script.last_modified) | $($script.days_since_modified) | $purpose |`n"
}

$reportContent += @"

### Recently Modified Unused Scripts (Needs Investigation)

| Script Path | Last Modified | Days Since | Purpose |
|-------------|---------------|------------|---------|
"@

foreach ($script in $recentUnused) {
    $purpose = $script.purpose -replace "`n", " "
    if ($purpose.Length -gt 50) {
        $purpose = $purpose.Substring(0, 50)
    }
    $reportContent += "| $($script.path) | $($script.last_modified) | $($script.days_since_modified) | $purpose |`n"
}

$reportContent += @"

## Recommended Actions

### Git Branch Cleanup

Run the following commands to remove stale and merged branches:

```bash
"@

foreach ($branch in ($branches | Where-Object { $_.is_stale -and $_.is_merged })) {
    $reportContent += "git branch -d $($branch.name)  # Remove locally`n"
}

$reportContent += @"

# Then to remove remote branches (if needed):
"@

foreach ($branch in ($branches | Where-Object { $_.is_stale -and $_.is_merged })) {
    $reportContent += "git push origin --delete $($branch.name)`n"
}

$reportContent += @"
```

### Script Backup and Removal Process

1. Create a backup archive of scripts before removal:

```bash
mkdir -p backup/obsolete_scripts
"@

foreach ($script in $staleUnused) {
    $dirName = Split-Path -Parent $script.path
    $reportContent += "mkdir -p backup/obsolete_scripts/$dirName`n"
    $reportContent += "cp $($script.path) backup/obsolete_scripts/$($script.path)`n"
}

$reportContent += @"
```

2. Remove scripts after verification:

```bash
"@

foreach ($script in $staleUnused) {
    $reportContent += "# rm $($script.path)`n"
}

$reportContent += @"
```

**Note:** Before executing removal commands, verify each item thoroughly. The commented 'rm' commands require manual review and uncommented execution.
"@

# Write the report to the file
$reportContent | Out-File -FilePath $FINAL_REPORT -Encoding utf8

Write-Host "Analysis complete!"
Write-Host "Branch inventory: $(Resolve-Path $OUTPUT_CSV)"
Write-Host "Script inventory: $(Resolve-Path $SCRIPT_INVENTORY_CSV)"
Write-Host "Final report: $(Resolve-Path $FINAL_REPORT)"