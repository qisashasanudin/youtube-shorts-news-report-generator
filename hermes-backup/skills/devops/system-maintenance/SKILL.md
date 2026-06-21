---
name: system-maintenance
description: System maintenance and periodic backup routines for Hermes environment assets.
icon: 🛠️
status: stable
last_update: 2026-06-21
---

# System Maintenance Skills

This skill handles automated background tasks for the Hermes environment, specifically focused on maintaining data integrity and system clean-up.

## Operations

### `backup_memory`
Syncs all saved user preferences and gathered facts from `.hermes/memories` to the project repository for persistent storage. This is a critical operation to ensure session context persists across hardware migrations or repository restorations.

**Manual Execution:**
Run the script in `/Users/qisashasanudin/.hermes/scripts/backup_memory.py`.

**Automation Logic:**
- **Frequency:** Hourly (0 * * * *).
- **Execution Mode:** `no_agent=True` (Zero tokens, direct script execution).
- **Format:** Multi-file sync of `.json`, `.md`, and `.txt` files from the memory root to the repository's designated backup path.

## Workflow Details
1.  **Source Path:** `/Users/qisashasanudin/.hermes/memories`
2.  **Target Path:** `/Users/qisashasanudin/repositories/youtube-shorts-news-report-generator/hermes-backup/memories`
3.  **Execution Method:** Use the `cronjob` tool with a self-contained prompt and the script path specified in the instructions.

## Pitfalls & Constraints
- **No ML Interaction:** Because this uses `no_agent=True`, do **not** allow this job to call any tools other than `terminal`. 
- **Error Handling:** If the source directory is missing, log a warning but do not fail the cron run.
- **Side Effects:** This task modifies files in the repository; ensure it only interacts with the `/hermes-backup` path to avoid disrupting active project code.

## Verification
Verify successful completion by checking:
`ls -R /Users/qisashasanudin/repositories/youtube-shorts-news-report-generator/hermes-backup/memories`
