# Running tests

All testing uses `ansible-test`, which supports sanity tests (linting/static analysis), unit tests, and integration tests.

## Sanity tests

Sanity tests don't require `--docker`.
Some tests may be skipped if their dependencies aren't installed locally (e.g. additional Python versions, shellcheck, PowerShell),
but this rarely matters when testing your own changes.

Run sanity tests against all files in your change set, not just the ones you're actively editing.

```bash
# Run all sanity tests
ansible-test sanity -v

# List available sanity tests
ansible-test sanity --list-tests

# Run specific sanity tests
ansible-test sanity -v --test pep8 --test pylint

# Run sanity on specific files (paths relative to repo root)
ansible-test sanity -v lib/ansible/modules/command.py

# Run all sanity tests in a container (for full coverage)
ansible-test sanity -v --docker
```

> [!NOTE]
> `--docker` without an argument defaults to the `default` container.
> Avoid placing a non-container argument immediately after `--docker`, as it will be interpreted as an image name.

## Unit tests

```bash
# Run all unit tests
ansible-test units -v --docker

# Run a specific unit test (paths relative to repo root, targets in test/units/)
ansible-test units -v --docker test/units/modules/test_command.py

# Run with coverage
ansible-test units -v --docker --coverage
```

## Integration tests

```bash
# Run all integration tests
ansible-test integration -v --docker ubuntu

# Run a specific integration target (directory name in test/integration/targets/)
ansible-test integration -v --docker ubuntu ping
```

## Container selection

- Sanity/Unit tests: `--docker` (defaults to the `default` container).
- Integration tests: `--docker ubuntu`, `--docker fedora`, etc. (NOT default/base).

The `base` and `default` containers are for sanity/unit tests only.
For integration tests, use distro-specific containers, depending on the modules being tested.

Available containers and their supported Python versions are listed in the `--help` output for each test command.

## Test isolation options

- `--docker` (supports Docker or Podman) -- preferred for reliable, isolated testing.
- `--venv` -- fallback when containers are unavailable, but unit tests may be unreliable due to host environment differences.
