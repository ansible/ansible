# (c) 2017, Oren Ben Meir <oren.benmeir@cyberark.com>, Jason Vanderhoof <jason.vanderhoof@cyberark.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: conjur_variable
    version_added: "2.5"
    short_description: Fetch credentials from CyberArk Conjur.
    description:
      - Retrieves credentials from Conjur using the server's Conjur identity.
    requirements:
      - The machine running Ansible has been given a Conjur identity.
    options:
      _term:
        description: Variable path
        required: True
"""

EXAMPLES = """
  - debug
    msg: {{ lookup('conjur_variable', '/path/to/secret') }}
"""

RETURN = """
  _raw:
    description:
      - Value stored in Conjur.
"""

import os.path
import ssl
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from base64 import b64encode
from httplib import HTTPSConnection
from httplib import HTTPConnection
from netrc import netrc
from os import environ
from time import time
from urllib import quote_plus
from urlparse import urlparse


class Token:
    def __init__(self, http_connection, id, api_key, account):
        self.http_connection = http_connection
        self.id = id
        self.api_key = api_key
        self.token = None
        self.refresh_time = 0
        self.account = account

    # refresh
    # Exchanges API key for an auth token, storing it base64 encoded within the
    # 'token' member variable. If it fails to obtain a token, the process exits.
    def refresh(self):

        authn_url = '/authn/{}/{}/authenticate'.format(quote_plus(self.account), quote_plus(self.id))
        self.http_connection.request('POST', authn_url, self.api_key)

        response = self.http_connection.getresponse()

        if response.status != 200:
            raise Exception('Failed to authenticate as \'{}\''.format(self.id))

        self.token = b64encode(response.read())
        self.refresh_time = time() + 5 * 60

    # get_header_value
    # Returns the value for the Authorization header. Refreshes the auth token
    # before returning if necessary.
    def get_header_value(self):
        if time() >= self.refresh_time:
            self.refresh()

        return 'Token token="{}"'.format(self.token)

class LookupModule(LookupBase):
    def retrieve_secrets(self, conf, conjur_https, token, terms):

        secrets = []
        for term in terms:
            variable_name = term.split()[0]
            headers = {'Authorization': token.get_header_value()}
            url = '/secrets/{}/variable/{}'.format(conf['account'], quote_plus(variable_name))

            conjur_https.request('GET', url, headers=headers)
            response = conjur_https.getresponse()
            if response.status != 200:
                raise Exception('Failed to retrieve variable \'{}\' with response status: {} {}'.format(variable_name,
                                                                                                        response.status,
                                                                                                        response.reason))

            secrets.append(response.read())

        return secrets

    def run(self, terms, variables=None, **kwargs):
        # Load Conjur configuration
        conf = self.merge_dictionaries(
            self.load_conf('/etc/conjur.conf'),
            self.load_conf('~/.conjurrc'),
            {
                "account": environ.get('CONJUR_ACCOUNT'),
                "appliance_url": environ.get("CONJUR_APPLIANCE_URL"),
                "cert_file": environ.get('CONJUR_CERT_FILE')
            } if (environ.get('CONJUR_ACCOUNT') is not None and environ.get('CONJUR_APPLIANCE_URL')
                  is not None and (environ.get('CONJUR_APPLIANCE_URL').startswith('https') is not True or environ.get('CONJUR_CERT_FILE') is not None))
            else {}
        )
        if not conf:
            raise Exception('Conjur configuration should be in environment variables or in one of the following paths: \'~/.conjurrc\', \'/etc/conjur.conf\'')

        # Load Conjur identity
        identity = self.merge_dictionaries(
            self.load_identity('/etc/conjur.identity', conf['appliance_url']),
            self.load_identity('~/.netrc', conf['appliance_url']),
            {
                "id": environ.get('CONJUR_AUTHN_LOGIN'),
                "api_key": environ.get('CONJUR_AUTHN_API_KEY')
            } if (environ.get('CONJUR_AUTHN_LOGIN') is not None and environ.get('CONJUR_AUTHN_API_KEY') is not None)
            else {}
        )
        if not identity:
            raise Exception('Conjur identity should be in environment variables or in one of the following paths: \'~/.netrc\', \'/etc/conjur.identity\'')

        if conf['appliance_url'].startswith('https'):
            # Load our certificate for validation
            ssl_context = ssl.create_default_context()
            ssl_context.load_verify_locations(conf['cert_file'])
            conjur_connection = HTTPSConnection(urlparse(conf['appliance_url']).netloc,
                                       context = ssl_context)
        else:
            conjur_connection = HTTPConnection(urlparse(conf['appliance_url']).netloc)

        token = Token(conjur_connection, identity['id'], identity['api_key'], conf['account'])

        # retrieve secrets of the given variables from Conjur
        return self.retrieve_secrets(conf, conjur_connection, token, terms)

    # if the conf is not in the path specified, or if an exception is thrown while reading the conf file
    # we don't exit as the conf might be in another path
    def load_conf(self, conf_path):
        conf_path = os.path.expanduser(conf_path)

        if not os.path.isfile(conf_path):
            return {}

        try:
            config_map = {}
            lines = open(conf_path).read().splitlines()
            for line in lines:
                if line == '---':
                    continue
                parts = line.split(': ')
                config_map[parts[0]] = parts[1]
            return config_map
        except:
            pass

        return {}


    # if the identity is not in the path specified, or if an exception is thrown while reading the identity file
    # we don't exit as the identity might be in another path
    def load_identity(self, identity_path, appliance_url):
        identity_path = os.path.expanduser(identity_path)

        if not os.path.isfile(identity_path):
            return {}

        try:
            identity = netrc(identity_path)
            id, _, api_key = identity.authenticators('{}/authn'.format(appliance_url))
            if not id or not api_key:
                return {}

            return {"id": id, "api_key": api_key}
        except:
            pass

        return {}


    def merge_dictionaries(self, *arg):
        ret = {}
        for a in arg:
            ret.update(a)
        return ret
