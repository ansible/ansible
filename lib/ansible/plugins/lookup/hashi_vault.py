# (c) 2015, Jonathan Davila <jonathan(at)davila.io>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
  lookup: hashi_vault
  author:
    - Jonathan Davila <jdavila(at)ansible.com>
    - Brian Scholer (@briantist)
  version_added: "2.0"
  extends_documentation_fragment:
    - aws_credentials
    - aws_region
  short_description: Retrieve secrets from HashiCorp's vault
  requirements:
    - hvac (python library)
    - hvac 0.7.0+ (for namespace support)
    - hvac 0.9.3+ (for non-deprecated methods)
    - botocore (only if inferring aws params from boto)
  description:
    - Retrieve secrets from HashiCorp's vault.
  notes:
    - Due to a current limitation in the HVAC library there won't necessarily be an error if a bad endpoint is specified.
    - As of Ansible 2.10, only the latest secret is returned when specifying a KV v2 path.
  options:
    secret:
      description: query you are making.
      required: True
    token:
      description: Vault token. If using token auth and no token is supplied, will check in ~/.vault-token <- TODO UPDATE
      env:
        - name: VAULT_TOKEN
    token_path:
      description: If no token is specified, will try to read the token file from this path.
      env:
        - name: HOME
      ini:
        - section: lookup_hashi_vault
          key: token_path
    token_file:
      description: If no token is specified, will try to read the token from this file in C(token_path).
      ini:
        - section: lookup_hashi_vault
          key: token_file
      default: '.vault-token'
    url:
      description: URL to vault service.
      env:
        - name: VAULT_ADDR
      ini:
        - section: lookup_hashi_vault
          key: url
      default: 'http://127.0.0.1:8200'
    username:
      description: Authentication user name.
    password:
      description: Authentication password.
    role_id:
      description: Role id for a vault AppRole auth.
      env:
        - name: VAULT_ROLE_ID
      ini:
        - section: lookup_hashi_vault
          key: role_id
    secret_id:
      description: Secret id for a vault AppRole auth.
      env:
        - name: VAULT_SECRET_ID
    auth_method:
      description:
        - Authentication method to be used.
        - C(userpass) is added in version 2.8.
        - C(aws_iam_login) is added in version 2.10.
      env:
        - name: VAULT_AUTH_METHOD
      ini:
        - section: lookup_hashi_vault
          key: auth_method
      choices:
        - token
        - userpass
        - ldap
        - approle
        - aws_iam_login
      default: token
    mount_point:
      description: Vault mount point, only required if you have a custom mount point.
    ca_cert:
      description: Path to certificate to use for authentication.
      aliases: [ cacert ]
    validate_certs:
      description: Controls verification and validation of SSL certificates, mostly you only want to turn off with self signed ones.
      type: boolean
      default: True
    namespace:
      version_added: "2.8"
      description: Namespace where secrets reside. Requires HVAC 0.7.0+ and Vault 0.11+.
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

# When using KV v2 the PATH should include "data" between the secret engine mount and path (e.g. "secret/data/:path")
# see: https://www.vaultproject.io/api/secret/kv/kv-v2.html#read-secret-version
- name: Return latest KV v2 secret from path
  debug:
    msg: "{{ lookup('hashi_vault', 'secret=secret/data/hello token=my_vault_token url=http://myvault_url:8200') }}"


"""

RETURN = """
_raw:
  description:
    - secrets(s) requested
"""

import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

HAS_HVAC = False
try:
    import hvac
    HAS_HVAC = True
except ImportError:
    HAS_HVAC = False

HAS_BOTOCORE = False
try:
    # import boto3
    import botocore
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

HAS_BOTO3 = False
try:
    import boto3
    # import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class HashiVault:
    def get_options(self, *option_names, **kwargs):
        ret = {}
        include_falsey = kwargs.get('include_falsey', False)
        for option in option_names:
            val = self.options.get(option)
            if val or include_falsey:
                ret[option] = val
        return ret

    def __init__(self, **kwargs):
        self.options = kwargs

        # check early that auth method is actually available
        self.auth_function = 'auth_' + self.options['auth_method']
        if not (hasattr(self, self.auth_function) and callable(getattr(self, self.auth_function))):
            raise AnsibleError(
                "Authentication method '%s' is not implemented. ('%s' member function not found)" % (self.options['auth_method'], self.auth_function)
            )

        client_args = {
            'url': self.options['url'],
            'verify': self.options['ca_cert']
        }

        if self.options.get('namespace'):
            client_args['namespace'] = self.options['namespace']

        if self.options['auth_method'] == 'token':
            client_args['token'] = self.options.get('token')

        self.client = hvac.Client(**client_args)

        # Check for deprecated version:
        # hvac is moving auth methods into the auth_methods class
        # which lives in the client.auth member.
        self.hvac_is_old = not hasattr(self.client, 'auth')

        self.authenticate(**kwargs)

    # If a particular backend is asked for (and its method exists) we call it, otherwise drop through to using
    # token auth. This means if a particular auth backend is requested and a token is also given, then we
    # ignore the token and attempt authentication against the specified backend.
    #
    # to enable a new auth backend, simply add a new 'def auth_<type>' method below.
    #
    # TODO: Update this

    def authenticate(self, **kwargs):
        getattr(self, self.auth_function)(**kwargs)

    def get(self):
        secret = self.options['secret']
        field = self.options['secret_field']

        data = self.client.read(secret)

        # Check response for KV v2 fields and flatten nested secret data.
        #
        # https://vaultproject.io/api/secret/kv/kv-v2.html#sample-response-1
        try:
            # sentinel field checks
            check_dd = data['data']['data']
            check_md = data['data']['metadata']
            # unwrap nested data
            data = data['data']
        except KeyError:
            pass

        if data is None:
            raise AnsibleError("The secret %s doesn't seem to exist for hashi_vault lookup" % secret)

        if not field:
            return data['data']

        if field not in data['data']:
            raise AnsibleError("The secret %s does not contain the field '%s'. for hashi_vault lookup" % (secret, field))

        return data['data'][field]

    # begin auth implementation methods

    def auth_token(self, **kwargs):
        if not self.client.is_authenticated():
            raise AnsibleError("Invalid Hashicorp Vault Token Specified for hashi_vault lookup.")

    def auth_userpass(self, **kwargs):
        params = self.get_options('username', 'password', 'mount_point')
        if self.hvac_is_old:
            Display().warning('HVAC should be updated to version 0.9.3 or higher. Deprecated methods will be used.')
            self.client.auth_userpass(**params)
        else:
            self.client.auth.userpass.login(**params)

    def auth_ldap(self, **kwargs):
        params = self.get_options('username', 'password', 'mount_point')
        if self.hvac_is_old:
            Display().warning('HVAC should be updated to version 0.9.3 or higher. Deprecated methods will be used.')
            self.client.auth_ldap(**params)
        else:
            self.client.auth.ldap.login(**params)

    def auth_approle(self, **kwargs):
        params = self.get_options('role_id', 'secret_id')
        self.client.auth_approle(**params)

    def auth_iam_login(self, **kwargs):
        params = self.options['iam_login_credentials']
        if self.hvac_is_old:
            Display().warning('HVAC should be updated to version 0.9.3 or higher. Deprecated methods will be used.')
            self.client.auth_aws_iam(**params)
        else:
            self.client.auth.aws.iam_login(**params)

    # end auth implementation methods


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        if not HAS_HVAC:
            raise AnsibleError("Please pip install hvac to use the hashi_vault lookup module.")

        ret = []

        for term in terms:
            opts = kwargs.copy()
            opts.update(self.parse_term(term))
            self.set_options(direct=opts)
            self.process_options()
            # return [self.get_option('aws_access_key')]
            # return [self._options]
            ret.append(HashiVault(**self._options).get())

        return ret

    def parse_term(self, term):
        '''parses a term string into options'''
        param_dict = {}

        for i, param in enumerate(term.split()):
            try:
                key, value = param.split('=')
            except ValueError:
                if (i == 0):
                    # allow secret to be specified as value only if it's first
                    key = 'secret'
                    value = param
                else:
                    raise AnsibleError("hashi_vault lookup plugin needs key=value pairs, but received %s" % term)
            param_dict[key] = value
        return param_dict

    def process_options(self):
        '''performs deep validation and value loading for options'''

        # ca_cert to verify
        self.boolean_or_cacert()

        # auth methods
        self.auth_methods()

        # secret field splitter
        self.field_ops()

    # begin options processing methods

    def boolean_or_cacert(self):
        # This is needed because of this (https://hvac.readthedocs.io/en/stable/source/hvac_v1.html):
        #
        # # verify (Union[bool,str]) - Either a boolean to indicate whether TLS verification should
        # # be performed when sending requests to Vault, or a string pointing at the CA bundle to use for verification.
        #
        '''' return a bool or cacert '''
        ca_cert = self.get_option('ca_cert')
        validate_certs = self.get_option('validate_certs')

        if not (validate_certs and ca_cert):
            self.set_option('ca_cert', validate_certs)

    def field_ops(self):
        # split secret and field
        secret = self.get_option('secret')

        s_f = secret.rsplit(':', 1)
        self.set_option('secret', s_f[0])
        if len(s_f) >= 2:
            field = s_f[1]
        else:
            field = None
        self.set_option('secret_field', field)

    def auth_methods(self):
        # enforce and set the list of available auth methods
        # TODO: can this be read from the choices: field in documentation?
        avail_auth_methods = ['token', 'approle', 'userpass', 'ldap', 'aws_iam_role']
        self.set_option('avail_auth_methods', avail_auth_methods)
        auth_method = self.get_option('auth_method')

        if auth_method not in avail_auth_methods:
            raise AnsibleError(
                "Authentication method '%s' not supported. Available options are %r" % (auth_method, avail_auth_methods)
            )

        # run validator if available
        auth_validator = 'validate_auth_' + auth_method
        if hasattr(self, auth_validator) and callable(getattr(self, auth_validator)):
            getattr(self, auth_validator)(auth_method)

    # end options processing methods

    # begin auth method validators

    def validate_by_required_fields(self, auth_method, *field_names):
        missing = [field for field in field_names if not self.get_option(field)]

        if missing:
            raise AnsibleError("Authentication method %s requires options %r to be set, but these are missing: %r" % (auth_method, field_names, missing))

    def validate_auth_userpass(self, auth_method):
        self.validate_by_required_fields(auth_method, 'username', 'password')

    def validate_auth_ldap(self, auth_method):
        self.validate_by_required_fields(auth_method, 'username', 'password')

    def validate_auth_approle(self, auth_method):
        self.validate_by_required_fields(auth_method, 'role_id', 'secret_id')

    def validate_auth_token(self, auth_method):
        if auth_method == 'token':
            if not self.get_option('token') and self.get_option('token_path'):
                token_filename = os.path.join(
                    self.get_option('token_path'),
                    self.get_option('token_file')
                )
                if os.path.exists(token_filename):
                    with open(token_filename) as token_file:
                        self.set_option('token', token_file.read().strip())

            if not self.get_option('token'):
                raise AnsibleError("No Vault Token specified or discovered.")

    def validate_auth_iam(self, auth_method):
        params = {
            'access_key': self.get_option('aws_access_key'),
            'secret_key': self.get_option('aws_secret_key')
        }

        if self.get_option('role_id'):
            params['role'] = self.get_option('role_id')

        if self.get_option('region'):
            params['region'] = self.get_option('region')

        if not (params['access_key'] and params['secret_key']):
            profile = self.get_option('aws_profile')
            if profile:
                # try to load boto profile
                if not HAS_BOTO3:
                    raise AnsibleError("boto3 is required for loading a boto profile.")
                session_credentials = boto3.session.Session(profile_name=profile).get_credentials()
            else:
                # try to load from IAM credentials
                if not HAS_BOTOCORE:
                    raise AnsibleError("botocore is required for loading IAM role credentials.")
                session_credentials = botocore.session.get_session().get_credentials()

            if not session_credentials:
                raise AnsibleError("No AWS credentials supplied or available.")

            params['access_key'] = session_credentials.access_key
            params['secret_key'] = session_credentials.secret_key
            if session_credentials.token:
                params['session_token'] = session_credentials.token

        self.set_option('iam_login_credentials', params)

    # end auth method validators
