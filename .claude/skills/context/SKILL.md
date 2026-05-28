---
name: context
description: Load Ansible project development guidelines, testing conventions, PR review processes, and code structure reference into context
user-invocable: true
---

# System Instructions

When this skill is invoked, read the AGENTS.md file from the repository root (`@../../../AGENTS.md`) and load its content into context. This provides comprehensive Ansible development guidelines.

After loading AGENTS.md, provide the user with confirmation that the context has been loaded and is available for answering questions or guiding development work.

If AGENTS.md cannot be found, inform the user and suggest they may be in a directory without the full ansible-core repository.

# Usage

Invoke this skill to load Ansible development context:

```
/context
```

The skill provides all guidelines and conventions that would normally be in AGENTS.md, making them available even when working outside the ansible-core repository or in environments where AGENTS.md is not accessible.

## When to Use

- Working on Ansible-related code outside the main repository
- Skills that need Ansible context but run in plugin marketplace
- Quick reference for Ansible testing/PR conventions
- Ensuring consistent approach to Ansible development

## What This Skill Does

This skill is informational only - it loads comprehensive Ansible development knowledge into context but performs no actions. After invocation, all subsequent responses will have access to:

- Testing commands
- PR review processes and checklists
- Licensing requirements
- Code style conventions
- Repository structure
- CI workflows

All this knowledge becomes available for answering questions or guiding development work.
