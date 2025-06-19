from __future__ import annotations

import contextlib as _contextlib
import dataclasses
import typing as t

from ansible.module_utils._internal._datatag import AnsibleSingletonTagBase, _tag_dataclass_kwargs
from ansible.module_utils._internal._datatag._tags import Deprecated
from ansible._internal._datatag._tags import Origin
from ansible.utils.display import Display

from ._access import NotifiableAccessContextBase
from ._utils import TemplateContext

display = Display()


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class _JinjaConstTemplate(AnsibleSingletonTagBase):
    # deprecated: description='embedded Jinja constant string template support' core_version='2.23'
    pass


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class _TrippedDeprecationInfo:
    template: str
    deprecated: Deprecated


class DeprecatedAccessAuditContext(NotifiableAccessContextBase):
    """When active, captures metadata about managed accesses to `Deprecated` tagged objects."""

    _type_interest = frozenset([Deprecated])

    @classmethod
    def when(cls, condition: bool, /) -> t.Self | _contextlib.nullcontext:
        """Returns a new instance if `condition` is True (usually `TemplateContext.is_top_level`), otherwise a `nullcontext` instance."""
        if condition:
            return cls()

        return _contextlib.nullcontext()

    def __init__(self) -> None:
        self._tripped_deprecation_info: dict[int, _TrippedDeprecationInfo] = {}

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        result = super().__exit__(exc_type, exc_val, exc_tb)

        for item in self._tripped_deprecation_info.values():
            if Origin.is_tagged_on(item.template):
                msg = item.deprecated.msg
            else:
                # without an origin, we need to include what context we do have (the template)
                msg = f'While processing {item.template!r}: {item.deprecated.msg}'

            display._deprecated_with_plugin_info(
                msg=msg,
                help_text=item.deprecated.help_text,
                version=item.deprecated.version,
                date=item.deprecated.date,
                obj=item.template,
                deprecator=item.deprecated.deprecator,
                formatted_traceback=item.deprecated.formatted_traceback,
            )

        return result

    def _notify(self, o: t.Any) -> None:
        deprecated = Deprecated.get_required_tag(o)
        deprecated_key = id(deprecated)

        if deprecated_key in self._tripped_deprecation_info:
            return  # record only the first access for each deprecated tag in a given context

        template_ctx = TemplateContext.current(optional=True)
        template = template_ctx.template_value if template_ctx else None

        # when the current template input is a container, provide a descriptive string with origin propagated (if possible)
        if not isinstance(template, str):
            # DTFIX-FUTURE: ascend the template stack to try and find the nearest string source template
            origin = Origin.get_tag(template)

            # DTFIX-FUTURE: this should probably use a synthesized description value on the tag
            #              it is reachable from the data_tagging_controller test: ../playbook_output_validator/filter.py actual_stdout.txt actual_stderr.txt
            # -[DEPRECATION WARNING]: `something_old` is deprecated, don't use it! This feature will be removed in version 1.2.3.
            # +[DEPRECATION WARNING]: While processing '<<container>>': `something_old` is deprecated, don't use it! This feature will be removed in ...
            template = '<<container>>'

            if origin:
                origin.tag(template)

        self._tripped_deprecation_info[deprecated_key] = _TrippedDeprecationInfo(
            template=template,
            deprecated=deprecated,
        )
