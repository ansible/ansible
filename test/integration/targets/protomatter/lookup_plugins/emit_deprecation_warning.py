from __future__ import annotations

from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        Display().deprecated("Hello World!", version='2.9999')

        return []
