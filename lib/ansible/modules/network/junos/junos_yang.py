#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: junos_yang
version_added: "2.5"
author: "Christian Giese (@GIC-de)"
short_description: Install custom YANG modules on devices running Junos
description:
  - This module installs or updates custom YANG modules and scripts on devices
    running Junos. The official Junos OpenConfig YANG package must be installed
    with the junos_package module.
extends_documentation_fragment: junos
options:
  package:
    description:
      - The C(package) argument specifies a unique ID to identify the module
        for future delete or update operations.
    required: true
    default: null
  modules:
    description:
      - The C(modules) argument takes a list of YANG module files with absolute
        path to file.
    required: true
    default: null
  deviation_modules:
    description:
      - The C(deviation_modules) argument takes a list of YANG deviation module
        files with absolute path to file.
    required: false
    default: null
  translation_scripts:
    description:
      - The C(translation_scripts) argument takes a list of YANG translation
        script files (SLAX or Python) with absolute path to file.
    required: false
    default: null
  action_scripts:
    description:
      - The C(action_scripts) argument takes a list of YANG action script
        files (SLAX or Python) with absolute path to file.
    required: false
    default: null
  update:
    description:
      - The C(update) argument instructs the module to update the YANG module
        if already installed.
    required: false
    default: false
    choices: ['true', 'false']
requirements:
  - junos-eznc
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vMX JUNOS version 17.3R1.10.
"""

EXAMPLES = """
# the required set of connection arguments have been purposely left off
# the examples for brevity
- name: install/update demo YANG module and translation script
  junos_yang:
    package: demo
    modules:
    - /var/yang/demo/demo.yang
    - /var/yang/demo/demo-types.yang
    translation_scripts:
    - /var/yang/demo/demo_translate.py
    update: true
"""

RETURN = """
msg:
  description: the output of `request system yang ...` command
  returned: when updated or installed
  type: string
updated:
  description: present only if yang module was updated instead of installed
  returned: when updated
  type: string
changed:
  description: true if yang module was updated or installed
  returned: always
  type: bool
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, get_param
from ansible.module_utils.pycompat24 import get_exception

import os

try:
    from jnpr.junos import Device
    from jnpr.junos.utils.scp import SCP
    from jnpr.junos.exception import ConnectError
    HAS_PYEZ = True
except ImportError:
    HAS_PYEZ = False


def connect(module):
    host = get_param(module, 'host')

    kwargs = {
        'port': get_param(module, 'port') or 830,
        'user': get_param(module, 'username')
    }

    if get_param(module, 'password'):
        kwargs['passwd'] = get_param(module, 'password')

    if get_param(module, 'ssh_keyfile'):
        kwargs['ssh_private_key_file'] = get_param(module, 'ssh_keyfile')

    kwargs['gather_facts'] = False

    try:
        device = Device(host, **kwargs)
        device.open()
        device.timeout = get_param(module, 'timeout') or 10
    except ConnectError:
        exc = get_exception()
        module.fail_json('unable to connect to %s: %s' % (host, str(exc)))

    return device


def install_yang(module, device, update):
    if module.check_mode:
        return "skipped installation because of check mode"

    rpc_kwargs = {"package": module.params['package']}

    # transfer files to home directory of remote device
    with SCP(device) as scp:
        for argument_name in ("modules", "deviation_modules", "translation_scripts", "action_scripts"):
            argument = module.params[argument_name]
            if argument:
                _argument_name = argument_name[:-1].replace("_", "-")
                rpc_kwargs[_argument_name] = []
                for src in argument:
                    scp.put(src)    # upload file
                    _filename = os.path.basename(src)
                    rpc_kwargs[_argument_name].append(_filename)

    # install YANG via SSH instead of NETCONF becuase schema will change
    device.timeout = 300    # set timeout to 5 minutes
    if update:
        reply = device.rpc.request_yang_update(**rpc_kwargs)
    else:
        reply = device.rpc.request_yang_add(**rpc_kwargs)
    return reply.findtext(".//output")

def main():
    """ Main entry point for Ansible module execution
    """
    argument_spec = dict(
        package=dict(required=True),
        modules=dict(type='list'),
        deviation_modules=dict(type='list'),
        translation_scripts=dict(type='list'),
        action_scripts=dict(type='list'),
        update=dict(type='bool', default=False),
        transport=dict(default='netconf', choices=['netconf'])
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if module.params['provider'] is None:
        module.params['provider'] = {}

    if not HAS_PYEZ:
        module.fail_json(
            msg='junos-eznc is required but does not appear to be installed. '
                'It can be installed using `pip  install junos-eznc`'
        )

    result = dict(changed=False)

    # open pyez connection
    device = connect(module)

    reply = device.rpc.get_system_yang_packages(id=module.params['package'])
    if reply.find(".//yang-pkg-id") is not None:
        # already installed
        if module.params['update']:
            # update module
            result['msg'] = install_yang(module, device, update=True)
            result['changed'] = True
            result['updated'] = True
    else:
        # install module
        result['msg'] = install_yang(module, device, update=False)
        result['changed'] = True

    try:
        # close pyez connection and ignore exceptions
        device.close()
    except:
        pass

    module.exit_json(**result)


if __name__ == '__main__':
    main()
