# (c) 2015, Jonathan Davila <jdavila(at)ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
# USAGE: {{ lookup('hashi_vault', 'secret=secret/hello token=c975b780-d1be-8016-866b-01d0f9b688a5 url=http://myvault:8200')}}
#
# You can skip setting the url if you set the VAULT_ADDR environment variable
# or if you want it to default to localhost:8200
#
# NOTE: Due to a current limitation in the HVAC library there won't
# necessarily be an error if a bad endpoint is specified.
#
# Requires hvac library. Install with pip.
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


ANSIBLE_HASHI_VAULT_ADDR = 'http://127.0.0.1:8200'

if os.getenv('VAULT_ADDR') is not None:
    ANSIBLE_HASHI_VAULT_ADDR = os.environ['VAULT_ADDR']

class HashiVault:
    def __init__(self, **kwargs):
        try:
            import hvac
        except ImportError:
            AnsibleError("Please pip install hvac to use this module")

        self.url = kwargs.pop('url')
        self.secret = kwargs.pop('secret')
        self.token = kwargs.pop('token')

        self.client = hvac.Client(url=self.url, token=self.token)

        if self.client.is_authenticated():
            pass
        else:
            raise AnsibleError("Invalid Hashicorp Vault Token Specified")

    def get(self):
        data = self.client.read(self.secret)
        if data is None:
            raise AnsibleError("The secret %s doesn't seem to exist" % self.secret)
        else:
            return data['data']['value']


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        vault_args = terms[0].split(' ')
        vault_dict = {}
        ret = []

        for param in vault_args:
            key, value = param.split('=')
            vault_dict[key] = value

        vault_conn = HashiVault(**vault_dict)

        for term in terms:
           key = term.split()[0]
           value = vault_conn.get()
           ret.append(value)
        return ret
