# Development environment setup

ansible-core and all CLIs (including ansible-test) require a POSIX OS.
On Windows, use WSL (Windows Subsystem for Linux).

## Editable install

Ansible development typically uses an editable installation after forking and cloning:

```bash
pip install -e .
```

## Hacking script

An alternative to an editable installation is to source the `hacking/env-setup` script:

```bash
source hacking/env-setup
```

## Running tests without installation

If you only need to run tests, you can invoke `ansible-test` directly without installing or sourcing the hacking script:

```bash
bin/ansible-test sanity -v --docker default
```
