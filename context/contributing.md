# Contributing

## Keep changes focused

Changes should be limited to what's necessary to solve the problem at hand.
Avoid unrelated reformatting, refactoring, or style adjustments in the same change.

Unfocused changes make review harder by increasing the diff size and obscuring the important parts.
They can also lead to unnecessary back-and-forth around style and preferences.

## Branch and release management

- All PRs target the `devel` branch.
- Use GitHub templates when creating issues/PRs (`.github/ISSUE_TEMPLATE/` and `.github/PULL_REQUEST_TEMPLATE/`).
- For issues: fill out the `component` field with project root relative file path.
- For PRs: adjust the issue type in the template as listed in `.github/PULL_REQUEST_TEMPLATE/PULL_REQUEST_TEMPLATE.md`.
- Validate issues are fixed in `devel` before reporting against stable releases.
- Bug fixes: backported to latest stable only.
- Critical bug fixes: backported to latest and previous stable.
- Security issues: contact security@ansible.com privately, not via GitHub.
