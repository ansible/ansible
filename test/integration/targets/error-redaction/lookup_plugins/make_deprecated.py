from __future__ import annotations

from ansible.module_utils.datatag import deprecate_value
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        return [deprecate_value(
            value=value,
            msg='Something deprecated.',
            version='99.0.0',
        ) for value in terms]
