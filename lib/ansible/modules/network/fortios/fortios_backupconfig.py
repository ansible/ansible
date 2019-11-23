#!/usr/bin/python
#
# Ansible module to backup configuration on fortios devices
# (c) 2019, Patrick Pellissier <polaris197@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: fortios_backupconfig
version_added: "2.1"
author: "Patrick Pellissier (@polaris197)"
short_description: Backup config on Fortinet FortiOS firewall devices
description:
  - This module provides backup of FortiOS Devices configuration.
  - Remove pager and empty lines
extends_documentation_fragment: fortios
options:
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

"""

RETURN = """
running_config:
  description: full config string
  returned: always
  type: str
"""

import re
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


def _sanitize(output):
    for (regex, replace) in [(re.compile(r'^--More--\s*(?:\r|)$', re.M), ''), (re.compile(r'\n\s*\n', re.M), '\n')]:
        output = regex.sub(replace, output)
    return output


def load_config(conn, path='', vdom=None):
    """
    This method will load config represented as str, sanitize and return the config as a str.

    Args:
        * **path** (str) -- This is the block of config you want to load. For example *system interface*\
            or *router bgp*
    """
    logger.info('Loading config. path:%s' % (path))

    if vdom is not None:
        if vdom == 'global':
            command = 'conf global\nshow {0}\nend'.format(path)
        else:
            command = 'conf vdom\nedit {0}\nshow {1}\nend'.format(vdom, path)
    else:
        command = 'show {0}'.format(path)
        
    return _sanitize("\n".join(conn.execute_command(command)))


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
    except Exception as e:
        module.fail_json(msg='Error connecting device : {0}'.format(repr(e)))

    # get  config
    running_config = ""
    try:
        running_config = load_config(conn,path=module.params['filter'], vdom=module.params['vdom'])
        result['running_config'] = running_config
    except Exception as e:
        module.fail_json(msg='Error reading config : {0}'.format(repr(e)))

    # backup config
    if module.params['backup']:
        backup(module, running_config)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
