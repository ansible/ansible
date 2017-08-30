#!/usr/bin/python
#
# Copyright 2017 F5 Networks Inc.
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
module: bigip_snmp_trap
short_description: Manipulate SNMP trap information on a BIG-IP.
description:
  - Manipulate SNMP trap information on a BIG-IP.
version_added: 2.4
options:
  name:
    description:
      - Name of the SNMP configuration endpoint.
    required: True
  snmp_version:
    description:
      - Specifies to which Simple Network Management Protocol (SNMP) version
        the trap destination applies.
    choices:
      - 1
      - 2c
  community:
    description:
      - Specifies the community name for the trap destination.
  destination:
    description:
      - Specifies the address for the trap destination. This can be either an
        IP address or a hostname.
  port:
    description:
      - Specifies the port for the trap destination.
  network:
    description:
      - Specifies the name of the trap network. This option is not supported in
        versions of BIG-IP < 12.1.0. If used on versions < 12.1.0, it will simply
        be ignored.
    choices:
      - other
      - management
      - default
  state:
    description:
      - When C(present), ensures that the cloud connector exists. When
        C(absent), ensures that the cloud connector does not exist.
    default: present
    choices:
      - present
      - absent
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - This module only supports version v1 and v2c of SNMP.
  - The C(network) option is not supported on versions of BIG-IP < 12.1.0 because
    the platform did not support that option until 12.1.0. If used on versions
    < 12.1.0, it will simply be ignored.
extends_documentation_fragment: f5
requirements:
  - f5-sdk >= 2.2.0
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Create snmp v1 trap
  bigip_snmp_trap:
      community: "general"
      destination: "1.2.3.4"
      name: "my-trap1"
      network: "management"
      port: "9000"
      snmp_version: "1"
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
  delegate_to: localhost

- name: Create snmp v2 trap
  bigip_snmp_trap:
      community: "general"
      destination: "5.6.7.8"
      name: "my-trap2"
      network: "default"
      port: "7000"
      snmp_version: "2c"
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
  delegate_to: localhost
'''

RETURN = '''
snmp_version:
    description: The new C(snmp_version) configured on the remote device.
    returned: changed and success
    type: string
    sample: "2c"
community:
    description: The new C(community) name for the trap destination.
    returned: changed and success
    type: list
    sample: "secret"
destination:
    description: The new address for the trap destination in either IP or hostname form.
    returned: changed and success
    type: string
    sample: "1.2.3.4"
port:
    description: The new C(port) of the trap destination.
    returned: changed and success
    type: string
    sample: "900"
network:
    description: The new name of the network the SNMP trap is on.
    returned: changed and success
    type: string
    sample: "management"
'''

from distutils.version import LooseVersion
from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iControlUnexpectedHTTPError
)


class Parameters(AnsibleF5Parameters):
    api_map = {
        'version': 'snmp_version',
        'community': 'community',
        'host': 'destination'
    }

    @property
    def snmp_version(self):
        if self._values['snmp_version'] is None:
            return None
        return str(self._values['snmp_version'])

    @property
    def port(self):
        if self._values['port'] is None:
            return None
        return int(self._values['port'])

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


class NetworkedParameters(Parameters):
    updatables = [
        'snmp_version', 'community', 'destination', 'port', 'network'
    ]

    returnables = [
        'snmp_version', 'community', 'destination', 'port', 'network'
    ]

    api_attributes = [
        'version', 'community', 'host', 'port', 'network'
    ]

    @property
    def network(self):
        if self._values['network'] is None:
            return None
        network = str(self._values['network'])
        if network == 'management':
            return 'mgmt'
        elif network == 'default':
            return ''
        else:
            return network


class NonNetworkedParameters(Parameters):
    updatables = [
        'snmp_version', 'community', 'destination', 'port'
    ]

    returnables = [
        'snmp_version', 'community', 'destination', 'port'
    ]

    api_attributes = [
        'version', 'community', 'host', 'port'
    ]

    @property
    def network(self):
        return None


class ModuleManager(object):
    def __init__(self, client):
        self.client = client

    def exec_module(self):
        if self.is_version_non_networked():
            manager = NonNetworkedManager(self.client)
        else:
            manager = NetworkedManager(self.client)

        return manager.exec_module()

    def is_version_non_networked(self):
        """Checks to see if the TMOS version is less than 13

        Anything less than BIG-IP 13.x does not support users
        on different partitions.

        :return: Bool
        """
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.1.0'):
            return True
        else:
            return False


class BaseManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None

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

    def exists(self):
        result = self.client.api.tm.sys.snmp.traps_s.trap.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        self._set_changed_options()
        if self.client.check_mode:
            return True
        if all(getattr(self.want, v) is None for v in self.required_resources):
            raise F5ModuleError(
                "You must specify at least one of "
                ', '.join(self.required_resources)
            )
        self.create_on_device()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.want.api_params()
        result = self.client.api.tm.sys.snmp.traps_s.trap.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.sys.snmp.traps_s.trap.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the snmp trap")
        return True

    def remove_from_device(self):
        result = self.client.api.tm.sys.snmp.traps_s.trap.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if result:
            result.delete()


class NetworkedManager(BaseManager):
    def __init__(self, client):
        super(NetworkedManager, self).__init__(client)
        self.required_resources = [
            'version', 'community', 'destination', 'port', 'network'
        ]
        self.want = NetworkedParameters(self.client.module.params)
        self.changes = NetworkedParameters()

    def _set_changed_options(self):
        changed = {}
        for key in NetworkedParameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = NetworkedParameters(changed)

    def _update_changed_options(self):
        changed = {}
        for key in NetworkedParameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if changed:
            self.changes = NetworkedParameters(changed)
            return True
        return False

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.snmp.traps_s.trap.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        self._ensure_network(result)
        return NetworkedParameters(result)

    def _ensure_network(self, result):
        # BIG-IP's value for "default" is that the key does not
        # exist. This conflicts with our purpose of having a key
        # not exist (which we equate to "i dont want to change that"
        # therefore, if we load the information from BIG-IP and
        # find that there is no 'network' key, that is BIG-IP's
        # way of saying that the network value is "default"
        if 'network' not in result:
            result['network'] = 'default'


class NonNetworkedManager(BaseManager):
    def __init__(self, client):
        super(NonNetworkedManager, self).__init__(client)
        self.required_resources = [
            'version', 'community', 'destination', 'port'
        ]
        self.want = NonNetworkedParameters(self.client.module.params)
        self.changes = NonNetworkedParameters()

    def _set_changed_options(self):
        changed = {}
        for key in NonNetworkedParameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = NonNetworkedParameters(changed)

    def _update_changed_options(self):
        changed = {}
        for key in NonNetworkedParameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if changed:
            self.changes = NonNetworkedParameters(changed)
            return True
        return False

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.snmp.traps_s.trap.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return NonNetworkedParameters(result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(
                required=True
            ),
            snmp_version=dict(
                choices=['1', '2c']
            ),
            community=dict(),
            destination=dict(),
            port=dict(),
            network=dict(
                choices=['other', 'management', 'default']
            ),
            state=dict(
                default='present',
                choices=['absent', 'present']
            )
        )
        self.f5_product_name = 'bigip'


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    mm = ModuleManager(client)
    results = mm.exec_module()
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
