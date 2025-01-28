from __future__ import annotations as _annotations

import contextlib as _contextlib
import typing as _t

from jinja2 import environment as _environment

from ansible import errors as _errors
from ansible import _internal
from ansible._internal._templating import _jinja_bits, _engine, _jinja_common
from ansible.utils.display import Display as _Display

if _t.TYPE_CHECKING:  # pragma: nocover
    import collections as _collections
    import os as _os

    from ansible.parsing import dataloader as _dataloader

    _VariableContainer = dict[str, _t.Any] | _collections.ChainMap[str, _t.Any]


_display: _t.Final[_Display] = _Display()
_UNSET = _t.cast(_t.Any, ...)


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
        # DTFIX-RELEASE: come up with a better way to handle this so it can be deprecated
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
            help_text='Consider using `copy_with_new_env`, `set_temporary_context` or passing `overrides` to `template`.',
            version='2.23',
        )

        return self._engine.environment

    def copy_with_new_env(
        self,
        *,
        searchpath: str | None = None,
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

        templar._overrides = self._overrides.merge(context_overrides)

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
        previous_overrides = self._overrides

        # DTFIX-MERGE: deprecate this entire function in favor of copy_with_new_env
        #              when doing so, also eliminate the same named function from TemplateEngine (if we still need it, why deprecate this one?)

        if context_overrides:
            _display.deprecated(
                msg='Passing Jinja environment overrides to `set_temporary_context` is deprecated.',
                help_text='Pass Jinja environment overrides to individual `template` calls.',
                version='2.23',
            )

            self._overrides = self._overrides.merge(context_overrides)

        try:
            with self._engine.set_temporary_context(searchpath=searchpath, available_variables=available_variables):
                yield
        finally:
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
            # Skipping a deferred deprecation due to no known usage outside anible-core.
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
            )
        except _errors.AnsibleUndefinedVariable:
            # DTFIX-MERGE: depending on outcome of "what entrypoints are always top-level?" discussion, we may need to handle UndefinedMarker here as well
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
