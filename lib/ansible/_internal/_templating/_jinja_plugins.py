"""Jinja template plugins (filters, tests, lookups) and custom global functions."""

from __future__ import annotations

import collections.abc as c
import dataclasses
import datetime
import functools
import inspect
import re
import typing as t

from jinja2 import defaults

from ansible.module_utils._internal._ambient_context import AmbientContextBase
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible.plugins import AnsibleJinja2Plugin
from ansible.plugins.loader import lookup_loader, Jinja2Loader
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

from ._datatag import _JinjaConstTemplate
from ._errors import AnsibleTemplatePluginRuntimeError, AnsibleTemplatePluginLoadError, AnsibleTemplatePluginNotFoundError
from ._jinja_common import MarkerError, _TemplateConfig, get_first_marker_arg, Marker, JinjaCallContext, CapturedExceptionMarker
from ._lazy_containers import lazify_container_kwargs, lazify_container_args, lazify_container, _AnsibleLazyTemplateMixin
from ._utils import LazyOptions, TemplateContext

_display = Display()

_TCallable = t.TypeVar("_TCallable", bound=t.Callable)
_ITERATOR_TYPES: t.Final = (c.Iterator, c.ItemsView, c.KeysView, c.ValuesView, range)


class JinjaPluginIntercept(c.MutableMapping):
    """
    Simulated dict class that loads Jinja2Plugins at request
    otherwise all plugins would need to be loaded a priori.

    NOTE: plugin_loader still loads all 'builtin/legacy' at
    start so only collection plugins are really at request.
    """

    def __init__(self, jinja_builtins: c.Mapping[str, AnsibleJinja2Plugin], plugin_loader: Jinja2Loader):
        super(JinjaPluginIntercept, self).__init__()

        self._plugin_loader = plugin_loader
        self._jinja_builtins = jinja_builtins
        self._wrapped_funcs: dict[str, t.Callable] = {}

    def _wrap_and_set_func(self, instance: AnsibleJinja2Plugin) -> t.Callable:
        if self._plugin_loader.type == 'filter':
            plugin_func = self._wrap_filter(instance)
        else:
            plugin_func = self._wrap_test(instance)

        self._wrapped_funcs[instance._load_name] = plugin_func

        return plugin_func

    def __getitem__(self, key: str) -> t.Callable:
        instance: AnsibleJinja2Plugin | None = None
        plugin_func: t.Callable[..., t.Any] | None

        if plugin_func := self._wrapped_funcs.get(key):
            return plugin_func

        try:
            instance = self._plugin_loader.get(key)
        except KeyError:
            # The plugin name was invalid or no plugin was found by that name.
            pass
        except Exception as ex:
            # An unexpected exception occurred.
            raise AnsibleTemplatePluginLoadError(self._plugin_loader.type, key) from ex

        if not instance:
            try:
                instance = self._jinja_builtins[key]
            except KeyError:
                raise AnsibleTemplatePluginNotFoundError(self._plugin_loader.type, key) from None

        plugin_func = self._wrap_and_set_func(instance)

        return plugin_func

    def __setitem__(self, key: str, value: t.Callable) -> None:
        self._wrap_and_set_func(self._plugin_loader._wrap_func(key, key, value))

    def __delitem__(self, key):
        raise NotImplementedError()

    def __contains__(self, item: t.Any) -> bool:
        try:
            self.__getitem__(item)
        except AnsibleTemplatePluginLoadError:
            return True
        except AnsibleTemplatePluginNotFoundError:
            return False

        return True

    def __iter__(self):
        raise NotImplementedError()  # dynamic container

    def __len__(self):
        raise NotImplementedError()  # dynamic container

    @staticmethod
    def _invoke_plugin(instance: AnsibleJinja2Plugin, *args, **kwargs) -> t.Any:
        if not instance.accept_args_markers:
            if (first_marker := get_first_marker_arg(args, kwargs)) is not None:
                return first_marker

        try:
            with JinjaCallContext(accept_lazy_markers=instance.accept_lazy_markers):
                return instance.j2_function(*lazify_container_args(args), **lazify_container_kwargs(kwargs))
        except MarkerError as ex:
            return ex.source
        except Exception as ex:
            try:
                raise AnsibleTemplatePluginRuntimeError(instance.plugin_type, instance.ansible_name) from ex  # DTFIX-FUTURE: which name to use? PluginInfo?
            except AnsibleTemplatePluginRuntimeError as captured:
                return CapturedExceptionMarker(captured)

    def _wrap_test(self, instance: AnsibleJinja2Plugin) -> t.Callable:
        """Intercept point for all test plugins to ensure that args are properly templated/lazified."""

        @functools.wraps(instance.j2_function)
        def wrapper(*args, **kwargs) -> bool | Marker:
            result = self._invoke_plugin(instance, *args, **kwargs)

            if isinstance(result, Marker):
                return result

            if not isinstance(result, bool):
                template = TemplateContext.current().template_value

                _display.deprecated(
                    msg=f"The test plugin {instance.ansible_name!r} returned a non-boolean result of type {type(result)!r}. "
                    "Test plugins must have a boolean result.",
                    obj=template,
                    version="2.23",
                )

                result = bool(result)

            return result

        return wrapper

    def _wrap_filter(self, instance: AnsibleJinja2Plugin) -> t.Callable:
        """Intercept point for all filter plugins to ensure that args are properly templated/lazified."""

        @functools.wraps(instance.j2_function)
        def wrapper(*args, **kwargs) -> t.Any:
            result = self._invoke_plugin(instance, *args, **kwargs)
            result = _wrap_plugin_output(result)

            return result

        return wrapper


class _DirectCall:
    """Functions/methods marked `_DirectCall` bypass Jinja Environment checks for `Marker`."""

    _marker_attr: t.Final[str] = "_directcall"

    @classmethod
    def mark(cls, src: _TCallable) -> _TCallable:
        setattr(src, cls._marker_attr, True)
        return src

    @classmethod
    def is_marked(cls, value: t.Callable) -> bool:
        return callable(value) and getattr(value, cls._marker_attr, False)


@_DirectCall.mark
def _query(plugin_name: str, /, *args, **kwargs) -> t.Any:
    """wrapper for lookup, force wantlist true"""
    kwargs['wantlist'] = True
    return _invoke_lookup(plugin_name=plugin_name, lookup_terms=list(args), lookup_kwargs=kwargs)


@_DirectCall.mark
def _lookup(plugin_name: str, /, *args, **kwargs) -> t.Any:
    # convert the args tuple to a list, since some plugins make a poor assumption that `run.args` is a list
    return _invoke_lookup(plugin_name=plugin_name, lookup_terms=list(args), lookup_kwargs=kwargs)


@dataclasses.dataclass
class _LookupContext(AmbientContextBase):
    """Ambient context that wraps lookup execution, providing information about how it was invoked."""

    invoked_as_with: bool


@_DirectCall.mark
def _invoke_lookup(*, plugin_name: str, lookup_terms: list, lookup_kwargs: dict[str, t.Any], invoked_as_with: bool = False) -> t.Any:
    templar = TemplateContext.current().templar

    from ansible import template as _template

    try:
        instance: LookupBase | None = lookup_loader.get(plugin_name, loader=templar._loader, templar=_template.Templar._from_template_engine(templar))
    except Exception as ex:
        raise AnsibleTemplatePluginLoadError('lookup', plugin_name) from ex

    if instance is None:
        raise AnsibleTemplatePluginNotFoundError('lookup', plugin_name)

    # if the lookup doesn't understand `Marker` and there's at least one in the top level, short-circuit by returning the first one we found
    if not instance.accept_args_markers and (first_marker := get_first_marker_arg(lookup_terms, lookup_kwargs)) is not None:
        return first_marker

    # don't pass these through to the lookup
    wantlist = lookup_kwargs.pop('wantlist', False)
    errors = lookup_kwargs.pop('errors', 'strict')

    with JinjaCallContext(accept_lazy_markers=instance.accept_lazy_markers):
        try:
            if _TemplateConfig.allow_embedded_templates:
                # for backwards compat, only trust constant templates in lookup terms
                with JinjaCallContext(accept_lazy_markers=True):
                    # Force lazy marker support on for this call; the plugin's understanding is irrelevant, as is any existing context, since this backward
                    # compat code always understands markers.
                    lookup_terms = [templar.template(value) for value in _trust_jinja_constants(lookup_terms)]

                # since embedded template support is enabled, repeat the check for `Marker` on lookup_terms, since a template may render as a `Marker`
                if not instance.accept_args_markers and (first_marker := get_first_marker_arg(lookup_terms, {})) is not None:
                    return first_marker
            else:
                lookup_terms = AnsibleTagHelper.tag_copy(lookup_terms, (lazify_container(value) for value in lookup_terms), value_type=list)

            with _LookupContext(invoked_as_with=invoked_as_with):
                # The lookup context currently only supports the internal use-case where `first_found` requires extra info when invoked via `with_first_found`.
                # The context may be public API in the future, but for now, other plugins should not implement this kind of dynamic behavior,
                # though we're stuck with it for backward compatibility on `first_found`.
                lookup_res = instance.run(lookup_terms, variables=templar.available_variables, **lazify_container_kwargs(lookup_kwargs))

            # DTFIX-FUTURE: Consider allowing/requiring lookup plugins to declare how their result should be handled.
            #        Currently, there are multiple behaviors that are less than ideal and poorly documented (or not at all):
            #        * When `errors=warn` or `errors=ignore` the result is `None` unless `wantlist=True`, in which case the result is `[]`.
            #        * The user must specify `wantlist=True` to receive the plugin return value unmodified.
            #          A plugin can achieve similar results by wrapping its result in a list -- unless of course the user specifies `wantlist=True`.
            #        * When `wantlist=True` is specified, the result is not guaranteed to be a list as the option implies (except on plugin error).
            #        * Sequences are munged unless the user specifies `wantlist=True`:
            #          * len() == 0 - Return an empty sequence.
            #          * len() == 1 - Return the only element in the sequence.
            #          * len() >= 2 when all elements are `str` - Return all the values joined into a single comma separated string.
            #          * len() >= 2 when at least one element is not `str` - Return the sequence as-is.

            if not is_sequence(lookup_res):
                # DTFIX-FUTURE: deprecate return types which are not a list
                #   previously non-Sequence return types were deprecated and then became an error in 2.18
                #   however, the deprecation message (and this error) mention `list` specifically rather than `Sequence`
                #   letting non-list values through will trigger variable type checking warnings/errors
                raise TypeError(f'returned {type(lookup_res)} instead of {list}')

        except MarkerError as ex:
            return ex.source
        except Exception as ex:
            # DTFIX-FUTURE: convert this to the new error/warn/ignore context manager
            if errors == 'warn':
                _display.error_as_warning(
                    msg=f'An error occurred while running the lookup plugin {plugin_name!r}.',
                    exception=ex,
                )
            elif errors == 'ignore':
                _display.display(f'An error of type {type(ex)} occurred while running the lookup plugin {plugin_name!r}: {ex}', log_only=True)
            else:
                raise AnsibleTemplatePluginRuntimeError('lookup', plugin_name) from ex

            return [] if wantlist else None

        if not wantlist and lookup_res:
            # when wantlist=False the lookup result is either partially delaizified (single element) or fully delaizified (multiple elements)

            if len(lookup_res) == 1:
                lookup_res = lookup_res[0]
            else:
                try:
                    lookup_res = ",".join(lookup_res)  # for backwards compatibility, attempt to join `ran` into single string
                except TypeError:
                    pass  # for backwards compatibility, return `ran` as-is when the sequence contains non-string values

        return _wrap_plugin_output(lookup_res)


def _now(utc=False, fmt=None):
    """Jinja2 global function (now) to return current datetime, potentially formatted via strftime."""
    if utc:
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    else:
        now = datetime.datetime.now()

    if fmt:
        return now.strftime(fmt)

    return now


def _jinja_const_template_warning(value: object, is_conditional: bool) -> None:
    """Issue a warning regarding embedded template usage."""
    help_text = "Use inline expressions, for example: "

    if is_conditional:
        help_text += """`when: "{{ a_var }}" == 42` becomes `when: a_var == 42`"""
    else:
        help_text += """`msg: "{{ lookup('env', '{{ a_var }}') }}"` becomes `msg: "{{ lookup('env', a_var) }}"`"""

    # deprecated: description='disable embedded templates by default and deprecate the feature' core_version='2.23'
    _display.warning(
        msg="Jinja constant strings should not contain embedded templates. This feature will be disabled by default in ansible-core 2.23.",
        obj=value,
        help_text=help_text,
    )


def _trust_jinja_constants(o: t.Any) -> t.Any:
    """
    Recursively apply TrustedAsTemplate to values tagged with _JinjaConstTemplate and remove the tag.
    Only container types emitted by the Jinja compiler are checked, since others do not contain constants.
    This is used to provide backwards compatibility with historical lookup behavior for positional arguments.
    """
    if _JinjaConstTemplate.is_tagged_on(o):
        _jinja_const_template_warning(o, is_conditional=False)

        return TrustedAsTemplate().tag(_JinjaConstTemplate.untag(o))

    o_type = type(o)

    if o_type is dict:
        return {k: _trust_jinja_constants(v) for k, v in o.items()}

    if o_type in (list, tuple):
        return o_type(_trust_jinja_constants(v) for v in o)

    return o


def _wrap_plugin_output(o: t.Any) -> t.Any:
    """Utility method to ensure that iterators/generators returned from a plugins are consumed."""
    if isinstance(o, _ITERATOR_TYPES):
        o = list(o)

    return _AnsibleLazyTemplateMixin._try_create(o, LazyOptions.SKIP_TEMPLATES)


_PLUGIN_SOURCES = dict(
    filter=defaults.DEFAULT_FILTERS,
    test=defaults.DEFAULT_TESTS,
)


def _get_builtin_short_description(plugin: object) -> str:
    """
    Make a reasonable effort to break a function docstring down to a single sentence.
    We can't use the full docstring due to embedded formatting, particularly RST.
    This isn't intended to be perfect, just good enough until we can write our own docs for these.
    """
    value = re.split(r'(\.|!|\s\(|:\s)', inspect.getdoc(plugin), 1)[0].replace('\n', ' ')

    if value:
        value += '.'

    return value


def get_jinja_builtin_plugin_descriptions(plugin_type: str) -> dict[str, str]:
    """Returns a dictionary of Jinja builtin plugin names and their short descriptions."""
    return {f'ansible.builtin.{name}': _get_builtin_short_description(plugin) for name, plugin in _PLUGIN_SOURCES[plugin_type].items() if name.isidentifier()}
