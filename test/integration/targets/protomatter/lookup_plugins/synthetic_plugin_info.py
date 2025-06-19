from __future__ import annotations

from ansible.module_utils._internal import _messages
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        return [_messages.PluginInfo(
            resolved_name='ns.col.module',
            type=_messages.PluginType.MODULE,
        )]
