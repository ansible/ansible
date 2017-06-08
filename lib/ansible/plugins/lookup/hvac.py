from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

'''
Lookup plugin to grab sechrets from a hashicorp vault store.
============================================================
Plugin will lookup secrets for a playbook from the key value store in a
hashicorp vault. Values can be easily set in the vault using vault's CLI e.g.

$ vault write secret/hello value=world excited=yes

this can then be looked up in a playbook as follows

- debug: msg='secret is {{lookup('hvac', 'secret/hello', token='auth_token'}}'

Keys other than the default of 'value' can be provided after the path to define what to retrieve e.g.

- debug: msg='secret is {{lookup('hvac', 'secret/hello', key='excited' token='auth_token'}}'

By default this will lookup secret values via the vault server running on http://localhost:8200
this can be changed by setting the env variable 'ANSIBLE_HVAC_URL' to point to the url
of the vault store you'd like to use.
'''

######################################################################

import os
import sys
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

try:
    import json
except ImportError:
    import simplejson as json

try:
    import hvac
    HAS_HVAC = True
except ImportError as err:
    HAS_HVAC = False


class LookupModule(LookupBase):

    def __init__(self, loader=None, templar=None, **kwargs):

        super(LookupModule, self).__init__(loader, templar, **kwargs)

        self.agent_url = 'http://localhost:8200'
        if os.getenv('ANSIBLE_HVAC_URL') is not None:
            self.agent_url = os.environ['ANSIBLE_HVAC_URL']

    def run(self, terms, variables=None, **kwargs):
        if not HAS_HVAC:
            raise AnsibleError(
                'hvac is required for hvac lookup. '
                'See https://github.com/ianunruh/hvac#installation')

        hvac_client = hvac.Client(self.agent_url)
        hvac_client.token = kwargs['token']

        values = []
        for term in terms:
            result = hvac_client.read(term)
            if result:
                for key in ['data'] + kwargs['key'].split('.'):
                    result = result[key]
                values.append(result)
            else:
                raise AnsibleError(
                    "Could not find secret %s in vault" % term)
        return values
