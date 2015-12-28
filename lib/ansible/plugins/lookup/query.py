# Ansible lookup plugin for generic querying arbitrary data structures
#
#
# Usage:
#
# - debug: var=item
#   with_query:
#     - "{{ hosts }}"
#     - '[*].volumes[*]'

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms

try:
    from dq import query
    HAS_DQ = True
except:
    HAS_DQ = False

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        if not HAS_DQ:
            raise AnsibleError('You need to install "dq" prior to running this module')

        data = listify_lookup_plugin_terms(terms[0], templar=self._templar, loader=self._loader)
        expr = terms[1]
        result = query(expr, data)
        if hasattr(result, '__iter__'):
            return list(result)
        else:
            return [ result ]
