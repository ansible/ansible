#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: panos_ike_crypto_profile
short_description: Configures IKE Crypto profile on the firewall with subset of settings
description:
    - Use the IKE Crypto Profiles page to specify protocols and algorithms for identification, authentication, and
    - encryption (IKEv1 or IKEv2, Phase 1).
author: "Ivan Bojer (@ivanbojer)"
version_added: "2.8"
requirements:
    - pan-python can be obtained from PyPi U(https://pypi.python.org/pypi/pan-python)
    - pandevice can be obtained from PyPi U(https://pypi.python.org/pypi/pandevice)
notes:
    - Checkmode is not supported.
    - Panorama is NOT supported.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device being configured.
        required: true
    username:
        description:
            - Username credentials to use for auth unless I(api_key) is set.
        default: "admin"
    password:
        description:
            - Password credentials to use for auth unless I(api_key) is set.
        required: true
    api_key:
        description:
            - API key that can be used instead of I(username)/I(password) credentials.
    state:
        description:
            - Create or remove static route.
        choices: ['present', 'absent']
        default: 'present'
    commit:
        description:
            - Commit configuration if changed.
        default: true
    name:
        description:
            - Name for the profile.
        required: true
    dhgroup:
        description:
            - Specify the priority for Diffie-Hellman (DH) groups.
        default: group2
    authentication:
        description:
            - Specify the priority for hash algorithms.
        default: sha1
    encryption:
        description:
            - Select the appropriate Encapsulating Security Payload (ESP) authentication options.
        default: ['aes-256-cbc', '3des']
    lifetime_sec:
        description:
            - Select unit of time and enter the length of time that the negotiated IKE Phase 1 key will be effective.
        default: 28800
'''

EXAMPLES = '''
- name: Add IKE crypto config to the firewall
    panos_ike_crypto_profile:
      ip_address: '{{ ip_address }}'
      username: '{{ username }}'
      password: '{{ password }}'
      state: 'present'
      name: 'IKE-Ansible'
      dhgroup: 'group2'
      authentication: 'sha1'
      encryption: ['aes-256-cbc', '3des']
      lifetime_sec: '28800'
      commit: 'False'
'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception

try:
    from pan.xapi import PanXapiError
    import pandevice
    from pandevice import base
    from pandevice import panorama
    from pandevice.errors import PanDeviceError
    from pandevice import network

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


# def get_devicegroup(device, devicegroup):
#     dg_list = device.refresh_devices()
#     for group in dg_list:
#         if isinstance(group, pandevice.panorama.DeviceGroup):
#             if group.name == devicegroup:
#                 return group
#     return False


class IKEProfile:
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name')
        self.authentication = kwargs.get('authentication')
        self.encryption = kwargs.get('encryption')
        self.dh_group = kwargs.get('dh_group')
        self.lifetime_secs = kwargs.get('lifetime_secs')


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(no_log=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True),
        dhgroup=dict(default='group2'),
        authentication=dict(default='sha1'),
        encryption=dict(type='list', default=['aes-256-cbc', '3des']),
        lifetime_sec=dict(type='int', default=28800),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False,
                           required_one_of=[['api_key', 'password']])
    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries.')

    ip_address = module.params['ip_address']
    password = module.params['password']
    username = module.params['username']
    api_key = module.params['api_key']
    state = module.params['state']
    ike_profile_name = module.params['name']
    ike_dhgroup = module.params['dhgroup']
    ike_authentication = module.params['authentication']
    ike_encryption = module.params['encryption']
    ike_lifetime_sec = module.params['lifetime_sec']
    commit = module.params['commit']

    # If Panorama, validate the devicegroup
    # dev_group = None
    # if devicegroup and isinstance(device, panorama.Panorama):
    #     dev_group = get_devicegroup(device, devicegroup)
    #     if dev_group:
    #         device.add(dev_group)
    #     else:
    #         module.fail_json(msg='\'%s\' device group not found in Panorama. Is the name correct?' % devicegroup)

    ikeProfile = IKEProfile(name=ike_profile_name,
                            authentication=ike_authentication,
                            encryption=ike_encryption,
                            dh_group=ike_dhgroup, lifetime_secs=ike_lifetime_sec)

    ike_crypto_prof = network.IkeCryptoProfile(ikeProfile.name,
                                               ikeProfile.dh_group,
                                               ikeProfile.authentication,
                                               ikeProfile.encryption,
                                               ikeProfile.lifetime_secs,
                                               None, None, None, 0)

    # Create the device with the appropriate pandevice type
    device = base.PanDevice.create_from_device(ip_address, username, password, api_key=api_key)

    changed = False
    try:
        # fetch all crypto profiles
        profiles = network.IkeCryptoProfile.refreshall(device)
        if state == "present":
            device.add(ike_crypto_prof)
            for p in profiles:
                if p.name == ike_crypto_prof.name:
                    if not ike_crypto_prof.equal(p):
                        ike_crypto_prof.apply()
                        changed = True
                    break
            else:
                ike_crypto_prof.create()
                changed = True
        elif state == "absent":
            ike_crypto_prof = device.find(ikeProfile.name, network.IkeCryptoProfile)
            if ike_crypto_prof:
                ike_crypto_prof.delete()
                changed = True
        else:
            module.fail_json(msg='[%s] state is not implemented yet' % state)
    except PanDeviceError:
        exc = get_exception()
        module.fail_json(msg=exc.message)

    if commit and changed:
        device.commit(sync=True)

    module.exit_json(msg='IKE Crypto profile config successful.', changed=changed)


if __name__ == '__main__':
    main()
