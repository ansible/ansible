from __future__ import annotations as _annotations

import contextlib as _contextlib
import io as _io
import os as _os
import typing as _t

from jinja2 import environment as _environment

from ansible import _internal
from ansible import errors as _errors
from ansible._internal._datatag import _tags, _wrappers
from ansible._internal._templating import _jinja_bits, _engine, _jinja_common, _template_vars

from ansible.module_utils import datatag as _module_utils_datatag
from ansible.utils.display import Display as _Display

if _t.TYPE_CHECKING:  # pragma: nocover
    import collections as _collections

    from ansible.parsing import dataloader as _dataloader

    _VariableContainer = dict[str, _t.Any] | _collections.ChainMap[str, _t.Any]


_display: _t.Final[_Display] = _Display()
_UNSET = _t.cast(_t.Any, object())
_TRUSTABLE_TYPES = (str, _io.IOBase)

AnsibleUndefined = _jinja_common.UndefinedMarker
"""Backwards compatibility alias for UndefinedMarker."""


class Templar:
    """Primary public API container for Ansible's template engine."""

    def __init__(
        self,
        loader: _dataloader.DataLoader | None = None,
        variables: _VariableContainer | None = None,
    ) -> None:
        self._engine = _engine.TemplateEngine(loader=loader, variables=variables)
        self._overrides = _jinja_bits.TemplateOverrides.DEFAULT

    @classmethod
    @_internal.experimental
    def _from_template_engine(cls, engine: _engine.TemplateEngine) -> _t.Self:
        """
        EXPERIMENTAL: For internal use within ansible-core only.
        Create a `Templar` instance from the given `TemplateEngine` instance.
        """
        templar = object.__new__(cls)
        templar._engine = engine.copy()
        templar._overrides = _jinja_bits.TemplateOverrides.DEFAULT

        return templar

    def resolve_variable_expression(
        self,
        expression: str,
        *,
        local_variables: dict[str, _t.Any] | None = None,
    ) -> _t.Any:
        """
        Resolve a potentially untrusted string variable expression consisting only of valid identifiers, integers, dots, and indexing containing these.
        Optional local variables may be provided, which can only be referenced directly by the given expression.
        Valid: x, x.y, x[y].z, x[1], 1, x[y.z]
        Error: 'x', x['y'], q('env')
        """
        return self._engine.resolve_variable_expression(expression, local_variables=local_variables)

    def evaluate_expression(
        self,
        expression: str,
        *,
        local_variables: dict[str, _t.Any] | None = None,
        escape_backslashes: bool = True,
    ) -> _t.Any:
        """
        Evaluate a trusted string expression and return its result.
        Optional local variables may be provided, which can only be referenced directly by the given expression.
        """
        return self._engine.evaluate_expression(expression, local_variables=local_variables, escape_backslashes=escape_backslashes)

    def evaluate_conditional(self, conditional: str | bool) -> bool:
        """
        Evaluate a trusted string expression or boolean and return its boolean result. A non-boolean result will raise `AnsibleBrokenConditionalError`.
        The ALLOW_BROKEN_CONDITIONALS configuration option can temporarily relax this requirement, allowing truthy conditionals to succeed.
        The ALLOW_EMBEDDED_TEMPLATES configuration option can temporarily enable inline Jinja template delimiter support (e.g., {{ }}, {% %}).
        """
        return self._engine.evaluate_conditional(conditional)

    @property
    def basedir(self) -> str:
        """The basedir from DataLoader."""
        # DTFIX-FUTURE: come up with a better way to handle this so it can be deprecated
        return self._engine.basedir

    @property
    def available_variables(self) -> _VariableContainer:
        """Available variables this instance will use when templating."""
        return self._engine.available_variables

    @available_variables.setter
    def available_variables(self, variables: _VariableContainer) -> None:
        self._engine.available_variables = variables

    @property
    def _available_variables(self) -> _VariableContainer:
        """Deprecated. Use `available_variables` instead."""
        # Commonly abused by numerous collection lookup plugins and the Ceph Ansible `config_template` action.
        _display.deprecated(
            msg='Direct access to the `_available_variables` internal attribute is deprecated.',
            help_text='Use `available_variables` instead.',
            version='2.23',
        )

        return self.available_variables

    @property
    def _loader(self) -> _dataloader.DataLoader:
        """Deprecated. Use `copy_with_new_env` to create a new instance."""
        # Abused by cloud.common, community.general and felixfontein.tools collections to create a new Templar instance.
        _display.deprecated(
            msg='Direct access to the `_loader` internal attribute is deprecated.',
            help_text='Use `copy_with_new_env` to create a new instance.',
            version='2.23',
        )

        return self._engine._loader

    @property
    def environment(self) -> _environment.Environment:
        """Deprecated."""
        _display.deprecated(
            msg='Direct access to the `environment` attribute is deprecated.',
            help_text='Consider using `copy_with_new_env` or passing `overrides` to `template`.',
            version='2.23',
        )

        return self._engine.environment

    def copy_with_new_env(
        self,
        *,
        searchpath: str | _os.PathLike | _t.Sequence[str | _os.PathLike] | None = None,
        available_variables: _VariableContainer | None = None,
        **context_overrides: _t.Any,
    ) -> Templar:
        """Return a new templar based on the current one with customizations applied."""
        if context_overrides.pop('environment_class', _UNSET) is not _UNSET:
            _display.deprecated(
                msg="The `environment_class` argument is ignored.",
                version='2.23',
            )

        if context_overrides:
            _display.deprecated(
                msg='Passing Jinja environment overrides to `copy_with_new_env` is deprecated.',
                help_text='Pass Jinja environment overrides to individual `template` calls.',
                version='2.23',
            )

        templar = Templar(
            loader=self._engine._loader,
            variables=self._engine._variables if available_variables is None else available_variables,
        )

        # backward compatibility: filter out None values from overrides, even though it is a valid value for some of them
        templar._overrides = self._overrides.merge({key: value for key, value in context_overrides.items() if value is not None})

        if searchpath is not None:
            templar._engine.environment.loader.searchpath = searchpath

        return templar

    @_contextlib.contextmanager
    def set_temporary_context(
        self,
        *,
        searchpath: str | _os.PathLike | _t.Sequence[str | _os.PathLike] | None = None,
        available_variables: _VariableContainer | None = None,
        **context_overrides: _t.Any,
    ) -> _t.Generator[None, None, None]:
        """Context manager used to set temporary templating context, without having to worry about resetting original values afterward."""
        _display.deprecated(
            msg='The `set_temporary_context` method on `Templar` is deprecated.',
            help_text='Use the `copy_with_new_env` method on `Templar` instead.',
            version='2.23',
        )

        targets = dict(
            searchpath=self._engine.environment.loader,
            available_variables=self._engine,
        )

        target_args = dict(
            searchpath=searchpath,
            available_variables=available_variables,
        )

        original: dict[str, _t.Any] = {}
        previous_overrides = self._overrides

        try:
            for key, value in target_args.items():
                if value is not None:
                    target = targets[key]
                    original[key] = getattr(target, key)
                    setattr(target, key, value)

            # backward compatibility: filter out None values from overrides, even though it is a valid value for some of them
            self._overrides = self._overrides.merge({key: value for key, value in context_overrides.items() if value is not None})

            yield
        finally:
            for key, value in original.items():
                setattr(targets[key], key, value)

            self._overrides = previous_overrides

    # noinspection PyUnusedLocal
    def template(
        self,
        variable: _t.Any,
        convert_bare: bool = _UNSET,
        preserve_trailing_newlines: bool = True,
        escape_backslashes: bool = True,
        fail_on_undefined: bool = True,
        overrides: dict[str, _t.Any] | None = None,
        convert_data: bool = _UNSET,
        disable_lookups: bool = _UNSET,
    ) -> _t.Any:
        """Templates (possibly recursively) any given data as input."""
        # DTFIX-FUTURE: offer a public version of TemplateOverrides to support an optional strongly typed `overrides` argument
        if convert_bare is not _UNSET:
            # Skipping a deferred deprecation due to minimal usage outside ansible-core.
            # Use `hasattr(templar, 'evaluate_expression')` to determine if `template` or `evaluate_expression` should be used.
            _display.deprecated(
                msg="Passing `convert_bare` to `template` is deprecated.",
                help_text="Use `evaluate_expression` instead.",
                version="2.23",
            )

            if convert_bare and isinstance(variable, str):
                contains_filters = "|" in variable
                first_part = variable.split("|")[0].split(".")[0].split("[")[0]
                convert_bare = (contains_filters or first_part in self.available_variables) and not self.is_possibly_template(variable, overrides)
            else:
                convert_bare = False
        else:
            convert_bare = False

        if fail_on_undefined is None:
            # The pre-2.19 config fallback is ignored for content portability.
            _display.deprecated(
                msg="Falling back to `True` for `fail_on_undefined`.",
                help_text="Use either `True` or `False` for `fail_on_undefined` when calling `template`.",
                version="2.23",
            )

            fail_on_undefined = True

        if convert_data is not _UNSET:
            # Skipping a deferred deprecation due to minimal usage outside ansible-core.
            # Use `hasattr(templar, 'evaluate_expression')` as a surrogate check to determine if `convert_data` is accepted.
            _display.deprecated(
                msg="Passing `convert_data` to `template` is deprecated.",
                version="2.23",
            )

        if disable_lookups is not _UNSET:
            # Skipping a deferred deprecation due to no known usage outside ansible-core.
            # Use `hasattr(templar, 'evaluate_expression')` as a surrogate check to determine if `disable_lookups` is accepted.
            _display.deprecated(
                msg="Passing `disable_lookups` to `template` is deprecated.",
                version="2.23",
            )

        try:
            if convert_bare:  # pre-2.19 compat
                return self.evaluate_expression(variable, escape_backslashes=escape_backslashes)

            return self._engine.template(
                variable=variable,
                options=_engine.TemplateOptions(
                    preserve_trailing_newlines=preserve_trailing_newlines,
                    escape_backslashes=escape_backslashes,
                    overrides=self._overrides.merge(overrides),
                ),
                mode=_engine.TemplateMode.ALWAYS_FINALIZE,
            )
        except _errors.AnsibleUndefinedVariable:
            if not fail_on_undefined:
                return variable

            raise

    def is_template(self, data: _t.Any) -> bool:
        """
        Evaluate the input data to determine if it contains a template, even if that template is invalid. Containers will be recursively searched.
        Objects subject to template-time transforms that do not yield a template are not considered templates by this method.
        Gating a conditional call to `template` with this method is redundant and inefficient -- request templating unconditionally instead.
        """
        return self._engine.is_template(data, self._overrides)

    def is_possibly_template(
        self,
        data: _t.Any,
        overrides: dict[str, _t.Any] | None = None,
    ) -> bool:
        """
        A lightweight check to determine if the given value is a string that looks like it contains a template, even if that template is invalid.
        Returns `True` if the given value is a string that starts with a Jinja overrides header or if it contains template start strings.
        Gating a conditional call to `template` with this method is redundant and inefficient -- request templating unconditionally instead.
        """
        return isinstance(data, str) and _jinja_bits.is_possibly_template(data, self._overrides.merge(overrides))

    def do_template(
        self,
        data: _t.Any,
        preserve_trailing_newlines: bool = True,
        escape_backslashes: bool = True,
        fail_on_undefined: bool = True,
        overrides: dict[str, _t.Any] | None = None,
        disable_lookups: bool = _UNSET,
        convert_data: bool = _UNSET,
    ) -> _t.Any:
        """Deprecated. Use `template` instead."""
        _display.deprecated(
            msg='The `do_template` method on `Templar` is deprecated.',
            help_text='Use the `template` method on `Templar` instead.',
            version='2.23',
        )

        if not isinstance(data, str):
            return data

        return self.template(
            variable=data,
            preserve_trailing_newlines=preserve_trailing_newlines,
            escape_backslashes=escape_backslashes,
            fail_on_undefined=fail_on_undefined,
            overrides=overrides,
            disable_lookups=disable_lookups,
            convert_data=convert_data,
        )


def generate_ansible_template_vars(
    path: str,
    fullpath: str | None = None,
    dest_path: str | None = None,
) -> dict[str, object]:
    """
    Generate and return a dictionary with variable metadata about the template specified by `fullpath`.
    If `fullpath` is `None`, `path` will be used instead.
    """
    # deprecated description="deprecate `generate_ansible_template_vars`, collections should inline the necessary variables" core_version="2.23"
    return _template_vars.generate_ansible_template_vars(path=path, fullpath=fullpath, dest_path=dest_path, include_ansible_managed=True)


def trust_as_template[T: str | _io.IOBase | _t.TextIO | _t.BinaryIO](value: T) -> T:
    """
    Returns `value` tagged as trusted for templating.
    Raises a `TypeError` if `value` is not a supported type.
    """
    if isinstance(value, str):
        return _tags.TrustedAsTemplate().tag(value)  # type: ignore[return-value]

    if isinstance(value, _io.IOBase):  # covers TextIO and BinaryIO at runtime, but type checking disagrees
        return _wrappers.TaggedStreamWrapper(value, _tags.TrustedAsTemplate())

    raise TypeError(f"Trust cannot be applied to {_module_utils_datatag.native_type_name(value)}, only to 'str' or 'IOBase'.")


def is_trusted_as_template(value: object) -> bool:
    """
    Returns `True` if `value` is a `str` or `IOBase` marked as trusted for templating, otherwise returns `False`.
    Returns `False` for types which cannot be trusted for templating.
    Containers are not recursed and will always return `False`.
    This function should not be needed for production code, but may be useful in unit tests.
    """
    return isinstance(value, _TRUSTABLE_TYPES) and _tags.TrustedAsTemplate.is_tagged_on(value)


def accept_args_markers[T: _t.Callable](plugin: T) -> T:
    """
    A decorator to mark a Jinja plugin as capable of handling `Marker` values for its top-level arguments.
    Non-decorated plugin invocation is skipped when a top-level argument is a `Marker`, with the first such value substituted as the plugin result.
    This ensures that only plugins which understand `Marker` instances for top-level arguments will encounter them.
    """
    plugin.accept_args_markers = True

    return plugin


def accept_lazy_markers[T: _t.Callable](plugin: T) -> T:
    """
    A decorator to mark a Jinja plugin as capable of handling `Marker` values retrieved from lazy containers.
    Non-decorated plugins will trigger a `MarkerError` exception when attempting to retrieve a `Marker` from a lazy container.
    This ensures that only plugins which understand lazy retrieval of `Marker` instances will encounter them.
    """
    plugin.accept_lazy_markers = True

    return plugin


get_first_marker_arg = _jinja_common.get_first_marker_arg
