from __future__ import annotations

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    """Test plugin whose run method has a kwarg named terms that is not the first positional arg."""
    def run(self, not_terms, variables=None, terms=None, **kwargs):  # pylint:disable=arguments-renamed
        """Echo back a dictionary with the first posarg and the terms kwarg to ensure we didn't conflate posarg 0 and the terms kwarg"""
        return [dict(not_terms=not_terms, terms=terms)]
