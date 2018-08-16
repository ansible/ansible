#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
module: bigip_snmp_trap
short_description: Manipulate SNMP trap information on a BIG-IP
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
    choices: ['1', '2c']
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
      - The value C(default) was removed in BIG-IP version 13.1.0. Specifying this
        value when configuring a BIG-IP will cause the module to stop and report
        an error. The usual remedy is to choose one of the other options, such as
        C(management).
    choices:
      - other
      - management
      - default
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures that the resource does not exist.
    default: present
    choices:
      - present
      - absent
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
notes:
  - This module only supports version v1 and v2c of SNMP.
  - The C(network) option is not supported on versions of BIG-IP < 12.1.0 because
    the platform did not support that option until 12.1.0. If used on versions
    < 12.1.0, it will simply be ignored.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create snmp v1 trap
  bigip_snmp_trap:
    community: general
    destination: 1.2.3.4
    name: my-trap1
    network: management
    port: 9000
    snmp_version: 1
    server: lb.mydomain.com
    user: admin
    password: secret
  delegate_to: localhost

- name: Create snmp v2 trap
  bigip_snmp_trap:
    community: general
    destination: 5.6.7.8
    name: my-trap2
    network: default
    port: 7000
    snmp_version: 2c
    server: lb.mydomain.com
    user: admin
    password: secret
  delegate_to: localhost
'''

RETURN = r'''
snmp_version:
  description: The new C(snmp_version) configured on the remote device.
  returned: changed and success
  type: string
  sample: 2c
community:
  description: The new C(community) name for the trap destination.
  returned: changed and success
  type: list
  sample: secret
destination:
  description: The new address for the trap destination in either IP or hostname form.
  returned: changed and success
  type: string
  sample: 1.2.3.4
port:
  description: The new C(port) of the trap destination.
  returned: changed and success
  type: string
  sample: 900
network:
  description: The new name of the network the SNMP trap is on.
  returned: changed and success
  type: string
  sample: management
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

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


class V3Parameters(Parameters):
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
            raise F5ModuleError(
                "'default' is not a valid option for this version of BIG-IP. "
                "Use either 'management', 'or 'other' instead."
            )
        else:
            return network


class V2Parameters(Parameters):
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


class V1Parameters(Parameters):
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
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

    def exec_module(self):
        if self.is_version_without_network():
            manager = V1Manager(**self.kwargs)
        elif self.is_version_with_default_network():
            manager = V2Manager(**self.kwargs)
        else:
            manager = V3Manager(**self.kwargs)

        return manager.exec_module()

    def is_version_without_network(self):
        """Is current BIG-IP version missing "network" value support

        Returns:
            bool: True when it is missing. False otherwise.
        """
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.1.0'):
            return True
        else:
            return False

    def is_version_with_default_network(self):
        """Is current BIG-IP version missing "default" network value support

        Returns:
            bool: True when it is missing. False otherwise.
        """
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('13.1.0'):
            return True
        else:
            return False


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
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
        if self.module.check_mode:
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
        if self.module.check_mode:
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
        if self.module.check_mode:
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


class V3Manager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(V3Manager, self).__init__(**kwargs)
        self.required_resources = [
            'version', 'community', 'destination', 'port', 'network'
        ]
        self.want = V3Parameters(params=self.module.params)
        self.changes = V3Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in V3Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = V3Parameters(params=changed)

    def _update_changed_options(self):
        changed = {}
        for key in V3Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if changed:
            self.changes = V3Parameters(params=changed)
            return True
        return False

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.snmp.traps_s.trap.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return V3Parameters(params=result)


class V2Manager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(V2Manager, self).__init__(**kwargs)
        self.required_resources = [
            'version', 'community', 'destination', 'port', 'network'
        ]
        self.want = V2Parameters(params=self.module.params)
        self.changes = V2Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in V2Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = V2Parameters(params=changed)

    def _update_changed_options(self):
        changed = {}
        for key in V2Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if changed:
            self.changes = V2Parameters(params=changed)
            return True
        return False

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.snmp.traps_s.trap.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        self._ensure_network(result)
        return V2Parameters(params=result)

    def _ensure_network(self, result):
        # BIG-IP's value for "default" is that the key does not
        # exist. This conflicts with our purpose of having a key
        # not exist (which we equate to "i dont want to change that"
        # therefore, if we load the information from BIG-IP and
        # find that there is no 'network' key, that is BIG-IP's
        # way of saying that the network value is "default"
        if 'network' not in result:
            result['network'] = 'default'


class V1Manager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(V1Manager, self).__init__(**kwargs)
        self.required_resources = [
            'version', 'community', 'destination', 'port'
        ]
        self.want = V1Parameters(params=self.module.params)
        self.changes = V1Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in V1Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = V1Parameters(params=changed)

    def _update_changed_options(self):
        changed = {}
        for key in V1Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if changed:
            self.changes = V1Parameters(params=changed)
            return True
        return False

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.snmp.traps_s.trap.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return V1Parameters(params=result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True
            ),
            snmp_version=dict(
                choices=['1', '2c']
            ),
            community=dict(no_log=True),
            destination=dict(),
            port=dict(),
            network=dict(
                choices=['other', 'management', 'default']
            ),
            state=dict(
                default='present',
                choices=['absent', 'present']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
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
