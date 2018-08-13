# (c) 2018, Yunge Zhu <yungez@microsoft.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy
import os
import random
import requests
import shlex
import shutil
import subprocess
import sys
import tempfile
import warnings
from binascii import hexlify
from binascii import unhexlify
from binascii import Error as BinasciiError

from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils._text import to_bytes, to_text, to_native

try:
    from __main__ import display
    from azure.keyvault import KeyVaultClient, KeyVaultAuthentication, KeyVaultId
    from azure.keyvault.models.key_vault_error import KeyVaultErrorException
except ImportError:
    from ansible.utils.display import Display
    display = Display()

MSI_ENDPOINT = 'http://169.254.169.254/metadata/identity/oauth2/token'
AZURE_VAULT_RESOURCE_URI = 'https://vault.azure.net'


def get_secret(vault_uri, secret_name, secret_version):

    try:
        client = get_client()
        secret_bundle = client.get_secret(vault_uri, secret_name, secret_version)

        if secret_bundle:
            return secret_bundle.value
    except KeyVaultErrorException as e:
        raise AnsibleError("Failed to get secret from Azure Key Vault: {0}".format(str(e)))

    return None


def get_client():
    def get_token_from_MSI(server, resource, scope):
        token_params = {
            'api-version': '2018-02-01',
            'resource': AZURE_VAULT_RESOURCE_URI
        }
        token_headers = { 'Metadata': 'true'}

        try:
            token_res = requests.get(MSI_ENDPOINT, params=token_params, headers=token_headers)
            token = token_res.json()["access_token"]
            token_type = token_res.json()["token_type"]
            return token_type, token
        except requests.exceptions.RequestException as e:
            display.warning("Unable to fetch MSI token. {0}".format(e))
        return None
    
    return KeyVaultClient(KeyVaultAuthentication(get_token_from_MSI))

