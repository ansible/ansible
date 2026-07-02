from __future__ import annotations

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        return ['subdir_lookup_from_user_dir']
