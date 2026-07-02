# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) and other compatible agentic tools when working with code in this repository.

**Note:** This file is for AI assistant use only. For human developers, see the [Ansible Developer Guide](https://docs.ansible.com/ansible-core/devel/dev_guide/index.html).

## ⚠️ IMPORTANT: Always Start Here

**BEFORE starting any PR review or development task:**

1. **Read this file first** - Don't work from memory or assumptions
2. **Read all [context](context) files** for the project's coding conventions and policies
3. **Use TodoWrite** to create a task list and track progress systematically
4. **Follow the numbered steps** in the relevant process sections
5. **Reference Quick Reference** for correct commands and patterns

## ⚠️ CRITICAL: Licensing Requirements

**NEVER suggest, recommend, or approve code that violates the project's [licensing requirements](context/licensing.md).**
Always verify any new dependencies or suggested libraries are license-compatible.
This is non-negotiable -- licensing violations can create serious legal issues for the project.

## General Principles

When reviewing code, don't flag issues that `ansible-test sanity` already catches.
Focus review effort on things automated checks can't verify.

## Attribution

Agents should disclose their involvement in contributions.
We recommend using an `Assisted-by:` commit trailer identifying the AI tool that assisted.

## Quick Reference

```bash
# PR Review and CI
gh pr view <number>                                       # Get PR details
gh pr view <number> --comments                            # Check for ansibot CI failures
gh pr checks <number>                                     # Get Azure Pipelines URLs
gh pr checkout <number>                                   # Switch to PR branch
gh pr diff <number>                                       # See all changes
/azp-logs <number>                                        # Download CI logs for PR
```

**Critical Reminders:**

- **Licensing**: See [Licensing Requirements](context/licensing.md) - GPLv3/BSD-2-Clause only
- **Testing**: See [running-tests](context/running-tests.md) for `ansible-test` commands and container selection

## Helping Developers with CI Failures

When developers submit PRs and encounter CI failures, use these approaches to help diagnose and resolve issues:

**1. Check for ansibot comments:**

```bash
# Get all PR comments to find ansibot CI failure reports
gh pr view <number> --comments
```

Look for comments from `ansibot` that contain:
- Test failure details with specific error messages
- File paths and line numbers for failures
- Links to sanity test documentation (e.g., `[explain](https://docs.ansible.com/...`)

**2. Get CI check status and URLs:**

```bash
# See all CI check results with Azure Pipelines URLs
gh pr checks <number>
```

This shows:
- Overall CI status (pass/fail) with timing
- Direct links to Azure DevOps build results
- Individual job results (Sanity Test 1/2, Docker tests, Units, etc.)

**3. CI failure analysis workflow:**

1. Check ansibot comments first for immediate error details
2. Use `gh pr checks <number>` to get Azure Pipelines URLs for detailed logs
3. Focus on failed jobs (marked as `fail`) and examine their specific error output
4. For sanity test failures, the error messages usually indicate exactly what needs to be fixed
5. For test failures, run the same tests locally using `ansible-test` to reproduce and debug

**4. Downloading Azure Pipelines logs for analysis:**

When CI failures need deeper investigation beyond what's visible in ansibot comments or the web UI, use the `/azp-logs` skill:

```bash
# Download logs using PR number (automatically finds latest build)
/azp-logs <pr_number>

# Or use build ID directly from gh pr checks output
/azp-logs <build_id>

# Or use the full Azure Pipelines URL
/azp-logs https://dev.azure.com/ansible/ansible/_build/results?buildId=12345
```

The skill uses `hacking/azp/download.py` to download console logs into a directory named after the build ID.

**After downloading, analyze the logs:**
- Grep for common failure patterns: `grep -r "FAILED\|ERROR\|Traceback" <build_id>/`
- Focus on logs from failed jobs identified in `gh pr checks` output
- Compare error messages with ansibot comments to get full context
- Sanity test failures usually have clear error messages with file:line references
- Integration/unit test failures may require examining full test output and tracebacks

**Advanced usage:**
The download script supports filtering and customization:

```bash
# Download only logs matching specific job names
./hacking/azp/download.py <build_id> --console-logs --match-job-name "Sanity.*"

# Download artifacts and metadata too
./hacking/azp/download.py <build_id> --all
```

See `.claude/skills/azp-logs/SKILL.md` for complete documentation.

## PR Review Guidelines

### PR Review Checklist

Use this checklist for EVERY PR review:

```text
□ Created TodoWrite list for review steps
□ Step 1: Get PR details with gh pr view <number>
□ Step 2: Get PR diff with gh pr diff <number>
□ Step 3: Check required components (changelog, tests)
□ Step 4: Checkout PR branch with gh pr checkout <number>
□ Step 5: Review existing feedback with gh pr view <number> --comments
□ Step 6: Verify all issues addressed
□ Step 7: Call out any unresolved feedback
□ Mark each TodoWrite item as completed when done
```

When assisting with PR reviews, verify:

- Changelog fragment exists (see [changelog requirements](context/documentation-standards.md#changelog-requirements))
- Appropriate tests are included (see [test expectations](context/writing-tests.md#test-expectations-for-pull-requests))

### Review Process

Follow these steps in order for thorough PR reviews:

1. **Get PR details**: Use `gh pr view <number>` to understand the PR scope and description
2. **Get PR diff**: Use `gh pr diff <number>` to see all changes
3. **Check required components FIRST** (changelog and tests -- see links above)
4. **Checkout PR branch**: Use `gh pr checkout <number>` to examine code holistically with changes applied
5. **Review existing feedback**: Use `gh pr view <number> --comments` to see all comments and previous review feedback
6. **Verify all issues addressed**: Ensure all bot failures, reviewer requests, and discussion points are resolved
7. **Call out any unresolved review feedback**: Explicitly mention any discussions or requests that remain unaddressed

### Review Task Management

- Use TodoWrite tool to track review steps for complex PRs
- Mark tasks as in_progress when actively working on them
- Complete tasks immediately after finishing each step
- This provides visibility to users about review progress

### Review Tools

- `gh pr view <number>` - Get PR details and description
- `gh pr view <number> --comments` - See all comments and review feedback
- `gh pr diff <number>` - Get complete diff of changes
- `gh pr checkout <number>` - Switch to PR branch for holistic examination
- `Read` tool - Examine specific changed files in detail
- `Grep` tool - Search for related code patterns or test coverage (uses ripgrep/rg)
