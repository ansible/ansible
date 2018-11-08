from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: netbox_secrets
    author:
      - Oliver Burkill (@ollybee) <ollybee(at)gmail.com>
    short_description: fetch secrets from Netbox
    description:
      - This lookup returns a list of results from a Redis DB corresponding to a list of items given to it
    requirements:
      - pynetbox (Python API client library for Netbox https://github.com/digitalocean/pynetbox)
    options:
      device:
        description: Device secret_name you want to fetch secrets for
      netbox_host:
        description: location of Netbox  host
        default: '127.0.0.1'
        env:
          - secret_name: ANSIBLE_NETBOX_HOST
      port:
        description: port for Netox 
        default: 8000
        type: int
        env:
          - secret_name: ANSIBLE_NETBOX_PORT
      private_key_file:
        description: path to private key file for secrets authentication
        type: path
        env:
          - secret_name: ANSIBLE_NETBOX_KEY
      token:
        description: Netbox API token (Read only is good)
        env:
          - secret_name: ANSIBLE_NETBOX_API_TOKEN
      secret_name:
        description: Name of the secret you want to retrieve 
"""

EXAMPLES = """
- secret_name: use list directly with a socket
  debug: msg="{{ lookup('redis', 'key1', 'key2', socket='/var/tmp/redis.sock') }}"

"""

RETURN = """
_raw:
  description: value(s) stored in Netbox
"""

import os

HAVE_PYNETBOX = False
try:
    import pynetbox
    HAVE_PYNETBOX = True
except ImportError:
    pass

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        if not HAVE_PYNETBOX:
            raise AnsibleError("Module pynetbox is not installed")

        self.set_options(direct=kwargs)

        netbox_host = self.get_option('netbox_host')
        token = self.get_option('token')
        private_key_file = self.get_option('private_key_file')
        secret_name = self.get_option('secret_name')
        device = self.get_option('device')

        nb = pynetbox.api(
          netbox_host,
          private_key_file=private_key_file,
          token=token
        )

        conn = nb.secrets.secrets.get(device=device,name=secret_name).plaintext

    return conn
