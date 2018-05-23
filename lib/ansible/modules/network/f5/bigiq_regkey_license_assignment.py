#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigiq_regkey_license_assignment
short_description: Manage regkey license assignment on BIG-IPs from a BIG-IQ.
description:
  - Manages the assignment of regkey licenses on a BIG-IQ. Assignment means that
    the license is assigned to a BIG-IP, or, it needs to be assigned to a BIG-IP.
    Additionally, this module supported revoking the assignments from BIG-IP devices.
version_added: 2.6
options:
  pool:
    description:
      - The registration key pool to use.
    required: True
  key:
    description:
      - The registration key that you want to assign from the pool.
    required: True
  device:
    description:
      - When C(managed) is C(no), specifies the address, or hostname, where the BIG-IQ
        can reach the remote device to register.
      - When C(managed) is C(yes), specifies the managed device, or device UUID, that
        you want to register.
      - If C(managed) is C(yes), it is very important that you do not have more than
        one device with the same name. BIG-IQ internally recognizes devices by their ID,
        and therefore, this module's cannot guarantee that the correct device will be
        registered. The device returned is the device that will be used.
  managed:
    description:
      - Whether the specified device is a managed or un-managed device.
      - When C(state) is C(present), this parameter is required.
    type: bool
  device_port:
    description:
      - Specifies the port of the remote device to connect to.
      - If this parameter is not specified, the default of C(443) will be used.
    default: 443
  device_username:
    description:
      - The username used to connect to the remote device.
      - This username should be one that has sufficient privileges on the remote device
        to do licensing. Usually this is the C(Administrator) role.
      - When C(managed) is C(no), this parameter is required.
  device_password:
    description:
      - The password of the C(device_username).
      - When C(managed) is C(no), this parameter is required.
  state:
    description:
      - When C(present), ensures that the device is assigned the specified license.
      - When C(absent), ensures the license is revokes from the remote device and freed
        on the BIG-IQ.
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Register an unmanaged device
  bigiq_regkey_license_assignment:
    pool: my-regkey-pool
    key: XXXX-XXXX-XXXX-XXXX-XXXX
    device: 1.1.1.1
    managed: no
    device_username: admin
    device_password: secret
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Register an managed device, by name
  bigiq_regkey_license_assignment:
    pool: my-regkey-pool
    key: XXXX-XXXX-XXXX-XXXX-XXXX
    device: bigi1.foo.com
    managed: yes
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Register an managed device, by UUID
  bigiq_regkey_license_assignment:
    pool: my-regkey-pool
    key: XXXX-XXXX-XXXX-XXXX-XXXX
    device: 7141a063-7cf8-423f-9829-9d40599fa3e0
    managed: yes
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import re

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigiq import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import exit_json
    from library.module_utils.network.f5.common import fail_json
except ImportError:
    from ansible.module_utils.network.f5.bigiq import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import exit_json
    from ansible.module_utils.network.f5.common import fail_json
try:
    import netaddr
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'deviceReference': 'device_reference',
        'deviceAddress': 'device_address',
        'httpsPort': 'device_port'
    }

    api_attributes = [
        'deviceReference', 'deviceAddress', 'httpsPort', 'managed'
    ]

    returnables = [
        'device_address', 'device_reference', 'device_username', 'device_password',
        'device_port', 'managed'
    ]

    updatables = [
        'device_reference', 'device_address', 'device_username', 'device_password',
        'device_port', 'managed'
    ]

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def device_password(self):
        if self._values['device_password'] is None:
            return None
        return self._values['device_password']

    @property
    def device_username(self):
        if self._values['device_username'] is None:
            return None
        return self._values['device_username']

    @property
    def device_address(self):
        if self.device_is_address:
            return self._values['device']

    @property
    def device_port(self):
        if self._values['device_port'] is None:
            return None
        return int(self._values['device_port'])

    @property
    def device_is_address(self):
        try:
            netaddr.IPAddress(self.device)
            return True
        except (ValueError, netaddr.core.AddrFormatError):
            return False

    @property
    def device_is_id(self):
        pattern = r'[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}'
        if re.match(pattern, self.device):
            return True
        return False

    @property
    def device_is_name(self):
        if not self.device_is_address and not self.device_is_id:
            return True
        return False

    @property
    def device_reference(self):
        if not self.managed:
            return None
        if self.device_is_address:
            # This range lookup is how you do lookups for single IP addresses. Weird.
            filter = "address+eq+'{0}...{0}'".format(self.device)
        elif self.device_is_name:
            filter = "hostname+eq+'{0}'".format(self.device)
        elif self.device_is_id:
            filter = "uuid+eq+'{0}'".format(self.device)
        else:
            raise F5ModuleError(
                "Unknown device format '{0}'".format(self.device)
            )

        uri = "https://{0}:{1}/mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices/?$filter={2}&$top=1".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            filter
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if resp.status == 200 and response['totalItems'] == 0:
            raise F5ModuleError(
                "No device with the specified address was found."
            )
        elif 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)
        id = response['items'][0]['uuid']
        result = dict(
            link='https://localhost/mgmt/shared/resolver/device-groups/cm-bigip-allBigIpDevices/devices/{0}'.format(id)
        )
        return result

    @property
    def pool_id(self):
        filter = "(name eq '{0}')".format(self.pool)
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses?$filter={2}&$top=1'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            filter
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if resp.status == 200 and response['totalItems'] == 0:
            raise F5ModuleError(
                "No pool with the specified name was found."
            )
        elif 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)
        return response['items'][0]['id']

    @property
    def member_id(self):
        if self.device_is_address:
            # This range lookup is how you do lookups for single IP addresses. Weird.
            filter = "deviceAddress+eq+'{0}...{0}'".format(self.device)
        elif self.device_is_name:
            filter = "deviceName+eq+'{0}'".format(self.device)
        elif self.device_is_id:
            filter = "deviceMachineId+eq+'{0}'".format(self.device)
        else:
            raise F5ModuleError(
                "Unknown device format '{0}'".format(self.device)
            )
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}/members/?$filter={4}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.pool_id,
            self.key,
            filter
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if resp.status == 200 and response['totalItems'] == 0:
            return None
        elif 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)
        result = response['items'][0]['id']
        return result


class Changes(Parameters):
    pass


class UsableChanges(Changes):
    @property
    def device_port(self):
        if self._values['managed']:
            return None
        return self._values['device_port']

    @property
    def device_username(self):
        if self._values['managed']:
            return None
        return self._values['device_username']

    @property
    def device_password(self):
        if self._values['managed']:
            return None
        return self._values['device_password']

    @property
    def device_reference(self):
        if not self._values['managed']:
            return None
        return self._values['device_reference']

    @property
    def device_address(self):
        if self._values['managed']:
            return None
        return self._values['device_address']

    @property
    def managed(self):
        return None


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


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = ModuleParameters(params=self.module.params, client=self.client)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

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
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

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

    def present(self):
        if self.exists():
            return False
        return self.create()

    def exists(self):
        if self.want.member_id is None:
            return False
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}/members/{4}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.pool_id,
            self.want.key,
            self.want.member_id
        )
        resp = self.client.api.get(uri)
        if resp.status == 200:
            return True
        return False

    def remove(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if not self.want.managed:
            if self.want.device_username is None:
                raise F5ModuleError(
                    "You must specify a 'device_username' when working with unmanaged devices."
                )
            if self.want.device_password is None:
                raise F5ModuleError(
                    "You must specify a 'device_password' when working with unmanaged devices."
                )
        if self.module.check_mode:
            return True
        self.create_on_device()
        if not self.exists():
            raise F5ModuleError(
                "Failed to license the remote device."
            )
        self.wait_for_device_to_be_licensed()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}/members/'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.pool_id,
            self.want.key
        )

        if not self.want.managed:
            params['username'] = self.want.device_username
            params['password'] = self.want.device_password

        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)

    def wait_for_device_to_be_licensed(self):
        count = 0
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}/members/{4}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.pool_id,
            self.want.key,
            self.want.member_id
        )
        while count < 3:
            resp = self.client.api.get(uri)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp._content)
            if response['status'] == 'LICENSED':
                count += 1
            else:
                count = 0

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}/members/{4}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.pool_id,
            self.want.key,
            self.want.member_id
        )
        params = {}
        if not self.want.managed:
            params.update(self.changes.api_params())
            params['id'] = self.want.member_id
            params['username'] = self.want.device_username
            params['password'] = self.want.device_password
        self.client.api.delete(uri, json=params)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            pool=dict(required=True),
            key=dict(required=True, no_log=True),
            device=dict(required=True),
            managed=dict(type='bool'),
            device_port=dict(type='int', default=443),
            device_username=dict(no_log=True),
            device_password=dict(no_log=True),
            state=dict(default='present', choices=['absent', 'present'])
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['state', 'present', ['key', 'managed']],
            ['managed', False, ['device', 'device_username', 'device_password']],
            ['managed', True, ['device']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )
    if not HAS_NETADDR:
        module.fail_json(msg="The python netaddr module is required")

    try:
        client = F5RestClient(module=module)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        exit_json(module, results, client)
    except F5ModuleError as ex:
        fail_json(module, ex, client)


if __name__ == '__main__':
    main()
