# Public surface area

Starting with ansible-core 2.19 we're trying to be more intentional about what features are part of our public API
and other public surface areas (e.g. CLI, configuration options, module arguments, ansible-core provided Jinja globals, etc.).

## Imports in public Python modules

To make public Python modules more self-documenting:

- Imports in any file considered public API must be sunder-prefixed (e.g. `_module_name`),
to avoid confusion about imported objects being part of the public module API.
- Prefer module-level imports (e.g. `from ansible._internal import _amodule`) with dotted usage (e.g. `foo: _amodule.thing`).
This solves many circular import issues and reduces the need for sunder-prefix aliasing on internal imports in public API.
Hot code paths can use locals or aliased objects, but sparingly and only where it really matters.

## Internal by default

New feature implementations in Python code should always be:

- Added to a module beneath the `ansible._internal` or `ansible.module_utils._internal` package.
- In a sunder-prefixed module (easier public module imports without aliasing).

Only public types and functions should be added to new modules outside `_internal` packages.
Small sunder-prefixed utility types and functions are okay in public modules,
but in general, non-public API surface area for most new implementations should live completely under an `_internal` package.

Internal-only types/functions/methods beneath an `_internal` package do not generally require sunder-prefixing on their names.
