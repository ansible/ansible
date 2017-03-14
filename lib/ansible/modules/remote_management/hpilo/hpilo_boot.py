#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Dag Wieers <dag@wieers.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: hpilo_boot
version_added: "2.3"
author: Dag Wieers (@dagwieers)
short_description: Boot system using specific media through HP iLO interface
description:
- "This module boots a system through its HP iLO interface. The boot media
  can be one of: cdrom, floppy, hdd, network or usb."
- This module requires the hpilo python module.
options:
  host:
    description:
    - The HP iLO hostname/address that is linked to the physical system.
    required: true
  login:
    description:
    - The login name to authenticate to the HP iLO interface.
    default: Administrator
  password:
    description:
    - The password to authenticate to the HP iLO interface.
    default: admin
  media:
    description:
    - The boot media to boot the system from
    default: network
    choices: [ "cdrom", "floppy", "hdd", "network", "normal", "usb" ]
  image:
    description:
    - The URL of a cdrom, floppy or usb boot media image.
      protocol://username:password@hostname:port/filename
    - protocol is either 'http' or 'https'
    - username:password is optional
    - port is optional
  state:
    description:
    - The state of the boot media.
    - "no_boot: Do not boot from the device"
    - "boot_once: Boot from the device once and then notthereafter"
    - "boot_always: Boot from the device each time the serveris rebooted"
    - "connect: Connect the virtual media device and set to boot_always"
    - "disconnect: Disconnects the virtual media device and set to no_boot"
    - "poweroff: Power off the server"
    default: boot_once
    choices: [ "boot_always", "boot_once", "connect", "disconnect", "no_boot", "poweroff" ]
  force:
    description:
    - Whether to force a reboot (even when the system is already booted).
    - As a safeguard, without force, hpilo_boot will refuse to reboot a server that is already running.
    default: no
    choices: [ "yes", "no" ]
requirements:
- hpilo
notes:
- To use a USB key image you need to specify floppy as boot media.
- This module ought to be run from a system that can access the HP iLO
  interface directly, either by using C(local_action) or using C(delegate_to).
'''

EXAMPLES = r'''
- name: Task to boot a system using an ISO from an HP iLO interface only if the system is an HP server
  hpilo_boot:
    host: YOUR_ILO_ADDRESS
    login: YOUR_ILO_LOGIN
    password: YOUR_ILO_PASSWORD
    media: cdrom
    image: http://some-web-server/iso/boot.iso
  when: cmdb_hwmodel.startswith('HP ')
  delegate_to: localhost

- name: Power off a server
  hpilo_boot:
    host: YOUR_ILO_HOST
    login: YOUR_ILO_LOGIN
    password: YOUR_ILO_PASSWORD
    state: poweroff
  delegate_to: localhost
'''

RETURN = '''
# Default return values
'''


import time
import warnings
from ansible.module_utils.basic import AnsibleModule

try:
    import hpilo
    HAS_HPILO = True
except ImportError:
    HAS_HPILO = False


# Suppress warnings from hpilo
warnings.simplefilter('ignore')


def main():

    module = AnsibleModule(
        argument_spec = dict(
            host = dict(required=True, type='str'),
            login = dict(default='Administrator', type='str'),
            password = dict(default='admin', type='str', no_log=True),
            media = dict(default=None, type='str', choices=['cdrom', 'floppy', 'rbsu', 'hdd', 'network', 'normal', 'usb']),
            image = dict(default=None, type='str'),
            state = dict(default='boot_once', type='str', choices=['boot_always', 'boot_once', 'connect', 'disconnect', 'no_boot', 'poweroff']),
            force = dict(default=False, type='bool'),
        )
    )

    if not HAS_HPILO:
        module.fail_json(msg='The hpilo python module is required')

    host = module.params['host']
    login = module.params['login']
    password = module.params['password']
    media = module.params['media']
    image = module.params['image']
    state = module.params['state']
    force = module.params['force']

    ilo = hpilo.Ilo(host, login=login, password=password)
    changed = False
    status = {}
    power_status = 'UNKNOWN'

    if media and state in ('boot_always', 'boot_once', 'connect', 'disconnect', 'no_boot'):

        # Workaround for: Error communicating with iLO: Problem manipulating EV
        try:
            ilo.set_one_time_boot(media)
        except hpilo.IloError:
            time.sleep(60)
            ilo.set_one_time_boot(media)

        # TODO: Verify if image URL exists/works
        if image:
            ilo.insert_virtual_media(media, image)
            changed = True

        if media == 'cdrom':
            ilo.set_vm_status('cdrom', state, True)
            status = ilo.get_vm_status()
            changed = True
        elif media in ('floppy', 'usb'):
            ilo.set_vf_status(state, True)
            status = ilo.get_vf_status()
            changed = True

    # Only perform a boot when state is boot_once or boot_always, or in case we want to force a reboot
    if state in ('boot_once', 'boot_always') or force:

        power_status = ilo.get_host_power_status()

        if not force and power_status == 'ON':
            module.fail_json(msg='HP iLO (%s) reports that the server is already powered on !' % host)

        if power_status == 'ON':
            #ilo.cold_boot_server()
            ilo.warm_boot_server()
            changed = True
        else:
            ilo.press_pwr_btn()
            #ilo.reset_server()
            #ilo.set_host_power(host_power=True)
            changed = True

    elif state in ('poweroff'):

        power_status = ilo.get_host_power_status()

        if not power_status == 'OFF':
            ilo.hold_pwr_btn()
            #ilo.set_host_power(host_power=False)
            changed = True

    module.exit_json(changed=changed, power=power_status, **status)

if __name__ == '__main__':
    main()
