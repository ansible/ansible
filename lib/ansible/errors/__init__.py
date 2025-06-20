# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import collections.abc as _c
import enum
import types
import typing as t

from json import JSONDecodeError

from ansible.module_utils.common.text.converters import to_text
from ..module_utils.datatag import native_type_name
from ansible._internal._datatag import _tags
from .._internal._errors import _error_utils
from ansible.module_utils._internal import _text_utils

if t.TYPE_CHECKING:
    from ansible.plugins import loader as _t_loader


class ExitCode(enum.IntEnum):
    SUCCESS = 0  # used by TQM, must be bit-flag safe
    GENERIC_ERROR = 1  # used by TQM, must be bit-flag safe
    HOST_FAILED = 2  # TQM-sourced, must be bit-flag safe
    HOST_UNREACHABLE = 4  # TQM-sourced, must be bit-flag safe
    PARSER_ERROR = 4  # FIXME: CLI-sourced, conflicts with HOST_UNREACHABLE
    INVALID_CLI_OPTION = 5
    UNICODE_ERROR = 6  # obsolete, no longer used
    KEYBOARD_INTERRUPT = 99
    UNKNOWN_ERROR = 250


class AnsibleError(Exception):
    """
    This is the base class for all errors raised from Ansible code,
    and can be instantiated with two optional parameters beyond the
    error message to control whether detailed information is displayed
    when the error occurred while parsing a data file of some kind.

    Usage:

        raise AnsibleError('some message here', obj=obj)

    Where "obj" may be tagged with Origin to provide context for error messages.
    """

    _exit_code = ExitCode.GENERIC_ERROR
    _default_message = ''
    _default_help_text: str | None = None
    _include_cause_message = True
    """
    When `True`, the exception message will be augmented with cause message(s).
    Subclasses doing complex error analysis can disable this to take responsibility for reporting cause messages as needed.
    """

    def __init__(
        self,
        message: str = "",
        obj: t.Any = None,
        show_content: bool = True,
        suppress_extended_error: bool | types.EllipsisType = ...,
        orig_exc: BaseException | None = None,
        help_text: str | None = None,
    ) -> None:
        # DTFIX-FUTURE: these fallback cases mask incorrect use of AnsibleError.message, what should we do?
        if message is None:
            message = ''
        elif not isinstance(message, str):
            message = str(message)

        if self._default_message and message:
            message = _text_utils.concat_message(self._default_message, message)
        elif self._default_message:
            message = self._default_message
        elif not message:
            message = f'Unexpected {type(self).__name__} error.'

        super().__init__(message)

        self._show_content = show_content
        self._message = message
        self._help_text_value = help_text or self._default_help_text
        self.obj = obj

        # deprecated: description='deprecate support for orig_exc, callers should use `raise ... from` only' core_version='2.23'
        # deprecated: description='remove support for orig_exc' core_version='2.27'
        self.orig_exc = orig_exc

        if suppress_extended_error is not ...:
            from ..utils.display import Display

            if suppress_extended_error:
                self._show_content = False

            Display().deprecated(
                msg=f"The `suppress_extended_error` argument to `{type(self).__name__}` is deprecated.",
                version="2.23",
                help_text="Use `show_content=False` instead.",
            )

    @property
    def _original_message(self) -> str:
        return self._message

    @property
    def message(self) -> str:
        """
        Return the original message with cause message(s) appended.
        The cause will not be followed on any `AnsibleError` with `_include_cause_message=False`.
        """
        return _error_utils.format_exception_message(self)

    @message.setter
    def message(self, val) -> None:
        self._message = val

    @property
    def _formatted_source_context(self) -> str | None:
        with _error_utils.RedactAnnotatedSourceContext.when(not self._show_content):
            if source_context := _error_utils.SourceContext.from_value(self.obj):
                return str(source_context)

        return None

    @property
    def _help_text(self) -> str | None:
        return self._help_text_value

    @_help_text.setter
    def _help_text(self, value: str | None) -> None:
        self._help_text_value = value

    def __str__(self) -> str:
        return self.message

    def __getstate__(self) -> dict[str, t.Any]:
        """Augment object.__getstate__ to preserve additional values not represented in BaseException.__dict__."""
        state = t.cast(dict[str, t.Any], super().__getstate__())
        state.update(
            args=self.args,
            __cause__=self.__cause__,
            __context__=self.__context__,
            __suppress_context__=self.__suppress_context__,
        )

        return state

    def __reduce__(self) -> tuple[t.Callable, tuple[type], dict[str, t.Any]]:
        """
        Enable copy/pickle of AnsibleError derived types by correcting for BaseException's ancient C __reduce__ impl that:

        * requires use of a type constructor with positional args
        * assumes positional args are passed through from the derived type __init__ to BaseException.__init__ unmodified
        * does not propagate args/__cause__/__context__/__suppress_context__

        NOTE: This does not preserve the dunder attributes on non-AnsibleError derived cause/context exceptions.
              As a result, copy/pickle will discard chained exceptions after the first non-AnsibleError cause/context.
        """
        return type(self).__new__, (type(self),), self.__getstate__()


class AnsibleUndefinedConfigEntry(AnsibleError):
    """The requested config entry is not defined."""


class AnsibleTaskError(AnsibleError):
    """Task execution failed; provides contextual information about the task."""

    _default_message = 'Task failed.'


class AnsiblePromptInterrupt(AnsibleError):
    """User interrupt."""


class AnsiblePromptNoninteractive(AnsibleError):
    """Unable to get user input."""


class AnsibleAssertionError(AnsibleError, AssertionError):
    """Invalid assertion."""


class AnsibleOptionsError(AnsibleError):
    """Invalid options were passed."""

    # FIXME: This exception is used for many non-CLI related errors.
    #          The few cases which are CLI related should really be handled by argparse instead, at which point the exit code here can be removed.
    _exit_code = ExitCode.INVALID_CLI_OPTION


class AnsibleRequiredOptionError(AnsibleOptionsError):
    """Bad or incomplete options passed."""


class AnsibleParserError(AnsibleError):
    """A playbook or data file could not be parsed."""

    _exit_code = ExitCode.PARSER_ERROR


class AnsibleFieldAttributeError(AnsibleParserError):
    """Errors caused during field attribute processing."""


class AnsibleJSONParserError(AnsibleParserError):
    """JSON-specific parsing failure wrapping an exception raised by the JSON parser."""

    _default_message = 'JSON parsing failed.'
    _include_cause_message = False  # hide the underlying cause message, it's included by `handle_exception` as needed

    @classmethod
    def handle_exception(cls, exception: Exception, origin: _tags.Origin) -> t.NoReturn:
        if isinstance(exception, JSONDecodeError):
            origin = origin.replace(line_num=exception.lineno, col_num=exception.colno)

        message = str(exception)

        error = cls(message, obj=origin)

        raise error from exception


class AnsibleInternalError(AnsibleError):
    """Internal safeguards tripped, something happened in the code that should never happen."""


class AnsibleRuntimeError(AnsibleError):
    """Ansible had a problem while running a playbook."""


class AnsibleModuleError(AnsibleRuntimeError):
    """A module failed somehow."""


class AnsibleConnectionFailure(AnsibleRuntimeError, _error_utils.ContributesToTaskResult):
    """
    The transport / connection_plugin had a fatal error.

    This exception provides a result dictionary via the ContributesToTaskResult mixin.
    """

    @property
    def result_contribution(self) -> t.Mapping[str, object]:
        return dict(unreachable=True)

    @property
    def omit_failed_key(self) -> bool:
        return True


class AnsibleAuthenticationFailure(AnsibleConnectionFailure):
    """Invalid username/password/key."""

    _default_message = "Failed to authenticate."


class AnsibleCallbackError(AnsibleRuntimeError):
    """A callback failure."""


class AnsibleTemplateError(AnsibleRuntimeError):
    """A template related error."""


class TemplateTrustCheckFailedError(AnsibleTemplateError):
    """Raised when processing was requested on an untrusted template or expression."""

    _default_message = 'Encountered untrusted template or expression.'
    _default_help_text = ('Templates and expressions must be defined by trusted sources such as playbooks or roles, '
                          'not untrusted sources such as module results.')


class AnsibleTemplateTransformLimitError(AnsibleTemplateError):
    """The internal template transform limit was exceeded."""

    _default_message = "Template transform limit exceeded."


class AnsibleTemplateSyntaxError(AnsibleTemplateError):
    """A syntax error was encountered while parsing a Jinja template or expression."""


class AnsibleBrokenConditionalError(AnsibleTemplateError):
    """A broken conditional with non-boolean result was used."""

    _default_help_text = 'Broken conditionals can be temporarily allowed with the `ALLOW_BROKEN_CONDITIONALS` configuration option.'


class AnsibleUndefinedVariable(AnsibleTemplateError):
    """An undefined variable was encountered while processing a template or expression."""


class AnsibleValueOmittedError(AnsibleTemplateError):
    """
    Raised when the result of a template operation was the Omit singleton. This exception purposely does
    not derive from AnsibleError to avoid elision of the traceback, since uncaught errors of this type always
    indicate a bug.
    """

    _default_message = "A template was resolved to an Omit scalar."
    _default_help_text = "Callers must be prepared to handle this value. This is most likely a bug in the code requesting templating."


class AnsibleTemplatePluginError(AnsibleTemplateError):
    """An error sourced by a template plugin (lookup/filter/test)."""


# deprecated: description='add deprecation warnings for these aliases' core_version='2.23'
AnsibleFilterError = AnsibleTemplatePluginError
AnsibleLookupError = AnsibleTemplatePluginError


class AnsibleFileNotFound(AnsibleRuntimeError):
    """A file missing failure."""

    def __init__(self, message="", obj=None, show_content=True, suppress_extended_error=..., orig_exc=None, paths=None, file_name=None):

        self.file_name = file_name
        self.paths = paths

        if message:
            message += "\n"
        if self.file_name:
            message += "Could not find or access '%s'" % to_text(self.file_name)
        else:
            message += "Could not find file"

        if self.paths and isinstance(self.paths, _c.Sequence):
            searched = to_text('\n\t'.join(self.paths))
            if message:
                message += "\n"
            message += "Searched in:\n\t%s" % searched

        message += " on the Ansible Controller.\nIf you are using a module and expect the file to exist on the remote, see the remote_src option"

        super(AnsibleFileNotFound, self).__init__(message=message, obj=obj, show_content=show_content,
                                                  suppress_extended_error=suppress_extended_error, orig_exc=orig_exc)


class AnsibleAction(AnsibleRuntimeError, _error_utils.ContributesToTaskResult):
    """Base Exception for Action plugin flow control."""

    def __init__(self, message="", obj=None, show_content=True, suppress_extended_error=..., orig_exc=None, result=None):
        super().__init__(message=message, obj=obj, show_content=show_content, suppress_extended_error=suppress_extended_error, orig_exc=orig_exc)

        self._result = result or {}

    @property
    def result_contribution(self) -> _c.Mapping[str, object]:
        return self._result

    @property
    def result(self) -> dict[str, object]:
        """Backward compatibility property returning a mutable dictionary."""
        return dict(self.result_contribution)


class AnsibleActionSkip(AnsibleAction):
    """
    An action runtime skip.

    This exception provides a result dictionary via the ContributesToTaskResult mixin.
    """

    @property
    def result_contribution(self) -> _c.Mapping[str, object]:
        return self._result | dict(
            skipped=True,
            msg=self.message,
        )

    @property
    def omit_failed_key(self) -> bool:
        return True

    @property
    def omit_exception_key(self) -> bool:
        return True


class AnsibleActionFail(AnsibleAction):
    """
    An action runtime failure.

    This exception provides a result dictionary via the ContributesToTaskResult mixin.
    """

    @property
    def result_contribution(self) -> _c.Mapping[str, object]:
        return self._result | dict(
            failed=True,
            msg=self.message,
        )


class _ActionDone(AnsibleAction):
    """
    Imports as `_AnsibleActionDone` are deprecated. An action runtime early exit.

    This exception provides a result dictionary via the ContributesToTaskResult mixin.
    """

    @property
    def omit_failed_key(self) -> bool:
        return not self._result.get('failed')

    @property
    def omit_exception_key(self) -> bool:
        return not self._result.get('failed')


class AnsiblePluginError(AnsibleError):
    """Base class for Ansible plugin-related errors that do not need AnsibleError contextual data."""

    def __init__(self, message: str | None = None, plugin_load_context: _t_loader.PluginLoadContext | None = None, help_text: str | None = None) -> None:
        super(AnsiblePluginError, self).__init__(message, help_text=help_text)

        self.plugin_load_context = plugin_load_context


class AnsiblePluginRemovedError(AnsiblePluginError):
    """A requested plugin has been removed."""


class AnsiblePluginCircularRedirect(AnsiblePluginError):
    """A cycle was detected in plugin redirection."""


class AnsibleCollectionUnsupportedVersionError(AnsiblePluginError):
    """A collection is not supported by this version of Ansible."""


class AnsibleTypeError(AnsibleRuntimeError, TypeError):
    """Ansible-augmented TypeError subclass."""


class AnsiblePluginNotFound(AnsiblePluginError):
    """Indicates we did not find an Ansible plugin."""


class AnsibleConditionalError(AnsibleRuntimeError):
    """Errors related to failed conditional expression evaluation."""


class AnsibleVariableTypeError(AnsibleRuntimeError):
    """An error due to attempted storage of an unsupported variable type."""

    @classmethod
    def from_value(cls, *, obj: t.Any) -> t.Self:
        # avoid an incorrect error message when `obj` is a type
        type_name = type(obj).__name__ if isinstance(obj, type) else native_type_name(obj)

        return cls(message=f'Type {type_name!r} is unsupported for variable storage.', obj=obj)


def __getattr__(name: str) -> t.Any:
    """Inject import-time deprecation warnings."""
    from ..utils.display import Display

    match name:
        case 'AnsibleFilterTypeError':
            Display().deprecated(
                msg=f"Importing {name!r} is deprecated.",
                help_text=f"Import {AnsibleTypeError.__name__!r} instead.",
                version="2.23",
            )

            return AnsibleTypeError

        case '_AnsibleActionDone':
            Display().deprecated(
                msg=f"Importing {name!r} is deprecated.",
                help_text="Return directly from action plugins instead.",
                version="2.23",
            )

            return _ActionDone

    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
