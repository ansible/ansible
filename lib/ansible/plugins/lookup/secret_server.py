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
        terms:
            description:
                - The list of keys to lookup on the Secret Server.
            type: list
            elements: string
            required: True
        username:
            description:
                - Username for the Secret Server user.
            default: None
            type: string
            env:
                - name: SS_USER_ANSIBLE
            required: true (either ENV or kwargs)
        password:
            description:
                - Password for the Secret Server user.
            default: None
            type: string
            env:
                - name: SS_PASSWORD_ANSIBLE
            required: true (either ENV or kwargs)
        domain:
            description:
                - Domain for the organisation in the Secret Server.
            default: None
            type: string
            env:
                - name: SS_DOMAIN_ANSIBLE
            required: false (required only with SAAS)
        address:
            description:
                - FQDN / IP for the Secret Server.
            default: None
            type: string
            env:
                - name: SS_ADDRESS_ANSIBLE
            required: true (either ENV or kwargs)
        key:
            description:
                - Name of the key for which you want to obtain the value.
            default: password
            type: string
            required: false
'''

EXAMPLES = '''
    - name: "Get passowrd for customer_1 with ENV variables"
      debug:
        msg: "{{ lookup('secret_server', 'customer_1') }}"

    - name: "Get Key=Username for customer_1 with ENV variables"
      debug:
        msg: "{{ lookup('secret_server', 'customer_1', key='username') }}"

    - name: "Get passowrd for customer_1"
      debug:
        msg: >
            "{{ lookup('secret_server', 'customer_1',
            address='server1.example.com', domain='example.com',
            username='awesome_user', password='awesome_password') }}"
'''

RETURN = '''
    raw:
        description:
            - List of values associated with input keys.
        type: list
        elements: strings
'''

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
import os

try:
    import requests
    import urllib3
    from __main__ import display
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

if os.getenv('SS_ADDRESS_ANSIBLE') is not None:
    SS_ADDRESS_ANSIBLE = os.getenv('SS_ADDRESS_ANSIBLE')
else:
    SS_ADDRESS_ANSIBLE = None


class SecretServer(object):
    def __init__(self, username=None, password=None, secret_key=None,
                 domain=None, address=None, key='password'):
        self.username = username
        self.password = password
        self.secret_key = secret_key
        self.domain = domain
        self.address = address
        self.key = key

    def connect_api(self, path, address, auth_key=None, method='GET',
                    connection='secure', headers=None, body=None):

        if connection.upper() == 'SECURE':
            connection = 'https://'
        else:
            connection = 'http://'

        api_url = "{0}{1}" . format(connection, address)
        url = "{0}{1}" . format(api_url, path)

        if not headers:
            headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer' + ' ' + auth_key
                    }
        if method.upper() == 'GET':
            r = requests.request(method, url, headers=headers, verify=False)
        else:
            r = requests.request(method, url, data=body, headers=headers)
        return r.json()

    def get_token(self):
        user = self.username
        password = self.password
        domain = self.domain

        if domain:
            body = 'username={0}&password={1}&domain={2}&grant_type=password'.format(
                    user, password, domain)
        else:
            body = 'username={0}&password={1}&grant_type=password'.format(
                    user, password)
        method = 'POST'
        path = '/oauth2/token'
        headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
        }
        api = self.connect_api(path, self.address, method=method, body=body,
                               headers=headers)
        if api.get('access_token'):
            global token
            token = api['access_token']
        else:
            raise AnsibleError("Secret Server Error: {0}".format(api))

    def find_secret_id(self):
        secret = self.secret_key

        path = '/api/v1/secrets?filter.searchText={0}'.format(secret)
        api = self.connect_api(path, self.address, auth_key=token)
        if api.get('records'):
            return api['records'][0]['id']
        else:
            raise AnsibleError("Secret Server Error: {0}".format(api))

    def get_the_secret_value(self):
        secret_id = self.find_secret_id()
        key = self.key

        path = '/api/v1/secrets/{0}/fields/{1}'.format(secret_id, key)
        api = self.connect_api(path, self.address, auth_key=token)
        return api


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        # We are going to disable SSl Certificate warnings
        urllib3.disable_warnings()

        username = kwargs.get('username', SS_USER_ANSIBLE)
        password = kwargs.get('password', SS_PASSWORD_ANSIBLE)
        domain = kwargs.get('domain', SS_DOMAIN_ANSIBLE)
        address = kwargs.get('address', SS_ADDRESS_ANSIBLE)
        key = kwargs.get('key', 'password')

        ret = []

        for term in terms:

            display.vvvv("Searching for value for {0}".format(term))
            secret_key = term
            if domain:
                ss = SecretServer(username=username, password=password,
                                  secret_key=secret_key, domain=domain,
                                  address=address, key=key)
            else:
                ss = SecretServer(username=username, password=password,
                                  secret_key=secret_key, address=address,
                                  key=key)
            ss.get_token()
            value = ss.get_the_secret_value()
            ret.append(value)

        return ret
