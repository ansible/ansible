from __future__ import annotations

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    accept_args_markers = False

    def run(self, terms, variables, **kwargs):
        return terms
