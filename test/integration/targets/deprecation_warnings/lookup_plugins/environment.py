from __future__ import annotations

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        # mimics the way collections reach into the deprecated attribute to use the Jinja environment directly
        environment = self._templar.environment  # deprecated getter

        self._templar.environment = environment  # deprecated setter, restores the same environment

        return [environment.from_string('{{ deprecated_var }}').render(deprecated_var='from the deprecated getter')]
