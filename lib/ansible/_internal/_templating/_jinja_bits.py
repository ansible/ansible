from __future__ import annotations

import ast
import collections.abc as c
import dataclasses
import enum
import pathlib
import tempfile
import types
import typing as t

from collections import ChainMap

import jinja2.nodes

from jinja2 import pass_context, defaults, TemplateSyntaxError, FileSystemLoader
from jinja2.environment import Environment, Template, TemplateModule, TemplateExpression
from jinja2.compiler import Frame
from jinja2.lexer import TOKEN_VARIABLE_BEGIN, TOKEN_VARIABLE_END, TOKEN_STRING, Lexer
from jinja2.nativetypes import NativeCodeGenerator
from jinja2.nodes import Const, EvalContext
from jinja2.runtime import Context, Macro
from jinja2.sandbox import SandboxedEnvironment
from jinja2.utils import missing, LRUCache

from ansible.utils.display import Display
from ansible.errors import AnsibleVariableTypeError, AnsibleTemplateSyntaxError, AnsibleTemplateError
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils._internal._datatag import (
    _AnsibleTaggedDict,
    _AnsibleTaggedList,
    _AnsibleTaggedTuple,
    _AnsibleTaggedStr,
    AnsibleTagHelper,
)

from ansible._internal._errors._handler import ErrorAction
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate

from ._access import AnsibleAccessContext
from ._datatag import _JinjaConstTemplate
from ._utils import LazyOptions
from ._jinja_common import (
    MarkerError,
    Marker,
    CapturedExceptionMarker,
    UndefinedMarker,
    _TemplateConfig,
    TruncationMarker,
    validate_arg_type,
    JinjaCallContext,
    _SandboxMode,
)
from ._jinja_plugins import JinjaPluginIntercept, _query, _lookup, _now, _wrap_plugin_output, get_first_marker_arg, _DirectCall, _jinja_const_template_warning
from ._lazy_containers import (
    _AnsibleLazyTemplateMixin,
    _AnsibleLazyTemplateDict,
    _AnsibleLazyTemplateList,
    _AnsibleLazyAccessTuple,
    lazify_container_args,
    lazify_container_kwargs,
    lazify_container,
    register_known_types,
)
from ._utils import Omit, TemplateContext, PASS_THROUGH_SCALAR_VAR_TYPES

from ansible.module_utils._internal._json._profiles import _json_subclassable_scalar_types
from ansible.module_utils import _internal
from ansible.module_utils._internal import _ambient_context, _dataclass_validation
from ansible.plugins.loader import filter_loader, test_loader
from ansible.vars.hostvars import HostVars, HostVarsVars
from ...module_utils.datatag import native_type_name

JINJA2_OVERRIDE = '#jinja2:'
"""
String values prefixed with this sequence are interpreted as templates, even without template delimiters.
The values following this prefix up to the first newline are parsed as Jinja2 template overrides.
To include this literal value at the start of a string, a space or other character must precede it.
"""

JINJA_KEYWORDS = frozenset(
    {
        # scalar singletons (see jinja2.nodes.Name.can_assign)
        'true',
        'false',
        'none',
        'True',
        'False',
        'None',
        # other
        'not',  # unary operator always applicable to names
    }
)
"""Names which have special meaning to Jinja and cannot be resolved as variable names."""

display = Display()


@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class TemplateOverrides:
    DEFAULT: t.ClassVar[t.Self]

    block_start_string: str = defaults.BLOCK_START_STRING
    block_end_string: str = defaults.BLOCK_END_STRING
    variable_start_string: str = defaults.VARIABLE_START_STRING
    variable_end_string: str = defaults.VARIABLE_END_STRING
    comment_start_string: str = defaults.COMMENT_START_STRING
    comment_end_string: str = defaults.COMMENT_END_STRING
    line_statement_prefix: str | None = defaults.LINE_STATEMENT_PREFIX
    line_comment_prefix: str | None = defaults.LINE_COMMENT_PREFIX
    trim_blocks: bool = True  # AnsibleEnvironment overrides this default, so don't use the Jinja default here
    lstrip_blocks: bool = defaults.LSTRIP_BLOCKS
    newline_sequence: t.Literal['\n', '\r\n', '\r'] = defaults.NEWLINE_SEQUENCE
    keep_trailing_newline: bool = defaults.KEEP_TRAILING_NEWLINE

    def __post_init__(self) -> None:
        pass  # overridden by _dataclass_validation._inject_post_init_validation

    def _post_validate(self) -> None:
        if not (self.block_start_string != self.variable_start_string != self.comment_start_string != self.block_start_string):
            raise ValueError('Block, variable and comment start strings must be different.')

    def overlay_kwargs(self) -> dict[str, t.Any]:
        """
        Return a dictionary of arguments for passing to Environment.overlay.
        The dictionary will be empty if all fields have their default value.
        """
        # DTFIX-FUTURE: calculate default/non-default during __post_init__
        fields = [(field, getattr(self, field.name)) for field in dataclasses.fields(self)]
        kwargs = {field.name: value for field, value in fields if value != field.default}

        return kwargs

    def _contains_start_string(self, value: str) -> bool:
        """Returns True if the given value contains a variable, block or comment start string."""
        # DTFIX-FUTURE: this is inefficient, use a compiled regex instead

        for marker in (self.block_start_string, self.variable_start_string, self.comment_start_string):
            if marker in value:
                return True

        return False

    def _starts_and_ends_with_jinja_delimiters(self, value: str) -> bool:
        """Returns True if the given value starts and ends with Jinja variable, block or comment delimiters."""
        # DTFIX-FUTURE: this is inefficient, use a compiled regex instead

        for marker in (self.block_start_string, self.variable_start_string, self.comment_start_string):
            if value.startswith(marker):
                break
        else:
            return False

        for marker in (self.block_end_string, self.variable_end_string, self.comment_end_string):
            if value.endswith(marker):
                return True

        return False

    def _extract_template_overrides(self, template: str) -> tuple[str, TemplateOverrides]:
        if template.startswith(JINJA2_OVERRIDE):
            eol = template.find('\n')

            if eol == -1:
                raise ValueError(f"Missing newline after {JINJA2_OVERRIDE!r} override.")

            line = template[len(JINJA2_OVERRIDE) : eol]
            template = template[eol + 1 :]
            override_kwargs = {}

            for pair in line.split(','):
                if not pair.strip():
                    raise ValueError(f"Empty {JINJA2_OVERRIDE!r} override pair not allowed.")

                if ':' not in pair:
                    raise ValueError(f"Missing key-value separator `:` in {JINJA2_OVERRIDE!r} override pair {pair!r}.")

                key, val = pair.split(':', 1)
                key = key.strip()

                if key not in _TEMPLATE_OVERRIDE_FIELD_NAMES:
                    raise ValueError(f"Invalid {JINJA2_OVERRIDE!r} override key {key!r}.")

                override_kwargs[key] = ast.literal_eval(val)

            overrides = dataclasses.replace(self, **override_kwargs)
        else:
            overrides = self

        return template, overrides

    def merge(self, kwargs: dict[str, t.Any] | None, /) -> TemplateOverrides:
        """Return a new instance based on the current instance with the given kwargs overridden."""
        if kwargs:
            return self.from_kwargs(dataclasses.asdict(self) | kwargs)

        return self

    @classmethod
    def from_kwargs(cls, kwargs: dict[str, t.Any] | None, /) -> TemplateOverrides:
        """TemplateOverrides instance factory; instances resolving to all default values will instead return the DEFAULT singleton for optimization."""
        if kwargs:
            value = cls(**kwargs)

            if value.overlay_kwargs():
                return value

        return cls.DEFAULT


_dataclass_validation.inject_post_init_validation(TemplateOverrides, allow_subclasses=True)

TemplateOverrides.DEFAULT = TemplateOverrides()

_TEMPLATE_OVERRIDE_FIELD_NAMES: t.Final[tuple[str, ...]] = tuple(sorted(field.name for field in dataclasses.fields(TemplateOverrides)))


class AnsibleContext(Context):
    """
    A custom context which intercepts resolve_or_missing() calls and
    runs them through AnsibleAccessContext. This allows usage of variables
    to be tracked. If needed, values can also be modified before being returned.
    """

    environment: AnsibleEnvironment  # narrow the type specified by the base

    def __init__(self, *args, **kwargs):
        super(AnsibleContext, self).__init__(*args, **kwargs)

    __repr__ = object.__repr__  # prevent Jinja from dumping vars in case this gets repr'd

    def get_all(self):
        """
        Override Jinja's default get_all to return all vars in the context as a ChainMap with a mutable layer at the bottom.
        This provides some isolation against accidental changes to inherited variable contexts without requiring copies.
        """
        layers = []

        if self.vars:
            layers.append(self.vars)
        if self.parent:
            layers.append(self.parent)

        # HACK: always include a sacrificial plain-dict on the bottom layer, since Jinja's debug and stacktrace rewrite code invokes
        # `__setitem__` outside a call context; this will ensure that it always occurs on a plain dict instead of a lazy one.
        return ChainMap({}, *layers)

    # noinspection PyShadowingBuiltins
    def derived(self, locals: t.Optional[t.Dict[str, t.Any]] = None) -> Context:
        # this is a clone of Jinja's impl of derived, but using our lazy-aware _new_context

        context = _new_context(
            environment=self.environment,
            template_name=self.name,
            blocks={},
            shared=True,
            jinja_locals=locals,
            jinja_vars=self.get_all(),
        )
        context.eval_ctx = self.eval_ctx
        context.blocks.update((k, list(v)) for k, v in self.blocks.items())
        return context

    def keys(self, *args, **kwargs):
        """Base Context delegates to `dict.keys` against `get_all`, which would fail since we return a ChainMap. No known usage."""
        raise NotImplementedError()

    def values(self, *args, **kwargs):
        """Base Context delegates to `dict.values` against `get_all`, which would fail since we return a ChainMap. No known usage."""
        raise NotImplementedError()

    def items(self, *args, **kwargs):
        """Base Context delegates to built-in `dict.items` against `get_all`, which would fail since we return a ChainMap. No known usage."""
        raise NotImplementedError()


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ArgSmuggler:
    """
    Utility wrapper to wrap/unwrap args passed to Jinja `Template.render` and `TemplateExpression.__call__`.
    e.g., see https://github.com/pallets/jinja/blob/3.1.3/src/jinja2/environment.py#L1296 and
    https://github.com/pallets/jinja/blob/3.1.3/src/jinja2/environment.py#L1566.
    """

    jinja_vars: c.Mapping[str, t.Any] | None

    @classmethod
    def package_jinja_vars(cls, jinja_vars: c.Mapping[str, t.Any]) -> dict[str, ArgSmuggler]:
        """Wrap the supplied vars dict in an ArgSmuggler to prevent premature templating from Jinja's internal dict copy."""
        return dict(_smuggled_vars=ArgSmuggler(jinja_vars=jinja_vars))

    @classmethod
    def extract_jinja_vars(cls, maybe_smuggled_vars: c.Mapping[str, t.Any] | None) -> c.Mapping[str, t.Any]:
        """
        If the supplied vars dict contains an ArgSmuggler instance with the expected key, unwrap it and return the smuggled value.
        Otherwise, return the supplied dict as-is.
        """
        if maybe_smuggled_vars and ((smuggler := maybe_smuggled_vars.get('_smuggled_vars')) and isinstance(smuggler, ArgSmuggler)):
            return smuggler.jinja_vars

        return maybe_smuggled_vars


class AnsibleTemplateExpression:
    """
    Wrapper around Jinja's TemplateExpression for converting MarkerError back into Marker.
    This is needed to make expression error handling consistent with templates, since Jinja does not support a custom type for Environment.compile_expression.
    """

    def __init__(self, template_expression: TemplateExpression) -> None:
        self._template_expression = template_expression

    def __call__(self, jinja_vars: c.Mapping[str, t.Any]) -> t.Any:
        try:
            return self._template_expression(ArgSmuggler.package_jinja_vars(jinja_vars))
        except MarkerError as ex:
            return ex.source


class AnsibleTemplate(Template):
    """
    A helper class, which prevents Jinja2 from running lazy containers through dict().
    """

    _python_source_temp_path: pathlib.Path | None = None

    def __del__(self):
        # DTFIX-FUTURE: this still isn't working reliably; something else must be keeping the template object alive
        if self._python_source_temp_path:
            self._python_source_temp_path.unlink(missing_ok=True)

    def __call__(self, jinja_vars: c.Mapping[str, t.Any]) -> t.Any:
        return self.render(ArgSmuggler.package_jinja_vars(jinja_vars))

    # noinspection PyShadowingBuiltins
    def new_context(
        self,
        vars: c.Mapping[str, t.Any] | None = None,
        shared: bool = False,
        locals: c.Mapping[str, t.Any] | None = None,
    ) -> Context:
        return _new_context(
            environment=self.environment,
            template_name=self.name,
            blocks=self.blocks,
            shared=shared,
            jinja_locals=locals,
            jinja_vars=ArgSmuggler.extract_jinja_vars(vars),
            jinja_globals=self.globals,
        )


class AnsibleCodeGenerator(NativeCodeGenerator):
    """
    Custom code generation behavior to support deprecated Ansible features and fill in gaps in Jinja native.
    This can be removed once the deprecated Ansible features are removed and the native fixes are upstreamed in Jinja.
    """

    def _output_const_repr(self, group: t.Iterable[t.Any]) -> str:
        """
        Prevent Jinja's code generation from stringifying single nodes before generating its repr.
        This complements the behavioral change in AnsibleEnvironment.concat which returns single nodes without stringifying them.
        """
        # DTFIX-FUTURE: contribute this upstream as a fix to Jinja's native support
        group_list = list(group)

        if len(group_list) == 1:
            return repr(group_list[0])

        # NB: This is slightly more efficient than Jinja's _output_const_repr, which generates a throw-away list instance to pass to join.
        #     Before removing this, ensure that upstream Jinja has this change.
        return repr("".join(map(str, group_list)))

    def visit_Const(self, node: Const, frame: Frame) -> None:
        """
        Override Jinja's visit_Const to inject a runtime call to AnsibleEnvironment._access_const for constant strings that are possibly templates, which
        may require special handling at runtime. See that method for details. An example that hits this path:
        {{ lookup("file", "{{ output_dir }}/bla") }}
        """
        value = node.as_const(frame.eval_ctx)

        if _TemplateConfig.allow_embedded_templates and type(value) is str and is_possibly_template(value):  # pylint: disable=unidiomatic-typecheck
            # deprecated: description='embedded Jinja constant string template support' core_version='2.23'
            self.write(f'environment._access_const({value!r})')
        else:
            # NB: This is actually more efficient than Jinja's visit_Const, which contains obsolete (as of Py2.7/3.1) float conversion instance checks. Before
            #     removing this override entirely, ensure that upstream Jinja has removed the obsolete code.
            #     See https://docs.python.org/release/2.7/whatsnew/2.7.html#python-3-1-features for more details.
            self.write(repr(value))


@pass_context
def _ansible_finalize(_ctx: AnsibleContext, value: t.Any) -> t.Any:
    """
    This function is called by Jinja with the result of each variable template block (e.g., {{ }}) encountered in a template.
    The pass_context decorator prevents finalize from being called on constants at template compile time.
    The passed in AnsibleContext is unused -- it is the result of using the pass_context decorator.
    The important part for us is that this blocks constant folding, which ensures our custom visit_Const is used.
    It also ensures that template results are wrapped in lazy containers.
    """
    return lazify_container(value)


@dataclasses.dataclass(kw_only=True, slots=True)
class _TemplateCompileContext(_ambient_context.AmbientContextBase):
    """
    This context is active during Ansible's explicit compilation of templates/expressions, but not during Jinja's runtime compilation.
    Historically, Ansible-specific pre-processing like `escape_backslashes` was not applied to imported/included templates.
    """

    escape_backslashes: bool


class _CompileStateSmugglingCtx(_ambient_context.AmbientContextBase):
    template_source: str | None = None
    python_source: str | None = None
    python_source_temp_path: pathlib.Path | None = None


class AnsibleLexer(Lexer):
    """
    Lexer override to escape backslashes in string constants within Jinja expressions; prevents Jinja from double-escaping them.

    NOTE: This behavior is only applied to string constants within Jinja expressions (eg {{ "c:\newfile" }}), *not* statements ("{% set foo="c:\\newfile" %}").

    This is useful when templates are sourced from YAML double-quoted strings, as it avoids having backslashes processed twice: first by the
    YAML parser, and then again by the Jinja parser. Instead, backslashes are only processed by YAML.

    Example YAML:

    - debug:
        msg: "Test Case 1\\3; {{ test1_name | regex_replace('^(.*)_name$', '\\1')}}"

    Since the outermost YAML string is double-quoted, the YAML parser converts the double backslashes to single backslashes. Without escaping, Jinja
    would see only a single backslash ('\1') while processing the embedded template expression, interpret it as an escape sequence, and convert it
    to '\x01' (ASCII "SOH"). This is clearly not the intended `\1` backreference argument to the `regex_replace` filter (which would require the
    double-escaped string '\\\\1' to yield the intended result).

    Since the "\\3" in the input YAML was not part of a template expression, the YAML-parsed "\3" remains after Jinja rendering. This would be
    confusing for playbook authors, as different escaping rules would be needed inside and outside the template expression.

    When templates are not sourced from YAML, escaping backslashes will prevent use of backslash escape sequences such as "\n" and "\t".

    See relevant Jinja lexer impl at e.g.: https://github.com/pallets/jinja/blob/3.1.2/src/jinja2/lexer.py#L646-L653.
    """

    def tokeniter(self, *args, **kwargs) -> t.Iterator[t.Tuple[int, str, str]]:
        """Pre-escape backslashes in expression ({{ }}) raw string constants before Jinja's Lexer.wrap() can interpret them as ASCII escape sequences."""
        token_stream = super().tokeniter(*args, **kwargs)

        # if we have no context, Jinja's doing a nested compile at runtime (eg, import/include); historically, no backslash escaping is performed
        if not (tcc := _TemplateCompileContext.current(optional=True)) or not tcc.escape_backslashes:
            yield from token_stream
            return

        in_variable = False

        for token in token_stream:
            token_type = token[1]

            if token_type == TOKEN_VARIABLE_BEGIN:
                in_variable = True
            elif token_type == TOKEN_VARIABLE_END:
                in_variable = False
            elif in_variable and token_type == TOKEN_STRING:
                token = token[0], token_type, token[2].replace('\\', '\\\\')

            yield token


def defer_template_error(ex: Exception, variable: t.Any, *, is_expression: bool) -> Marker:
    if not ex.__traceback__:
        raise AssertionError('ex must be a previously raised exception')

    if isinstance(ex, MarkerError):
        return ex.source

    exception_to_raise = create_template_error(ex, variable, is_expression)

    if exception_to_raise is ex:
        return CapturedExceptionMarker(ex)  # capture the previously raised exception

    try:
        raise exception_to_raise from ex  # raise the newly synthesized exception before capturing it
    except Exception as captured_ex:
        return CapturedExceptionMarker(captured_ex)


def create_template_error(ex: Exception, variable: t.Any, is_expression: bool) -> AnsibleTemplateError:
    if isinstance(ex, AnsibleTemplateError):
        exception_to_raise = ex
    else:
        kind = "expression" if is_expression else "template"
        ex_type = AnsibleTemplateError  # always raise an AnsibleTemplateError/subclass

        if isinstance(ex, RecursionError):
            msg = f"Recursive loop detected in {kind}."
        elif isinstance(ex, TemplateSyntaxError):
            msg = f"Syntax error in {kind}."

            if is_expression and is_possibly_template(variable):
                msg += " Template delimiters are not supported in expressions."

            ex_type = AnsibleTemplateSyntaxError
        else:
            msg = f"Error rendering {kind}."

        exception_to_raise = ex_type(msg, obj=variable)

    if exception_to_raise.obj is None:
        exception_to_raise.obj = TemplateContext.current().template_value

    # DTFIX-FUTURE: Look through the TemplateContext hierarchy to find the most recent non-template
    #   caller and use that for origin when no origin is available on obj. This could be useful for situations where the template
    #   was embedded in a plugin, or a plugin is otherwise responsible for losing the origin and/or trust. We can't just use the first
    #   non-template caller as that will lead to false positives for re-entrant calls (e.g. template plugins that call into templar).

    return exception_to_raise


# DTFIX1: implement CapturedExceptionMarker deferral support on call (and lookup), filter/test plugins, etc.
#                also update the protomatter integration test once this is done (the test was written differently since this wasn't done yet)

_BUILTIN_FILTER_ALIASES: dict[str, str] = {}
_BUILTIN_TEST_ALIASES: dict[str, str] = {
    '!=': 'ne',
    '<': 'lt',
    '<=': 'le',
    '==': 'eq',
    '>': 'gt',
    '>=': 'ge',
}

_BUILTIN_FILTERS = filter_loader._wrap_funcs(defaults.DEFAULT_FILTERS, _BUILTIN_FILTER_ALIASES)
_BUILTIN_TESTS = test_loader._wrap_funcs(t.cast(dict[str, t.Callable], defaults.DEFAULT_TESTS), _BUILTIN_TEST_ALIASES)


class AnsibleEnvironment(SandboxedEnvironment):
    """
    Our custom environment, which simply allows us to override the class-level
    values for the Template and Context classes used by jinja2 internally.
    """

    context_class = AnsibleContext
    template_class = AnsibleTemplate
    code_generator_class = AnsibleCodeGenerator
    intercepted_binops = frozenset(('eq',))

    _allowed_unsafe_attributes: dict[str, type | tuple[type, ...]] = dict(
        # Allow bitwise operations on int until bitwise filters are available.
        # see: https://github.com/ansible/ansible/issues/85204
        __and__=int,
        __lshift__=int,
        __or__=int,
        __rshift__=int,
        __xor__=int,
    )
    """
    Attributes which are considered unsafe by `is_safe_attribute`, which should be allowed when used on specific types.
    The attributes allowed here are intended only for backward compatibility with existing use cases.
    They should be exposed as filters in a future release and eventually deprecated.
    """

    _lexer_cache = LRUCache(50)

    # DTFIX-FUTURE: bikeshed a name/mechanism to control template debugging
    _debuggable_template_source = False
    _debuggable_template_source_path: pathlib.Path = pathlib.Path(__file__).parent.parent.parent.parent / '.template_debug_source'

    def __init__(self, *args, ansible_basedir: str | None = None, **kwargs) -> None:
        if ansible_basedir:
            kwargs.update(loader=FileSystemLoader(ansible_basedir))

        super().__init__(*args, extensions=_TemplateConfig.jinja_extensions, **kwargs)

        self.filters = JinjaPluginIntercept(_BUILTIN_FILTERS, filter_loader)  # type: ignore[assignment]
        self.tests = JinjaPluginIntercept(_BUILTIN_TESTS, test_loader)  # type: ignore[assignment,arg-type]

        # future Jinja releases may default-enable autoescape; force-disable to prevent the problems it could cause
        # see https://github.com/pallets/jinja/blob/3.1.2/docs/api.rst?plain=1#L69
        self.autoescape = False

        self.trim_blocks = True

        self.undefined = UndefinedMarker
        self.finalize = _ansible_finalize

        self.globals.update(
            range=range,  # the sandboxed environment limits range in ways that may cause us problems; use the real Python one
            now=_now,
            undef=_undef,
            omit=Omit,
            lookup=_lookup,
            query=_query,
            q=_query,
        )

        # Disabling the optimizer prevents compile-time constant expression folding, which prevents our
        # visit_Const recursive inline template expansion tricks from working in many cases where Jinja's
        # ignorance of our embedded templates are optimized away as fully-constant expressions,
        # eg {{ "{{'hi'}}" == "hi" }}. As of Jinja ~3.1, this specifically avoids cases where the @optimizeconst
        # visitor decorator performs constant folding, which bypasses our visit_Const impl and causes embedded
        # templates to be lost.
        # See also optimizeconst impl: https://github.com/pallets/jinja/blob/3.1.0/src/jinja2/compiler.py#L48-L49
        self.optimized = False

    def get_template(
        self,
        name: str | Template,
        parent: str | None = None,
        globals: c.MutableMapping[str, t.Any] | None = None,
    ) -> Template:
        """Ensures that templates built via `get_template` are also source debuggable."""
        with _CompileStateSmugglingCtx.when(self._debuggable_template_source) as ctx:
            template_obj = t.cast(AnsibleTemplate, super().get_template(name, parent, globals))

            if isinstance(ctx, _CompileStateSmugglingCtx):  # only present if debugging is enabled
                template_obj._python_source_temp_path = ctx.python_source_temp_path  # facilitate deletion of the temp file when template_obj is deleted

            return template_obj

    def is_safe_attribute(self, obj: t.Any, attr: str, value: t.Any) -> bool:
        # deprecated: description="remove relaxed template sandbox mode support" core_version="2.23"
        if _TemplateConfig.sandbox_mode == _SandboxMode.ALLOW_UNSAFE_ATTRIBUTES:
            return True

        if (type_or_tuple := self._allowed_unsafe_attributes.get(attr)) and isinstance(obj, type_or_tuple):
            return True

        return super().is_safe_attribute(obj, attr, value)

    @property
    def lexer(self) -> AnsibleLexer:
        """Return/cache an AnsibleLexer with settings from the current AnsibleEnvironment"""
        # DTFIX-FUTURE: optimization - we should pre-generate the default cached lexer before forking, not leave it to chance (e.g. simple playbooks)
        key = tuple(getattr(self, name) for name in _TEMPLATE_OVERRIDE_FIELD_NAMES)

        lex = self._lexer_cache.get(key)

        if lex is None:
            self._lexer_cache[key] = lex = AnsibleLexer(self)

        return lex

    def call_filter(
        self,
        name: str,
        value: t.Any,
        args: c.Sequence[t.Any] | None = None,
        kwargs: c.Mapping[str, t.Any] | None = None,
        context: Context | None = None,
        eval_ctx: EvalContext | None = None,
    ) -> t.Any:
        """
        Ensure that filters directly invoked by plugins will see non-templating lazy containers.
        Without this, `_wrap_filter` will wrap `args` and `kwargs` in templating lazy containers.
        This provides consistency with plugin output handling by preventing auto-templating of trusted templates passed in native containers.
        """
        # DTFIX-FUTURE: need better logic to handle non-list/non-dict inputs for args/kwargs
        args = _AnsibleLazyTemplateMixin._try_create(list(args or []), LazyOptions.SKIP_TEMPLATES)
        kwargs = _AnsibleLazyTemplateMixin._try_create(kwargs, LazyOptions.SKIP_TEMPLATES)

        return super().call_filter(name, value, args, kwargs, context, eval_ctx)

    def call_test(
        self,
        name: str,
        value: t.Any,
        args: c.Sequence[t.Any] | None = None,
        kwargs: c.Mapping[str, t.Any] | None = None,
        context: Context | None = None,
        eval_ctx: EvalContext | None = None,
    ) -> t.Any:
        """
        Ensure that tests directly invoked by plugins will see non-templating lazy containers.
        Without this, `_wrap_test` will wrap `args` and `kwargs` in templating lazy containers.
        This provides consistency with plugin output handling by preventing auto-templating of trusted templates passed in native containers.
        """
        # DTFIX-FUTURE: need better logic to handle non-list/non-dict inputs for args/kwargs
        args = _AnsibleLazyTemplateMixin._try_create(list(args or []), LazyOptions.SKIP_TEMPLATES)
        kwargs = _AnsibleLazyTemplateMixin._try_create(kwargs, LazyOptions.SKIP_TEMPLATES)

        return super().call_test(name, value, args, kwargs, context, eval_ctx)

    def compile_expression(self, source: str, *args, **kwargs) -> TemplateExpression:
        # compile_expression parses and passes the tree to from_string; for debug support, activate the context here to capture the intermediate results
        with _CompileStateSmugglingCtx.when(self._debuggable_template_source) as ctx:
            if isinstance(ctx, _CompileStateSmugglingCtx):  # only present if debugging is enabled
                ctx.template_source = source

            return super().compile_expression(source, *args, **kwargs)

    def from_string(self, source: str | jinja2.nodes.Template, *args, **kwargs) -> AnsibleTemplate:
        # if debugging is enabled, use existing context when present (e.g., from compile_expression)
        current_ctx = _CompileStateSmugglingCtx.current(optional=True) if self._debuggable_template_source else None

        with _CompileStateSmugglingCtx.when(self._debuggable_template_source and not current_ctx) as new_ctx:
            template_obj = t.cast(AnsibleTemplate, super().from_string(source, *args, **kwargs))

            if isinstance(ctx := current_ctx or new_ctx, _CompileStateSmugglingCtx):  # only present if debugging is enabled
                template_obj._python_source_temp_path = ctx.python_source_temp_path  # facilitate deletion of the temp file when template_obj is deleted

        return template_obj

    def _parse(self, source: str, *args, **kwargs) -> jinja2.nodes.Template:
        if csc := _CompileStateSmugglingCtx.current(optional=True):
            csc.template_source = source

        return super()._parse(source, *args, **kwargs)

    def _compile(self, source: str, filename: str) -> types.CodeType:
        if csc := _CompileStateSmugglingCtx.current(optional=True):
            origin = Origin.get_tag(csc.template_source) or Origin.UNKNOWN

            source = '\n'.join(
                (
                    "import sys; breakpoint() if type(sys.breakpointhook) is not type(breakpoint) else None",
                    f"# original template source from {str(origin)!r}: ",
                    '\n'.join(f'# {line}' for line in (csc.template_source or '').splitlines()),
                    source,
                )
            )

            source_temp_dir = self._debuggable_template_source_path
            source_temp_dir.mkdir(parents=True, exist_ok=True)

            with tempfile.NamedTemporaryFile(dir=source_temp_dir, mode='w', suffix='.py', prefix='j2_src_', delete=False) as source_file:
                filename = source_file.name

                source_file.write(source)
                source_file.flush()

            csc.python_source = source
            csc.python_source_temp_path = pathlib.Path(filename)

        res = super()._compile(source, filename)

        return res

    @staticmethod
    def concat(nodes: t.Iterable[t.Any]) -> t.Any:  # type: ignore[override]
        node_list = list(_flatten_nodes(nodes))

        if not node_list:
            return None

        # this code is complemented by our tweaked CodeGenerator _output_const_repr that ensures that literal constants
        # in templates aren't double-repr'd in the generated code
        if len(node_list) == 1:
            return node_list[0]

        # In order to ensure that all markers are tripped, do a recursive finalize before we repr (otherwise we can end up
        # repr'ing a Marker). This requires two passes, but avoids the need for a parallel reimplementation of all repr methods.
        try:
            node_list = _finalize_template_result(node_list, FinalizeMode.CONCAT)
        except MarkerError as ex:
            return ex.source  # return the first Marker encountered

        return ''.join([to_text(v) for v in node_list])

    @staticmethod
    def _access_const(const_template: t.LiteralString) -> t.Any:
        """
        Called during template rendering on template-looking string constants embedded in the template.
        It provides the following functionality:
        * Propagates origin from the containing template.
        * For backward compatibility when embedded templates are enabled:
          * Conditionals - Renders embedded template constants and accesses the result. Warns on each constant immediately.
          * Non-conditionals - Tags constants for deferred rendering of templates in lookup terms. Warns on each constant during lookup invocation.
        """
        ctx = TemplateContext.current()

        if (tv := ctx.template_value) and (origin := Origin.get_tag(tv)):
            const_template = origin.tag(const_template)

        if ctx._render_jinja_const_template:
            _jinja_const_template_warning(const_template, is_conditional=True)

            result = ctx.templar.template(TrustedAsTemplate().tag(const_template))
            AnsibleAccessContext.current().access(result)
        else:
            # warnings will be issued when lookup terms processing occurs, to avoid false positives
            result = _JinjaConstTemplate().tag(const_template)

        return result

    def getitem(self, obj: t.Any, argument: t.Any) -> t.Any:
        value = super().getitem(obj, argument)

        AnsibleAccessContext.current().access(value)

        return value

    def getattr(self, obj: t.Any, attribute: str) -> t.Any:
        """
        Get `attribute` from the attributes of `obj`, falling back to items in `obj`.
        If no item was found, return a sandbox-specific `UndefinedMarker` if `attribute` is protected by the sandbox,
        otherwise return a normal `UndefinedMarker` instance.
        This differs from the built-in Jinja behavior which will not fall back to items if `attribute` is protected by the sandbox.
        """
        # example template that uses this: "{{ some.thing }}" -- obj is the "some" dict, attribute is "thing"

        is_safe = True

        try:
            value = getattr(obj, attribute)
        except AttributeError:
            value = _sentinel
        else:
            if not (is_safe := self.is_safe_attribute(obj, attribute, value)):
                value = _sentinel

        if value is _sentinel:
            try:
                value = obj[attribute]
            except (TypeError, LookupError):
                return self.undefined(obj=obj, name=attribute) if is_safe else self.unsafe_undefined(obj, attribute)

        AnsibleAccessContext.current().access(value)

        return value

    def call(
        self,
        __context: Context,
        __obj: t.Any,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> t.Any:
        if _DirectCall.is_marked(__obj):
            # Both `_lookup` and `_query` handle arg proxying and `Marker` args internally.
            # Performing either before calling them will interfere with that processing.
            return super().call(__context, __obj, *args, **kwargs)

        # Jinja's generated macro code handles Markers, so preemptive raise on Marker args and lazy retrieval should be disabled for the macro invocation.
        is_macro = isinstance(__obj, Macro)

        if not is_macro and (first_marker := get_first_marker_arg(args, kwargs)) is not None:
            return first_marker

        try:
            with JinjaCallContext(accept_lazy_markers=is_macro):
                call_res = super().call(__context, __obj, *lazify_container_args(args), **lazify_container_kwargs(kwargs))

                if __obj is range:
                    # Preserve the ability to do `range(1000000000) | random` by not converting range objects to lists.
                    # Historically, range objects were only converted on Jinja finalize and filter outputs, so they've always been floating around in templating
                    # code and visible to user plugins.
                    return call_res

                return _wrap_plugin_output(call_res)

        except MarkerError as ex:
            return ex.source


AnsibleTemplate.environment_class = AnsibleEnvironment

_DEFAULT_UNDEF = UndefinedMarker("Mandatory variable has not been overridden", _no_template_source=True)

_sentinel: t.Final[object] = object()


@_DirectCall.mark
def _undef(hint: str | None = None) -> UndefinedMarker:
    """Jinja2 global function (undef) for creating getting a `UndefinedMarker` instance, optionally with a custom hint."""
    validate_arg_type('hint', hint, (str, type(None)))

    if not hint:
        return _DEFAULT_UNDEF

    return UndefinedMarker(hint)


def _flatten_nodes(nodes: t.Iterable[t.Any]) -> t.Iterable[t.Any]:
    """
    Yield nodes from a potentially recursive iterable of nodes.
    The recursion is required to expand template imports (TemplateModule).
    Any exception raised while consuming a template node will be yielded as a Marker for that node.
    """
    iterator = iter(nodes)

    while True:
        try:
            node = next(iterator)
        except StopIteration:
            break
        except Exception as ex:
            yield defer_template_error(ex, TemplateContext.current().template_value, is_expression=False)
            # DTFIX-FUTURE: We should be able to determine if truncation occurred by having the code generator smuggle out the number of expected nodes.
            yield TruncationMarker()
        else:
            if type(node) is TemplateModule:  # pylint: disable=unidiomatic-typecheck
                yield from _flatten_nodes(node._body_stream)
            else:
                yield node


def _flatten_and_lazify_vars(mapping: c.Mapping) -> t.Iterable[c.Mapping]:
    """Prevent deeply-nested Jinja vars ChainMaps from being created by nested contexts and ensure that all top-level containers support lazy templating."""
    mapping_type = type(mapping)
    if mapping_type is ChainMap:
        # noinspection PyUnresolvedReferences
        for m in mapping.maps:
            yield from _flatten_and_lazify_vars(m)
    elif mapping_type is _AnsibleLazyTemplateDict:
        yield mapping
    elif mapping_type in (dict, _AnsibleTaggedDict):
        # don't propagate empty dictionary layers
        if mapping:
            yield _AnsibleLazyTemplateMixin._try_create(mapping)
    else:
        raise NotImplementedError(f"unsupported mapping type in Jinja vars: {mapping_type}")


def _new_context(
    *,
    environment: Environment,
    template_name: str | None,
    blocks: dict[str, t.Callable[[Context], c.Iterator[str]]],
    shared: bool = False,
    jinja_locals: c.Mapping[str, t.Any] | None = None,
    jinja_vars: c.Mapping[str, t.Any] | None = None,
    jinja_globals: c.MutableMapping[str, t.Any] | None = None,
) -> Context:
    """Override Jinja's context vars setup to use ChainMaps and containers that support lazy templating."""
    layers = []

    if jinja_locals:
        # Omit values set to Jinja's internal `missing` sentinel; they are locals that have not yet been
        # initialized in the current context, and should not be exposed to child contexts. e.g.: {% import 'a' as b with context %}.
        # The `b` local will be `missing` in the `a` context and should not be propagated as a local to the child context we're creating.
        layers.append(_AnsibleLazyTemplateMixin._try_create({k: v for k, v in jinja_locals.items() if v is not missing}))

    if jinja_vars:
        layers.extend(_flatten_and_lazify_vars(jinja_vars))

    if jinja_globals and not shared:
        # Even though we don't currently support templating globals, it's easier to ensure that everything is template-able rather than trying to
        # pick apart the ChainMaps to enforce non-template-able globals, or to risk things that *should* be template-able not being lazified.
        layers.extend(_flatten_and_lazify_vars(jinja_globals))

    if not layers:
        # ensure we have at least one layer (which should be lazy), since _flatten_and_lazify_vars eliminates most empty layers
        layers.append(_AnsibleLazyTemplateMixin._try_create({}))

    # only return a ChainMap if we're combining layers, or we have none
    parent = layers[0] if len(layers) == 1 else ChainMap(*layers)

    # the `parent` cast is only to satisfy Jinja's overly-strict type hint
    return environment.context_class(environment, t.cast(dict, parent), template_name, blocks, globals=jinja_globals)


def is_possibly_template(value: str, overrides: TemplateOverrides = TemplateOverrides.DEFAULT):
    """
    A lightweight check to determine if the given string looks like it contains a template, even if that template is invalid.
    Returns `True` if the given string starts with a Jinja overrides header or if it contains template start strings.
    """
    return value.startswith(JINJA2_OVERRIDE) or overrides._contains_start_string(value)


def is_possibly_all_template(value: str, overrides: TemplateOverrides = TemplateOverrides.DEFAULT):
    """
    A lightweight check to determine if the given string looks like it contains *only* a template, even if that template is invalid.
    Returns `True` if the given string starts with a Jinja overrides header or if it starts and ends with Jinja template delimiters.
    """
    return value.startswith(JINJA2_OVERRIDE) or overrides._starts_and_ends_with_jinja_delimiters(value)


class FinalizeMode(enum.Enum):
    TOP_LEVEL = enum.auto()
    CONCAT = enum.auto()


_FINALIZE_FAST_PATH_EXACT_MAPPING_TYPES = frozenset(
    (
        dict,
        _AnsibleTaggedDict,
        _AnsibleLazyTemplateDict,
        HostVars,
        HostVarsVars,
    )
)
"""Fast-path exact mapping types for finalization. These types bypass diagnostic warnings for type conversion."""

_FINALIZE_FAST_PATH_EXACT_ITERABLE_TYPES = frozenset(
    (
        list,
        _AnsibleTaggedList,
        _AnsibleLazyTemplateList,
        tuple,
        _AnsibleTaggedTuple,
        _AnsibleLazyAccessTuple,
    )
)
"""Fast-path exact iterable types for finalization. These types bypass diagnostic warnings for type conversion."""

_FINALIZE_DISALLOWED_EXACT_TYPES = frozenset((range,))
"""Exact types that cannot be finalized."""

# Jinja passes these into filters/tests via @pass_environment
register_known_types(
    AnsibleContext,
    AnsibleEnvironment,
    EvalContext,
)


def _finalize_dict(o: t.Any, mode: FinalizeMode) -> t.Iterator[tuple[t.Any, t.Any]]:
    for k, v in o.items():
        if v is not Omit:
            yield _finalize_template_result(k, mode), _finalize_template_result(v, mode)


def _finalize_list(o: t.Any, mode: FinalizeMode) -> t.Iterator[t.Any]:
    for v in o:
        if v is not Omit:
            yield _finalize_template_result(v, mode)


def _maybe_finalize_scalar(o: t.Any) -> t.Any:
    # DTFIX5: this should check all supported scalar subclasses, not just JSON ones (also, does the JSON serializer handle these cases?)
    for target_type in _json_subclassable_scalar_types:
        if not isinstance(o, target_type):
            continue

        match _TemplateConfig.unknown_type_conversion_handler.action:
            # we don't want to show the object value, and it can't be Origin-tagged; send the current template value for best effort
            case ErrorAction.WARNING:
                display.warning(
                    msg=f'Type {native_type_name(o)!r} is unsupported in variable storage, converting to {native_type_name(target_type)!r}.',
                    obj=TemplateContext.current(optional=True).template_value,
                )
            case ErrorAction.ERROR:
                raise AnsibleVariableTypeError.from_value(obj=TemplateContext.current(optional=True).template_value)

        return target_type(o)

    return None


def _finalize_fallback_collection(
    o: t.Any,
    mode: FinalizeMode,
    finalizer: t.Callable[[t.Any, FinalizeMode], t.Iterator],
    target_type: type[list | dict],
) -> t.Collection[t.Any]:
    match _TemplateConfig.unknown_type_conversion_handler.action:
        # we don't want to show the object value, and it can't be Origin-tagged; send the current template value for best effort
        case ErrorAction.WARNING:
            display.warning(
                msg=f'Type {native_type_name(o)!r} is unsupported in variable storage, converting to {native_type_name(target_type)!r}.',
                obj=TemplateContext.current(optional=True).template_value,
            )
        case ErrorAction.ERROR:
            raise AnsibleVariableTypeError.from_value(obj=TemplateContext.current(optional=True).template_value)

    return _finalize_collection(o, mode, finalizer, target_type)


def _finalize_collection(
    o: t.Any,
    mode: FinalizeMode,
    finalizer: t.Callable[[t.Any, FinalizeMode], t.Iterator],
    target_type: type[list | dict],
) -> t.Collection[t.Any]:
    return AnsibleTagHelper.tag(finalizer(o, mode), AnsibleTagHelper.tags(o), value_type=target_type)


def _finalize_template_result(o: t.Any, mode: FinalizeMode) -> t.Any:
    """Recurse the template result, rendering any encountered templates, converting containers to non-lazy versions."""
    # DTFIX5: add tests to ensure this method doesn't drift from allowed types
    o_type = type(o)

    # DTFIX-FUTURE: provide an optional way to check for trusted templates leaking out of templating (injected, but not passed through templar.template)

    if o_type is _AnsibleTaggedStr:
        return _JinjaConstTemplate.untag(o)  # prevent _JinjaConstTemplate from leaking into finalized results

    if o_type in PASS_THROUGH_SCALAR_VAR_TYPES:
        return o

    if o_type in _FINALIZE_FAST_PATH_EXACT_MAPPING_TYPES:  # silently convert known mapping types to dict
        return _finalize_collection(o, mode, _finalize_dict, dict)

    if o_type in _FINALIZE_FAST_PATH_EXACT_ITERABLE_TYPES:  # silently convert known sequence types to list
        return _finalize_collection(o, mode, _finalize_list, list)

    if o_type in Marker._concrete_subclasses:  # this early return assumes handle_marker follows our variable type rules
        return TemplateContext.current().templar.marker_behavior.handle_marker(o)

    if mode is not FinalizeMode.TOP_LEVEL:  # unsupported type (do not raise)
        return o

    if o_type in _FINALIZE_DISALLOWED_EXACT_TYPES:  # early abort for disallowed types that would otherwise be handled below
        raise AnsibleVariableTypeError.from_value(obj=o)

    if _internal.is_intermediate_mapping(o):  # since isinstance checks are slower, this is separate from the exact type check above
        return _finalize_fallback_collection(o, mode, _finalize_dict, dict)

    if _internal.is_intermediate_iterable(o):  # since isinstance checks are slower, this is separate from the exact type check above
        return _finalize_fallback_collection(o, mode, _finalize_list, list)

    if (result := _maybe_finalize_scalar(o)) is not None:
        return result

    raise AnsibleVariableTypeError.from_value(obj=o)
