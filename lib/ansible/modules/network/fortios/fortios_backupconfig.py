#!/usr/bin/python
#
# Ansible module to manage configuration on fortios devices
# (c) 2016, Benjamin Jolivot <bjolivot@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: fortios_backupconfig
version_added: "2.3"
author: "Patrick Pellissier (ppellissier)"
short_description: Manage config on Fortinet FortiOS firewall devices
description:
  - This module provides management of FortiOS Devices configuration.
extends_documentation_fragment: fortios
options:
  src:
    description:
      - The I(src) argument provides a path to the configuration template
        to load into the remote device.
  filter:
    description:
      - Only for partial backup, you can restrict by giving expected configuration path (ex. firewall address).
    default: ""
requirements:
  - pyFG
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
    backup_path: /tmp/forti_backup/
    filter: "firewall address"

- name: Update configuration from file
  fortios_config:
    host: 192.168.0.254
    username: admin
    password: password
    src: new_configuration.conf.j2

"""

RETURN = """
running_config:
  description: full config string
  returned: always
  type: str
change_string:
  description: The commands really executed by the module
  returned: only if config changed
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.fortios.fortios import fortios_argument_spec, fortios_required_if
from ansible.module_utils.network.fortios.fortios import backup

# check for pyFG lib
try:
    from pyFG import FortiOS, FortiConfig
    from pyFG.fortios import logger
    HAS_PYFG = True
except Exception:
    HAS_PYFG = False


# some blocks don't support update, so remove them
NOT_UPDATABLE_CONFIG_OBJECTS = [
    "vpn certificate local",
]

def load_config(conn, path='',vdom=None):
    """
    This method will load a block of config represented as a :py:class:`FortiConfig` object in the running
    config, in the candidate config or in both.

    Args:
        * **path** (str) -- This is the block of config you want to load. For example *system interface*\
            or *router bgp*
    """
    logger.info('Loading config. path:%s' % (path))

    if vdom is not None:
        if vdom == 'global':
            command = 'conf global\nshow %s\nend' % path
        else:
            command = 'conf vdom\nedit %s\nshow %s\nend' % (vdom, path)
    else:
        command = 'show %s' % path

    return conn.execute_command(command)

def main():
    argument_spec = dict(
        filter=dict(type='str', default=""),
    )

    argument_spec.update(fortios_argument_spec)

    required_if = fortios_required_if

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
    )

    result = dict(changed=False)

    # fail if pyFG not present
    if not HAS_PYFG:
        module.fail_json(msg='Could not import the python library pyFG required by this module')

    # define device
    conn = FortiOS(module.params['host'],
                username=module.params['username'],
                password=module.params['password'],
                timeout=module.params['timeout'],
                vdom=module.params['vdom'])

    # connect
    try:
        conn.open()
    except Exception:
        module.fail_json(msg='Error connecting device')

    # get  config
    running_config = ""
    try:
        running_config = load_config(conn,path=module.params['filter'],vdom=module.params['vdom'])
        result['running_config'] = running_config
    except Exception:
        module.fail_json(msg='Error reading running config')

    # backup config
    if module.params['backup']:
        backup(module, running_config)

    module.exit_json(**result)

if __name__ == '__main__':
    main()
