---
description: Review an Ansible PR following the project's standardized process from CLAUDE.md
argument-hint: <pr_number>
allowed-tools: [TodoWrite, Bash(gh pr view:*), Bash(gh pr diff:*), Bash(gh pr checkout:*), Bash(gh pr checks:*), Read, Grep, Glob, Search]
---

PR Review Command
=================

Review an Ansible PR following the project's standardized process from `CLAUDE.md`.

Usage
-----

```bash
/review <pr_number>
```

Arguments
---------

- `pr_number` (required): The GitHub PR number to review

Implementation
--------------

This command implements the PR Review Guidelines documented in the `PR Review Guidelines` section of CLAUDE.md.

Review Process Steps
--------------------

The command follows these numbered steps from CLAUDE.md:

1. **Create TodoWrite list** for systematic review tracking
2. **Get PR details**: `gh pr view <number>` to understand scope, motivation and the desired outcome
3. **Get PR diff**: `gh pr diff <number>` to see all changes
4. **Check required components FIRST**:
   - Verify changelog fragment exists in `changelogs/fragments/`
   - Verify changelog uses correct section (check `changelogs/config.yaml`)
   - Verify tests exist and specifically cover the changed code paths
   - Unit tests should be pytest style, and functional rather than tightly coupled to mocking
   - Integration tests required for almost all plugin changes
5. **Checkout PR branch**: `gh pr checkout <number>` to examine code holistically
6. **Review existing feedback**: `gh pr view <number> --comments` for all comments and previous reviews
7. **Verify all issues addressed**: Ensure bot failures, reviewer requests, and discussion points are resolved
8. **Call out unresolved feedback**: Explicitly mention any discussions/requests that remain unaddressed

Critical Review Elements
------------------------

- **Licensing**: Verify GPLv3/BSD-2-Clause compatibility for any new dependencies
- **Test scope**: Tests must exercise actual changed code, not just add random coverage
- **Changelog validation**: Fragment structure follows sections defined in `changelogs/config.yaml`

Each step is tracked in TodoWrite for visibility and systematic completion. A review round should not exceed 20 feedback items.
