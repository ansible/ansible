#!/usr/bin/python
#
# Ansible module to manage IPV4 policy objects in fortigate devices
# (c) 2016, Benjamin Jolivot <bjolivot@gmail.com>
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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'version': '1.0'
}

DOCUMENTATION = """
---
module: fortios_ipv4_policy
version_added: "2.3"
author: "Benjamin Jolivot (@bjolivot)"
short_description: Manage fortios firewall address objects
description:
  - This module provide management of firewall ipv4 policies on FortiOS devices.
extends_documentation_fragment: fortios
options:
  id:
    description:
      - Policy ID.
    required: true
  state:
    description:
      - Specifies if address need to be added or deleted.
    required: true
    choices: ['present', 'absent']
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
      - Specifies source address (or group) object name.
    required: true
  src_addr_negate:
    description:
      - Negate source address param.
    default: false
    choices: ["true", "false"]
  dst_addr:
    description:
      - Specifies destination address (or group) object name.
    required: true
  dst_addr_negate:
    description:
      - Negate destination address param.
    default: false
    choices: ["true", "false"]
  action:
    description:
      - Specifies accept or deny action policy.
    choices: ['accept', 'deny']
    required: true
  service:
    description:
      - "Specifies policy service(s), could be a list (ex: ['MAIL','DNS'])."
    required: true
    aliases: services
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
      - Specifies nat pool name.
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
    srcaddr: internal_network
    dstaddr: any
    service: dns
    nat: True
    state: present
    action: accept

"""

RETURN = """
firewall_address_config:
  description: full firewall adresses config string
  returned: always
  type: string
change_string:
  description: The commands executed by the module
  returned: only if config changed
  type: string
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception

#check for pyFG lib
try:
    from pyFG import FortiOS, FortiConfig
    from pyFG.fortios import logger
    from pyFG.exceptions import CommandExecutionException, FailedCommit, ForcedCommit
    HAS_PYFG=True
except:
    HAS_PYFG=False

def main():
    argument_spec = dict(
        host            = dict(required=True ),
        username        = dict(required=True ),
        password        = dict(required=True, type='str', no_log=True ),
        timeout         = dict(type='int', default=60),
        vdom            = dict(type='str', default=None ),
        comment         = dict(),
        id              = dict(type='str', required=True),
        src_intf        = dict(default='any'),
        dst_intf        = dict(default='any'),
        state           = dict(choices=['present', 'absent'], default='present'),
        src_addr        = dict(required=True, type='str'),
        dst_addr        = dict(required=True, type='str'),
        src_addr_negate = dict(type='bool', default=False),
        dst_addr_negate = dict(type='bool', default=False),
        action          = dict(choices=['accept','deny'], required=True),
        service         = dict(aliases=['services'], required=True, type='list'),
        service_negate  = dict(type='bool', default=False),
        schedule        = dict(type='str', default='always'),
        nat             = dict(type='bool', default=False),
        fixedport       = dict(type='bool', default=False),
        poolname        = dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    result = dict(changed=False)

    # fail if libs not present
    msg = ""
    if not HAS_PYFG:
        module.fail_json(msg='Could not import the python library pyFG required by this module')

    #define device
    f = FortiOS( module.params['host'],
        username=module.params['username'],
        password=module.params['password'],
        timeout=module.params['username'],
        vdom=module.params['vdom'])

    path = 'firewall policy'

    #connect
    try:
        f.open()
    except:
        module.fail_json(msg='Error connecting device')

    #get  config
    try:
        f.load_config(path=path)
        result['firewall_address_config'] = f.running_config.to_text()
    except:
        module.fail_json(msg='Error reading running config')

    #Absent State
    if module.params['state'] == 'absent':
        f.candidate_config[path].del_block(module.params['id'])
        change_string = f.compare_config()
        if change_string != "":
            result['change_string'] = change_string
            result['changed'] = True

    #Present state
    if module.params['state'] == 'present':
        new_policy = FortiConfig(module.params['id'], 'edit')

        #src / dest / service / interfaces
        new_policy.set_param('srcintf', '"{0}"'.format(module.params['src_intf']))
        new_policy.set_param('dstintf', '"{0}"'.format(module.params['dst_intf']))
        new_policy.set_param('srcaddr', '"{0}"'.format(module.params['src_addr']))
        new_policy.set_param('dstaddr', '"{0}"'.format(module.params['dst_addr']))
        new_policy.set_param('service', " ".join('"' + item + '"' for item in module.params['service']))

        # negate src / dest / service
        if module.params['src_addr_negate']:
            new_policy.set_param('srcaddr-negate', 'enable')
        if module.params['dst_addr_negate']:
            new_policy.set_param('dstaddr-negate', 'enable')
        if module.params['service_negate']:
            new_policy.set_param('service-negate', 'enable')

        # action
        new_policy.set_param('action', '{0}'.format(module.params['action']))

        # Schedule
        new_policy.set_param('schedule', '"{0}"'.format(module.params['schedule']))

        # comment
        if module.params['comment'] is not None:
            new_policy.set_param('comment', '"{0}"'.format(module.params['comment']))

        #add to candidate config
        f.candidate_config[path][module.params['id']] = new_policy

        #check if change needed
        change_string = f.compare_config()

        if change_string != "":
            result['change_string'] = change_string
            result['changed'] = True

    #Commit if not check mode
    if module.check_mode is False and change_string != "":
        try:
            f.commit()
        except FailedCommit:
            #rollback
            e = get_exception()
            module.fail_json(msg="Unable to commit change, check your args, the error was {0}".format(e.message))

    module.exit_json(**result)

if __name__ == '__main__':
    main()

