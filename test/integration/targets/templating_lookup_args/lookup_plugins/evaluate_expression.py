from __future__ import annotations

from ansible.plugins.lookup import LookupBase
from ansible.template import trust_as_template


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        templar = self._templar.copy_with_new_env(available_variables={})
        templar.available_variables = {"foo": {}}
        return [templar.evaluate_expression(trust_as_template(term)) for term in terms]
