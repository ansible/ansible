#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: junos_package
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Installs packages on remote devices running Junos
description:
  - This module can install new and updated packages on remote
    devices running Junos.  The module will compare the specified
    package with the one running on the remote device and install
    the specified version if there is a mismatch
extends_documentation_fragment: junos
options:
  src:
    description:
      - The I(src) argument specifies the path to the source package to be
        installed on the remote device in the advent of a version mismatch.
        The I(src) argument can be either a localized path or a full
        path to the package file to install.
    required: true
    default: null
    aliases: ['package']
  version:
    description:
      - The I(version) argument can be used to explicitly specify the
        version of the package that should be installed on the remote
        device.  If the I(version) argument is not specified, then
        the version is extracts from the I(src) filename.
    required: false
    default: null
  reboot:
    description:
      - In order for a package to take effect, the remote device must be
        restarted.  When enabled, this argument will instruct the module
        to reboot the device once the updated package has been installed.
        If disabled or the remote package does not need to be changed,
        the device will not be started.
    required: true
    default: true
    choices: ['true', 'false']
  no_copy:
    description:
      - The I(no_copy) argument is responsible for instructing the remote
        device on where to install the package from.  When enabled, the
        package is transferred to the remote device prior to installing.
    required: false
    default: false
    choices: ['true', 'false']
  force:
    description:
      - The I(force) argument instructs the module to bypass the package
        version check and install the packaged identified in I(src) on
        the remote device.
    required: true
    default: false
    choices: ['true', 'false']
requirements:
  - junos-eznc
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
# the required set of connection arguments have been purposely left off
# the examples for brevity

- name: install local package on remote device
  junos_package:
    src: junos-vsrx-12.1X46-D10.2-domestic.tgz

- name: install local package on remote device without rebooting
  junos_package:
    src: junos-vsrx-12.1X46-D10.2-domestic.tgz
    reboot: no
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, get_param
from ansible.module_utils.pycompat24 import get_exception

try:
    from jnpr.junos import Device
    from jnpr.junos.utils.sw import SW
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


def install_package(module, device):
    junos = SW(device)
    package = module.params['src']
    no_copy = module.params['no_copy']

    def progress_log(dev, report):
        module.log(report)

    module.log('installing package')
    result = junos.install(package, progress=progress_log, no_copy=no_copy)

    if not result:
        module.fail_json(msg='Unable to install package on device')

    if module.params['reboot']:
        module.log('rebooting system')
        junos.reboot()


def main():
    """ Main entry point for Ansible module execution
    """
    argument_spec = dict(
        src=dict(type='path', required=True, aliases=['package']),
        version=dict(),
        reboot=dict(type='bool', default=True),
        no_copy=dict(default=False, type='bool'),
        force=dict(type='bool', default=False),
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

    do_upgrade = module.params['force'] or False

    device = connect(module)

    if not module.params['force']:
        facts = device.facts_refresh()
        has_ver = device.facts.get('version')
        wants_ver = module.params['version']
        do_upgrade = has_ver != wants_ver

    if do_upgrade:
        if not module.check_mode:
            install_package(module, device)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
