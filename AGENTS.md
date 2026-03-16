# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) and other compatible agentic tools when working with code in this repository.

**Note:** This file is for AI assistant use only. For human developers, see the [Ansible Developer Guide](https://docs.ansible.com/ansible-core/devel/dev_guide/index.html).

## ⚠️ IMPORTANT: Always Start Here

**BEFORE starting any PR review or development task:**

1. **Read this file first** - Don't work from memory or assumptions
2. **Use TodoWrite** to create a task list and track progress systematically
3. **Follow the numbered steps** in the relevant process sections
4. **Reference Quick Reference** for correct commands and patterns

## ⚠️ CRITICAL: Licensing Requirements

**NEVER suggest, recommend, or approve code that violates these requirements:**

- **ansible-core**: All code must be **GPLv3 compatible**
- **lib/ansible/module_utils/**: Defaults to **BSD-2-Clause** (more permissive)
- **External dependencies**: Only recommend libraries compatible with these licenses
- **PR reviews**: Always verify any new dependencies or suggested libraries are license-compatible
- **When in doubt**: Ask about licensing compatibility rather than assuming

**This is non-negotiable** - licensing violations can create serious legal issues for the project.

## Quick Reference

Most commonly used commands and patterns:

```bash
# Testing
ansible-test sanity -v --docker default                   # Run all sanity tests
ansible-test sanity -v --docker default --test <test>     # Run specific sanity test
ansible-test units -v --docker default                    # Run unit tests
ansible-test integration -v --docker ubuntu2404           # Run integration tests

# PR Review and CI
gh pr view <number>                                       # Get PR details
gh pr view <number> --comments                            # Check for ansibot CI failures
gh pr checks <number>                                     # Get Azure Pipelines URLs
gh pr checkout <number>                                   # Switch to PR branch
gh pr diff <number>                                       # See all changes
```

**Container Selection:**

- Sanity/Unit tests: `--docker default`
- Integration tests: `--docker ubuntu2204`, `--docker ubuntu2404`, etc. (NOT default/base)

**Critical Reminders:**

- **Licensing**: See [Licensing Requirements](#️-critical-licensing-requirements) - GPLv3/BSD-2-Clause only

## Development Environment Setup

Ansible development typically uses an editable install after forking and cloning:

```bash
# After forking and cloning the repository
pip install -e .
```

**Note:** ansible-core and all CLIs (including ansible-test) require a POSIX OS. On Windows, use WSL (Windows Subsystem for Linux).

## Testing and CI

### Basic Testing Commands

```bash
# Run sanity tests - these are linting/static analysis (pylint, mypy, pep8, etc.)
ansible-test sanity -v --docker default

# List available sanity tests
ansible-test sanity --list-tests

# Run specific sanity tests
ansible-test sanity -v --docker default --test pep8 --test pylint

# Run sanity on specific files (paths relative to repo root)
ansible-test sanity -v --docker default lib/ansible/modules/command.py

# Run unit tests (recommended with Docker)
ansible-test units -v --docker default

# Run specific unit test (paths relative to repo root, targets in test/units/)
ansible-test units -v --docker default test/units/modules/test_command.py

# Run integration tests (choose appropriate container - NOT base/default)
ansible-test integration -v --docker ubuntu2404

# Run specific integration target (directory name in test/integration/targets/)
ansible-test integration -v --docker ubuntu2404 setup_remote_tmp_dir

# Run with coverage
ansible-test units -v --docker default --coverage

# Alternative: use --venv if Docker/Podman unavailable (less reliable for units/integration)
ansible-test sanity -v --venv
```

Available Docker containers for testing can be found in `./test/lib/ansible_test/_data/completion/docker.txt`.
The `base` and `default` containers are for sanity/unit tests only. For integration tests, use distro-specific
containers, depending on the modules being tested.

**Test isolation options:**

- `--docker` (supports Docker or Podman) - preferred for reliable, isolated testing
- `--venv` - fallback when containers unavailable, but unit tests may be unreliable due to host environment differences

### Helping Developers with CI Failures

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

**3. Common CI failure patterns:**

- **Sanity failures**: Usually have specific fixes (trailing whitespace, import errors, etc.)
- **Integration test failures**: May require platform-specific containers or test adjustments
- **Unit test failures**: Often indicate actual code issues that need debugging

**4. CI failure analysis workflow:**

1. Check ansibot comments first for immediate error details
2. Use `gh pr checks <number>` to get Azure Pipelines URLs for detailed logs
3. Focus on failed jobs (marked as `fail`) and examine their specific error output
4. For sanity test failures, the error messages usually indicate exactly what needs to be fixed
5. For test failures, run the same tests locally using `ansible-test` to reproduce and debug

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

### Required Components

- Changelog fragment exists in `changelogs/fragments/`
- Appropriate tests are included and cover the changed code
  - Unit tests should be pytest style, and functional rather than tightly coupled to mocking
  - Integration tests required for almost all plugin changes (tests the public API)
  - Tests should exercise the actual changed code, not just add random coverage

### Review Process

Follow these steps in order for thorough PR reviews:

1. **Get PR details**: Use `gh pr view <number>` to understand the PR scope and description
2. **Get PR diff**: Use `gh pr diff <number>` to see all changes
3. **Check required components FIRST**:
   - Verify changelog fragment exists and uses correct section (check `changelogs/config.yaml` for valid sections)
   - Verify tests exist and specifically cover the changed code paths
4. **Checkout PR branch**: Use `gh pr checkout <number>` to examine code holistically with changes applied
5. **Review existing feedback**: Use `gh pr view <number> --comments` to see all comments and previous review feedback
6. **Verify all issues addressed**: Ensure all bot failures, reviewer requests, and discussion points are resolved
7. **Call out any unresolved review feedback**: Explicitly mention any discussions or requests that remain unaddressed

### Common Review Issues to Check

- **Changelog section errors**: Verify changelog uses valid section from `changelogs/config.yaml`. Fragment structure follows sections defined there.
- **Test scope**: Ensure tests exercise the actual changed code, not just add random coverage.
  Integration tests required for almost all plugin changes (tests the public API).
  Tests should be functional rather than tightly coupled to mocking.

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

## Development Guidelines

### Code Style Notes

- Line limit is 160 characters (not 80)
- E402 (module level import not at top) is ignored
- In `lib/ansible/modules/`, imports must come after DOCUMENTATION, EXAMPLES, and RETURN definitions
- Don't add obvious comments about code
- Use native type hints with `from __future__ import annotations` (converts to strings at runtime)
- Don't document module parameters in docstrings - migrate to type hints instead
- **No trailing whitespace**: Always clean up trailing spaces on lines, especially when editing existing files

### Python Version Support

- Controller code: support range defined in `pyproject.toml`
- Modules/module_utils: minimum version in `lib/ansible/module_utils/basic.py` (`_PY_MIN`) up to max from `pyproject.toml`
- Modules support a wider Python version range than controller code

### Dependencies and Imports

- Prefer Python stdlib over external dependencies
- Use existing code from within the Ansible project
- `lib/ansible/modules/` can only import from `lib/ansible/module_utils/` (modules are packaged for remote execution)
- `lib/ansible/module_utils/` cannot import from outside itself

## Documentation Standards

### Module and Plugin Documentation

- Modules and plugins require DOCUMENTATION, EXAMPLES, and RETURN blocks as static YAML string variables
- These blocks cannot be dynamically generated - they are parsed via AST/token parsing
- Alternative: "sidecar" documentation as `.yml` files with same stem name adjacent to plugin files
- All modules should have a `main()` function and `if __name__ == '__main__':` block
- Use `version_added` fields in documentation following existing version format patterns

### Changelog Requirements

- Changes require entries in `changelogs/fragments/` as YAML files
- Create a new fragment file per PR (never reuse existing fragments to avoid merge conflicts)
- Fragment structure follows sections defined in `changelogs/config.yaml` under the `sections` key
- Naming: `{issue_number}-{short-description}.yml` or `{component}-{description}.yml` if no issue
- Format: `- {component} - {description} ({optional URL to GH issue})`
- Content supports Sphinx markup (use double backticks for code references)

## Repository Management

### Plugin Development

- New plugins should go into collections, not ansible-core
- ansible-core rarely accepts new plugins; core team makes these decisions

### Branch and Release Management

- All PRs target the `devel` branch
- Use GitHub templates when creating issues/PRs (`.github/ISSUE_TEMPLATE/` and `.github/PULL_REQUEST_TEMPLATE/`)
- For issues: fill out the `component` field with project root relative file path
- For PRs: adjust the issue type in the template as listed in `.github/PULL_REQUEST_TEMPLATE/PULL_REQUEST_TEMPLATE.md`
- Validate issues are fixed in `devel` before reporting against stable releases
- Bug fixes: backported to latest stable only
- Critical bug fixes: backported to latest and previous stable
- Security issues: contact security@ansible.com privately, not via GitHub

### Backwards Compatibility

- Backwards compatibility is prioritized over most other concerns
- Deprecation cycle: 4 releases (deprecation + 2 releases + removal)
- Use `Display.deprecated` or `AnsibleModule.deprecate` with version from `lib/ansible/release.py` plus 3
- Example: deprecating in 2.19 means removal in 2.22

## Code Structure Reference

### Core Structure

- `lib/ansible/` - Main Ansible library code
  - `cli/` - Command-line interface implementations (ansible, ansible-playbook, etc.)
  - `executor/` - Task execution engine and strategies (includes PowerShell support in `powershell/`)
  - `inventory/` - Inventory management and parsing
  - `modules/` - Core modules (built-in automation modules)
  - `module_utils/` - Shared utilities for modules (includes C# in `csharp/` and PowerShell in `powershell/`)
  - `plugins/` - Plugin framework (filters, tests, lookups, etc.)
  - `vars/` - Variable management
  - `config/` - Configuration handling
  - `collections/` - Ansible Collections framework

### Key Components

- **CLI Layer**: Entry points in `lib/ansible/cli/` handle command parsing and dispatch
- **Executor**: `lib/ansible/executor/` contains the core execution engine that runs tasks and plays
- **Module System**: Modules in `lib/ansible/modules/` are the units of work; they're executed remotely
- **Plugin Architecture**: `lib/ansible/plugins/` provides extensibility through filters, tests, lookups, etc.
- **Inventory**: `lib/ansible/inventory/` manages host and group definitions
- **Collections**: Modern packaging format for distributing Ansible content

### Testing Infrastructure

- `test/units/` - Unit tests mirroring the lib structure
- `test/integration/` - Integration tests organized by target (named after plugin/functionality being tested)
  - Some targets have `context/controller` or `context/target` in their `aliases` file when not easily inferable
  - Only modules run on target hosts; all other plugins execute locally in the ansible process
- `test/lib/` - Test utilities and frameworks
- `ansible-test` - Unified testing tool for all test types

For CI failure debugging, see [Helping Developers with CI Failures](#helping-developers-with-ci-failures).
