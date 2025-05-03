# Asset Removal Documentation

This document lists all assets marked for removal due to being unused or duplicated.

## CSS Files

| File Path | Size | Reason for Removal | Backup Location |
|-----------|------|-------------------|-----------------|
| static/css/m3.css | 9.7KB | No references found in templates or JS | backup/static/css/m3.css |
| staticfiles/css/m3.css | 9.7KB | Compiled version of unused m3.css | Not backed up (compiled) |

## JavaScript Files

| File Path | Size | Reason for Removal | Backup Location |
|-----------|------|-------------------|-----------------|
| static/js/bot_management.js | 5.9KB | No references found, possible confusion with 'bot-management.js' | backup/static/js/bot_management.js |
| dashboard/static/js/fallback-poller.js | 6.0KB | No references in any templates or JS imports | backup/dashboard/static/js/fallback-poller.js |
| dashboard/static/js/websocket-manager.js | 5.6KB | No references in any templates or JS imports | backup/dashboard/static/js/websocket-manager.js |

## Image Files

| File Path | Size | Reason for Removal | Backup Location |
|-----------|------|-------------------|-----------------|
| static/img/default-avatar.svg | 316B | No references, PNG version used instead | backup/static/img/default-avatar.svg |
| dashboard/static/img/default-avatar.png | 1.7KB | Duplicate of static/img/default-avatar.png | backup/dashboard/static/img/default-avatar.png |

## Cleanup Plan

1. Back up each file to the corresponding backup directory
2. Remove the files from their original locations
3. Run tests to ensure no regressions
4. Monitor for any 404 errors after deployment

## Estimated Size Savings

- Total uncompressed: ~30KB
- Compressed estimate: ~8KB
- Additional savings from consolidated frameworks will be assessed in later tasks
