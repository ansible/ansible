from __future__ import annotations

from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        for value in terms:
            display.warning("Some warning.", obj=value)

        return terms
