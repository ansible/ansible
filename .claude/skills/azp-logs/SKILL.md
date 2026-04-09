---
description: Download Azure Pipelines CI logs for analysis
argument-hint: <pr_number|build_id|build_url>
allowed-tools: [Bash(gh pr view:*), Bash(gh pr checks:*), Bash(ls:*), Read, Grep]
---

Azure Pipelines Logs Downloader
================================

Download Azure Pipelines CI logs for analyzing test failures and CI issues.

**IMPORTANT**: Always ask the user before downloading logs. The download may take 5-10 minutes (or longer for large CI runs)
depending on the number of jobs and log size.

Usage
-----

```bash
/azp-logs <pr_number|build_id|build_url>
```

Arguments
---------

- `pr_number`: GitHub PR number (will extract build ID from latest CI run)
- `build_id`: Azure Pipelines build ID (numeric)
- `build_url`: Full Azure Pipelines URL (e.g., <https://dev.azure.com/ansible/ansible/_build/results?buildId=12345>)

Implementation
--------------

This command uses the existing `hacking/azp/download.py` script to download CI logs.

**Before running**: Always confirm with the user before downloading logs. Inform them that:
- The download may take 5-10 minutes for a full CI run (potentially longer for very large runs)
- Logs will be saved to a directory named after the build ID
- The download size can be 10-50MB depending on the number of jobs

Process Steps
-------------

1. **Ask user for confirmation**: Explain what will be downloaded and estimated time

2. **Determine build ID**:
   - If given a PR number: Use `gh pr checks <number>` to get the Azure Pipelines URL
   - If given a URL: Pass it directly to download.py (it extracts buildId automatically)
   - If given a build ID: Use directly

3. **Download logs**: Run `hacking/azp/download.py` with appropriate flags:

   ```bash
   ./hacking/azp/download.py <build_id_or_url> --console-logs -v
   ```

4. **Analyze logs**: After download completes, examine logs in `<build_id>/` directory:
   - Grep for common failure patterns: `FAILED`, `ERROR`, `Traceback`
   - Focus on logs from failed jobs (check job names)
   - Compare with ansibot comments for context

Download Script Options
-----------------------

The `hacking/azp/download.py` script supports:
- `--console-logs`: Download console logs (recommended for CI failure analysis)
- `--artifacts`: Download test artifacts
- `--run-metadata`: Download run metadata JSON
- `--all`: Download everything
- `--match-job-name <regex>`: Filter to specific jobs
- `--match-artifact-name <regex>`: Filter to specific artifacts
- `-v, --verbose`: Show what is being downloaded
- `-t, --test`: Dry run (show what would be downloaded)

For most CI failure analysis, use `--console-logs` to get the log files.

Common Analysis Patterns
------------------------

After downloading logs to `<build_id>/` directory:

```bash
# Find all errors and failures
grep -r "FAILED\|ERROR\|Traceback" <build_id>/

# Find specific test failures
grep -r "FAILED test" <build_id>/

# Find sanity test failures
grep -r "The test" <build_id>/ | grep -i "failed"

# List all downloaded log files
ls -lh <build_id>/
```

Notes
-----

- Logs are downloaded to a directory named after the build ID
- Console logs are named after the job hierarchy (e.g., "Job Name Stage Name.log")
- The Ansible project is public, so no authentication is required
