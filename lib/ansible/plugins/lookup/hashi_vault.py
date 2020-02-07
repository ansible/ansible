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
    - hvac 0.9.6+ (to avoid all deprecation warnings)
    - botocore (only if inferring aws params from boto)
    - boto3 (only if using a boto profile)
  description:
    - Retrieve secrets from HashiCorp's vault.
  notes:
    - Due to a current limitation in the HVAC library there won't necessarily be an error if a bad endpoint is specified.
    - As of Ansible 2.10, only the latest version of a secret is returned when specifying a KV v2 path.
    - As of Ansible 2.10, all options can be supplied via term string (space delimited key=value pairs) or by parameters (see examples).
    - As of Ansible 2.10, when C(secret) is the first option in the term string, C(secret=) is not required (see examples).
  options:
    secret:
      description: query you are making.
      required: True
    token:
      description:
        - Vault token. If using token auth and no token is supplied, explicitly or through env, then the plugin will check
        - for a token file, as determined by C(token_path) and C(token_file).
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
      description: Vault Role ID. Used in approle and aws_iam_login auth methods.
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
    return_format:
      version_added: "2.10"
      description:
        - Controls how multiple key/value pairs in a path are treated on return.
        - C(dict) returns a single dict containing the key/value pairs (same behavior as before 2.10).
        - C(values) returns a list of all the values only. Use when you don't care about the keys.
        - C(raw) returns the actual API result, which includes metadata and may have the data nested in other keys.
      choices:
        - dict
        - values
        - raw
      default: dict
      aliases: [ as ]
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

# The following examples work in Ansible 2.10+

- name: secret= is not required if secret is first
  debug:
    msg: "{{ lookup('hashi_vault', 'secret/data/hello token=<token> url=http://myvault_url:8200') }}"

- name: options can be specified as parameters rather than put in term string
  debug:
    msg: "{{ lookup('hashi_vault', 'secret/data/hello', token=my_token_var, url='http://myvault_url:8200') }}"

# return_format (or its alias 'as') can control how secrets are returned to you
- name: return secrets as a dict (default)
  set_fact:
    my_secrets: "{{ lookup('hashi_vault', 'secret/data/manysecrets', token=my_token_var, url='http://myvault_url:8200') }}"
- debug:
    msg: "{{ my_secrets['secret_key'] }}"
- debug:
    msg: "Secret '{{ item.key }}' has value '{{ item.value }}'"
  loop: "{{ my_secrets | dict2items }}"

- name: return secrets as values only
  debug:
    msg: "A secret value: {{ item }}"
  loop: "{{ query('hashi_vault', 'secret/data/manysecrets', token=my_token_var, url='http://myvault_url:8200', return_format='values') }}"

- name: return raw secret from API, including metadata
  set_fact:
    my_secret: "{{ lookup('hashi_vault', 'secret/data/hello:value', token=my_token_var, url='http://myvault_url:8200', as='raw') }}"
- debug:
    msg: "This is version {{ my_secret['metadata']['version'] }} of hello:value. The secret data is {{ my_secret['data']['data']['value'] }}"

# AWS IAM authentication method
# uses Ansible standard AWS options

- name: authenticate with aws_iam_login
  debug:
    msg: "{{ lookup('hashi_vault', 'secret/hello:value', auth_method='aws_iam_login' role_id='myroleid', profile=my_boto_profile, url='http://myvault:8200') }}"
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

        # this is the only auth_method-specific thing here, because if we're using a token, we need it now
        if self.options['auth_method'] == 'token':
            client_args['token'] = self.options.get('token')

        self.client = hvac.Client(**client_args)

        # Check for old version, before auth_methods class (added in 0.7.0):
        # https://github.com/hvac/hvac/releases/tag/v0.7.0
        #
        # hvac is moving auth methods into the auth_methods class
        # which lives in the client.auth member.
        #
        # Attempting to find which backends were moved into the class when (this is primarily for warnings):
        # 0.7.0 -- github, ldap, mfa, azure?, gcp
        # 0.7.1 -- okta
        # 0.8.0 -- kubernetes
        # 0.9.0 -- azure?, radius
        # 0.9.3 -- aws
        # 0.9.6 -- userpass
        self.hvac_has_auth_methods = hasattr(self.client, 'auth')

    # We've already checked to ensure a method exists for a particular auth_method, of the form:
    #
    # auth_<method_name>
    #
    def authenticate(self):
        getattr(self, self.auth_function)()

    def get(self):
        '''gets a secret. should always return a list'''
        secret = self.options['secret']
        field = self.options['secret_field']
        return_as = self.options['return_format']

        try:
            data = self.client.read(secret)
        except hvac.exceptions.Forbidden:
            raise AnsibleError("Forbidden: Permission Denied to secret '%s'." % secret)

        if data is None:
            raise AnsibleError("The secret '%s' doesn't seem to exist." % secret)

        if return_as == 'raw':
            return [data]

        # Check response for KV v2 fields and flatten nested secret data.
        # https://vaultproject.io/api/secret/kv/kv-v2.html#sample-response-1
        try:
            # sentinel field checks
            check_dd = data['data']['data']
            check_md = data['data']['metadata']
            # unwrap nested data
            data = data['data']
        except KeyError:
            pass

        if return_as == 'values':
            return list(data['data'].values())

        # everything after here implements return_as == 'dict'
        if not field:
            return [data['data']]

        if field not in data['data']:
            raise AnsibleError("The secret %s does not contain the field '%s'. for hashi_vault lookup" % (secret, field))

        return [data['data'][field]]

    # begin auth implementation methods
    #
    # To add new backends, 3 things should be added:
    #
    # 1. Add a new validate_auth_<method_name> method to the LookupModule, which is responsible for validating
    #    that it has the necessary options and whatever else it needs.
    #
    # 2. Add a new auth_<method_name> method to this class. These implementations are faily minimal as they should
    #    already have everything they need. This is also the place to check for deprecated auth methods as hvac
    #    continues to move backends into the auth_methods class.
    #
    # 3. Update the avail_auth_methods list in the LookupModules auth_methods() method (for now this is static).
    #
    def auth_token(self):
        if not self.client.is_authenticated():
            raise AnsibleError("Invalid Hashicorp Vault Token Specified for hashi_vault lookup.")

    def auth_userpass(self):
        params = self.get_options('username', 'password', 'mount_point')
        if self.hvac_has_auth_methods and hasattr(self.client.auth.userpass, 'login'):
            self.client.auth.userpass.login(**params)
        else:
            Display().warning("HVAC should be updated to version 0.9.6 or higher. Deprecated method 'auth_userpass' will be used.")
            self.client.auth_userpass(**params)

    def auth_ldap(self):
        params = self.get_options('username', 'password', 'mount_point')
# not hasattr(self.client, 'auth')
        if self.hvac_has_auth_methods and hasattr(self.client.auth.ldap, 'login'):
            self.client.auth.ldap.login(**params)
        else:
            Display().warning("HVAC should be updated to version 0.7.0 or higher. Deprecated method 'auth_ldap' will be used.")
            self.client.auth_ldap(**params)

    def auth_approle(self):
        params = self.get_options('role_id', 'secret_id')
        self.client.auth_approle(**params)

    def auth_aws_iam_login(self):
        params = self.options['iam_login_credentials']
        if self.hvac_has_auth_methods and hasattr(self.client.auth.aws, 'iam_login'):
            self.client.auth.aws.iam_login(**params)
        else:
            Display().warning("HVAC should be updated to version 0.9.3 or higher. Deprecated method 'auth_aws_iam' will be used.")
            self.client.auth_aws_iam(**params)

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
            # FUTURE: Create one object, authenticate once, and re-use it,
            # for gets, for better use during with_ loops.
            client = HashiVault(**self._options)
            client.authenticate()
            ret.extend(client.get())

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
        avail_auth_methods = ['token', 'approle', 'userpass', 'ldap', 'aws_iam_login']
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

    def validate_auth_aws_iam_login(self, auth_method):
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
