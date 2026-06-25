# Error handling

## Tracebacks

Do not manually generate tracebacks for errors or warnings.
Standardized traceback capture is included for errors, warnings and deprecation warnings for both controller and module code (Python).
See the `DISPLAY_TRACEBACK` config option for details on how to enable traceback capture and display.

## In modules

In most cases, just raise an exception.
The AnsiballZ wrapper now provides a general exception handler for Python modules, making use of `fail_json` unnecessary, unless the module result needs to be customized.
Calls to the various Python-module-side `warn` and `deprecate` methods/functions will also capture and marshal tracebacks to the controller when enabled.
When using `fail_json` to customize a module failure result, passing the `exception` argument to provide the currently active exception is unnecessary.

## Deferred exceptions in modules

When deferring exceptions in modules using `try/except` and `fail_json`, pass the captured `Exception` instance to `fail_json` using the `exception` argument.
The error handling infrastructure will handle collection of error details and traceback formatting.

## Exception context

Raising exceptions while another exception is active will cause the active exception to become the `__context__` for the newly raised exception.
This is usually not the intended behavior, and should be reserved for unexpected errors while handling the original exception.
In most cases a `raise from` is desired, either with `None` to suppress the original exception if it's not helpful,
or with the captured exception to set it as the `__cause__` for the newly raised exception.

Suppression example: `raise Exception("something") from None`

Cause example: `raise Exception("something") from ex`

## Raising new exceptions

Don't catch exceptions just to re-raise them, unless there's additional information that can be added in the newly raised exception.
In most cases, particularly for plugin/module failures, contextual information is automatically added,
making granular `try/except/raise` within the plugin or module unnecessary.

## Error messages

Do not repeat previous exception messages when constructing new exceptions.

Anti-pattern: `raise Exception("it broke: {ex}") from ex`

The built-in error chain handling mechanisms in Ansible will include the messages from cause/context exceptions automatically.

In general, error messages passed to exceptions should be a fairly terse description of what happened,
and not contain extra diagnostic, contextual, or prescriptive correction advice (see `obj` and `help_text` below for more on that).

## When and how to use AnsibleError

The `AnsibleError` exception type provides support for improved error reporting.
However, if no arguments other than a message are given, there's usually no benefit over using built-in exception types.
So what are those other arguments?

- `obj` - Usually a variable responsible for the error being raised -- not an `Exception` instance.
If this value is `Origin` tagged, then the error message shown to the user will be able to provide context showing what content triggered the error.
- `help_text` - Instructions and additional detail that helps the user understand how to resolve the error.
By putting that information here, it allows the `message` to be shorter and focus on the problem.
This information will be shown *after* the contextual error details provided by `obj`, if any.

## Display warnings and errors

The existing `warning` and `deprecated` methods on the `Display` object now support passing optional `help_text` and `obj` arguments,
matching those on `AnsibleError` for prescriptive guidance and source context from `Origin`-tagged values.
Additionally, the new `error_as_warning` method accepts an exception object and an optional contextual message directly,
allowing for a caught exception to be converted to a warning automatically
while still preserving the exception detail, traceback, and source object context (where applicable).

## Jinja plugin errors

In Jinja plugins, the `AnsibleFilterError` and `AnsibleLookupError` exception types are no longer needed.
Instead, use whatever exception type is appropriate for the error condition.
