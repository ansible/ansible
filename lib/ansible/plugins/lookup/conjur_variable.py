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
from ansible.module_utils.six.moves.urllib.parse import quote_plus
import yaml

from ansible.module_utils.urls import open_url

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        conf = self.load_configuration()
        identity = self.load_identity(conf['appliance_url'])

        # Use credentials to retrieve temporary authorization token
        conjur_url = '{0}/authn/{1}/{2}/authenticate'.format(conf['appliance_url'], conf['account'], identity['id'])
        display.vvvv('Authentication request to Conjur at: {0}, with user: {1}'.format(conjur_url, identity['id']))

        response = open_url(conjur_url, data=identity['api_key'], method='POST')

        if response.getcode() != 200:
            raise AnsibleError('Failed to authenticate as \'{0}\''.format(identity['id']))

        # Retrieve Conjur variable using the temporary token
        token = b64encode(response.read())
        headers = {'Authorization': 'Token token="{0}"'.format(token)}
        display.vvvv('Header: {0}'.format(headers))

        url = '{0}/secrets/{1}/variable/{2}'.format(conf['appliance_url'], conf['account'], quote_plus(terms[0]))
        display.vvvv('Conjur Variable URL: {0}'.format(url))

        response = open_url(url, headers=headers, method='GET')

        if response.getcode() == 200:
            display.vvvv('Conjur variable {0} was successfully retrieved'.format(terms[0]))
            return [response.read()]
        if response.getcode() == 401:
            raise AnsibleError('Conjur request has invalid authorization credentials')
        if response.getcode() == 403:
            raise AnsibleError('Conjur host does not have authorization to retrieve {0}'.format(terms[0]))
        if response.getcode() == 404:
            raise AnsibleError('The variable {0} does not exist'.format(terms[0]))

    # Load Conjur configuration from either `/etc/conjur.conf` or `~/.conjurrc`
    def load_configuration(self):
        for location in ['~/.conjurrc', '/etc/conjur.conf']:
            conf = self.load_conf_from_file(location)
            if conf:
                display.vvvv('configuration: {0}'.format(conf))
                return conf

        raise AnsibleError('Conjur configuration should be in one of the following files: \'~/.conjurrc\', \'/etc/conjur.conf\'')

    # Load Conjur identity from either `/etc/conjur.identity`, or `~/.netrc`
    def load_identity(self, appliance_url):
        for location in ['~/.netrc', '/etc/conjur.identity']:
            identity = self.load_identity_from_file(location, appliance_url)
            if identity:
                display.vvvv('configuration: {0}'.format(identity))
                return identity

        raise AnsibleError('Conjur identity should be in environment variables or in one of the following paths: \'~/.netrc\', \'/etc/conjur.identity\'')

    # Load identity and return as dictionary if file is present on file system
    def load_identity_from_file(self, identity_path, appliance_url):
        identity_path = os.path.expanduser(identity_path)

        if os.path.exists(identity_path):
            display.vvvv('Loading identity from: {0}'.format(identity_path))
            try:
                identity = netrc(identity_path)
                id, account, api_key = identity.authenticators('{0}/authn'.format(appliance_url))
                if not id or not api_key:
                    return {}

                return {'id': id, 'api_key': api_key}
            except Exception as exception:
                raise AnsibleError('Error: parsing {0} - {1}'.format(identity_path, str(exception)))

        return {}
