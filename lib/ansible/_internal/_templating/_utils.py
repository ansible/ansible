from __future__ import annotations

import typing as t

from ansible.module_utils import datatag
from ansible.module_utils._internal import _ambient_context

if t.TYPE_CHECKING:
    from ._engine import TemplateEngine, TemplateOptions


class TemplateContext(_ambient_context.AmbientContextBase):
    def __init__(
        self, *,
        template_value: t.Any,
        templar: TemplateEngine,
        options: TemplateOptions,
        stop_on_template: bool = False,
        _render_jinja_const_template: bool = False
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

    The Omit singleton value is accessible from all Ansible templating contexts via the Jinja global
    name `omit`. Item removal occurs during final recursive processing of template results. The singleton
    `Omit` placeholder value will be visible to plugins during templating. The only time a template result
    will include `Omit` outside a templating context is when the template renders to the scalar value `Omit`.
    """
    __slots__ = ()

    # DTFIX-MERGE: this keeps pickle happy, but not JSON/YAML for callbacks; just teach them about it?
    def __new__(cls):
        return Omit

    def __repr__(self):
        return "<<Omit>>"


Omit = object.__new__(_OmitType)

# DTFIX-MERGE: decide if these should be taggable; do we need to support other kinds of Undefineds, etc
datatag._untaggable_types.add(_OmitType)

IGNORE_SCALAR_VAR_TYPES = {value for value in datatag._ANSIBLE_ALLOWED_SCALAR_VAR_TYPES if not issubclass(value, str)}

PASS_THROUGH_SCALAR_VAR_TYPES = datatag._ANSIBLE_ALLOWED_SCALAR_VAR_TYPES | {
    _OmitType,  # allow pass through of omit for later handling after top-level finalize completes
}
