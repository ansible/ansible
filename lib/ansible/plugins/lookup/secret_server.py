# Copyright (c) 2018 Michal Taratuta <michalta@Softcat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
    author:
        - Michal Taratuta (@MichalTaratuta for Softcat.com)
    lookup: secret_server
    short_description: Get secret from a Secret Server.
    description:
        - Retrieves data from a Secret Server.
    options:
        _terms:
            description:
                - The list of keys to lookup on the Secret Server, if a key has
                  a 'space' in a name, it needs to be replace with a '+' sign.
                  i.e. 'test space name' => 'test+space+name'
            type: list
            elements: string
            required: True
        username:
            description:
                - Username for the Secret Server user.
            type: string
            env:
                - name: SS_USER_ANSIBLE
            required: true (either ENV or kwargs)
        password:
            description:
                - Password for the Secret Server user.
            type: string
            env:
                - name: SS_PASSWORD_ANSIBLE
            required: true (either ENV or kwargs)
        domain:
            description:
                - Domain for the organisation in the Secret Server.
            type: string
            env:
                - name: SS_DOMAIN_ANSIBLE
            required: false (required only with SAAS)
        url:
            description:
                - FQDN / IP for the Secret Server.
            type: string
            env:
                - name: SS_URL_ANSIBLE
            required: true (either ENV or kwargs)
        key_type:
            description:
                - Name of the key for which you want to obtain the value.
            default: password
            type: string
            required: false
        validate_certs:
            description:
                - If False, SSL certificates will not be validated.
            default: True
            type: boolean
'''

EXAMPLES = '''
    - name: "Get passowrd for customer_1 with ENV variables"
      debug:
        msg: "{{ lookup('secret_server', 'customer_1') }}"

    - name: "Get key_type=username for customer_1 with ENV variables"
      debug:
        msg: "{{ lookup('secret_server', 'customer_1', key_type='username') }}"

    - name: "Find passsword for key with spaces i.e. 'test+space+name'"
      debug:
        msg: "{{ lookup('secret_server', 'test+space+name') }}"

        'test+space+name'

    - name: "Get passowrd for customer_1"
      debug:
        msg: >
            "{{ lookup('secret_server', 'customer_1',
            address='server1.example.com', domain='example.com',
            username='awesome_user', password='awesome_password') }}"
'''

RETURN = '''
    _raw:
        description:
            - List of values associated with input keys.
        type: list
        elements: strings
'''


try:
    from __main__ import display
    from ansible.errors import AnsibleError
    from ansible.plugins.lookup import LookupBase
    from ansible.module_utils.urls import open_url
    import os
    import json
except ImportError:
    from ansible.utils.display import Display
    display = Display()

# Check if ENV variables are present
if os.getenv('SS_USER_ANSIBLE') is not None:
    SS_USER_ANSIBLE = os.getenv('SS_USER_ANSIBLE')
else:
    SS_USER_ANSIBLE = None

if os.getenv('SS_PASSWORD_ANSIBLE') is not None:
    SS_PASSWORD_ANSIBLE = os.getenv('SS_PASSWORD_ANSIBLE')
else:
    SS_PASSWORD_ANSIBLE = None

if os.getenv('SS_DOMAIN_ANSIBLE') is not None:
    SS_DOMAIN_ANSIBLE = os.getenv('SS_DOMAIN_ANSIBLE')
else:
    SS_DOMAIN_ANSIBLE = None

if os.getenv('SS_URL_ANSIBLE') is not None:
    SS_URL_ANSIBLE = os.getenv('SS_URL_ANSIBLE')
else:
    SS_URL_ANSIBLE = None


class SecretServer(object):
    def __init__(self, validate_certs, url, key_type, username=None,
                 password=None, secret_key=None, domain=None):
        self.validate_certs = validate_certs
        self.url = url
        self.key_type = key_type
        self.username = username
        self.password = password
        self.secret_key = secret_key
        self.domain = domain

    def connect_api(self, url, path, auth_key=None,
                    method='GET', headers=None, data=None):

        api_url = "{0}{1}" . format(url, path)
        validate_certs = self.validate_certs

        if not headers:
            headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer' + ' ' + auth_key
                    }
        if method.upper() == 'GET':
            r = open_url(api_url, headers=headers,
                         validate_certs=validate_certs)
        else:
            r = open_url(api_url, method=method, data=data, headers=headers,
                         validate_certs=validate_certs)
        return json.loads(r.read())

    def get_token(self):
        user = self.username
        password = self.password
        domain = self.domain
        url = self.url

        if domain:
            data = 'username={0}&password={1}&domain={2}&grant_type=password'.format(
                    user, password, domain)
        else:
            data = 'username={0}&password={1}&grant_type=password'.format(
                    user, password)
        method = 'POST'
        path = '/oauth2/token'
        headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
        }
        api = self.connect_api(self.url, path, method=method, data=data,
                               headers=headers)
        if api.get('access_token'):
            global token
            token = api['access_token']
        else:
            raise AnsibleError("Secret Server Error: {0}".format(api))

    def find_secret_id(self):
        secret = self.secret_key

        path = '/api/v1/secrets?filter.searchText={0}'.format(secret)
        api = self.connect_api(self.url, path, auth_key=token)
        if api.get('records'):
            return api['records'][0]['id']
        else:
            raise AnsibleError("Secret Server Error: {0}".format(api))

    def get_the_secret_value(self):
        secret_id = self.find_secret_id()
        key_type = self.key_type

        path = '/api/v1/secrets/{0}/fields/{1}'.format(secret_id, key_type)
        api = self.connect_api(self.url, path, auth_key=token)
        return api


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        validate_certs = kwargs.get('validate_certs', True)
        url = kwargs.get('url', SS_URL_ANSIBLE)
        username = kwargs.get('username', SS_USER_ANSIBLE)
        password = kwargs.get('password', SS_PASSWORD_ANSIBLE)
        domain = kwargs.get('domain', SS_DOMAIN_ANSIBLE)
        key_type = kwargs.get('key_type', 'password')

        ret = []

        for term in terms:

            display.vvvv("Searching for value for {0}".format(term))
            secret_key = term
            if domain:
                ss = SecretServer(validate_certs=validate_certs, url=url,
                                  username=username, password=password,
                                  secret_key=secret_key, domain=domain,
                                  key_type=key_type)
            else:
                ss = SecretServer(validate_certs=validate_certs, url=url,
                                  username=username, password=password,
                                  secret_key=secret_key, key_type=key_type)
            ss.get_token()
            value = ss.get_the_secret_value()
            ret.append(value)

        return ret
