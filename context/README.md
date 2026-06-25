# Context for Humans and Agents

This directory contains information about developing ansible-core.
It should be equally applicable to both humans and agents.

This is **not** the place for:

- **Documentation on how to use Ansible** -- see the [ansible-documentation](https://github.com/ansible/ansible-documentation/) repository.
- **Learning how to develop content for Ansible** (modules, plugins, collections, roles, etc.) -- see the [Ansible Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/index.html).
- **Agent-specific instructions or guidance** -- see [AGENTS.md](../AGENTS.md).

## Table of Contents

- [contributing](contributing.md) - Contributing changes to ansible-core.
- [licensing](licensing.md) - Licensing requirements.
- [dev-environment](dev-environment.md) - Development environment setup.
- [code-structure](code-structure.md) - Directory layout, key components, import restrictions, and plugin policy.
- [coding-style](coding-style.md) - Python versions, dependencies, code formatting, and syntax conventions.
- [error-handling](error-handling.md) - Error and exception handling patterns.
- [data-tagging](data-tagging.md) - Working with data tags.
- [public-api](public-api.md) - Public surface area and internal-by-default conventions.
- [documentation-standards](documentation-standards.md) - Module/plugin documentation and changelog requirements.
- [running-tests](running-tests.md) - Running tests with ansible-test.
- [writing-tests](writing-tests.md) - Test expectations for pull requests.
- [deprecation](deprecation.md) - Backward compatibility and deprecation.
- [ci](ci.md) - Continuous integration.
