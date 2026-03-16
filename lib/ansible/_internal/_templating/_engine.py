# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import copy
import dataclasses
import enum
import typing as t
import collections.abc as c
import re

from collections import ChainMap

from ansible.errors import (
    AnsibleError,
    AnsibleValueOmittedError,
    AnsibleUndefinedVariable,
    AnsibleTemplateSyntaxError,
    AnsibleBrokenConditionalError,
    AnsibleTemplateTransformLimitError,
    TemplateTrustCheckFailedError,
)

from ansible.module_utils._internal._datatag import AnsibleTaggedObject, NotTaggableError, AnsibleTagHelper
from ansible._internal._errors._handler import Skippable
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible.utils.display import Display
from ansible.utils.vars import validate_variable_name
from ansible.parsing.dataloader import DataLoader

from ._datatag import DeprecatedAccessAuditContext
from ._jinja_bits import (
    AnsibleTemplate,
    _TemplateCompileContext,
    TemplateOverrides,
    AnsibleEnvironment,
    defer_template_error,
    create_template_error,
    is_possibly_template,
    is_possibly_all_template,
    AnsibleTemplateExpression,
    _finalize_template_result,
    FinalizeMode,
)
from ._jinja_common import _TemplateConfig, MarkerError, ExceptionMarker, JinjaCallContext
from ._lazy_containers import _AnsibleLazyTemplateMixin
from ._marker_behaviors import MarkerBehavior, FAIL_ON_UNDEFINED
from ._transform import _type_transform_mapping
from ._utils import Omit, TemplateContext, IGNORE_SCALAR_VAR_TYPES, LazyOptions
from ...module_utils.datatag import native_type_name

_display = Display()


_shared_empty_unmask_type_names: frozenset[str] = frozenset()

TRANSFORM_CHAIN_LIMIT: int = 10
"""Arbitrary limit for chained transforms to prevent cycles; an exception will be raised if exceeded."""


class TemplateMode(enum.Enum):
    # DTFIX-FUTURE: this enum ideally wouldn't exist - revisit/rename before making public
    DEFAULT = enum.auto()
    STOP_ON_TEMPLATE = enum.auto()
    STOP_ON_CONTAINER = enum.auto()
    ALWAYS_FINALIZE = enum.auto()


@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class TemplateOptions:
    DEFAULT: t.ClassVar[t.Self]

    value_for_omit: object = Omit
    escape_backslashes: bool = True
    preserve_trailing_newlines: bool = True
    # DTFIX-FUTURE: these aren't really overrides anymore, rename the dataclass and this field
    #                also mention in docstring this has no effect unless used to template a string
    overrides: TemplateOverrides = TemplateOverrides.DEFAULT


TemplateOptions.DEFAULT = TemplateOptions()


class TemplateEncountered(Exception):
    pass


class TemplateEngine:
    """
    The main class for templating, with the main entry-point of template().
    """

    _sentinel = object()

    def __init__(
        self,
        loader: DataLoader | None = None,
        variables: dict[str, t.Any] | ChainMap[str, t.Any] | None = None,
        variables_factory: t.Callable[[], dict[str, t.Any] | ChainMap[str, t.Any]] | None = None,
        marker_behavior: MarkerBehavior | None = None,
    ):
        self._loader = loader
        self._variables = variables
        self._variables_factory = variables_factory
        self._environment: AnsibleEnvironment | None = None

        # inherit marker behavior from the active template context's templar unless otherwise specified
        if not marker_behavior:
            if template_ctx := TemplateContext.current(optional=True):
                marker_behavior = template_ctx.templar.marker_behavior
            else:
                marker_behavior = FAIL_ON_UNDEFINED

        self._marker_behavior = marker_behavior

    def copy(self) -> t.Self:
        new_engine = copy.copy(self)
        new_engine._environment = None

        return new_engine

    def extend(self, marker_behavior: MarkerBehavior | None = None) -> t.Self:
        new_templar = type(self)(
            loader=self._loader,
            variables=self._variables,
            variables_factory=self._variables_factory,
            marker_behavior=marker_behavior or self._marker_behavior,
        )

        if self._environment:
            new_templar._environment = self._environment

        return new_templar

    @property
    def marker_behavior(self) -> MarkerBehavior:
        return self._marker_behavior

    @property
    def basedir(self) -> str:
        """The basedir from DataLoader."""
        return self._loader.get_basedir() if self._loader else '.'

    @property
    def environment(self) -> AnsibleEnvironment:
        if not self._environment:
            self._environment = AnsibleEnvironment(ansible_basedir=self.basedir)

        return self._environment

    def _create_overlay(self, template: str, overrides: TemplateOverrides) -> tuple[str, AnsibleEnvironment]:
        try:
            template, overrides = overrides._extract_template_overrides(template)
        except Exception as ex:
            raise AnsibleTemplateSyntaxError("Syntax error in template.", obj=template) from ex

        env = self.environment

        if overrides is not TemplateOverrides.DEFAULT and (overlay_kwargs := overrides.overlay_kwargs()):
            env = t.cast(AnsibleEnvironment, env.overlay(**overlay_kwargs))

        return template, env

    @staticmethod
    def _count_newlines_from_end(in_str):
        """
        Counts the number of newlines at the end of a string. This is used during
        the jinja2 templating to ensure the count matches the input, since some newlines
        may be thrown away during the templating.
        """

        i = len(in_str)
        j = i - 1

        try:
            while in_str[j] == '\n':
                j -= 1
        except IndexError:
            # Uncommon cases: zero length string and string containing only newlines
            return i

        return i - 1 - j

    @property
    def available_variables(self) -> dict[str, t.Any] | ChainMap[str, t.Any]:
        """Available variables this instance will use when templating."""
        # DTFIX3: ensure that we're always accessing this as a shallow container-level snapshot, and eliminate uses of anything
        #  that directly mutates this value. _new_context may resolve this for us?
        if self._variables is None:
            self._variables = self._variables_factory() if self._variables_factory else {}

        return self._variables

    @available_variables.setter
    def available_variables(self, variables: dict[str, t.Any] | ChainMap[str, t.Any]) -> None:
        self._variables = variables

    def resolve_variable_expression(
        self,
        expression: str,
        *,
        local_variables: dict[str, t.Any] | None = None,
    ) -> t.Any:
        """
        Resolve a potentially untrusted string variable expression consisting only of valid identifiers, integers, dots, and indexing containing these.
        Optional local variables may be provided, which can only be referenced directly by the given expression.
        Valid: x, x.y, x[y].z, x[1], 1, x[y.z]
        Error: 'x', x['y'], q('env')
        """
        components = re.split(r'[.\[\]]', expression)

        try:
            for component in components:
                if re.fullmatch('[0-9]*', component):
                    continue  # allow empty strings and integers

                validate_variable_name(component)
        except Exception as ex:
            raise AnsibleError(f'Invalid variable expression: {expression}', obj=expression) from ex

        return self.evaluate_expression(TrustedAsTemplate().tag(expression), local_variables=local_variables)

    @staticmethod
    def variable_name_as_template(name: str) -> str:
        """Return a trusted template string that will resolve the provided variable name. Raises an error if `name` is not a valid identifier."""
        validate_variable_name(name)
        return AnsibleTagHelper.tag('{{' + name + '}}', (AnsibleTagHelper.tags(name) | {TrustedAsTemplate()}))

    def transform(self, variable: t.Any) -> t.Any:
        """Recursively apply transformations to the given value and return the result."""
        return self.template(variable, mode=TemplateMode.ALWAYS_FINALIZE, lazy_options=LazyOptions.SKIP_TEMPLATES_AND_ACCESS)

    def template(
        self,
        variable: t.Any,  # DTFIX-FUTURE: once we settle the new/old API boundaries, rename this (here and in other methods)
        *,
        options: TemplateOptions = TemplateOptions.DEFAULT,
        mode: TemplateMode = TemplateMode.DEFAULT,
        lazy_options: LazyOptions = LazyOptions.DEFAULT,
    ) -> t.Any:
        """Templates (possibly recursively) any given data as input."""
        original_variable = variable

        for _attempt in range(TRANSFORM_CHAIN_LIMIT):
            if variable is None or (value_type := type(variable)) in IGNORE_SCALAR_VAR_TYPES:
                return variable  # quickly ignore supported scalar types which are not be templated

            value_is_str = isinstance(variable, str)

            if template_ctx := TemplateContext.current(optional=True):
                stop_on_template = template_ctx.stop_on_template
            else:
                stop_on_template = False

            if mode is TemplateMode.STOP_ON_TEMPLATE:
                stop_on_template = True

            with (
                TemplateContext(template_value=variable, templar=self, options=options, stop_on_template=stop_on_template) as ctx,
                DeprecatedAccessAuditContext.when(ctx.is_top_level),
                JinjaCallContext(accept_lazy_markers=True),  # let default Jinja marker behavior apply, since we're descending into a new template
            ):
                try:
                    if not value_is_str:
                        # transforms are currently limited to non-str types as an optimization
                        if (transform := _type_transform_mapping.get(value_type)) and value_type.__name__ not in lazy_options.unmask_type_names:
                            variable = transform(variable)
                            continue

                        template_result = _AnsibleLazyTemplateMixin._try_create(variable, lazy_options)
                    elif not lazy_options.template:
                        template_result = variable
                    elif not is_possibly_template(variable, options.overrides):
                        template_result = variable
                    elif not self._trust_check(variable, skip_handler=stop_on_template):
                        template_result = variable
                    elif stop_on_template:
                        raise TemplateEncountered()
                    else:
                        compiled_template = self._compile_template(variable, options)

                        template_result = compiled_template(self.available_variables)
                        template_result = self._post_render_mutation(variable, template_result, options)
                except TemplateEncountered:
                    raise
                except Exception as ex:
                    template_result = defer_template_error(ex, variable, is_expression=False)

                if ctx.is_top_level or mode is TemplateMode.ALWAYS_FINALIZE:
                    template_result = self._finalize_top_level_template_result(
                        variable, options, template_result, stop_on_container=mode is TemplateMode.STOP_ON_CONTAINER
                    )

            return template_result

        raise AnsibleTemplateTransformLimitError(obj=original_variable)

    @staticmethod
    def _finalize_top_level_template_result(
        variable: t.Any,
        options: TemplateOptions,
        template_result: t.Any,
        is_expression: bool = False,
        stop_on_container: bool = False,
    ) -> t.Any:
        """
        This method must be called for expressions and top-level templates to recursively finalize the result.
        This renders any embedded templates and triggers `Marker` and omit behaviors.
        """
        try:
            if template_result is Omit:
                # When the template result is Omit, raise an AnsibleValueOmittedError if value_for_omit is Omit, otherwise return value_for_omit.
                # Other occurrences of Omit will simply drop out of containers during _finalize_template_result.
                if options.value_for_omit is Omit:
                    raise AnsibleValueOmittedError()

                return options.value_for_omit  # trust that value_for_omit is an allowed type

            if stop_on_container and type(template_result) in AnsibleTaggedObject._collection_types:
                # Use of stop_on_container implies the caller will perform necessary checks on values,
                # most likely by passing them back into the templating system.
                try:
                    return template_result._non_lazy_copy()
                except AttributeError:
                    return template_result  # non-lazy containers are returned as-is

            return _finalize_template_result(template_result, FinalizeMode.TOP_LEVEL)
        except TemplateEncountered:
            raise
        except Exception as ex:
            raise_from: BaseException

            if isinstance(ex, MarkerError):
                exception_to_raise = ex.source._as_exception()

                # MarkerError is never suitable for use as the cause of another exception, it is merely a raiseable container for the source marker
                # used for flow control (so its stack trace is rarely useful). However, if the source derives from a ExceptionMarker, its contained
                # exception (previously raised) should be used as the cause. Other sources do not contain exceptions, so cannot provide a cause.
                raise_from = exception_to_raise if isinstance(ex.source, ExceptionMarker) else None
            else:
                exception_to_raise = ex
                raise_from = ex

            exception_to_raise = create_template_error(exception_to_raise, variable, is_expression)

            if exception_to_raise is ex:
                raise  # when the exception to raise is the active exception, just re-raise it

            if exception_to_raise is raise_from:
                raise_from = exception_to_raise.__cause__  # preserve the exception's cause, if any, otherwise no cause will be used

            raise exception_to_raise from raise_from  # always raise from something to avoid the currently active exception becoming __context__

    def _compile_template(self, template: str, options: TemplateOptions) -> t.Callable[[c.Mapping[str, t.Any]], t.Any]:
        # NOTE: Creating an overlay that lives only inside _compile_template means that overrides are not applied
        # when templating nested variables, where Templar.environment is used, not the overlay. They are, however,
        # applied to includes and imports.
        try:
            stripped_template, env = self._create_overlay(template, options.overrides)

            with _TemplateCompileContext(escape_backslashes=options.escape_backslashes):
                return t.cast(AnsibleTemplate, env.from_string(stripped_template))
        except Exception as ex:
            return self._defer_jinja_compile_error(ex, template, False)

    def _compile_expression(self, expression: str, options: TemplateOptions) -> t.Callable[[c.Mapping[str, t.Any]], t.Any]:
        """
        Compile a Jinja expression, applying optional compile-time behavior via an environment overlay (if needed). The overlay is
        necessary to avoid mutating settings on the Templar's shared environment, which could be visible to other code running concurrently.
        In the specific case of escape_backslashes, the setting only applies to a top-level template at compile-time, not runtime, to
        ensure that any nested template calls (e.g., include and import) do not inherit the (lack of) escaping behavior.
        """
        try:
            with _TemplateCompileContext(escape_backslashes=options.escape_backslashes):
                return AnsibleTemplateExpression(self.environment.compile_expression(expression, False))
        except Exception as ex:
            return self._defer_jinja_compile_error(ex, expression, True)

    def _defer_jinja_compile_error(self, ex: Exception, variable: str, is_expression: bool) -> t.Callable[[c.Mapping[str, t.Any]], t.Any]:
        deferred_error = defer_template_error(ex, variable, is_expression=is_expression)

        def deferred_exception(_jinja_vars: c.Mapping[str, t.Any]) -> t.Any:
            # a template/expression compile error always results in a single node representing the compile error
            return self.marker_behavior.handle_marker(deferred_error)

        return deferred_exception

    def _post_render_mutation(self, template: str, result: t.Any, options: TemplateOptions) -> t.Any:
        if options.preserve_trailing_newlines and isinstance(result, str):
            # The low level calls above do not preserve the newline
            # characters at the end of the input data, so we
            # calculate the difference in newlines and append them
            # to the resulting output for parity
            #
            # Using AnsibleEnvironment's keep_trailing_newline instead would
            # result in change in behavior when trailing newlines
            # would be kept also for included templates, for example:
            # "Hello {% include 'world.txt' %}!" would render as
            # "Hello world\n!\n" instead of "Hello world!\n".
            data_newlines = self._count_newlines_from_end(template)
            res_newlines = self._count_newlines_from_end(result)

            if data_newlines > res_newlines:
                newlines = options.overrides.newline_sequence * (data_newlines - res_newlines)
                result = AnsibleTagHelper.tag_copy(result, result + newlines)

        # If the input string template was source-tagged and the result is not, propagate the source tag to the new value.
        # This provides further contextual information when a template-derived value/var causes an error.
        if not Origin.is_tagged_on(result) and (origin := Origin.get_tag(template)):
            try:
                result = origin.tag(result)
            except NotTaggableError:
                pass  # best effort- if we can't, oh well

        return result

    def is_template(self, data: t.Any, overrides: TemplateOverrides = TemplateOverrides.DEFAULT) -> bool:
        """
        Evaluate the input data to determine if it contains a template, even if that template is invalid. Containers will be recursively searched.
        Objects subject to template-time transforms that do not yield a template are not considered templates by this method.
        Gating a conditional call to `template` with this method is redundant and inefficient -- request templating unconditionally instead.
        """
        options = TemplateOptions(overrides=overrides) if overrides is not TemplateOverrides.DEFAULT else TemplateOptions.DEFAULT

        try:
            self.template(data, options=options, mode=TemplateMode.STOP_ON_TEMPLATE)
        except TemplateEncountered:
            return True
        else:
            return False

    def resolve_to_container(self, variable: t.Any, options: TemplateOptions = TemplateOptions.DEFAULT) -> t.Any:
        """
        Recursively resolve scalar string template input, stopping at the first container encountered (if any).
        Used for e.g., partial templating of task arguments, where the plugin needs to handle final resolution of some args internally.
        """
        return self.template(variable, options=options, mode=TemplateMode.STOP_ON_CONTAINER)

    def evaluate_expression(
        self,
        expression: str,
        *,
        local_variables: dict[str, t.Any] | None = None,
        escape_backslashes: bool = True,
        _render_jinja_const_template: bool = False,
    ) -> t.Any:
        """
        Evaluate a trusted string expression and return its result.
        Optional local variables may be provided, which can only be referenced directly by the given expression.
        """
        if not isinstance(expression, str):
            raise TypeError(f"Expressions must be {str!r}, got {type(expression)!r}.")

        options = TemplateOptions(escape_backslashes=escape_backslashes, preserve_trailing_newlines=False)

        with (
            TemplateContext(template_value=expression, templar=self, options=options, _render_jinja_const_template=_render_jinja_const_template) as ctx,
            DeprecatedAccessAuditContext.when(ctx.is_top_level),
        ):
            try:
                if not TrustedAsTemplate.is_tagged_on(expression):
                    raise TemplateTrustCheckFailedError(obj=expression)

                template_variables = ChainMap(local_variables, self.available_variables) if local_variables else self.available_variables
                compiled_template = self._compile_expression(expression, options)

                template_result = compiled_template(template_variables)
                template_result = self._post_render_mutation(expression, template_result, options)
            except Exception as ex:
                template_result = defer_template_error(ex, expression, is_expression=True)

            return self._finalize_top_level_template_result(expression, options, template_result, is_expression=True)

    _BROKEN_CONDITIONAL_ALLOWED_FRAGMENT = 'Broken conditionals are currently allowed because the `ALLOW_BROKEN_CONDITIONALS` configuration option is enabled.'
    _CONDITIONAL_AS_TEMPLATE_MSG = 'Conditionals should not be surrounded by templating delimiters such as {{ }} or {% %}.'

    def _strip_conditional_handle_empty(self, conditional) -> t.Any:
        """
        Strips leading/trailing whitespace from the input expression.
        If `ALLOW_BROKEN_CONDITIONALS` is enabled, None/empty is coerced to True (legacy behavior, deprecated).
        Otherwise, None/empty results in a broken conditional error being raised.
        """
        if isinstance(conditional, str):
            # Leading/trailing whitespace on conditional expressions is not a problem, except we can't tell if the expression is empty (which *is* a problem).
            # Always strip conditional input strings. Neither conditional expressions nor all-template conditionals have legit reasons to preserve
            # surrounding whitespace, and they complicate detection and processing of all-template fallback cases.
            conditional = AnsibleTagHelper.tag_copy(conditional, conditional.strip())

        if conditional in (None, ''):
            # deprecated backward-compatible behavior; None/empty input conditionals are always True
            if _TemplateConfig.allow_broken_conditionals:
                _display.deprecated(
                    msg='Empty conditional expression was evaluated as True.',
                    help_text=self._BROKEN_CONDITIONAL_ALLOWED_FRAGMENT,
                    obj=conditional,
                    version='2.23',
                )

                return True

            raise AnsibleBrokenConditionalError("Empty conditional expressions are not allowed.", obj=conditional)

        return conditional

    def _normalize_and_evaluate_conditional(self, conditional: str | bool) -> t.Any:
        """Validate and normalize a conditional input value, resolving allowed embedded template cases and evaluating the resulting expression."""
        conditional = self._strip_conditional_handle_empty(conditional)

        # this must follow `_strip_conditional_handle_empty`, since None/empty are coerced to bool (deprecated)
        if type(conditional) is bool:  # pylint: disable=unidiomatic-typecheck
            return conditional

        try:
            if not isinstance(conditional, str):
                if _TemplateConfig.allow_broken_conditionals:
                    # because the input isn't a string, the result will never be a bool; the broken conditional warning in the caller will apply on the result
                    return self.template(conditional, mode=TemplateMode.ALWAYS_FINALIZE)

                raise AnsibleBrokenConditionalError(message="Conditional expressions must be strings.", obj=conditional)

            if is_possibly_all_template(conditional):
                # Indirection of trusted expressions is always allowed. If the expression appears to be entirely wrapped in template delimiters,
                # we must resolve it. e.g. `when: "{{ some_var_resolving_to_a_trusted_expression_string }}"`.
                # Some invalid meta-templating corner cases may sneak through here (e.g., `when: '{{ "foo" }} == {{ "bar" }}'`); these will
                # result in an untrusted expression error.
                result = self.template(conditional, mode=TemplateMode.ALWAYS_FINALIZE)
                result = self._strip_conditional_handle_empty(result)

                if not isinstance(result, str):
                    _display.deprecated(msg=self._CONDITIONAL_AS_TEMPLATE_MSG, obj=conditional, version='2.23')

                    return result  # not an expression

                # The only allowed use of templates for conditionals is for indirect usage of an expression.
                # Any other usage should simply be an expression, not an attempt at meta templating.
                expression = result
            else:
                expression = conditional

            # Disable escape_backslashes when processing conditionals, to maintain backwards compatibility.
            # This is necessary because conditionals were previously evaluated using {% %}, which was *NOT* affected by escape_backslashes.
            # Now that conditionals use expressions, they would be affected by escape_backslashes if it was not disabled.
            return self.evaluate_expression(expression, escape_backslashes=False, _render_jinja_const_template=True)

        except AnsibleUndefinedVariable as ex:
            # DTFIX-FUTURE: we're only augmenting the message for context here; once we have proper contextual tracking, we can dump the re-raise
            raise AnsibleUndefinedVariable("Error while evaluating conditional.", obj=conditional) from ex

    def evaluate_conditional(self, conditional: str | bool) -> bool:
        """
        Evaluate a trusted string expression or boolean and return its boolean result. A non-boolean result will raise `AnsibleBrokenConditionalError`.
        The ALLOW_BROKEN_CONDITIONALS configuration option can temporarily relax this requirement, allowing truthy conditionals to succeed.
        """
        result = self._normalize_and_evaluate_conditional(conditional)

        if isinstance(result, bool):
            return result

        bool_result = bool(result)

        result_origin = Origin.get_tag(result) or Origin.UNKNOWN

        msg = (
            f'Conditional result ({bool_result}) was derived from value of type {native_type_name(result)!r} at {str(result_origin)!r}. '
            'Conditionals must have a boolean result.'
        )

        if _TemplateConfig.allow_broken_conditionals:
            _display.deprecated(
                msg=msg,
                obj=conditional,
                help_text=self._BROKEN_CONDITIONAL_ALLOWED_FRAGMENT,
                version='2.23',
            )

            return bool_result

        raise AnsibleBrokenConditionalError(msg, obj=conditional)

    @staticmethod
    def _trust_check(value: str, skip_handler: bool = False) -> bool:
        """
        Return True if the given value is trusted for templating, otherwise return False.
        When the value is not trusted, a warning or error may be generated, depending on configuration.
        """
        if TrustedAsTemplate.is_tagged_on(value):
            return True

        if not skip_handler:
            with Skippable, _TemplateConfig.untrusted_template_handler.handle(TemplateTrustCheckFailedError, skip_on_ignore=True):
                raise TemplateTrustCheckFailedError(obj=value)

        return False
