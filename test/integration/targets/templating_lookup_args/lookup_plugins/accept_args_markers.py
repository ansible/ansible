from __future__ import annotations

from ansible._internal._templating._jinja_common import Marker
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    accept_args_markers = True

    def run(self, terms, variables, **kwargs):
        return [isinstance(term, Marker) for term in terms]
