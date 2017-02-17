#!/usr/bin/python
#
# Ansible module to manage configuration on fortios devices
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
module: fortios_address
version_added: "2.3"
author: "Benjamin Jolivot (@bjolivot)"
short_description: Manage fortios firewall config
description:
  - This module provide management of FortiOS Devices configuration.
extends_documentation_fragment: fortios
options:
  src:
    description:
      - The I(src) argument provides a path to the configuration file
        to load into the remote device.
  filter:
    description:
      - Only for partial backup, you can restrict by giving expected configuration path (ex. firewall address).
    default: ""
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory.  If the directory does not
        exist, it is created.
    default: no
    choices: ['yes', 'no']
notes:
  - This module requires pyFG python library
"""

EXAMPLES = """
- name: Backup current config
  fortios_config:
    host: 192.168.0.254
    username: admin
    password: password
    backup: yes

- name: Backup only address objects
  fortios_config:
    host: 192.168.0.254
    username: admin
    password: password
    backup: yes
    filter: "firewall address"

- name: Update configuration from file
  fortios_config:
    host: 192.168.0.254
    username: admin
    password: password
    src: new_configuration.conf

"""

RETURN = """
running_config:
  description: full config string
  returned: always
  type: string
change_string:
  description: The commands really executed by the module
  returned: only if config changed
  type: string
"""

import os
import time
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

# some blocks don't support update, so remove them
NOT_UPDATABLE_CONFIG_OBJECTS=[
    "vpn certificate local",
]

def main():
    argument_spec = dict(
        host      = dict(required=True ),
        username  = dict(required=True ),
        password  = dict(required=True, type='str', no_log=True ),
        timeout   = dict(type='int', default=60),
        vdom      = dict(type='str', default=None ),
        src       = dict(type='str', default=None),
        filter    = dict(type='str', default=""),
        backup    =dict(type='bool', default=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    result = dict(changed=False)

    # fail if pyFG not present
    if not HAS_PYFG:
        module.fail_json(msg='Could not import the python library pyFG required by this module')

    #define device
    f = FortiOS( module.params['host'],
        username=module.params['username'],
        password=module.params['password'],
        timeout=module.params['username'],
        vdom=module.params['vdom'])

    #connect
    try:
        f.open()
    except:
        module.fail_json(msg='Error connecting device')

    #get  config
    try:
        f.load_config(path=module.params['filter'])
        result['running_config'] = f.running_config.to_text()

    except:
        module.fail_json(msg='Error reading running config')

    #backup config
    if module.params['backup']:
        backup_path = 'backup'
        if not os.path.exists(backup_path):
            os.mkdir(backup_path)
        tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
        filename = '%s/%s_config.%s' % (backup_path, module.params['host'], tstamp)
        open(filename, 'w').write(f.running_config.to_text())

    #update config
    if module.params['src'] is not None:
        #store config in str
        try:
            conf_str = open(module.params['src'], 'r').read()
            f.load_config(in_candidate=True, config_text=conf_str)
        except:
            module.fail_json(msg="Can't open configuration file, or configuration invalid")

        #get updates lines
        change_string = f.compare_config()

        #remove not updatable parts
        c = FortiConfig()
        c.parse_config_output(change_string)

        for o in NOT_UPDATABLE_CONFIG_OBJECTS:
            c.del_block(o)

        change_string = c.to_text()

        if change_string != "":
            result['change_string'] = change_string
            result['changed'] = True

        #Commit if not check mode
        if module.check_mode is False and change_string != "":
            try:
                f.commit(change_string)
            except CommandExecutionException:
                e = get_exception()
                module.fail_json(msg="Unable to execute command, check your args, the error was {0}".format(e.message))
            except FailedCommit:
                e = get_exception()
                module.fail_json(msg="Unable to commit, check your args, the error was {0}".format(e.message))
            except ForcedCommit:
                e = get_exception()
                module.fail_json(msg="Failed to force commit, check your args, the error was {0}".format(e.message))

    module.exit_json(**result)

if __name__ == '__main__':
    main()

