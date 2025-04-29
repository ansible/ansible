from __future__ import annotations

from ansible.module_utils.common.messages import PluginInfo
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        return [PluginInfo(
            requested_name='requested_name',
            resolved_name='resolved_name',
            type='type',
        )]
