from __future__ import annotations

import dataclasses
import datetime
import typing as t

from ansible.module_utils.common import messages as _messages
from ansible.module_utils._internal import _datatag


@dataclasses.dataclass(**_datatag._tag_dataclass_kwargs)
class Deprecated(_datatag.AnsibleDatatagBase):
    msg: str
    help_text: t.Optional[str] = None
    removal_date: t.Optional[datetime.date] = None
    removal_version: t.Optional[str] = None
    plugin: t.Optional[_messages.PluginInfo] = None

    @classmethod
    def _from_dict(cls, d: t.Dict[str, t.Any]) -> Deprecated:
        source = d
        removal_date = source.get('removal_date')

        if removal_date is not None:
            source = source.copy()
            source['removal_date'] = datetime.date.fromisoformat(removal_date)

        return cls(**source)

    def _as_dict(self) -> t.Dict[str, t.Any]:
        # deprecated: description='no-args super() with slotted dataclass requires 3.14+' python_version='3.13'
        # see: https://github.com/python/cpython/pull/124455
        value = super(Deprecated, self)._as_dict()

        if self.removal_date is not None:
            value['removal_date'] = self.removal_date.isoformat()

        return value
