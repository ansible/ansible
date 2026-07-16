# Coding style and syntax

For new code and updates to existing code, including unit tests.

In general, prefer newer Python features as they become available.
A feature is available when the minimum supported Python version for the code being written supports it,
and it doesn't conflict with other supported versions.

## Python version support

- Controller code: minimum version defined in `pyproject.toml` (`requires-python`).
- Modules/module_utils: minimum version in `lib/ansible/module_utils/basic.py` (`_PY_MIN`).
- Modules support a wider Python version range than controller code.
- Supported Python versions for testing are defined within `ansible-test`.

## Dependencies

- Prefer Python stdlib over external dependencies.
- Use existing code from within the Ansible project.

## Markdown

Markdown files use [GitHub Flavored Markdown](https://github.github.com/gfm/) (verified by the "pymarkdown" sanity test).

Use dashes (`-`) for unordered list items, not asterisks.
End list items with periods.

## ASCII characters

- Use ASCII quotes (`'` and `"`) instead of Unicode smart quotes (verified by the "no-smart-quotes" sanity test).
- Use ASCII dashes (`-` or `--`) instead of em dashes.

## Line length

The line limit is 160 characters.

## Trailing whitespace

Don't leave trailing whitespace on lines.

## Docstrings

Explain what the annotated code does, but don't create structured entries for parameters.
Don't document parameter types in docstrings -- use type hints instead.

Anything considered a public API must have a docstring.
Internal code should, and it often makes sense for unit tests, too.

## Line breaks in source text

Try to stick to one sentence per line in text like docstrings, comments and changelog fragments.

## Native type annotations

Use native type hints with `from __future__ import annotations` (verified by the "boilerplate" sanity test).
Include type annotations on function/method arguments and return types, unless the annotation becomes too complex (e.g. `TypedDict`).
The "mypy" sanity test only performs type checking on annotated functions/methods.

Prefer PEP 695 type parameter syntax over `TypeVar` and `ParamSpec` declarations.
For example, use `def foo[T](x: T) -> T` instead of declaring `T = TypeVar('T')` separately.
This does not apply to `module_utils/` code, which must support older Python versions that lack the feature.

## Format strings

Use f-strings instead of `%` strings or `str.format`, except for logging where formatting is deferred.

## Quoting strings

Use the `!r` format qualifier to quote a value instead of manually quoting.

Example: `f"A string with a {quoted!r} value."`

## Code formatting check/fix for internals

The `black` sanity test runs against all `_internal` packages, using default settings with an increased line length of 160 and no quote conversion.
Use `ansible-test` to automatically apply required formatting changes.

Example: `ansible-test sanity --test black --fix`

## Import ordering in modules

The E402 pycodestyle rule (module level import not at top) is ignored.
In `lib/ansible/modules/`, imports must come after the `DOCUMENTATION`, `EXAMPLES`, and `RETURN` definitions.
