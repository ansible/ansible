#!/usr/bin/python
#
# Ansible module to manage IPv4 policy objects in fortigate devices
# (c) 2017, Benjamin Jolivot <bjolivot@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: fortios_ipv4_policy
version_added: "2.3"
author: "Benjamin Jolivot (@bjolivot)"
short_description: Manage IPv4 policy objects on Fortinet FortiOS firewall devices
description:
  - This module provides management of firewall IPv4 policies on FortiOS devices.
extends_documentation_fragment: fortios
options:
  id:
    description:
      - "Policy ID.
        Warning: policy ID number is different than Policy sequence number.
        The policy ID is the number assigned at policy creation.
        The sequence number represents the order in which the Fortigate will evaluate the rule for policy enforcement,
        and also the order in which rules are listed in the GUI and CLI.
        These two numbers do not necessarily correlate: this module is based off policy ID.
        TIP: policy ID can be viewed in the GUI by adding 'ID' to the display columns"
    required: true
  state:
    description:
      - Specifies if policy I(id) need to be added or deleted.
    choices: ['present', 'absent']
    default: present
  src_intf:
    description:
      - Specifies source interface name.
    default: any
  dst_intf:
    description:
      - Specifies destination interface name.
    default: any
  src_addr:
    description:
      - Specifies source address (or group) object name(s). Required when I(state=present).
  src_addr_negate:
    description:
      - Negate source address param.
    default: false
    choices: ["true", "false"]
  dst_addr:
    description:
      - Specifies destination address (or group) object name(s). Required when I(state=present).
  dst_addr_negate:
    description:
      - Negate destination address param.
    default: false
    choices: ["true", "false"]
  policy_action:
    description:
      - Specifies accept or deny action policy. Required when I(state=present).
    choices: ['accept', 'deny']
    aliases: ['action']
  service:
    description:
      - "Specifies policy service(s), could be a list (ex: ['MAIL','DNS']). Required when I(state=present)."
    aliases:
      - services
  service_negate:
    description:
      - Negate policy service(s) defined in service value.
    default: false
    choices: ["true", "false"]
  schedule:
    description:
      - defines policy schedule.
    default: 'always'
  nat:
    description:
      - Enable or disable Nat.
    default: false
    choices: ["true", "false"]
  fixedport:
    description:
      - Use fixed port for nat.
    default: false
    choices: ["true", "false"]
  poolname:
    description:
      - Specifies NAT pool name.
  av_profile:
    description:
      - Specifies Antivirus profile name.
  webfilter_profile:
    description:
      - Specifies Webfilter profile name.
  ips_sensor:
    description:
      - Specifies IPS Sensor profile name.
  application_list:
    description:
      - Specifies Application Control name.
  logtraffic:
    version_added: "2.4"
    description:
      - Logs sessions that matched policy.
    default: utm
    choices: ['disable', 'utm', 'all']
  logtraffic_start:
    version_added: "2.4"
    description:
      - Logs beginning of session as well.
    default: false
    choices: ["true", "false"]
  comment:
    description:
      - free text to describe policy.
notes:
  - This module requires pyFG library.
"""

EXAMPLES = """
- name: Allow external DNS call
  fortios_ipv4_policy:
    host: 192.168.0.254
    username: admin
    password: password
    id: 42
    src_addr: internal_network
    dst_addr: all
    service: dns
    nat: True
    state: present
    policy_action: accept
    logtraffic: disable

- name: Public Web
  fortios_ipv4_policy:
    host: 192.168.0.254
    username: admin
    password: password
    id: 42
    src_addr: all
    dst_addr: webservers
    services:
      - http
      - https
    state: present
    policy_action: accept
"""

RETURN = """
firewall_address_config:
  description: full firewall addresses config string
  returned: always
  type: string
change_string:
  description: The commands executed by the module
  returned: only if config changed
  type: string
msg_error_list:
  description: "List of errors returned by CLI (use -vvv for better readability)."
  returned: only when error
  type: string
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.fortios import fortios_argument_spec, fortios_required_if
from ansible.module_utils.fortios import backup, AnsibleFortios


def main():
    argument_spec = dict(
        comment                   = dict(type='str'),
        id                        = dict(type='int', required=True),
        src_intf                  = dict(default='any'),
        dst_intf                  = dict(default='any'),
        state                     = dict(choices=['present', 'absent'], default='present'),
        src_addr                  = dict(type='list'),
        dst_addr                  = dict(type='list'),
        src_addr_negate           = dict(type='bool', default=False),
        dst_addr_negate           = dict(type='bool', default=False),
        policy_action             = dict(choices=['accept','deny'], aliases=['action']),
        service                   = dict(aliases=['services'], type='list'),
        service_negate            = dict(type='bool', default=False),
        schedule                  = dict(type='str', default='always'),
        nat                       = dict(type='bool', default=False),
        fixedport                 = dict(type='bool', default=False),
        poolname                  = dict(type='str'),
        av_profile                = dict(type='str'),
        webfilter_profile         = dict(type='str'),
        ips_sensor                = dict(type='str'),
        application_list          = dict(type='str'),
        logtraffic                = dict(choices=['disable','all','utm'], default='utm'),
        logtraffic_start          = dict(type='bool', default=False),
    )

    # merge global required_if & argument_spec from module_utils/fortios.py
    argument_spec.update(fortios_argument_spec)

    ipv4_policy_required_if = [
        ['state', 'present', ['src_addr', 'dst_addr', 'policy_action', 'service']],
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=fortios_required_if + ipv4_policy_required_if ,
    )

    # init forti object
    fortigate = AnsibleFortios(module)

    # Security policies root path
    config_path = 'firewall policy'

    # test params
    # NAT related
    if not module.params['nat']:
        if module.params['poolname']:
            module.fail_json(msg='Poolname param requires NAT to be true.')
        if module.params['fixedport']:
            module.fail_json(msg='Fixedport param requires NAT to be true.')

    # log options
    if module.params['logtraffic_start']:
        if not module.params['logtraffic'] == 'all':
            module.fail_json(msg='Logtraffic_start param requires logtraffic to be set to "all".')

    # id must be str(int) for pyFG to work
    policy_id = str(module.params['id'])

    # load config
    fortigate.load_config(config_path)

    # Absent State
    if module.params['state'] == 'absent':
        fortigate.candidate_config[config_path].del_block(policy_id)

    # Present state
    elif module.params['state'] == 'present':
        new_policy = fortigate.get_empty_configuration_block(policy_id, 'edit')

        # src / dest / service / interfaces
        new_policy.set_param('srcintf', '"%s"' % (module.params['src_intf']))
        new_policy.set_param('dstintf', '"%s"' % (module.params['dst_intf']))


        new_policy.set_param('srcaddr', " ".join('"' + item + '"' for item in module.params['src_addr']))
        new_policy.set_param('dstaddr', " ".join('"' + item + '"' for item in module.params['dst_addr']))
        new_policy.set_param('service', " ".join('"' + item + '"' for item in module.params['service']))

        # negate src / dest / service
        if module.params['src_addr_negate']:
            new_policy.set_param('srcaddr-negate', 'enable')
        if module.params['dst_addr_negate']:
            new_policy.set_param('dstaddr-negate', 'enable')
        if module.params['service_negate']:
            new_policy.set_param('service-negate', 'enable')

        # action
        new_policy.set_param('action', '%s' % (module.params['policy_action']))

        # logging
        new_policy.set_param('logtraffic', '%s' % (module.params['logtraffic']))
        if module.params['logtraffic'] == 'all':
            if module.params['logtraffic_start']:
                new_policy.set_param('logtraffic-start', 'enable')
            else:
                new_policy.set_param('logtraffic-start', 'disable')

        # Schedule
        new_policy.set_param('schedule', '%s' % (module.params['schedule']))

        # NAT
        if module.params['nat']:
            new_policy.set_param('nat', 'enable')
            if module.params['fixedport']:
                new_policy.set_param('fixedport', 'enable')
            if module.params['poolname'] is not None:
                new_policy.set_param('ippool', 'enable')
                new_policy.set_param('poolname', '"%s"' % (module.params['poolname']))

        # security profiles:
        if module.params['av_profile'] is not None:
            new_policy.set_param('av-profile', '"%s"' % (module.params['av_profile']))
        if module.params['webfilter_profile'] is not None:
            new_policy.set_param('webfilter-profile', '"%s"' % (module.params['webfilter_profile']))
        if module.params['ips_sensor'] is not None:
            new_policy.set_param('ips-sensor', '"%s"' % (module.params['ips_sensor']))
        if module.params['application_list'] is not None:
            new_policy.set_param('application-list', '"%s"' % (module.params['application_list']))

        # comment
        if module.params['comment'] is not None:
            new_policy.set_param('comment', '"%s"' % (module.params['comment']))

        # add the new policy to the device
        fortigate.add_block(policy_id, new_policy)

    # Apply changes
    fortigate.apply_changes()


if __name__ == '__main__':
    main()
