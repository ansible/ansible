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
module: bigip_device_connectivity
short_description: Manages device IP configuration settings for HA on a BIG-IP
description:
  - Manages device IP configuration settings for HA on a BIG-IP. Each BIG-IP device
    has synchronization and failover connectivity information (IP addresses) that
    you define as part of HA pairing or clustering. This module allows you to configure
    that information.
version_added: 2.5
options:
  config_sync_ip:
    description:
      - Local IP address that the system uses for ConfigSync operations.
  mirror_primary_address:
    description:
      - Specifies the primary IP address for the system to use to mirror
        connections.
  mirror_secondary_address:
    description:
      - Specifies the secondary IP address for the system to use to mirror
        connections.
  unicast_failover:
    description:
      - Desired addresses to use for failover operations. Options C(address)
        and C(port) are supported with dictionary structure where C(address) is the
        local IP address that the system uses for failover operations. Port
        specifies the port that the system uses for failover operations. If C(port)
        is not specified, the default value C(1026) will be used.  If you are
        specifying the (recommended) management IP address, use 'management-ip' in
        the address field.
  failover_multicast:
    description:
      - When C(yes), ensures that the Failover Multicast configuration is enabled
        and if no further multicast configuration is provided, ensures that
        C(multicast_interface), C(multicast_address) and C(multicast_port) are
        the defaults specified in each option's description. When C(no), ensures
        that Failover Multicast configuration is disabled.
    type: bool
  multicast_interface:
    description:
      - Interface over which the system sends multicast messages associated
        with failover. When C(failover_multicast) is C(yes) and this option is
        not provided, a default of C(eth0) will be used.
  multicast_address:
    description:
      - IP address for the system to send multicast messages associated with
        failover. When C(failover_multicast) is C(yes) and this option is not
        provided, a default of C(224.0.0.245) will be used.
  multicast_port:
    description:
      - Port for the system to send multicast messages associated with
        failover. When C(failover_multicast) is C(yes) and this option is not
        provided, a default of C(62960) will be used. This value must be between
        0 and 65535.
notes:
  - This module is primarily used as a component of configuring HA pairs of
    BIG-IP devices.
  - Requires BIG-IP >= 12.0.0
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Configure device connectivity for standard HA pair
  bigip_device_connectivity:
    config_sync_ip: 10.1.30.1
    mirror_primary_address: 10.1.30.1
    unicast_failover:
      - address: management-ip
      - address: 10.1.30.1
    server: lb.mydomain.com
    user: admin
    password: secret
  delegate_to: localhost
'''

RETURN = r'''
changed:
  description: Denotes if the F5 configuration was updated.
  returned: always
  type: bool
config_sync_ip:
  description: The new value of the C(config_sync_ip) setting.
  returned: changed
  type: string
  sample: 10.1.1.1
mirror_primary_address:
  description: The new value of the C(mirror_primary_address) setting.
  returned: changed
  type: string
  sample: 10.1.1.2
mirror_secondary_address:
  description: The new value of the C(mirror_secondary_address) setting.
  returned: changed
  type: string
  sample: 10.1.1.3
unicast_failover:
  description: The new value of the C(unicast_failover) setting.
  returned: changed
  type: list
  sample: [{'address': '10.1.1.2', 'port': 1026}]
failover_multicast:
  description: Whether a failover multicast attribute has been changed or not.
  returned: changed
  type: bool
multicast_interface:
  description: The new value of the C(multicast_interface) setting.
  returned: changed
  type: string
  sample: eth0
multicast_address:
  description: The new value of the C(multicast_address) setting.
  returned: changed
  type: string
  sample: 224.0.0.245
multicast_port:
  description: The new value of the C(multicast_port) setting.
  returned: changed
  type: string
  sample: 1026
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

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
    from netaddr import IPAddress, AddrFormatError
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'unicastAddress': 'unicast_failover',
        'configsyncIp': 'config_sync_ip',
        'multicastInterface': 'multicast_interface',
        'multicastIp': 'multicast_address',
        'multicastPort': 'multicast_port',
        'mirrorIp': 'mirror_primary_address',
        'mirrorSecondaryIp': 'mirror_secondary_address',
        'managementIp': 'management_ip'
    }
    api_attributes = [
        'configsyncIp', 'multicastInterface', 'multicastIp', 'multicastPort',
        'mirrorIp', 'mirrorSecondaryIp', 'unicastAddress'
    ]
    returnables = [
        'config_sync_ip', 'multicast_interface', 'multicast_address',
        'multicast_port', 'mirror_primary_address', 'mirror_secondary_address',
        'failover_multicast', 'unicast_failover'
    ]
    updatables = [
        'config_sync_ip', 'multicast_interface', 'multicast_address',
        'multicast_port', 'mirror_primary_address', 'mirror_secondary_address',
        'failover_multicast', 'unicast_failover'
    ]

    @property
    def multicast_port(self):
        if self._values['multicast_port'] is None:
            return None
        result = int(self._values['multicast_port'])
        if result < 0 or result > 65535:
            raise F5ModuleError(
                "The specified 'multicast_port' must be between 0 and 65535."
            )
        return result

    @property
    def multicast_address(self):
        if self._values['multicast_address'] is None:
            return None
        elif self._values['multicast_address'] in ["none", "any6", '']:
            return "any6"
        elif self._values['multicast_address'] == 'any':
            return 'any'
        result = self._get_validated_ip_address('multicast_address')
        return result

    @property
    def mirror_primary_address(self):
        if self._values['mirror_primary_address'] is None:
            return None
        elif self._values['mirror_primary_address'] in ["none", "any6", '']:
            return "any6"
        result = self._get_validated_ip_address('mirror_primary_address')
        return result

    @property
    def mirror_secondary_address(self):
        if self._values['mirror_secondary_address'] is None:
            return None
        elif self._values['mirror_secondary_address'] in ["none", "any6", '']:
            return "any6"
        result = self._get_validated_ip_address('mirror_secondary_address')
        return result

    @property
    def config_sync_ip(self):
        if self._values['config_sync_ip'] is None:
            return None
        elif self._values['config_sync_ip'] in ["none", '']:
            return "none"
        result = self._get_validated_ip_address('config_sync_ip')
        return result

    def _validate_unicast_failover_port(self, port):
        try:
            result = int(port)
        except ValueError:
            raise F5ModuleError(
                "The provided 'port' for unicast failover is not a valid number"
            )
        except TypeError:
            result = 1026
        return result

    def _validate_unicast_failover_address(self, address):
        try:
            if address != 'management-ip':
                result = IPAddress(address)
                return str(result)
            else:
                return address
        except KeyError:
            raise F5ModuleError(
                "An 'address' must be supplied when configuring unicast failover"
            )
        except AddrFormatError:
            raise F5ModuleError(
                "'address' field in unicast failover is not a valid IP address"
            )

    def _get_validated_ip_address(self, address):
        try:
            IPAddress(self._values[address])
            return self._values[address]
        except AddrFormatError:
            raise F5ModuleError(
                "The specified '{0}' is not a valid IP address".format(
                    address
                )
            )


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def unicast_failover(self):
        if self._values['unicast_failover'] is None:
            return None
        if self._values['unicast_failover'] == ['none']:
            return []
        result = []
        for item in self._values['unicast_failover']:
            address = item.get('address', None)
            port = item.get('port', None)
            address = self._validate_unicast_failover_address(address)
            port = self._validate_unicast_failover_port(port)
            result.append(
                dict(
                    effectiveIp=address,
                    effectivePort=port,
                    ip=address,
                    port=port
                )
            )
        if result:
            return result
        else:
            return None


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
        except Exception:
            pass
        result = self._filter_params(result)
        return result


class ReportableChanges(Changes):
    returnables = [
        'config_sync_ip', 'multicast_interface', 'multicast_address',
        'multicast_port', 'mirror_primary_address', 'mirror_secondary_address',
        'failover_multicast', 'unicast_failover'
    ]

    @property
    def mirror_secondary_address(self):
        if self._values['mirror_secondary_address'] in ['none', 'any6']:
            return 'none'
        return self._values['mirror_secondary_address']

    @property
    def mirror_primary_address(self):
        if self._values['mirror_primary_address'] in ['none', 'any6']:
            return 'none'
        return self._values['mirror_primary_address']

    @property
    def multicast_address(self):
        if self._values['multicast_address'] in ['none', 'any6']:
            return 'none'
        return self._values['multicast_address']


class UsableChanges(Changes):
    @property
    def mirror_primary_address(self):
        if self._values['mirror_primary_address'] == ['any6', 'none', 'any']:
            return "any6"
        else:
            return self._values['mirror_primary_address']

    @property
    def mirror_secondary_address(self):
        if self._values['mirror_secondary_address'] == ['any6', 'none', 'any']:
            return "any6"
        else:
            return self._values['mirror_secondary_address']

    @property
    def multicast_address(self):
        if self._values['multicast_address'] == ['any6', 'none', 'any']:
            return "any"
        else:
            return self._values['multicast_address']

    @property
    def unicast_failover(self):
        if self._values['unicast_failover'] is None:
            return None
        elif self._values['unicast_failover']:
            return self._values['unicast_failover']
        return "none"


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    def to_tuple(self, failovers):
        result = []
        for x in failovers:
            for k, v in iteritems(x):
                # Have to do this in cases where the BIG-IP stores the word
                # "management-ip" when you specify the management IP address.
                #
                # Otherwise, a difference would be registered.
                if v == self.have.management_ip:
                    v = 'management-ip'
                result += [(str(k), str(v))]
        return result

    @property
    def unicast_failover(self):
        if self.want.unicast_failover == [] and self.have.unicast_failover is None:
            return None
        if self.want.unicast_failover is None:
            return None
        if self.have.unicast_failover is None:
            return self.want.unicast_failover
        want = self.to_tuple(self.want.unicast_failover)
        have = self.to_tuple(self.have.unicast_failover)
        if set(want) == set(have):
            return None
        else:
            return self.want.unicast_failover

    @property
    def failover_multicast(self):
        values = ['multicast_address', 'multicast_interface', 'multicast_port']
        if self.want.failover_multicast is False:
            if self.have.multicast_interface == 'eth0' and self.have.multicast_address == 'any' and self.have.multicast_port == 0:
                return None
            else:
                result = dict(
                    failover_multicast=True,
                    multicast_port=0,
                    multicast_interface='eth0',
                    multicast_address='any'
                )
                return result
        else:
            if all(self.have._values[x] in [None, 'any6', 'any'] for x in values):
                return True


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = ModuleParameters(params=self.module.params)
        self.changes = UsableChanges()

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        result = dict()

        try:
            changed = self.update()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        collection = self.client.api.tm.cm.devices.get_collection()
        for resource in collection:
            if resource.selfDevice == 'true':
                resource.modify(**params)
                return
        raise F5ModuleError(
            "The host device was not found."
        )

    def read_current_from_device(self):
        collection = self.client.api.tm.cm.devices.get_collection()
        for resource in collection:
            if resource.selfDevice == 'true':
                result = resource.attrs
                return ApiParameters(params=result)
        raise F5ModuleError(
            "The host device was not found."
        )


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            multicast_port=dict(
                type='int'
            ),
            multicast_address=dict(),
            multicast_interface=dict(),
            failover_multicast=dict(
                type='bool'
            ),
            unicast_failover=dict(
                type='list'
            ),
            mirror_primary_address=dict(),
            mirror_secondary_address=dict(),
            config_sync_ip=dict()
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_together = [
            ['multicast_address', 'multicast_interface', 'multicast_port']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_together=spec.required_together
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
