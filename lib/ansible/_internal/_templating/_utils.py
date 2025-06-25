from __future__ import annotations

import dataclasses
import typing as t

from ansible.module_utils._internal import _ambient_context, _datatag

if t.TYPE_CHECKING:
    from ._engine import TemplateEngine, TemplateOptions


@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class LazyOptions:
    """Templating options that apply to lazy containers, which are inherited by descendent lazy containers."""

    DEFAULT: t.ClassVar[t.Self]
    """A shared instance with the default options to minimize instance creation for arg defaults."""
    SKIP_TEMPLATES: t.ClassVar[t.Self]
    """A shared instance with only `template=False` set to minimize instance creation for arg defaults."""
    SKIP_TEMPLATES_AND_ACCESS: t.ClassVar[t.Self]
    """A shared instance with both `template=False` and `access=False` set to minimize instance creation for arg defaults."""

    template: bool = True
    """Enable/disable templating."""

    access: bool = True
    """Enable/disables access calls."""

    unmask_type_names: frozenset[str] = frozenset()
    """Disables template transformations for the provided type names."""


LazyOptions.DEFAULT = LazyOptions()
LazyOptions.SKIP_TEMPLATES = LazyOptions(template=False)
LazyOptions.SKIP_TEMPLATES_AND_ACCESS = LazyOptions(template=False, access=False)


class TemplateContext(_ambient_context.AmbientContextBase):
    def __init__(
        self,
        *,
        template_value: t.Any,
        templar: TemplateEngine,
        options: TemplateOptions,
        stop_on_template: bool = False,
        _render_jinja_const_template: bool = False,
    ):
        self._template_value = template_value
        self._templar = templar
        self._options = options
        self._stop_on_template = stop_on_template
        self._parent_ctx = TemplateContext.current(optional=True)
        self._render_jinja_const_template = _render_jinja_const_template

    @property
    def is_top_level(self) -> bool:
        return not self._parent_ctx

    @property
    def template_value(self) -> t.Any:
        return self._template_value

    @property
    def templar(self) -> TemplateEngine:
        return self._templar

    @property
    def options(self) -> TemplateOptions:
        return self._options

    @property
    def stop_on_template(self) -> bool:
        return self._stop_on_template


class _OmitType:
    """
    A placeholder singleton used to dynamically omit items from a dict/list/tuple/set when the value is `Omit`.

    The `Omit` singleton is accessible from all Ansible templating contexts via the Jinja global name `omit`.
    The `Omit` placeholder value will be visible to Jinja plugins during templating.
    Jinja plugins requiring omit behavior are responsible for handling encountered `Omit` values.
    `Omit` values remaining in template results will be automatically dropped during template finalization.
    When a finalized template renders to a scalar `Omit`, `AnsibleValueOmittedError` will be raised.
    Passing a value other than `Omit` for `value_for_omit` to the `template` call allows that value to be substituted instead of raising.
    """

    __slots__ = ()

    def __new__(cls):
        return Omit

    def __repr__(self):
        return "<<Omit>>"


Omit = object.__new__(_OmitType)

_datatag._untaggable_types.add(_OmitType)


# DTFIX0: review these type sets to ensure they're not overly permissive/dynamic
IGNORE_SCALAR_VAR_TYPES = {value for value in _datatag._ANSIBLE_ALLOWED_SCALAR_VAR_TYPES if not issubclass(value, str)}

PASS_THROUGH_SCALAR_VAR_TYPES = _datatag._ANSIBLE_ALLOWED_SCALAR_VAR_TYPES | {
    _OmitType,  # allow pass through of omit for later handling after top-level finalize completes
}
