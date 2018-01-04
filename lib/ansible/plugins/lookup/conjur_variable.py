# (c) 2017, Jason Vanderhoof <jason.vanderhoof@cyberark.com>, Oren Ben Meir <oren.benmeir@cyberark.com>
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
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from base64 import b64encode
from netrc import netrc
from os import environ
from time import time
from urllib import quote_plus
import yaml

import requests
from requests.auth import HTTPBasicAuth

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        # Load Conjur configuration
        conf = self.merge_dictionaries(
            self.load_conf('/etc/conjur.conf'),
            self.load_conf('~/.conjurrc')
        )
        if not conf:
            raise AnsibleError('Conjur configuration should be in one of the following files: \'~/.conjurrc\', \'/etc/conjur.conf\'')
        display.vvvv('configuration: {0}'.format(conf))

        # Load Conjur identity
        identity = self.merge_dictionaries(
            self.load_identity('/etc/conjur.identity', conf['appliance_url']),
            self.load_identity('~/.netrc', conf['appliance_url'])
        )
        if not identity:
            raise AnsibleError('Conjur identity should be in environment variables or in one of the following paths: \'~/.netrc\', \'/etc/conjur.identity\'')
        display.vvvv('configuration: {0}'.format(identity))

        # Use credentials to retrieve temporary authorization token
        conjur_url = '{0}/authn/{1}/{2}/authenticate'.format(conf['appliance_url'], conf['account'], identity['id'])
        display.vvvv('Authentication request to Conjur at: {0}, with user: {1}'.format(conjur_url, identity['id']))

        if 'cert_file' in conf:
            response = requests.post(conjur_url, data=identity['api_key'], verify=conf['cert_file'])
        else:
            response = requests.post(conjur_url, data=identity['api_key'])
        display.vvvv('response: {0}'.format(response.text))

        if response.status_code != 200:
            raise AnsibleError('Failed to authenticate as \'{0}\''.format(identity['id']))

        # Retrieve Conjur variable using the temporary token
        token = b64encode(response.text)
        headers = {'Authorization': 'Token token="{0}"'.format(token)}
        display.vvvv('Header: {0}'.format(headers))

        url = '{0}/secrets/{1}/variable/{2}'.format(conf['appliance_url'], conf['account'], quote_plus(terms[0]))
        display.vvvv('Conjur Variable URL: {0}'.format(url))

        if 'cert_file' in conf:
            response = requests.get(url, headers=headers, verify=conf['cert_file'])
        else:
            response = requests.get(url, headers=headers)

        if response.status_code == 200:
            display.vvvv('Conjur variable {0} was successfully retrieved'.format(terms[0]))
            return [response.text]
        if response.status_code == 401:
            raise AnsibleError('Conjur request has invalid authorization credentials')
        if response.status_code == 403:
            raise AnsibleError('Conjur host does not have authorization to retrieve {0}'.format(terms[0]))
        if response.status_code == 404:
            raise AnsibleError('The variable {0} does not exist'.format(terms[0]))

    # Load configuration and return as dictionary if file is present on file system
    def load_conf(self, conf_path):
        conf_path = os.path.expanduser(conf_path)

        if conf_path and os.path.exists(conf_path):
            display.vvvv('Loading configuration from: {0}'.format(conf_path))
            with open(conf_path) as f:
                try:
                    return yaml.safe_load(f.read())
                except Exception as exception:
                    AnsibleError('Error: parsing {0} - {1}'.format(conf_path, str(exception)))
        return {}

    # Load identity and return as dictionary if file is present on file system
    def load_identity(self, identity_path, appliance_url):
        identity_path = os.path.expanduser(identity_path)

        if identity_path and os.path.exists(identity_path):
            display.vvvv('Loading identity from: {0}'.format(identity_path))
            try:
                identity = netrc(identity_path)
                id, account, api_key = identity.authenticators('{0}/authn'.format(appliance_url))
                if not id or not api_key:
                    return {}

                return {'id': id, 'api_key': api_key}
            except Exception as exception:
                AnsibleError('Error: parsing {0} - {1}'.format(identity_path, str(exception)))

        return {}

    def merge_dictionaries(self, *arg):
        ret = {}
        for a in arg:
            ret.update(a)
        return ret
