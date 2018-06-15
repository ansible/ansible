#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_device_trust
short_description: Manage the trust relationships between BIG-IPs
description:
  - Manage the trust relationships between BIG-IPs. Devices, once peered, cannot
    be updated. If updating is needed, the peer must first be removed before it
    can be re-added to the trust.
version_added: 2.5
options:
  peer_server:
    description:
      - The peer address to connect to and trust for synchronizing configuration.
        This is typically the management address of the remote device, but may
        also be a Self IP.
    required: True
  peer_hostname:
    description:
      - The hostname that you want to associate with the device. This value will
        be used to easily distinguish this device in BIG-IP configuration.
      - When trusting a new device, if this parameter is not specified, the value
        of C(peer_server) will be used as a default.
  peer_user:
    description:
      - The API username of the remote peer device that you are trusting. Note
        that the CLI user cannot be used unless it too has an API account. If this
        value is not specified, then the value of C(user), or the environment
        variable C(F5_USER) will be used.
  peer_password:
    description:
      - The password of the API username of the remote peer device that you are
        trusting. If this value is not specified, then the value of C(password),
        or the environment variable C(F5_PASSWORD) will be used.
  type:
    description:
      - Specifies whether the device you are adding is a Peer or a Subordinate.
        The default is C(peer).
      - The difference between the two is a matter of mitigating risk of
        compromise.
      - A subordinate device cannot sign a certificate for another device.
      - In the case where the security of an authority device in a trust domain
        is compromised, the risk of compromise is minimized for any subordinate
        device.
      - Designating devices as subordinate devices is recommended for device
        groups with a large number of member devices, where the risk of compromise
        is high.
    choices:
      - peer
      - subordinate
    default: peer
  state:
    description:
      - When C(present), ensures the specified devices are trusted.
      - When C(absent), removes the device trusts.
    default: present
    choices:
      - absent
      - present
requirements:
  - netaddr
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Add trusts for all peer devices to Active device
  bigip_device_trust:
    server: lb.mydomain.com
    user: admin
    password: secret
    peer_server: "{{ item.ansible_host }}"
    peer_hostname: "{{ item.inventory_hostname }}"
    peer_user: "{{ item.bigip_username }}"
    peer_password: "{{ item.bigip_password }}"
  with_items: hostvars
  when: inventory_hostname in groups['master']
  delegate_to: localhost
'''

RETURN = r'''
peer_server:
  description: The remote IP address of the trusted peer.
  returned: changed
  type: string
  sample: 10.0.2.15
peer_hostname:
  description: The remote hostname used to identify the trusted peer.
  returned: changed
  type: string
  sample: test-bigip-02.localhost.localdomain
'''

import re

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False

try:
    import netaddr
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'deviceName': 'peer_hostname',
        'caDevice': 'type',
        'device': 'peer_server',
        'username': 'peer_user',
        'password': 'peer_password'
    }

    api_attributes = [
        'name', 'caDevice', 'device', 'deviceName', 'username', 'password'
    ]

    returnables = [
        'peer_server', 'peer_hostname'
    ]

    updatables = []

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
            return result
        except Exception:
            return result

    @property
    def peer_server(self):
        if self._values['peer_server'] is None:
            return None
        try:
            result = str(netaddr.IPAddress(self._values['peer_server']))
            return result
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The provided 'peer_server' parameter is not an IP address."
            )

    @property
    def peer_hostname(self):
        if self._values['peer_hostname'] is None:
            return self.peer_server
        regex = re.compile(r'[^a-zA-Z0-9.\-_]')
        result = regex.sub('_', self._values['peer_hostname'])
        return result

    @property
    def type(self):
        if self._values['type'] == 'peer':
            return True
        return False


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Parameters(params=changed)

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def provided_password(self):
        if self.want.password:
            return self.password
        if self.want.provider.get('password', None):
            return self.want.provider.get('password')
        if self.module.params.get('password', None):
            return self.module.params.get('password')

    def provided_username(self):
        if self.want.username:
            return self.username
        if self.want.provider.get('user', None):
            return self.provider.get('user')
        if self.module.params.get('user', None):
            return self.module.params.get('user')

    def present(self):
        if self.exists():
            return False
        else:
            return self.create()

    def create(self):
        self._set_changed_options()
        if self.want.peer_user is None:
            self.want.update({'peer_user': self.provided_username()})
        if self.want.peer_password is None:
            self.want.update({'peer_password': self.provided_password()})
        if self.want.peer_hostname is None:
            self.want.update({'peer_hostname': self.want.peer_server})
        if self.module.check_mode:
            return True

        self.create_on_device()
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        if self.want.peer_hostname is None:
            self.want.update({'peer_hostname': self.want.peer_server})
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to remove the trusted peer.")
        return True

    def exists(self):
        result = self.client.api.tm.cm.devices.get_collection()
        for device in result:
            try:
                if device.managementIp == self.want.peer_server:
                    return True
            except AttributeError:
                pass
        return False

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.cm.add_to_trust.exec_cmd(
            'run',
            name='Root',
            **params
        )

    def remove_from_device(self):
        self.client.api.tm.cm.remove_from_trust.exec_cmd(
            'run', deviceName=self.want.peer_hostname, name=self.want.peer_hostname
        )


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            peer_server=dict(required=True),
            peer_hostname=dict(),
            peer_user=dict(),
            peer_password=dict(no_log=True),
            type=dict(
                choices=['peer', 'subordinate'],
                default='peer'
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")
    if not HAS_NETADDR:
        module.fail_json(msg="The python netaddr module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
