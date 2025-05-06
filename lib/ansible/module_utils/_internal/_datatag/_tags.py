from __future__ import annotations

import dataclasses
import typing as t

from ansible.module_utils.common import messages as _messages
from ansible.module_utils._internal import _datatag


@dataclasses.dataclass(**_datatag._tag_dataclass_kwargs)
class Deprecated(_datatag.AnsibleDatatagBase):
    msg: str
    help_text: t.Optional[str] = None
    date: t.Optional[str] = None
    version: t.Optional[str] = None
    deprecator: t.Optional[_messages.PluginInfo] = None
