from __future__ import annotations

from ansible.plugins.lookup import LookupBase
from ansible.template import Templar


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        # mimics the way collections abuse the deprecated internal attribute to create a new Templar instance
        loader = self._templar._loader  # deprecated getter

        new_templar = Templar(loader=loader, variables=dict(deprecated_var='from the deprecated getter'))

        self._templar._loader = loader  # deprecated setter

        return [new_templar.template('{{ deprecated_var }}')]
