# (c) 2018, Jason Vanderhoof <jason.vanderhoof@cyberark.com>, Oren Ben Meir <oren.benmeir@cyberark.com>
# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
    lookup: conjur_variable
    version_added: "2.5"
    short_description: Fetch credentials from CyberArk Conjur.
    description:
      - "Retrieves credentials from Conjur using the controlling host's Conjur identity. Conjur info: U(https://www.conjur.org/)."
    requirements:
      - 'The controlling host running Ansible has a Conjur identity. (More: U(https://developer.conjur.net/key_concepts/machine_identity.html))'
    options:
      _term:
        description: Variable path
        required: True
      identity_file:
        description: Path to the Conjur identity file. The identity file follows the netrc file format convention.
        type: path
        default: /etc/conjur.identity
        required: False
        ini:
          - section: conjur,
            key: identity_file_path
        env:
          - name: CONJUR_IDENTITY_FILE
      config_file:
        description: Path to the Conjur configuration file. The configuration file is a YAML file.
        type: path
        default: /etc/conjur.conf
        required: False
        ini:
          - section: conjur,
            key: config_file_path
        env:
          - name: CONJUR_CONFIG_FILE
"""

EXAMPLES = """
  - debug:
      msg: "{{ lookup('conjur_variable', '/path/to/secret') }}"
"""

RETURN = """
  _raw:
    description:
      - Value stored in Conjur.
"""

import os.path
from ansible.errors import AnsibleError
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


# Load configuration and return as dictionary if file is present on file system
def _load_conf_from_file(conf_path):
    display.vvv('conf file: {0}'.format(conf_path))

    if not os.path.exists(conf_path):
        raise AnsibleError('Conjur configuration file `{0}` was not found on the controlling host'
                           .format(conf_path))

    display.vvvv('Loading configuration from: {0}'.format(conf_path))
    with open(conf_path) as f:
        config = yaml.safe_load(f.read())
        if 'account' not in config or 'appliance_url' not in config:
            raise AnsibleError('{0} on the controlling host must contain an `account` and `appliance_url` entry'
                               .format(conf_path))
        return config


# Load identity and return as dictionary if file is present on file system
def _load_identity_from_file(identity_path, appliance_url):
    display.vvvv('identity file: {0}'.format(identity_path))

    if not os.path.exists(identity_path):
        raise AnsibleError('Conjur identity file `{0}` was not found on the controlling host'
                           .format(identity_path))

    display.vvvv('Loading identity from: {0} for {1}'.format(identity_path, appliance_url))

    conjur_authn_url = '{0}/authn'.format(appliance_url)
    identity = netrc(identity_path)

    if identity.authenticators(conjur_authn_url) is None:
        raise AnsibleError('The netrc file on the controlling host does not contain an entry for: {0}'
                           .format(conjur_authn_url))

    id, account, api_key = identity.authenticators(conjur_authn_url)
    if not id or not api_key:
        raise AnsibleError('{0} on the controlling host must contain a `login` and `password` entry for {1}'
                           .format(identity_path, appliance_url))

    return {'id': id, 'api_key': api_key}


# Use credentials to retrieve temporary authorization token
def _fetch_conjur_token(conjur_url, account, username, api_key):
    conjur_url = '{0}/authn/{1}/{2}/authenticate'.format(conjur_url, account, username)
    display.vvvv('Authentication request to Conjur at: {0}, with user: {1}'.format(conjur_url, username))

    response = open_url(conjur_url, data=api_key, method='POST')
    code = response.getcode()
    if code != 200:
        raise AnsibleError('Failed to authenticate as \'{0}\' (got {1} response)'
                           .format(username, code))

    return response.read()


# Retrieve Conjur variable using the temporary token
def _fetch_conjur_variable(conjur_variable, token, conjur_url, account):
    token = b64encode(token)
    headers = {'Authorization': 'Token token="{0}"'.format(token)}
    display.vvvv('Header: {0}'.format(headers))

    url = '{0}/secrets/{1}/variable/{2}'.format(conjur_url, account, quote_plus(conjur_variable))
    display.vvvv('Conjur Variable URL: {0}'.format(url))

    response = open_url(url, headers=headers, method='GET')

    if response.getcode() == 200:
        display.vvvv('Conjur variable {0} was successfully retrieved'.format(conjur_variable))
        return [response.read()]
    if response.getcode() == 401:
        raise AnsibleError('Conjur request has invalid authorization credentials')
    if response.getcode() == 403:
        raise AnsibleError('The controlling host\'s Conjur identity does not have authorization to retrieve {0}'
                           .format(conjur_variable))
    if response.getcode() == 404:
        raise AnsibleError('The variable {0} does not exist'.format(conjur_variable))

    return {}


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        conf_file = self.get_option('config_file')
        conf = _load_conf_from_file(conf_file)

        identity_file = self.get_option('identity_file')
        identity = _load_identity_from_file(identity_file, conf['appliance_url'])

        token = _fetch_conjur_token(conf['appliance_url'], conf['account'], identity['id'], identity['api_key'])
        return _fetch_conjur_variable(terms[0], token, conf['appliance_url'], conf['account'])
