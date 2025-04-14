from __future__ import annotations

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    accept_args_markers = True

    def run(self, terms, variables=None, **kwargs):
        return terms
