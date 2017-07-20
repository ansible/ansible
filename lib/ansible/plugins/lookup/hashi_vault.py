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
# USAGE: {{ lookup('hashi_vault', 'secret=secret/hello:value token=c975b780-d1be-8016-866b-01d0f9b688a5 url=http://myvault:8200')}}
#
# To authenticate with a username/password against the LDAP auth backend in Vault:
#
# USAGE: {{ lookup('hashi_vault', 'secret=secret/hello:value auth_method=ldap mount_point=ldap username=myuser password=mypassword url=http://myvault:8200')}}
#
# The mount_point param defaults to ldap, so is only required if you have a custom mount point.
#
# To use a ssl Vault add verify param:
#
# USAGE: {{ lookup('hashi_vault', 'secret=secret/hello:value token=c975b780-d1be-8016-866b-01d0f9b688a5 url=https://myvault:8200 validate_certs=False')}}
#
# The validate_certs param posible values are: True or False. By default it's in True. If False no verify of ssl will be done.
# To use ca certificate file you can specify the path as parameter cacert
#
# USAGE: {{ lookup('hashi_vault', 'secret=secret/hello:value token=xxxx-xxx-xxx url=https://myvault:8200 validate_certs=True cacert=/cacert/path/ca.pem')}}
#
# You can skip setting the url if you set the VAULT_ADDR environment variable
# or if you want it to default to localhost:8200
#
# NOTE: Due to a current limitation in the HVAC library there won't
# necessarily be an error if a bad endpoint is specified.
#
# Requires hvac library. Install with pip.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.lookup import LookupBase

HAS_HVAC = False
try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False


ANSIBLE_HASHI_VAULT_ADDR = 'http://127.0.0.1:8200'

if os.getenv('VAULT_ADDR') is not None:
    ANSIBLE_HASHI_VAULT_ADDR = os.environ['VAULT_ADDR']


class HashiVault:
    def __init__(self, **kwargs):

        self.url = kwargs.get('url', ANSIBLE_HASHI_VAULT_ADDR)

        self.token = kwargs.get('token')
        if self.token is None:
            raise AnsibleError("No Hashicorp Vault Token specified for hash_vault lookup")

        # split secret arg, which has format 'secret/hello:value' into secret='secret/hello' and secret_field='value'
        s = kwargs.get('secret')
        if s is None:
            raise AnsibleError("No secret specified for hashi_vault lookup")

        s_f = s.split(':')
        self.secret = s_f[0]
        if len(s_f) >= 2:
            self.secret_field = s_f[1]
        else:
            self.secret_field = 'value'

        # if a particular backend is asked for (and its method exists) we call it, otherwise drop through to using
        # token auth.   this means if a particular auth backend is requested and a token is also given, then we
        # ignore the token and attempt authentication against the specified backend.
        #
        # to enable a new auth backend, simply add a new 'def auth_<type>' method below.
        #
        self.auth_method = kwargs.get('auth_method')
        if self.auth_method:
            try:
                self.client = hvac.Client(url=self.url)
                # prefixing with auth_ to limit which methods can be accessed
                getattr(self, 'auth_' + self.auth_method)(**kwargs)
            except AttributeError:
                raise AnsibleError("Authentication method '%s' not supported" % self.auth_method)
        else:
            self.token = kwargs.get('token', os.environ.get('VAULT_TOKEN', None))
            if self.token is None and os.environ.get('HOME'):
                token_filename = os.path.join(
                    os.environ.get('HOME'),
                    '.vault-token'
                )
                if os.path.exists(token_filename):
                    with open(token_filename) as token_file:
                        self.token = token_file.read().strip()

            if self.token is None:
                raise AnsibleError("No Vault Token specified")

            self.verify = self.boolean_or_cacert(kwargs.get('validate_certs', True), kwargs.get('cacert', ''))

            self.client = hvac.Client(url=self.url, token=self.token, verify=self.verify)

        if not self.client.is_authenticated():
            raise AnsibleError("Invalid Hashicorp Vault Token Specified for hashi_vault lookup")

    def get(self):
        data = self.client.read(self.secret)

        if data is None:
            raise AnsibleError("The secret %s doesn't seem to exist for hashi_vault lookup" % self.secret)

        if self.secret_field == '':  # secret was specified with trailing ':'
            return data['data']

        if self.secret_field not in data['data']:
            raise AnsibleError("The secret %s does not contain the field '%s'. for hashi_vault lookup" % (self.secret, self.secret_field))

        return data['data'][self.secret_field]

    def auth_ldap(self, **kwargs):
        username = kwargs.get('username')
        if username is None:
            raise AnsibleError("Authentication method ldap requires a username")

        password = kwargs.get('password')
        if password is None:
            raise AnsibleError("Authentication method ldap requires a password")

        mount_point = kwargs.get('mount_point')
        if mount_point is None:
            mount_point = 'ldap'

        self.client.auth_ldap(username, password, mount_point)

    def boolean_or_cacert(self, validate_certs, cacert):
        validate_certs = boolean(validate_certs, strict=False)
        '''' return a bool or cacert '''
        if validate_certs is True:
            if cacert != '':
                return cacert
            else:
                return True
        else:
            return False


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        if not HAS_HVAC:
            raise AnsibleError("Please pip install hvac to use the hashi_vault lookup module.")

        vault_args = terms[0].split(' ')
        vault_dict = {}
        ret = []

        for param in vault_args:
            try:
                key, value = param.split('=')
            except ValueError:
                raise AnsibleError("hashi_vault lookup plugin needs key=value pairs, but received %s" % terms)
            vault_dict[key] = value

        vault_conn = HashiVault(**vault_dict)

        for term in terms:
            key = term.split()[0]
            value = vault_conn.get()
            ret.append(value)

        return ret
