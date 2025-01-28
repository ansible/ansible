from __future__ import annotations

import dataclasses
import datetime
import typing as t

from ansible.module_utils.datatag import _tag_dataclass_kwargs, AnsibleDatatagBase


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class Deprecated(AnsibleDatatagBase):
    msg: str
    removal_date: t.Optional[datetime.date] = None
    removal_version: t.Optional[str] = None

    @classmethod
    def _from_dict(cls, d: t.Dict[str, t.Any]) -> Deprecated:
        source = d
        removal_date = source.get('removal_date')

        if removal_date is not None:
            source = source.copy()
            source['removal_date'] = datetime.date.fromisoformat(removal_date)

        return cls(**source)

    def _as_dict(self) -> t.Dict[str, t.Any]:
        value = AnsibleDatatagBase._as_dict(self)

        if self.removal_date is not None:
            value['removal_date'] = self.removal_date.isoformat()

        return value
