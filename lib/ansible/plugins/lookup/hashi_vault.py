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
# or if you want it to default to http://localhost:8200
#
# You can skip setting the token if you set the VAULT_TOKEN environment variable

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import urllib2
import json
from urlparse import urljoin

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class HashiVault:
    def __init__(self, **kwargs):
        try:
            self.url = kwargs.pop('url')
        except:
            if os.getenv('VAULT_ADDR'):
                self.url = os.getenv('VAULT_ADDR')
            else:
                raise AnsibleError("VAULT_ADDR environment variable must be specified to acccess Hashicorp Vault")

        try:
            self.token = kwargs.pop('token')
        except:
            if os.environ['VAULT_TOKEN']:
                self.token = os.environ['VAULT_TOKEN']
            else:
                raise AnsibleError("VAULT_TOKEN environment variable must be specified to access Hashicorp Vault")

        self.secret = kwargs.pop('secret')

    def get(self):
        request_url = urljoin(self.url, "v1/%s" % (self.secret))

        try:
            headers = { 'X-Vault-Token' : self.token }
            req = urllib2.Request(request_url, None, headers)
            response = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            raise AnsibleError('Unable to read %s from Hashicorp Vault: %s' % (self.secret, e))
        except:
            raise AnsibleError('Unable to read %s from Hashicorp Vault' % self.secret)

        result = json.loads(response.read())

        return result['data']['value']


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
