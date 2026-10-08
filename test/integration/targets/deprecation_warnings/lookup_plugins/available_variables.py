from __future__ import annotations

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        # mimics the way collection lookup plugins abuse the deprecated internal attribute
        original = self._templar._available_variables  # deprecated getter

        try:
            self._templar._available_variables = dict(original, deprecated_var='from the deprecated setter')  # deprecated setter

            return [self._templar.template('{{ deprecated_var }}')]
        finally:
            self._templar.available_variables = original
