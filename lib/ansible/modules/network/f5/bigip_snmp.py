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
module: bigip_snmp
short_description: Manipulate general SNMP settings on a BIG-IP
description:
  - Manipulate general SNMP settings on a BIG-IP.
version_added: 2.4
options:
  allowed_addresses:
    description:
      - Configures the IP addresses of the SNMP clients from which the snmpd
        daemon accepts requests.
      - This value can be hostnames, IP addresses, or IP networks.
      - You may specify a single list item of C(default) to set the value back
        to the system's default of C(127.0.0.0/8).
      - You can remove all allowed addresses by either providing the word C(none), or
        by providing the empty string C("").
    type: raw
    version_added: 2.6
  contact:
    description:
      - Specifies the name of the person who administers the SNMP
        service for this system.
    type: str
  agent_status_traps:
    description:
      - When C(enabled), ensures that the system sends a trap whenever the
        SNMP agent starts running or stops running. This is usually enabled
        by default on a BIG-IP.
    type: str
    choices:
      - enabled
      - disabled
  agent_authentication_traps:
    description:
      - When C(enabled), ensures that the system sends authentication warning
        traps to the trap destinations. This is usually disabled by default on
        a BIG-IP.
    type: str
    choices:
      - enabled
      - disabled
  device_warning_traps:
    description:
      - When C(enabled), ensures that the system sends device warning traps
        to the trap destinations. This is usually enabled by default on a
        BIG-IP.
    type: str
    choices:
      - enabled
      - disabled
  location:
    description:
      - Specifies the description of this system's physical location.
    type: str
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Set snmp contact
  bigip_snmp:
    contact: Joe User
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Set snmp location
  bigip_snmp:
    location: US West 1
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
agent_status_traps:
  description: Value that the agent status traps was set to.
  returned: changed
  type: str
  sample: enabled
agent_authentication_traps:
  description: Value that the authentication status traps was set to.
  returned: changed
  type: str
  sample: enabled
device_warning_traps:
  description: Value that the warning status traps was set to.
  returned: changed
  type: str
  sample: enabled
contact:
  description: The new value for the person who administers SNMP on the device.
  returned: changed
  type: str
  sample: Joe User
location:
  description: The new value for the system's physical location.
  returned: changed
  type: str
  sample: US West 1a
allowed_addresses:
  description: The new allowed addresses for SNMP client connections.
  returned: changed
  type: list
  sample: ['127.0.0.0/8', 'foo.bar.com', '10.10.10.10']
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.compat.ipaddress import ip_network
    from library.module_utils.network.f5.common import is_valid_hostname
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.compat.ipaddress import ip_network
    from ansible.module_utils.network.f5.common import is_valid_hostname


class Parameters(AnsibleF5Parameters):
    api_map = {
        'agentTrap': 'agent_status_traps',
        'authTrap': 'agent_authentication_traps',
        'bigipTraps': 'device_warning_traps',
        'sysLocation': 'location',
        'sysContact': 'contact',
        'allowedAddresses': 'allowed_addresses',
    }

    updatables = [
        'agent_status_traps',
        'agent_authentication_traps',
        'device_warning_traps',
        'location',
        'contact',
        'allowed_addresses',
    ]

    returnables = [
        'agent_status_traps',
        'agent_authentication_traps',
        'device_warning_traps',
        'location', 'contact',
        'allowed_addresses',
    ]

    api_attributes = [
        'agentTrap',
        'authTrap',
        'bigipTraps',
        'sysLocation',
        'sysContact',
        'allowedAddresses',
    ]


class ApiParameters(Parameters):
    @property
    def allowed_addresses(self):
        if self._values['allowed_addresses'] is None:
            return None
        result = list(set(self._values['allowed_addresses']))
        result.sort()
        return result


class ModuleParameters(Parameters):
    @property
    def allowed_addresses(self):
        if self._values['allowed_addresses'] is None:
            return None
        result = []
        addresses = self._values['allowed_addresses']
        if isinstance(addresses, string_types):
            if addresses in ['', 'none']:
                return []
            else:
                addresses = [addresses]
        if len(addresses) == 1 and addresses[0] in ['default', '']:
            result = ['127.0.0.0/8']
            return result
        for address in addresses:
            try:
                # Check for valid IPv4 or IPv6 entries
                ip_network(u'%s' % str(address))
                result.append(address)
            except ValueError:
                # else fallback to checking reasonably well formatted hostnames
                if is_valid_hostname(address):
                    result.append(str(address))
                    continue
                raise F5ModuleError(
                    "The provided 'allowed_address' value {0} is not a valid IP or hostname".format(address)
                )
        result = list(set(result))
        result.sort()
        return result


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    pass


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

    @property
    def allowed_addresses(self):
        if self.want.allowed_addresses is None:
            return None
        if self.have.allowed_addresses is None:
            if self.want.allowed_addresses:
                return self.want.allowed_addresses
            return None
        want = set(self.want.allowed_addresses)
        have = set(self.have.allowed_addresses)
        if want != have:
            result = list(want)
            result.sort()
            return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.have = ApiParameters()
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

    def exec_module(self):
        result = dict()

        changed = self.update()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/snmp/".format(
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
        return ApiParameters(params=response)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/snmp/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.choices = ['enabled', 'disabled']
        argument_spec = dict(
            contact=dict(),
            agent_status_traps=dict(
                choices=self.choices
            ),
            agent_authentication_traps=dict(
                choices=self.choices
            ),
            device_warning_traps=dict(
                choices=self.choices
            ),
            location=dict(),
            allowed_addresses=dict(type='raw')
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

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
