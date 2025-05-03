# Cleanup Notification Email Template

## Subject
```
ACTION REQUIRED: Upcoming Removal of Deprecated Branches and Scripts in Social Cube
```

## Body
```
Dear Team,

We're planning to remove several deprecated branches and legacy scripts from our codebase to improve maintainability and reduce clutter.

## WHAT'S BEING REMOVED

### Branches:
- Branch: task/discord-bot-management-ui__1 (fully merged into main)
  Reason: Duplicate branch with the same changes as task/discord-bot-management-ui_2025-04-25_1

### Scripts:
- No scripts identified for removal at this time

## TIMELINE

- Week 1 (May 3-9): Items marked for deletion with notices (COMPLETED)
- Week 2 (May 10-16): Scripts moved to deprecated folder (if applicable) (IN PROGRESS)
- Week 3 (May 17-23): Complete removal after approval

## ACTIONS REQUIRED

1. Review the full inventory and verification reports:
   - Branch and Script Inventory: [docs/branch_script_inventory.md]
   - Verification Report: [docs/verification_report.md]
   - Removal Plan: [docs/removal_plan.md]

2. Attend the review meeting on [DATE] at [TIME]

3. Raise any concerns by replying to this email before May 16, 2025

## BACKUP INFORMATION

All items scheduled for removal have been backed up and can be restored if needed. The backup location is documented in the verification report.

## NEW GUIDELINES

As part of this cleanup effort, we have established new guidelines for branch management and script lifecycle. Please review:
- Code Maintenance Guidelines: [docs/code_maintenance_guidelines.md]

This documentation outlines our new branch naming conventions, regular cleanup schedule, and script documentation requirements.

Thank you for your cooperation in keeping our codebase clean and maintainable.

Best regards,
[Your Name]
```

## Usage Instructions

1. Replace `[DATE]` and `[TIME]` with the actual review meeting details
2. Replace `[Your Name]` with your name
3. For internal documentation links, you may need to replace them with actual URLs if sending via email
4. Consider sending the email from a team or project account rather than personal email
5. Keep a copy of the sent email for documentation purposes