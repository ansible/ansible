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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'version': '1.0'
}

DOCUMENTATION = """
---
module: qnos5_reboot
version_added: "2.3"
author: "Mark Yang (@QCT)"
short_description: Reboot a Quanta QNOS5 network device.
description:
  - Reboot a Quanta QNOS5 network device.
extends_documentation_fragment: qnos5
options:
  confirm:
    description:
      - Safeguard boolean. Set to true if you're sure you want to reboot.
    required: true
    default: null
    choices: ['yes', 'no']
  save:
    description:
      - Safeguard boolean. Set to true if you're sure to save the running-
        config to the startup-config at rebooting.
    required: false
    default: no
    choices: ['yes', 'no']
"""

EXAMPLES = """
- name: reboot the device
  qnos5_reboot:
    confirm: yes
    save: no
"""

RETURN = """
rebooted:
    description: Whether the device was instructed to reboot.
    returned: success
    type: boolean
    sample: true
"""
import re
import time

from functools import partial

from ansible.module_utils import qnos5
from ansible.module_utils import qnos5_cli
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.local import LocalAnsibleModule
from ansible.module_utils.network_common import ComplexList
from ansible.module_utils.netcli import Conditional
from ansible.module_utils.six import string_types
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.module_utils.six import iteritems


SHARED_LIB = 'qnos5'

def get_ansible_module():
    if SHARED_LIB == 'qnos5':
        return LocalAnsibleModule
    return AnsibleModule

def invoke(name, *args, **kwargs):
    obj = globals().get(SHARED_LIB)
    func = getattr(obj, name)
    return func(*args, **kwargs)

run_commands = partial(invoke, 'run_commands')
reload = partial(invoke, 'reload')
load_config = partial(invoke, 'load_config')
get_config = partial(invoke, 'get_config')

def check_args(module, warnings):
    if SHARED_LIB == 'qnos5_cli':
        qnos5_cli.check_args(module)

    confirm = module.params['confirm']
    if not confirm:
        module.fail_json(msg='confirm must be set to true for this '
                             'module to work.')

    save = module.params['save']
    if save=='':
        module.fail_json(msg='save must be set to true or falsefor this '
                             'module to work.')

def get_running_config(module):
    contents = module.params['config']
    if not contents:
        flags = []
        if module.params['defaults']:
            flags.append('all')
        contents = get_config(module, flags=flags)
    return NetworkConfig(indent=1, contents=contents)

def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        # this argument is deprecated (2.2) in favor of setting match: none
        # it will be removed in a future version
        response=dict(),
        confirm=dict(required=True, type='bool'),
        save=dict(required=True, type='bool'),
        config=dict(),
        defaults=dict(type='bool', default=False),
    )

    argument_spec.update(qnos5_cli.qnos5_cli_argument_spec)
    cls = get_ansible_module()
    module = cls(argument_spec=argument_spec,
                 supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False, 'warnings': warnings}

    changed = False
    rebooted = False
    save = module.params['save']
    result['response'] = reload(module, save)

    changed = save
    rebooted = True

    result['changed'] = changed
    result['rebooted'] = rebooted


    module.exit_json(**result)


if __name__ == '__main__':
    SHARED_LIB = 'qnos5_cli'
    main()
