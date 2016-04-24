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
      - The O(src) argument specifies the path to the source package to be
        installed on the remote device in the advent of a version mismatch.
        The O(src) argument can be either a localized path or a full
        path to the package file to install
    required: true
    default: null
    aliases: ['package']
  version:
    description:
      - The O(version) argument can be used to explicitly specify the
        version of the package that should be installed on the remote
        device.  If the O(version) argument is not specified, then
        the version is extracts from the O(src) filename
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
      - The O(no_copy) arugment is responsible for instructing the remote
        device on where to isntall the package from.  When enabled, the
        package is transferred to the remote device prior to installing.
    required: false
    default: false
    choices: ['true', 'false']
  force:
    description:
      - The O(force) argument instructs the module to bypass the package
        version check and install the packaged identified in O(src) on
        the remote device.
    require: true
    default: false
    choices: ['true', 'false']
requirements:
  - junos-eznc
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

from jnpr.junos.utils.sw import SW

def install_package(module):
    junos = SW(module.connection.device)
    package = module.params['src']
    no_copy = module.params['no_copy']

    progress_log = lambda x, y: module.log(y)

    module.log('installing package')
    result = junos.install(package, progress=progress_log, no_copy=no_copy)

    if not result:
        module.fail_json(msg='Unable to install package on device')

    if module.params['reboot']:
        module.log('rebooting system')
        junos.reboot()


def main():
    spec = dict(
        src=dict(type='path', required=True, aliases=['package']),
        version=dict(),
        reboot=dict(type='bool', default=True),
        no_copy=dict(default=False, type='bool'),
        force=dict(type='bool', default=False),
        transport=dict(default='netconf', choices=['netconf'])
    )

    module = get_module(argument_spec=spec,
                        supports_check_mode=True)

    result = dict(changed=False)

    do_upgrade = module.params['force'] or False
    if not module.params['force']:
        has_ver = module.get_facts().get('version')
        wants_ver = module.params['version'] or package_version(module)
        do_upgrade = has_ver != wants_ver

    if do_upgrade:
        if not module.check_mode:
            install_package(module)
        result['changed'] = True

    module.exit_json(**result)

from ansible.module_utils.basic import *
from ansible.module_utils.junos import *

if __name__ == '__main__':
    main()
