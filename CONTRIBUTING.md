# CONTRIBUTION RULES

Note that while we plan to enforce these rules as they are added, a lot of code was produced before they existed and we don't normally reprocess all of it, but opportunistically update it to meet the rules as we update it for other reasons.

Exceptions can be made for `module_utils/` as that code targets older versions of Python than the rest of core and not all rules might not be 100% compatible.

Documentation from docs.ansible.com is mostly designed for collection or 3rd party plugin developers, this document covers core code (this repo) but it also includes guidance on plugin development. If you find any contradictions, keep in mind that most of this applies to core >= 2.19, so which documnent you favor depends on the versions you plan to support.

## PUBLIC API

Anything under `_internal` should not be used by plugins or 3rd party applications, it is subject to change w/o notice and only directly core in code may depend on it.


# Error handling

How to handle errors in Ansible.

## Tracebacks

Do not manually generate tracebacks for errors or warnings. Standardized traceback capture is included for errors, warnings and deprecation warnings for both controller and module code (Python). See the `DISPLAY_TRACEBACK` config option for details on how to enable traceback capture and display.

## In modules

In most cases, just raise an exception. The AnsiballZ wrapper now provides a general exception handler for Python modules, making use of the `AnsibleModule.fail_json` method unnecessary, unless the module result needs to be customized. Calls to the various Python-module-side `warn` and `deprecate` methods/functions will also capture and marshal tracebacks to the controller when enabled.

## Deferred exceptions in modules

When deferring exceptions in modules using `try/except` and `fail_json`, pass the captured `Exception` instance to `fail_json` using the `exception` argument. The error handling infrastructure will handle collection of error details and traceback formatting.

## Exception context

Raising exceptions while another exception is active will cause the active exception to become the `__context__` for the newly raised exception. This is usually not the intended behavior, and should be reserved for unexpected errors while handling the original exception. In most cases a `raise from` is desired, either with `None` to suppress the original exception if it's not helpful, or with the captured exception to set it as the `__cause__` for the newly raised exception.

In earlier versions of Ansible, this could be done by setting `orig_exc` on `AnsibleError`. However, this is no longer needed and a simple `raise from` should be used instead.

Suppression example: `raise Exception("something") from None`
Cause example: `raise Exception("something") from ex`

## Raising new exceptions

Don't catch exceptions just to re-raise them, unless there's additional information that can be added in the newly raised exception. In most cases, particularly for plugin/module failures, contextual information is automatically added, making granular `try/except/raise` within the plugin or module unnecessary.

## Error messages

Do not repeat previous exception messages when constructing new exceptions.

Anti-pattern: `raise Exception("it broke: {ex}") from ex`

The built in error chain handling mechanisms in Ansible will include the messages from cause/context exceptions automatically. It will also make simple attempts at de-duplicating messages to compensate for existing code which goes against this recommendation.

In general, error messages passed to exceptions should be a fairly terse description of what happened, and not contain extra diagnostic, contextual, or prescriptive correction advice (see `obj` and `help_text` below for more on that).

## When and how to use AnsibleError

The `AnsibleError` exception type provides support for improved error reporting. However, if no arguments other than a message are given, there's usually no benefit over using built-in exception types. So what are those other arguments?

* `obj` \- Usually a variable responsible for the error being raised – not an `Exception` instance. If this value is `Origin` tagged, then the error message shown to the user will be able to provide context showing what content triggered the error.
* `help_text` \- Instructions and additional detail that helps the user understand how to resolve the error. By putting that information here, it allows the `message` to be shorter and focus on the problem. This information will be shown *after* the contextual error details provided by `obj`, if any.

## Display warnings and errors

The existing `warning` and `deprecated` methods on the `Display` object now support passing optional `help_text` and `obj` arguments \- matching those on `AnsibleError` for prescriptive guidance and source context from `Origin`\-tagged values. Additionally, the new `error_as_warning` method accepts an exception object and an optional contextual message directly, allowing for a caught exception to be converted to a warning automatically while still preserving the exception detail, traceback, and source object context (where applicable).

## Jinja plugin errors

In Jinja plugins, the `AnsibleFilterError` and `AnsibleLookupError` exception types are no longer needed. Instead, use whatever exception type is appropriate for the error condition.

# Public surface area

Starting with ansible-core 2.19 we're trying to be more intentional about what features are part of our public API and other public surface areas (e.g. CLI, configuration options, module arguments, ansible-core provided Jinja globals, etc.).

## Imports in public Python modules

To make public Python modules more self-documenting:

* Imports in any file considered public API must be sunder-prefixed (e.g. `_module_name`) to avoid confusion about imported objects being part of the public module API.
* Prefer module-level imports (e.g. `from ansible._internal import _amodule`) with dotted usage (e.g. `foo: _amodule.thing`). This solves many circular import issues and reduces the need for sunder-prefix aliasing on internal imports in public API. Hot code paths can use locals or aliased objects, but sparingly and only where it really matters.

## Internal by default

New feature implementations in Python code should always be:

* Added to a module beneath the `ansible._internal` or `ansible.module_utils._internal` package.
* In a sunder-prefixed module (easier public module imports without aliasing).

Only public types and functions should be added to new modules outside `_internal` packages. Small sunder-prefixed utility types and functions are okay in public modules, but in general, non-public API surface area for most new implementations should live completely under an `_internal` package.

Internal-only types/functions/methods beneath an `_internal` package do not generally require sunder-prefixing on their names.

# Data Tagging

Things to know about working with data tags.

## How not to break things

Avoid unnecessary mutation of values, such as calling `str.strip` or `to_text`, etc. as these will drop tags, losing things like origin and trust for templating. These can, of course, be used when required. However, they have historically been over-used and are often no longer necessary where they once were.

When mutation of a value is necessary, it's also necessary to carefully consider which tags, if any, need to be propagated to the resulting value.

# Coding style and syntax

For new code and updates to existing code, including unit tests.

## Docstrings

Explain what the annotated code does, but don't create structured entries for parameters.

Anything considered a public API must have a docstring. Internal code should, and it often makes sense for unit tests, too.

We don't generate API docs, and haven't selected a tool or format for structured documentation of parameters, so stick to prose for now.

## Line breaks in source text

Try to stick to one sentence per line in text like docstrings, comments and changelog fragments.

This is like [https://sembr.org/](https://sembr.org/), but a more lightweight approach.

## Native type annotations

Include native type annotations on function/method arguments and return types, unless the annotation becomes too complex (e.g. `TypedDict`). The "mypy" sanity test only performs type checking on annotated functions/methods.

Some extra rules for type hints:

  - Use `object` over `t.Any`
  - Use typing's `Never` for those that don't return


## Format strings

Use f-strings instead of `%` strings or `str.format`, except for logging where formatting is deferred.

## Quoting strings

Use the `!r` format qualifier to quote a value instead of manually quoting.

Example: `f"A string with a {quoted!r} value."`

## Code formatting check/fix for internals

The `black` sanity test runs against all `_internal` packages, using default settings with an increased line length of 160 and no quote conversion. Use `ansible-test` to automatically apply required formatting changes.

Example: `ansible-test sanity --test black --fix`
