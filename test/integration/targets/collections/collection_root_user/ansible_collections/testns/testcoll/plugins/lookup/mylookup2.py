from __future__ import annotations


from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        return ['mylookup2_from_user_dir']
