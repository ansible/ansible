# Backward compatibility and deprecation

Backward compatibility is prioritized over most other concerns.

## Deprecation cycle

- Deprecation cycle: 4 releases (deprecation + 2 releases + removal).
- Removal version: current version in `lib/ansible/release.py` plus 3.
- Example: deprecating in 2.19 means removal in 2.22.

## Deprecating code

Use `Display.deprecated` or `AnsibleModule.deprecate` with the removal version.
