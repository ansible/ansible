#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: pfsense_haproxy_backend_server
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense haproxy backend servers
description:
  - Manage pfSense haproxy servers
notes:
options:
  backend:
    description: The backend name.
    required: true
    type: str
  name:
    description: The server name.
    required: true
    type: str
  mode:
    description: How to use the server.
    required: false
    type: str
    choices: ['active', 'backup', 'disabled', 'inactive']
    default: 'active'
  forwardto:
    description: The name of the frontend to forward. When None, forwards to address and port
    required: false
    type: str
  address:
    description: IP or hostname of the backend (only resolved on start-up.)
    required: false
    type: str
  port:
    description: The port of the backend.
    required: false
    type: int
  ssl:
    description: Should haproxy encrypt the traffic to the backend with SSL (commonly used with mode http on frontend and a port 443 on backend).
    required: false
    type: bool
  checkssl:
    description: This can be used with for example a LDAPS health-checks where LDAPS is passed along with mode TCP
    required: false
    type: bool
  weight:
    description: >
      A weight between 0 and 256, this setting can be used when multiple servers on different hardware need to be balanced with a different part the traffic.
      A server with weight 0 wont get new traffic. Default if empty: 1
    required: false
    type: int
  sslserververify:
    description: SSL servers only, The server certificate will be verified against the CA and CRL certificate configured below.
    required: false
    type: bool
  verifyhost:
    description: SSL servers only, when set, must match the hostnames in the subject and subjectAlternateNames of the certificate provided by the server.
    required: false
    type: str
  ca:
    description: SSL servers only, set the CA authority to check the server certificate against.
    required: false
    type: str
  crl:
    description: SSL servers only, set the CRL to check revoked certificates.
    required: false
    type: str
  clientcert:
    description: SSL servers only, This certificate will be sent if the server send a client certificate request.
    required: false
    type: str
  cookie:
    description: Persistence only, Used to identify server when cookie persistence is configured for the backend.
    required: false
    type: str
  maxconn:
    description: Tuning, If the number of incoming concurrent requests goes higher than this value, they will be queued
    required: false
    type: int
  advanced:
    description: Allows for adding custom HAProxy settings to the server. These are passed as written, use escaping where needed.
    required: false
    type: str
  istemplate:
    description: If set, configures this server item as a template to provision servers from dns/srv responses.
    required: false
    type: str
  state:
    description: State in which to leave the backend server
    choices: [ "present", "absent" ]
    default: present
    type: str
"""

EXAMPLES = """
- name: Add backend server
  pfsense_haproxy_backend_server:
    backend: exchange
    name: exchange.acme.org
    address: exchange.acme.org
    port: 443
    state: present

- name: Remove backend server
  pfsense_haproxy_backend:
    backend: exchange
    name: exchange.acme.org
    state: absent
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: [
        "create haproxy_backend_server 'exchange.acme.org' on 'exchange', status='active', address='exchange.acme.org', port=443",
        "delete haproxy_backend_server 'exchange.acme.org' on 'exchange'"
    ]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.haproxy_backend_server import (
    PFSenseHaproxyBackendServerModule,
    HAPROXY_BACKEND_SERVER_ARGUMENT_SPEC,
    HAPROXY_BACKEND_SERVER_MUTUALLY_EXCLUSIVE,
)


def main():
    module = AnsibleModule(
        argument_spec=HAPROXY_BACKEND_SERVER_ARGUMENT_SPEC,
        mutually_exclusive=HAPROXY_BACKEND_SERVER_MUTUALLY_EXCLUSIVE,
        supports_check_mode=True)

    pfmodule = PFSenseHaproxyBackendServerModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
