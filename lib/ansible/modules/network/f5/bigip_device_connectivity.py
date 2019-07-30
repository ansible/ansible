#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

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
    type: str
  mirror_primary_address:
    description:
      - Specifies the primary IP address for the system to use to mirror
        connections.
    type: str
  mirror_secondary_address:
    description:
      - Specifies the secondary IP address for the system to use to mirror
        connections.
    type: str
  unicast_failover:
    description:
      - Desired addresses to use for failover operations. Options C(address)
        and C(port) are supported with dictionary structure where C(address) is the
        local IP address that the system uses for failover operations. Port
        specifies the port that the system uses for failover operations. If C(port)
        is not specified, the default value C(1026) will be used.  If you are
        specifying the (recommended) management IP address, use 'management-ip' in
        the address field.
    type: list
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
    type: str
  multicast_address:
    description:
      - IP address for the system to send multicast messages associated with
        failover. When C(failover_multicast) is C(yes) and this option is not
        provided, a default of C(224.0.0.245) will be used.
    type: str
  multicast_port:
    description:
      - Port for the system to send multicast messages associated with
        failover. When C(failover_multicast) is C(yes) and this option is not
        provided, a default of C(62960) will be used. This value must be between
        0 and 65535.
    type: int
  cluster_mirroring:
    description:
      - Specifies whether mirroring occurs within the same cluster or between
        different clusters on a multi-bladed system.
      - This parameter is only supported on platforms that have multiple blades,
        such as Viprion hardware. It is not supported on VE.
    type: str
    choices:
      - between-clusters
      - within-cluster
    version_added: 2.7
notes:
  - This module is primarily used as a component of configuring HA pairs of
    BIG-IP devices.
  - Requires BIG-IP >= 12.0.0
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Configure device connectivity for standard HA pair
  bigip_device_connectivity:
    config_sync_ip: 10.1.30.1
    mirror_primary_address: 10.1.30.1
    unicast_failover:
      - address: management-ip
      - address: 10.1.30.1
    provider:
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
  type: str
  sample: 10.1.1.1
mirror_primary_address:
  description: The new value of the C(mirror_primary_address) setting.
  returned: changed
  type: str
  sample: 10.1.1.2
mirror_secondary_address:
  description: The new value of the C(mirror_secondary_address) setting.
  returned: changed
  type: str
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
  type: str
  sample: eth0
multicast_address:
  description: The new value of the C(multicast_address) setting.
  returned: changed
  type: str
  sample: 224.0.0.245
multicast_port:
  description: The new value of the C(multicast_port) setting.
  returned: changed
  type: int
  sample: 1026
cluster_mirroring:
  description: The current cluster-mirroring setting.
  returned: changed
  type: str
  sample: between-clusters
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.ipaddress import is_valid_ip
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip


class Parameters(AnsibleF5Parameters):
    api_map = {
        'unicastAddress': 'unicast_failover',
        'configsyncIp': 'config_sync_ip',
        'multicastInterface': 'multicast_interface',
        'multicastIp': 'multicast_address',
        'multicastPort': 'multicast_port',
        'mirrorIp': 'mirror_primary_address',
        'mirrorSecondaryIp': 'mirror_secondary_address',
        'managementIp': 'management_ip',
    }
    api_attributes = [
        'configsyncIp',
        'multicastInterface',
        'multicastIp',
        'multicastPort',
        'mirrorIp',
        'mirrorSecondaryIp',
        'unicastAddress',
    ]
    returnables = [
        'config_sync_ip',
        'multicast_interface',
        'multicast_address',
        'multicast_port',
        'mirror_primary_address',
        'mirror_secondary_address',
        'failover_multicast',
        'unicast_failover',
        'cluster_mirroring',
    ]
    updatables = [
        'config_sync_ip',
        'multicast_interface',
        'multicast_address',
        'multicast_port',
        'mirror_primary_address',
        'mirror_secondary_address',
        'failover_multicast',
        'unicast_failover',
        'cluster_mirroring',
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
        if address != 'management-ip':
            if is_valid_ip(address):
                return address
            else:
                raise F5ModuleError(
                    "'address' field in unicast failover is not a valid IP address"
                )
        else:
            return address

    def _get_validated_ip_address(self, address):
        if is_valid_ip(self._values[address]):
            return self._values[address]
        raise F5ModuleError(
            "The specified '{0}' is not a valid IP address".format(address)
        )


class ApiParameters(Parameters):
    @property
    def cluster_mirroring(self):
        if self._values['cluster_mirroring'] is None:
            return None
        if self._values['cluster_mirroring'] == 'between':
            return 'between-clusters'
        return 'within-cluster'


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
                change = getattr(self, returnable)
                if isinstance(change, dict):
                    result.update(change)
                else:
                    result[returnable] = change
            result = self._filter_params(result)
        except Exception:
            pass
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

    @property
    def cluster_mirroring(self):
        if self._values['cluster_mirroring'] is None:
            return None
        elif self._values['cluster_mirroring'] == 'between-clusters':
            return 'between'
        return 'within'


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
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
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

        changed = self.update()

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
        if self.changes.cluster_mirroring:
            self.update_cluster_mirroring_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        if not params:
            return
        uri = "https://{0}:{1}/mgmt/tm/cm/device/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        for item in response['items']:
            if item['selfDevice'] == 'true':
                uri = "https://{0}:{1}/mgmt/tm/cm/device/{2}".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                    transform_name(item['partition'], item['name'])
                )
                resp = self.client.api.patch(uri, json=params)
                try:
                    response = resp.json()
                except ValueError as ex:
                    raise F5ModuleError(str(ex))

                if 'code' in response and response['code'] == 400:
                    if 'message' in response:
                        raise F5ModuleError(response['message'])
                    else:
                        raise F5ModuleError(resp.content)
                return
        raise F5ModuleError(
            "The host device was not found."
        )

    def update_cluster_mirroring_on_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/db/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            'statemirror.clustermirroring'
        )
        payload = {"value": self.changes.cluster_mirroring}
        resp = self.client.api.patch(uri, json=payload)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def read_current_from_device(self):
        db = self.read_cluster_mirroring_from_device()
        uri = "https://{0}:{1}/mgmt/tm/cm/device/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        for item in response['items']:
            if item['selfDevice'] == 'true':
                uri = "https://{0}:{1}/mgmt/tm/cm/device/{2}".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                    transform_name(item['partition'], item['name'])
                )
                resp = self.client.api.get(uri)
                try:
                    response = resp.json()
                except ValueError as ex:
                    raise F5ModuleError(str(ex))

                if 'code' in response and response['code'] == 400:
                    if 'message' in response:
                        raise F5ModuleError(response['message'])
                    else:
                        raise F5ModuleError(resp.content)
                if db:
                    response['cluster_mirroring'] = db['value']
                return ApiParameters(params=response)
        raise F5ModuleError(
            "The host device was not found."
        )

    def read_cluster_mirroring_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/db/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            'statemirror.clustermirroring'
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response


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
            config_sync_ip=dict(),
            cluster_mirroring=dict(
                choices=['within-cluster', 'between-clusters']
            )
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

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
