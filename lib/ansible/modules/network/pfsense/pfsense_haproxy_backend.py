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
module: pfsense_haproxy_backend
version_added: "2.10"
author: Frederic Bor (@f-bor)
short_description: Manage pfSense haproxy backends
description:
  - Manage pfSense haproxy backends
notes:
options:
  name:
    description: The backend name.
    required: true
    type: str
  balance:
    description: The load balancing option.
    required: false
    type: str
    choices: ['none', 'roundrobin', 'static-rr', 'leastconn', 'source', 'uri']
    default: 'none'
  balance_urilen:
    description: Indicates that the algorithm should only consider that many characters at the beginning of the URI to compute the hash.
    required: false
    type: int
  balance_uridepth:
    description: Indicates the maximum directory depth to be used to compute the hash. One level is counted for each slash in the request.
    required: false
    type: int
  balance_uriwhole:
    description: Allow using whole URI including url parameters behind a question mark.
    required: false
    type: bool
  connection_timeout:
    description: The time (in milliseconds) we give up if the connection does not complete within (default 30000).
    required: false
    type: int
  server_timeout:
    description: The time (in milliseconds) we accept to wait for data from the server, or for the server to accept data (default 30000).
    required: false
    type: int
  retries:
    description: After a connection failure to a server, it is possible to retry, potentially on another server.
    required: false
    type: int
  check_type:
    description: Health check method.
    type: str
    choices: ['none', 'Basic', 'HTTP', 'Agent', 'LDAP', 'MySQL', 'PostgreSQL', 'Redis', 'SMTP', 'ESMTP', 'SSL']
    default: 'none'
  check_frequency:
    description: The check interval (in milliseconds). For HTTP/HTTPS defaults to 1000 if left blank. For TCP no check will be performed if left empty.
    required: false
    type: int
  log_checks:
    description: When this option is enabled, any change of the health check status or to the server's health will be logged.
    required: false
    type: bool
  httpcheck_method:
    description: HTTP check method.
    required: false
    type: str
    choices: ['OPTIONS', 'HEAD', 'GET', 'POST', 'PUT', 'DELETE', 'TRACE']
  monitor_uri:
    description: Url used by http check requests.
    required: false
    type: str
  monitor_httpversion:
    description: Defaults to "HTTP/1.0" if left blank.
    required: false
    type: str
  monitor_username:
    description: Username used in checks (MySQL and PostgreSQL)
    required: false
    type: str
  monitor_domain:
    description: Domain used in checks (SMTP and ESMTP)
    required: false
    type: str
  state:
    description: State in which to leave the backend
    choices: [ "present", "absent" ]
    default: present
    type: str
"""

EXAMPLES = """
- name: Add backend
  pfsense_haproxy_backend:
    name: exchange
    balance: leastconn
    httpcheck_method: HTTP
    state: present

- name: Remove backend
  pfsense_haproxy_backend:
    name: exchange
    state: absent
"""

RETURN = """
commands:
    description: the set of commands that would be pushed to the remote device (if pfSense had a CLI)
    returned: always
    type: list
    sample: ["create haproxy_backend 'exchange', balance='leastconn', httpcheck_method='HTTP'", "delete haproxy_backend 'exchange'"]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.pfsense.haproxy_backend import PFSenseHaproxyBackendModule, HAPROXY_BACKEND_ARGUMENT_SPEC


def main():
    module = AnsibleModule(
        argument_spec=HAPROXY_BACKEND_ARGUMENT_SPEC,
        supports_check_mode=True)

    pfmodule = PFSenseHaproxyBackendModule(module)
    pfmodule.run(module.params)
    pfmodule.commit_changes()


if __name__ == '__main__':
    main()
