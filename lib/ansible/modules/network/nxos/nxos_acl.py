#!/usr/bin/python
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
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_acl
extends_documentation_fragment: nxos
version_added: "2.2"
short_description: Manages access list entries for ACLs.
description:
  - Manages access list entries for ACLs.
author:
  - Jason Edelman (@jedelman8)
  - Gabriele Gerbino (@GGabriele)
notes:
  - Tested against NXOSv 7.3.(0)D1(1) on VIRL
  - C(state=absent) removes the ACE if it exists.
  - C(state=delete_acl) deletes the ACL if it exists.
  - For idempotency, use port numbers for the src/dest port
    params like I(src_port1) and names for the well defined protocols
    for the I(proto) param.
  - Although this module is idempotent in that if the ace as presented in
    the task is identical to the one on the switch, no changes will be made.
    If there is any difference, what is in Ansible will be pushed (configured
    options will be overridden).  This is to improve security, but at the
    same time remember an ACE is removed, then re-added, so if there is a
    change, the new ACE will be exactly what parameters you are sending to
    the module.
options:
  seq:
    description:
      - Sequence number of the entry (ACE).
  name:
    description:
      - Case sensitive name of the access list (ACL).
    required: true
  action:
    description:
      - Action of the ACE.
    choices: ['permit', 'deny', 'remark']
  remark:
    description:
      - If action is set to remark, this is the description.
  proto:
    description:
      - Port number or protocol (as supported by the switch).
  src:
    description:
      - Source ip and mask using IP/MASK notation and
        supports keyword 'any'.
  src_port_op:
    description:
      - Source port operands such as eq, neq, gt, lt, range.
    choices: ['any', 'eq', 'gt', 'lt', 'neq', 'range']
  src_port1:
    description:
      - Port/protocol and also first (lower) port when using range
        operand.
  src_port2:
    description:
      - Second (end) port when using range operand.
  dest:
    description:
      - Destination ip and mask using IP/MASK notation and supports the
        keyword 'any'.
  dest_port_op:
    description:
      - Destination port operands such as eq, neq, gt, lt, range.
    choices: ['any', 'eq', 'gt', 'lt', 'neq', 'range']
  dest_port1:
    description:
      - Port/protocol and also first (lower) port when using range
        operand.
  dest_port2:
    description:
      - Second (end) port when using range operand.
  log:
    description:
      - Log matches against this entry.
    choices: ['enable']
  urg:
    description:
      - Match on the URG bit.
    choices: ['enable']
  ack:
    description:
      - Match on the ACK bit.
    choices: ['enable']
  psh:
    description:
      - Match on the PSH bit.
    choices: ['enable']
  rst:
    description:
      - Match on the RST bit.
    choices: ['enable']
  syn:
    description:
      - Match on the SYN bit.
    choices: ['enable']
  fin:
    description:
      - Match on the FIN bit.
    choices: ['enable']
  established:
    description:
      - Match established connections.
    choices: ['enable']
  fragments:
    description:
      - Check non-initial fragments.
    choices: ['enable']
  time_range:
    description:
      - Name of time-range to apply.
  precedence:
    description:
      - Match packets with given precedence.
    choices: ['critical', 'flash', 'flash-override', 'immediate',
              'internet', 'network', 'priority', 'routine']
  dscp:
    description:
      - Match packets with given dscp value.
    choices: ['af11', 'af12', 'af13', 'af21', 'af22', 'af23','af31','af32',
              'af33', 'af41', 'af42', 'af43', 'cs1', 'cs2', 'cs3', 'cs4',
              'cs5', 'cs6', 'cs7', 'default', 'ef']
  state:
    description:
      - Specify desired state of the resource.
    default: present
    choices: ['present','absent','delete_acl']
'''

EXAMPLES = '''
# configure ACL ANSIBLE
- nxos_acl:
    name: ANSIBLE
    seq: 10
    action: permit
    proto: tcp
    src: 192.0.2.1/24
    dest: any
    state: present
'''

RETURN = '''
commands:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["ip access-list ANSIBLE", "10 permit tcp 192.0.2.1/24 any"]
'''
from ansible.module_utils.network.nxos.nxos import load_config, run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def execute_show_command(command, module):
    command += ' | json'
    cmds = [command]
    body = run_commands(module, cmds)
    return body


def get_acl(module, acl_name, seq_number):
    command = 'show ip access-list'
    new_acl = []
    saveme = {}
    acl_body = {}

    body = execute_show_command(command, module)[0]
    if body:
        all_acl_body = body['TABLE_ip_ipv6_mac']['ROW_ip_ipv6_mac']
    else:
        # no access-lists configured on the device
        return {}, []

    if isinstance(all_acl_body, dict):
        # Only 1 ACL configured.
        if all_acl_body.get('acl_name') == acl_name:
            acl_body = all_acl_body
    else:
        for acl in all_acl_body:
            if acl.get('acl_name') == acl_name:
                acl_body = acl
                break

    try:
        acl_entries = acl_body['TABLE_seqno']['ROW_seqno']
        acl_name = acl_body.get('acl_name')
    except KeyError:  # could be raised if no ACEs are configured for an ACL
        return {}, [{'acl': 'no_entries'}]

    if isinstance(acl_entries, dict):
        acl_entries = [acl_entries]

    for each in acl_entries:
        temp = {}
        options = {}
        remark = each.get('remark')

        temp['name'] = acl_name
        temp['seq'] = str(each.get('seqno'))

        if remark:
            temp['remark'] = remark
            temp['action'] = 'remark'
        else:
            temp['action'] = each.get('permitdeny')
            temp['proto'] = str(each.get('proto', each.get('proto_str', each.get('ip'))))
            temp['src'] = each.get('src_any', each.get('src_ip_prefix'))
            temp['src_port_op'] = each.get('src_port_op')
            temp['src_port1'] = each.get('src_port1_num')
            temp['src_port2'] = each.get('src_port2_num')
            temp['dest'] = each.get('dest_any', each.get('dest_ip_prefix'))
            temp['dest_port_op'] = each.get('dest_port_op')
            temp['dest_port1'] = each.get('dest_port1_num')
            temp['dest_port2'] = each.get('dest_port2_num')

            options['log'] = each.get('log')
            options['urg'] = each.get('urg')
            options['ack'] = each.get('ack')
            options['psh'] = each.get('psh')
            options['rst'] = each.get('rst')
            options['syn'] = each.get('syn')
            options['fin'] = each.get('fin')
            options['established'] = each.get('established')
            options['dscp'] = each.get('dscp_str')
            options['precedence'] = each.get('precedence_str')
            options['fragments'] = each.get('fragments')
            options['time_range'] = each.get('timerange')

        keep = {}
        for key, value in temp.items():
            if value:
                keep[key] = value

        options_no_null = {}
        for key, value in options.items():
            if value is not None:
                options_no_null[key] = value
        keep['options'] = options_no_null

        if keep.get('seq') == seq_number:
            saveme = dict(keep)

        new_acl.append(keep)

    return saveme, new_acl


def _acl_operand(operand, srcp1, sprcp2):
    sub_entry = ' ' + operand

    if operand == 'range':
        sub_entry += ' ' + srcp1 + ' ' + sprcp2
    else:
        sub_entry += ' ' + srcp1

    return sub_entry


def config_core_acl(proposed):
    seq = proposed.get('seq')
    action = proposed.get('action')
    remark = proposed.get('remark')
    proto = proposed.get('proto')
    src = proposed.get('src')
    src_port_op = proposed.get('src_port_op')
    src_port1 = proposed.get('src_port1')
    src_port2 = proposed.get('src_port2')

    dest = proposed.get('dest')
    dest_port_op = proposed.get('dest_port_op')
    dest_port1 = proposed.get('dest_port1')
    dest_port2 = proposed.get('dest_port2')

    ace_start_entries = [action, proto, src]
    if not remark:
        ace = seq + ' ' + ' '.join(ace_start_entries)
        if src_port_op:
            ace += _acl_operand(src_port_op, src_port1, src_port2)
        ace += ' ' + dest
        if dest_port_op:
            ace += _acl_operand(dest_port_op, dest_port1, dest_port2)
    else:
        ace = seq + ' remark ' + remark

    return ace


def config_acl_options(options):
    ENABLE_ONLY = ['psh', 'urg', 'log', 'ack', 'syn',
                   'established', 'rst', 'fin', 'fragments',
                   'log']

    OTHER = ['dscp', 'precedence', 'time-range']
    # packet-length is the only option not currently supported

    if options.get('time_range'):
        options['time-range'] = options.get('time_range')
        options.pop('time_range')

    command = ''
    for option, value in options.items():
        if option in ENABLE_ONLY:
            if value == 'enable':
                command += ' ' + option
        elif option in OTHER:
            command += ' ' + option + ' ' + value
    if command:
        command = command.strip()
        return command


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def main():
    argument_spec = dict(
        seq=dict(required=False, type='str'),
        name=dict(required=True, type='str'),
        action=dict(required=False, choices=['remark', 'permit', 'deny']),
        remark=dict(required=False, type='str'),
        proto=dict(required=False, type='str'),
        src=dict(required=False, type='str'),
        src_port_op=dict(required=False),
        src_port1=dict(required=False, type='str'),
        src_port2=dict(required=False, type='str'),
        dest=dict(required=False, type='str'),
        dest_port_op=dict(required=False),
        dest_port1=dict(required=False, type='str'),
        dest_port2=dict(required=False, type='str'),
        log=dict(required=False, choices=['enable']),
        urg=dict(required=False, choices=['enable']),
        ack=dict(required=False, choices=['enable']),
        psh=dict(required=False, choices=['enable']),
        rst=dict(required=False, choices=['enable']),
        syn=dict(required=False, choices=['enable']),
        fragments=dict(required=False, choices=['enable']),
        fin=dict(required=False, choices=['enable']),
        established=dict(required=False, choices=['enable']),
        time_range=dict(required=False),
        precedence=dict(required=False, choices=['critical', 'flash',
                                                 'flash-override',
                                                 'immediate', 'internet',
                                                 'network', 'priority',
                                                 'routine']),
        dscp=dict(required=False, choices=['af11', 'af12', 'af13', 'af21',
                                           'af22', 'af23', 'af31', 'af32',
                                           'af33', 'af41', 'af42', 'af43',
                                           'cs1', 'cs2', 'cs3', 'cs4',
                                           'cs5', 'cs6', 'cs7', 'default',
                                           'ef']),
        state=dict(choices=['absent', 'present', 'delete_acl'], default='present')
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    results = dict(changed=False, warnings=warnings)

    state = module.params['state']
    action = module.params['action']
    remark = module.params['remark']
    dscp = module.params['dscp']
    precedence = module.params['precedence']
    seq = module.params['seq']
    name = module.params['name']
    seq = module.params['seq']

    if action == 'remark' and not remark:
        module.fail_json(msg='when state is action, remark param is also required')

    REQUIRED = ['seq', 'name', 'action', 'proto', 'src', 'dest']
    ABSENT = ['name', 'seq']
    if state == 'present':
        if action and remark and seq:
            pass
        else:
            for each in REQUIRED:
                if module.params[each] is None:
                    module.fail_json(msg="req'd params when state is present:",
                                     params=REQUIRED)
    elif state == 'absent':
        for each in ABSENT:
            if module.params[each] is None:
                module.fail_json(msg='require params when state is absent',
                                 params=ABSENT)
    elif state == 'delete_acl':
        if module.params['name'] is None:
            module.fail_json(msg="param name req'd when state is delete_acl")

    if dscp and precedence:
        module.fail_json(msg='only one of the params dscp/precedence '
                             'are allowed')

    OPTIONS_NAMES = ['log', 'urg', 'ack', 'psh', 'rst', 'syn', 'fin',
                     'established', 'dscp', 'precedence', 'fragments',
                     'time_range']

    CORE = ['seq', 'name', 'action', 'proto', 'src', 'src_port_op',
            'src_port1', 'src_port2', 'dest', 'dest_port_op',
            'dest_port1', 'dest_port2', 'remark']

    proposed_core = dict((param, value) for (param, value) in
                         module.params.items()
                         if param in CORE and value is not None)

    proposed_options = dict((param, value) for (param, value) in
                            module.params.items()
                            if param in OPTIONS_NAMES and value is not None)
    proposed = {}
    proposed.update(proposed_core)
    proposed.update(proposed_options)

    existing_options = {}

    # getting existing existing_core=dict, acl=list, seq=list
    existing_core, acl = get_acl(module, name, seq)
    if existing_core:
        existing_options = existing_core.get('options')
        existing_core.pop('options')

    commands = []
    delta_core = {}
    delta_options = {}

    if not existing_core.get('remark'):
        dcore = dict(
            set(proposed_core.items()).difference(
                existing_core.items())
        )
        if not dcore:
            # check the diff in the other way just in case
            dcore = dict(
                set(existing_core.items()).difference(
                    proposed_core.items())
            )
        delta_core = dcore
        if delta_core:
            delta_options = proposed_options
        else:
            doptions = dict(
                set(proposed_options.items()).difference(
                    existing_options.items())
            )
            # check the diff in the other way just in case
            if not doptions:
                doptions = dict(
                    set(existing_options.items()).difference(
                        proposed_options.items())
                )
            delta_options = doptions
    else:
        delta_core = dict(
            set(proposed_core.items()).difference(
                existing_core.items())
        )

    if state == 'present':
        if delta_core or delta_options:
            if existing_core:  # if the ace exists already
                commands.append(['no {0}'.format(seq)])
            if delta_options:
                myacl_str = config_core_acl(proposed_core)
                myacl_str += ' ' + config_acl_options(proposed_options)
            else:
                myacl_str = config_core_acl(proposed_core)
            command = [myacl_str]
            commands.append(command)
    elif state == 'absent':
        if existing_core:
            commands.append(['no {0}'.format(seq)])
    elif state == 'delete_acl':
        if acl[0].get('acl') != 'no_entries':
            commands.append(['no ip access-list {0}'.format(name)])

    cmds = []
    if commands:
        preface = []
        if state in ['present', 'absent']:
            preface = ['ip access-list {0}'.format(name)]
            commands.insert(0, preface)

        cmds = flatten_list(commands)
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            load_config(module, cmds)
            results['changed'] = True
            if 'configure' in cmds:
                cmds.pop(0)

    results['commands'] = cmds

    module.exit_json(**results)


if __name__ == '__main__':
    main()
