# (c) 2015, Jonathan Davila <jonathan(at)davila.io>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  lookup: hashi_vault
  author: Jonathan Davila <jdavila(at)ansible.com>
  version_added: "2.0"
  short_description: retrieve secrets from HashiCorp's vault
  requirements:
    - hvac (python library)
  description:
    - retrieve secrets from HashiCorp's vault
  notes:
    - Due to a current limitation in the HVAC library there won't necessarily be an error if a bad endpoint is specified.
  options:
    secret:
      description: query you are making.
      required: True
    token:
      description: vault token.
      env:
        - name: VAULT_TOKEN
    url:
      description: URL to vault service.
      env:
        - name: VAULT_ADDR
      default: 'http://127.0.0.1:8200'
    username:
      description: Authentication user name.
    password:
      description: Authentication password.
    role_id:
      description: Role id for a vault AppRole auth.
      env:
        - name: VAULT_ROLE_ID
    secret_id:
      description: Secret id for a vault AppRole auth.
      env:
        - name: VAULT_SECRET_ID
    auth_method:
      description:
      - Authentication method to be used.
      - C(userpass) is added in version 2.8.
      env:
        - name: VAULT_AUTH_METHOD
      choices:
        - userpass
        - ldap
        - approle
    mount_point:
      description: vault mount point, only required if you have a custom mount point.
      default: ldap
    ca_cert:
      description: path to certificate to use for authentication.
      aliases: [ cacert ]
    validate_certs:
      description: controls verification and validation of SSL certificates, mostly you only want to turn off with self signed ones.
      type: boolean
      default: True
    namespace:
      version_added: "2.8"
      description: namespace where secrets reside. requires HVAC 0.7.0+ and Vault 0.11+.
      default: None
"""

EXAMPLES = """
- debug:
    msg: "{{ lookup('hashi_vault', 'secret=secret/hello:value token=c975b780-d1be-8016-866b-01d0f9b688a5 url=http://myvault:8200')}}"

- name: Return all secrets from a path
  debug:
    msg: "{{ lookup('hashi_vault', 'secret=secret/hello token=c975b780-d1be-8016-866b-01d0f9b688a5 url=http://myvault:8200')}}"

- name: Vault that requires authentication via LDAP
  debug:
      msg: "{{ lookup('hashi_vault', 'secret=secret/hello:value auth_method=ldap mount_point=ldap username=myuser password=mypas url=http://myvault:8200')}}"

- name: Vault that requires authentication via username and password
  debug:
      msg: "{{ lookup('hashi_vault', 'secret=secret/hello:value auth_method=userpass username=myuser password=mypas url=http://myvault:8200')}}"

- name: Using an ssl vault
  debug:
      msg: "{{ lookup('hashi_vault', 'secret=secret/hola:value token=c975b780-d1be-8016-866b-01d0f9b688a5 url=https://myvault:8200 validate_certs=False')}}"

- name: using certificate auth
  debug:
      msg: "{{ lookup('hashi_vault', 'secret=secret/hi:value token=xxxx-xxx-xxx url=https://myvault:8200 validate_certs=True cacert=/cacert/path/ca.pem')}}"

- name: authenticate with a Vault app role
  debug:
      msg: "{{ lookup('hashi_vault', 'secret=secret/hello:value auth_method=approle role_id=myroleid secret_id=mysecretid url=http://myvault:8200')}}"

- name: Return all secrets from a path in a namespace
  debug:
    msg: "{{ lookup('hashi_vault', 'secret=secret/hello token=c975b780-d1be-8016-866b-01d0f9b688a5 url=http://myvault:8200 namespace=teama/admins')}}"
"""

RETURN = """
_raw:
  description:
    - secrets(s) requested
"""

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
        self.namespace = kwargs.get('namespace', None)
        self.avail_auth_method = ['approle', 'userpass', 'ldap']

        # split secret arg, which has format 'secret/hello:value' into secret='secret/hello' and secret_field='value'
        s = kwargs.get('secret')
        if s is None:
            raise AnsibleError("No secret specified for hashi_vault lookup")

        s_f = s.rsplit(':', 1)
        self.secret = s_f[0]
        if len(s_f) >= 2:
            self.secret_field = s_f[1]
        else:
            self.secret_field = ''

        self.verify = self.boolean_or_cacert(kwargs.get('validate_certs', True), kwargs.get('cacert', ''))

        # If a particular backend is asked for (and its method exists) we call it, otherwise drop through to using
        # token auth. This means if a particular auth backend is requested and a token is also given, then we
        # ignore the token and attempt authentication against the specified backend.
        #
        # to enable a new auth backend, simply add a new 'def auth_<type>' method below.
        #
        self.auth_method = kwargs.get('auth_method', os.environ.get('VAULT_AUTH_METHOD'))
        self.verify = self.boolean_or_cacert(kwargs.get('validate_certs', True), kwargs.get('cacert', ''))
        if self.auth_method and self.auth_method != 'token':
            try:
                if self.namespace is not None:
                    self.client = hvac.Client(url=self.url, verify=self.verify, namespace=self.namespace)
                else:
                    self.client = hvac.Client(url=self.url, verify=self.verify)
                # prefixing with auth_ to limit which methods can be accessed
                getattr(self, 'auth_' + self.auth_method)(**kwargs)
            except AttributeError:
                raise AnsibleError("Authentication method '%s' not supported."
                                   " Available options are %r" % (self.auth_method, self.avail_auth_method))
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

            if self.namespace is not None:
                self.client = hvac.Client(url=self.url, token=self.token, verify=self.verify, namespace=self.namespace)
            else:
                self.client = hvac.Client(url=self.url, token=self.token, verify=self.verify)

        if not self.client.is_authenticated():
            raise AnsibleError("Invalid Hashicorp Vault Token Specified for hashi_vault lookup")

    def get(self):
        data = self.client.read(self.secret)

        if data is None:
            raise AnsibleError("The secret %s doesn't seem to exist for hashi_vault lookup" % self.secret)

        if self.secret_field == '':
            return data['data']

        if self.secret_field not in data['data']:
            raise AnsibleError("The secret %s does not contain the field '%s'. for hashi_vault lookup" % (self.secret, self.secret_field))

        return data['data'][self.secret_field]

    def check_params(self, **kwargs):
        username = kwargs.get('username')
        if username is None:
            raise AnsibleError("Authentication method %s requires a username" % self.auth_method)

        password = kwargs.get('password')
        if password is None:
            raise AnsibleError("Authentication method %s requires a password" % self.auth_method)

        mount_point = kwargs.get('mount_point')

        return username, password, mount_point

    def auth_userpass(self, **kwargs):
        username, password, mount_point = self.check_params(**kwargs)
        if mount_point is None:
            mount_point = 'userpass'

        self.client.auth_userpass(username, password, mount_point=mount_point)

    def auth_ldap(self, **kwargs):
        username, password, mount_point = self.check_params(**kwargs)
        if mount_point is None:
            mount_point = 'ldap'

        self.client.auth_ldap(username, password, mount_point=mount_point)

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

    def auth_approle(self, **kwargs):
        role_id = kwargs.get('role_id', os.environ.get('VAULT_ROLE_ID', None))
        if role_id is None:
            raise AnsibleError("Authentication method app role requires a role_id")

        secret_id = kwargs.get('secret_id', os.environ.get('VAULT_SECRET_ID', None))
        if secret_id is None:
            raise AnsibleError("Authentication method app role requires a secret_id")

        self.client.auth_approle(role_id, secret_id)


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        if not HAS_HVAC:
            raise AnsibleError("Please pip install hvac to use the hashi_vault lookup module.")

        vault_args = terms[0].split()
        vault_dict = {}
        ret = []

        for param in vault_args:
            try:
                key, value = param.split('=')
            except ValueError:
                raise AnsibleError("hashi_vault lookup plugin needs key=value pairs, but received %s" % terms)
            vault_dict[key] = value

        if 'ca_cert' in vault_dict.keys():
            vault_dict['cacert'] = vault_dict['ca_cert']
            vault_dict.pop('ca_cert', None)

        vault_conn = HashiVault(**vault_dict)

        for term in terms:
            key = term.split()[0]
            value = vault_conn.get()
            ret.append(value)

        return ret
