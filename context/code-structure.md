# Core structure

- `lib/ansible/` - Main Ansible library code.
  - `cli/` - Command-line interface implementations (ansible, ansible-playbook, etc.).
  - `executor/` - Task execution engine and strategies (includes PowerShell support in `powershell/`).
  - `inventory/` - Inventory management and parsing.
  - `modules/` - Core modules (built-in automation modules).
  - `module_utils/` - Shared utilities for modules (includes C# in `csharp/` and PowerShell in `powershell/`).
  - `plugins/` - Plugin framework (filters, tests, lookups, etc.).
  - `vars/` - Variable management.
  - `config/` - Configuration handling.
  - `collections/` - Ansible Collections framework.

## Key components

- **CLI Layer**: Entry points in `lib/ansible/cli/` handle command parsing and dispatch.
- **Executor**: `lib/ansible/executor/` contains the core execution engine that runs tasks and plays.
- **Module System**: Modules in `lib/ansible/modules/` are the units of work; they're executed remotely.
- **Plugin Architecture**: `lib/ansible/plugins/` provides extensibility through filters, tests, lookups, etc.
- **Inventory**: `lib/ansible/inventory/` manages host and group definitions.
- **Collections**: Modern packaging format for distributing Ansible content.

## Plugin development

- New plugins should go into collections, not ansible-core.
- ansible-core rarely accepts new plugins; core team makes these decisions.

## Import restrictions

- `lib/ansible/modules/` can only import from `lib/ansible/module_utils/` (modules are packaged for remote execution).
- `lib/ansible/module_utils/` cannot import from outside itself.

## Resource embedding

Modules that need to execute code on Python versions outside the normal module_utils range
can use `EmbedManager.embed()` from `ansible.module_utils.embed` to bundle standalone scripts into the AnsiballZ payload.
Embedded resources go in `lib/ansible/module_utils/_embed/`.

## Testing infrastructure

- `test/units/` - Unit tests mirroring the lib structure.
- `test/integration/` - Integration tests organized by target (named after plugin/functionality being tested).
  - Some targets have `context/controller` or `context/target` in their `aliases` file when not easily inferable.
  - Only modules run on target hosts; all other plugins execute locally in the ansible process.
- `test/lib/` - Test utilities and frameworks.
- `ansible-test` - Unified testing tool for all test types.
