#!/usr/bin/python
""" PN-CLI vrouter-interface-add/remove/modify """

#
# This file is part of Ansible
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
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: pn_vrouterif
author: "Pluribus Networks (@amitsi)"
version_added: "2.2"
short_description: CLI command to add/remove/modify vrouter-interface.
description:
  - Execute vrouter-interface-add, vrouter-interface-remove,
    vrouter-interface-modify command.
  - You configure interfaces to vRouter services on a fabric, cluster,
    standalone switch or virtual network(VNET).
options:
  pn_cliusername:
    description:
      - Provide login username if user is not root.
    required: False
  pn_clipassword:
    description:
      - Provide login password if user is not root.
    required: False
  pn_cliswitch:
    description:
      - Target switch to run the cli on.
    required: False
  state:
    description:
      - State the action to perform. Use 'present' to add vrouter interface,
        'absent' to remove vrouter interface and 'update' to modify vrouter
        interface.
    required: True
    choices: ['present', 'absent', 'update']
  pn_vrouter_name:
    description:
      - Specify the name of the vRouter interface.
    required: True
  pn_vlan:
    description:
      - Specify the VLAN identifier. This is a value between 1 and 4092.
  pn_interface_ip:
    description:
      - Specify the IP address of the interface in x.x.x.x/n format.
  pn_assignment:
    description:
      - Specify the DHCP method for IP address assignment.
    choices: ['none', 'dhcp', 'dhcpv6', 'autov6']
  pn_vxlan:
    description:
      - Specify the VXLAN identifier. This is a value between 1 and 16777215.
  pn_interface:
    description:
      - Specify if the interface is management, data or span interface.
    choices: ['mgmt', 'data', 'span']
  pn_alias:
    description:
      - Specify an alias for the interface.
  pn_exclusive:
    description:
      - Specify if the interface is exclusive to the configuration. Exclusive
        means that other configurations cannot use the interface. Exclusive is
        specified when you configure the interface as span interface and allows
        higher throughput through the interface.
  pn_nic_enable:
    description:
      - Specify if the NIC is enabled or not
  pn_vrrp_id:
    description:
      - Specify the ID for the VRRP interface. The IDs on both vRouters must be
        the same IS number.
  pn_vrrp_priority:
    description:
      - Specify the priority for the VRRP interface. This is a value between
         1 (lowest) and 255 (highest).
  pn_vrrp_adv_int:
    description:
      - Specify a VRRP advertisement interval in milliseconds. The range is
        from 30 to 40950 with a default value of 1000.
  pn_l3port:
    description:
      - Specify a Layer 3 port for the interface.
  pn_secondary_macs:
    description:
      - Specify a secondary MAC address for the interface.
  pn_nic_str:
    description:
      - Specify the type of NIC. Used for vrouter-interface remove/modify.
"""

EXAMPLES = """
- name: Add vrouter-interface
  pn_vrouterif:
    pn_cliusername: admin
    pn_clipassword: admin
    state: 'present'
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: 101.101.101.2/24
    pn_vlan: 101

- name: Add VRRP..
  pn_vrouterif:
    pn_cliusername: admin
    pn_clipassword: admin
    state: 'present'
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: 101.101.101.2/24
    pn_vrrp_ip: 101.101.101.1/24
    pn_vrrp_priority: 100
    pn_vlan: 101

- name: Remove vrouter-interface
  pn_vrouterif:
    pn_cliusername: admin
    pn_clipassword: admin
    state: 'absent'
    pn_vrouter_name: 'ansible-vrouter'
    pn_interface_ip: 101.101.101.2/24
"""

RETURN = """
command:
  description: The CLI command run on the target node(s).
  returned: always
  type: str
stdout:
  description: The set of responses from the vrouterif command.
  returned: on success
  type: list
stderr:
  description: The set of error responses from the vrouterif command.
  returned: on error
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

import shlex

VROUTER_EXISTS = None
INTERFACE_EXISTS = None
NIC_EXISTS = None
VRRP_EXISTS = None


def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch
    :return: returns the cli string for further processing
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    if cliswitch == 'local':
        cli += ' switch-local '
    else:
        cli += ' switch ' + cliswitch
    return cli


def check_cli(module, cli):
    """
    This method checks if vRouter exists on the target node.
    This method also checks for idempotency using the vrouter-interface-show
    command.
    If the given vRouter exists, return VROUTER_EXISTS as True else False.

    If an interface with the given ip exists on the given vRouter,
    return INTERFACE_EXISTS as True else False. This is required for
    vrouter-interface-add.

    If nic_str exists on the given vRouter, return NIC_EXISTS as True else
    False. This is required for vrouter-interface-remove.

    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: VROUTER_EXISTS, INTERFACE_EXISTS, NIC_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    interface_ip = module.params['pn_interface_ip']
    nic_str = module.params['pn_nic_str']

    # Global flags
    global VROUTER_EXISTS, INTERFACE_EXISTS, NIC_EXISTS

    # Check for vRouter
    check_vrouter = cli + ' vrouter-show format name no-show-headers '
    check_vrouter = shlex.split(check_vrouter)
    out = module.run_command(check_vrouter)[1]
    out = out.split()

    if vrouter_name in out:
        VROUTER_EXISTS = True
    else:
        VROUTER_EXISTS = False

    if interface_ip:
        # Check for interface and VRRP and fetch nic for VRRP
        show = cli + ' vrouter-interface-show vrouter-name %s ' % vrouter_name
        show += 'ip %s format ip,nic no-show-headers' % interface_ip
        show = shlex.split(show)
        out = module.run_command(show)[1]
        if out:
            INTERFACE_EXISTS = True
        else:
            INTERFACE_EXISTS = False

    if nic_str:
        # Check for nic
        show = cli + ' vrouter-interface-show vrouter-name %s ' % vrouter_name
        show += ' format nic no-show-headers'
        show = shlex.split(show)
        out = module.run_command(show)[1]
        if nic_str in out:
            NIC_EXISTS = True
        else:
            NIC_EXISTS = False


def get_nic(module, cli):
    """
    This module checks if VRRP interface can be added. If No, return VRRP_EXISTS
    as True.
    If Yes, fetch the nic string from the primary interface and return nic and
    VRRP_EXISTS as False.
    :param module:
    :param cli:
    :return: nic, Global Boolean: VRRP_EXISTS
    """
    vrouter_name = module.params['pn_vrouter_name']
    interface_ip = module.params['pn_interface_ip']

    global VRRP_EXISTS

    # Check for interface and VRRP and fetch nic for VRRP
    show = cli + ' vrouter-interface-show vrouter-name %s ' % vrouter_name
    show += 'ip %s format ip,nic no-show-headers' % interface_ip
    show = shlex.split(show)
    out = module.run_command(show)[1]
    out = out.split()

    if len(out) > 3:
        VRRP_EXISTS = True
        return None
    else:
        nic = out[2]
        VRRP_EXISTS = False
        return nic


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    cliswitch = module.params['pn_cliswitch']
    state = module.params['state']
    command = get_command_from_state(state)

    cmd = shlex.split(cli)

    # 'out' contains the output
    # 'err' contains the error messages
    result, out, err = module.run_command(cmd)

    print_cli = cli.split(cliswitch)[1]

    # Response in JSON format
    if result != 0:
        module.exit_json(
            command=print_cli,
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            command=print_cli,
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            command=print_cli,
            msg="%s operation completed" % command,
            changed=True
        )


def get_command_from_state(state):
    """
    This method gets appropriate command name for the state specified. It
    returns the command name for the specified state.
    :param state: The state for which the respective command name is required.
    """
    command = None
    if state == 'present':
        command = 'vrouter-interface-add'
    if state == 'absent':
        command = 'vrouter-interface-remove'
    if state == 'update':
        command = 'vrouter-interface-modify'
    return command


def main():
    """ This portion is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
            pn_vrouter_name=dict(required=True, type='str'),
            pn_vlan=dict(type='int'),
            pn_interface_ip=dict(required=True, type='str'),
            pn_assignment=dict(type='str',
                               choices=['none', 'dhcp', 'dhcpv6', 'autov6']),
            pn_vxlan=dict(type='int'),
            pn_interface=dict(type='str', choices=['mgmt', 'data', 'span']),
            pn_alias=dict(type='str'),
            pn_exclusive=dict(type='bool'),
            pn_nic_enable=dict(type='bool'),
            pn_vrrp_id=dict(type='int'),
            pn_vrrp_priority=dict(type='int'),
            pn_vrrp_adv_int=dict(type='str'),
            pn_l3port=dict(type='str'),
            pn_secondary_macs=dict(type='str'),
            pn_nic_str=dict(type='str')
        ),
        required_if=(
            ["state", "present",
             ["pn_vrouter_name", "pn_interface_ip"]],
            ["state", "absent",
             ["pn_vrouter_name", "pn_nic_str"]]
        ),
    )

    # Accessing the arguments
    state = module.params['state']
    vrouter_name = module.params['pn_vrouter_name']
    vlan = module.params['pn_vlan']
    interface_ip = module.params['pn_interface_ip']
    assignment = module.params['pn_assignment']
    vxlan = module.params['pn_vxlan']
    interface = module.params['pn_interface']
    alias = module.params['pn_alias']
    exclusive = module.params['pn_exclusive']
    nic_enable = module.params['pn_nic_enable']
    vrrp_id = module.params['pn_vrrp_id']
    vrrp_priority = module.params['pn_vrrp_priority']
    vrrp_adv_int = module.params['pn_vrrp_adv_int']
    l3port = module.params['pn_l3port']
    secondary_macs = module.params['pn_secondary_macs']
    nic_str = module.params['pn_nic_str']

    command = get_command_from_state(state)

    # Building the CLI command string
    cli = pn_cli(module)

    check_cli(module, cli)
    if command == 'vrouter-interface-add':
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter %s does not exist' % vrouter_name
            )

        if vrrp_id:
            vrrp_primary = get_nic(module, cli)
            if VRRP_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg=('VRRP interface on %s already exists. Check '
                         'the IP addresses' % vrouter_name)
                )
            cli += ' %s vrouter-name %s ' % (command, vrouter_name)
            cli += (' ip %s vrrp-primary %s vrrp-id %s '
                    % (interface_ip, vrrp_primary, str(vrrp_id)))
            if vrrp_priority:
                cli += ' vrrp-priority %s ' % str(vrrp_priority)
            if vrrp_adv_int:
                cli += ' vrrp-adv-int %s ' % vrrp_adv_int

        else:
            if INTERFACE_EXISTS is True:
                module.exit_json(
                    skipped=True,
                    msg=('vRouter interface on %s already exists. Check the '
                         'IP addresses' % vrouter_name)
                )
            cli += ' %s vrouter-name %s ' % (command, vrouter_name)
            cli += ' ip %s ' % interface_ip

        if vlan:
            cli += ' vlan ' + str(vlan)

        if l3port:
            cli += ' l3-port ' + l3port

        if assignment:
            cli += ' assignment ' + assignment

        if vxlan:
            cli += ' vxlan ' + str(vxlan)

        if interface:
            cli += ' if ' + interface

        if alias:
            cli += ' alias-on ' + alias

        if exclusive is True:
            cli += ' exclusive '
        if exclusive is False:
            cli += ' no-exclusive '

        if nic_enable is True:
            cli += ' nic-enable '
        if nic_enable is False:
            cli += ' nic-disable '

        if secondary_macs:
            cli += ' secondary-macs ' + secondary_macs

    if command == 'vrouter-interface-remove':
        if VROUTER_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter %s does not exist' % vrouter_name
            )
        if NIC_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='vRouter interface with nic %s does not exist' % nic_str
            )
        cli += ' %s vrouter-name %s nic %s ' % (command, vrouter_name, nic_str)

    run_cli(module, cli)
# Ansible boiler-plate
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
