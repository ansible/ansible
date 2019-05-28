#!/usr/bin/python
# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_admin_service
author: "Pluribus Networks (@rajaspachipulusu17)"
version_added: "2.8"
short_description: CLI command to modify admin-service
description:
  - This module is used to modify services on the server-switch.
options:
  pn_cliswitch:
    description:
      - Target switch to run the CLI on.
    required: False
    type: str
  state:
    description:
      - State the action to perform. Use C(update) to modify the admin-service.
    required: True
    type: str
    choices: ['update']
  pn_web:
    description:
      - Web (HTTP) to enable or disable.
    required: False
    type: bool
  pn_web_ssl:
    description:
      - Web SSL (HTTPS) to enable or disable.
    required: False
    type: bool
  pn_snmp:
    description:
      - Simple Network Monitoring Protocol (SNMP) to enable or disable.
    required: False
    type: bool
  pn_web_port:
    description:
      - Web (HTTP) port to enable or disable.
    required: False
    type: str
  pn_web_ssl_port:
    description:
      - Web SSL (HTTPS) port to enable or disable.
    required: False
    type: str
  pn_nfs:
    description:
      - Network File System (NFS) to enable or disable.
    required: False
    type: bool
  pn_ssh:
    description:
      - Secure Shell to enable or disable.
    required: False
    type: bool
  pn_web_log:
    description:
      - Web logging to enable or disable.
    required: False
    type: bool
  pn__if:
    description:
      - administrative service interface.
    required: False
    type: str
    choices: ['mgmt', 'data']
  pn_icmp:
    description:
      - Internet Message Control Protocol (ICMP) to enable or disable.
    required: False
    type: bool
  pn_net_api:
    description:
      - Netvisor API to enable or disable APIs.
    required: False
    type: bool
"""

EXAMPLES = """
- name: admin service functionality
  pn_admin_service:
    pn_cliswitch: "sw01"
    state: "update"
    pn__if: "mgmt"
    pn_web: False
    pn_icmp: True

- name: admin service functionality
  pn_admin_service:
    pn_cliswitch: "sw01"
    state: "update"
    pn_web: False
    pn__if: "mgmt"
    pn_snmp: True
    pn_net_api: True
    pn_ssh: True
"""

RETURN = """
command:
  description: the CLI command run on the target node.
  returned: always
  type: str
stdout:
  description: set of responses from the admin-service command.
  returned: always
  type: list
stderr:
  description: set of error responses from the admin-service command.
  returned: on error
  type: list
changed:
  description: indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netvisor.pn_nvos import pn_cli, booleanArgs, run_cli


def main():
    """ This section is for arguments parsing """

    state_map = dict(
        update='admin-service-modify'
    )

    module = AnsibleModule(
        argument_spec=dict(
            pn_cliswitch=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=state_map.keys()),
            pn_web=dict(required=False, type='bool'),
            pn_web_ssl=dict(required=False, type='bool'),
            pn_snmp=dict(required=False, type='bool'),
            pn_web_port=dict(required=False, type='str'),
            pn_web_ssl_port=dict(required=False, type='str'),
            pn_nfs=dict(required=False, type='bool'),
            pn_ssh=dict(required=False, type='bool'),
            pn_web_log=dict(required=False, type='bool'),
            pn__if=dict(required=False, type='str', choices=['mgmt', 'data']),
            pn_icmp=dict(required=False, type='bool'),
            pn_net_api=dict(required=False, type='bool'),
        ),
        required_if=([['state', 'update', ['pn__if']]]),
        required_one_of=[['pn_web', 'pn_web_ssl', 'pn_snmp',
                          'pn_web_port', 'pn_web_ssl_port', 'pn_nfs',
                          'pn_ssh', 'pn_web_log', 'pn_icmp', 'pn_net_api']]
    )

    # Accessing the arguments
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    web = module.params['pn_web']
    web_ssl = module.params['pn_web_ssl']
    snmp = module.params['pn_snmp']
    web_port = module.params['pn_web_port']
    web_ssl_port = module.params['pn_web_ssl_port']
    nfs = module.params['pn_nfs']
    ssh = module.params['pn_ssh']
    web_log = module.params['pn_web_log']
    _if = module.params['pn__if']
    icmp = module.params['pn_icmp']
    net_api = module.params['pn_net_api']

    command = state_map[state]

    # Building the CLI command string
    cli = pn_cli(module, cliswitch)

    if command == 'admin-service-modify':
        cli += ' %s ' % command

        if _if:
            cli += ' if ' + _if
        if web_port:
            cli += ' web-port ' + web_port
        if web_ssl_port:
            cli += ' web-ssl-port ' + web_ssl_port

        cli += booleanArgs(web, 'web', 'no-web')
        cli += booleanArgs(web_ssl, 'web-ssl', 'no-web-ssl')
        cli += booleanArgs(snmp, 'snmp', 'no-snmp')
        cli += booleanArgs(nfs, 'nfs', 'no-nfs')
        cli += booleanArgs(ssh, 'ssh', 'no-ssh')
        cli += booleanArgs(icmp, 'icmp', 'no-icmp')
        cli += booleanArgs(net_api, 'net-api', 'no-net-api')
        cli += booleanArgs(web_log, 'web-log', 'no-web-log')

    run_cli(module, cli, state_map)


if __name__ == '__main__':
    main()
