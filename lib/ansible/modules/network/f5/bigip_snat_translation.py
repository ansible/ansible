#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_snat_translation
short_description:  Manage SNAT Translations on a BIG-IP
description:
  - Manage SNAT Translations on a BIG-IP.
version_added: 2.9
options:
  address:
    description:
      - Specifies the IP address of the SNAT translation. When a C(state) of present, enabled, or disabled is
        provided, this parameter is required.
      - This parameter cannot be updated after it is set.
    type: str
    aliases:
      - ip
  arp:
    description:
      - If C(yes), specifies that the NAT sends ARP requests.
    type: bool
  connection_limit:
    description:
      - Specifies a limit on the number of connections a translation address must reach before it no longer
        initiates a connection. The default value of 0 indicates that the setting is disabled.
      - The accepted value range is C(0 - 65535).
    type: int
  description:
    description:
      - Description of snat-translation. C(none or '') will set to default description of null.
    type: str
  ip_idle_timeout:
    description:
      - Specifies the amount of time that connections to an IP address initiated using a SNAT address are
        allowed to remain idle before being automatically disconnected. C(indefinite) prevents the connection
        from timing out.
      - The accepted value range is C(0 - 4294967295) seconds, specifying C(indefinite) will
        set it to the maximum value.
    type: str
  name:
    description:
      - The name of SNAT translation.
    type: str
    required: True
  partition:
    description:
      - Device partition to manage resources on.
      - Required with state C(absent) when partition other than Common used.
    type: str
  state:
    description:
      - The SNAT translation state. If C(absent), delete the SNAT translation
        if it exists. C(present) creates the SNAT translation and enable it.
        If C(enabled), enable the SNAT translation if it exists. If C(disabled),
        create the SNAT translation if needed, and set state to C(disabled).
    type: str
    choices:
      - present
      - absent
      - enabled
      - disabled
    default: present
  tcp_idle_timeout:
    description:
      - Specifies the amount of time that TCP connections initiated using a SNAT address are allowed
        to remain idle before being automatically disconnected. C(indefinite) Prevents the
        connection from timing out.
      - The accepted value range is C(0 - 4294967295) seconds, specifying C(indefinite) will
        set it to the maximum value.
    type: str
  traffic_group:
    description:
      - The traffic group for the snat-translation address. When creating a new address,
        if this value is not specified, the default of C(/Common/traffic-group-1)
        will be used.
    type: str
  udp_idle_timeout:
    description:
      - Specifies the amount of time that UDP connections initiated using a SNAT address are allowed
        to remain idle before being automatically disconnected. C(indefinite) Prevents the connection
        from timing out.
      - The accepted value range is C(0 - 4294967295) seconds, specifying C(indefinite) will
        set it to the maximum value.
    type: str
extends_documentation_fragment: f5
author:
  - Greg Crosby (@crosbygw)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a SNAT translation 'my-snat-translation'
  bigip_snat_translation:
    name: my-snat-pool
    state: present
    address: 10.10.10.10
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Modify a SNAT translation 'my-snat-translation'
  bigip_snat_translation:
    name: my-snat-pool
    state: present
    address: 10.10.10.10
    arp: no
    connection_limit: 300
    ip_idle_timeout: 1800
    tcp_idle_timeout: 1800
    udp_idle_timeout: 1800
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Disable a SNAT translation 'my-snat-translation'
  bigip_snat_translation:
    name: my-snat-pool
    state: disabled
    address: 10.10.10.10
    arp: no
    connection_limit: 300
    ip_idle_timeout: 1800
    tcp_idle_timeout: 1800
    udp_idle_timeout: 1800
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Enable a SNAT translation 'my-snat-translation'
  bigip_snat_translation:
    name: my-snat-pool
    state: enabled
    address: 10.10.10.10
    arp: no
    connection_limit: 300
    ip_idle_timeout: 1800
    tcp_idle_timeout: 1800
    udp_idle_timeout: 1800
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Create using partition other then /Common on a SNAT translation 'my-new-snat-translation'
  bigip_snat_translation:
    name: my-new-snat-pool
    state: enabled
    address: 10.10.10.10
    arp: no
    connection_limit: 300
    ip_idle_timeout: 1800
    partition: ansible
    tcp_idle_timeout: 1800
    udp_idle_timeout: 1800
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Modify using traffic group other then /Common/traffic-group-1 on a SNAT translation 'my-new-snat-translation'
  bigip_snat_translation:
    name: my-new-snat-pool
    state: enabled
    address: 10.10.10.10
    arp: no
    connection_limit: 300
    ip_idle_timeout: 1800
    partition: ansible
    tcp_idle_timeout: 1800
    traffic_group: /Common/ansible
    udp_idle_timeout: 1800
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

'''

RETURN = r'''
address:
  description:
    - ip address used for SNAT translation.
  returned: changed and success
  type: str
  sample: "10.10.10.10"
arp:
  description: Whether snat-translation send arp requests.
  returned: changed
  type: bool
  sample: yes
connection_limit:
  description: The new connection limit of the virtual address.
  returned: changed
  type: int
  sample: 1000
description:
  description: Description of the snat-translaiton.
  returned: changed
  type: str
  sample: My snat-translation
ip_idle_timeout:
  description: IP idle timeout value for snat-translation.
  returned: changed
  type: str
  sample: 300
state:
  description: The new state of the snat-translation.
  returned: changed
  type: str
  sample: disabled
tcp_idle_timeout:
  description: TCP idle timeout value for snat-translation.
  returned: changed
  type: str
  sample: 1800
traffic_group:
  description: Assigned traffic group.
  returned: changed
  type: str
  sample: /Common/traffic-group-1
udp_idle_timeout:
  description: UDP idle timeout value for snat-translation.
  returned: changed
  type: str
  sample: indifinite
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.ipaddress import compress_address
    from ansible.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import compress_address
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'connectionLimit': 'connection_limit',
        'ipIdleTimeout': 'ip_idle_timeout',
        'tcpIdleTimeout': 'tcp_idle_timeout',
        'trafficGroup': 'traffic_group',
        'udpIdleTimeout': 'udp_idle_timeout',
    }

    api_attributes = [
        'address',
        'arp',
        'connectionLimit',
        'description',
        'disabled',
        'enabled',
        'ipIdleTimeout',
        'tcpIdleTimeout',
        'trafficGroup',
        'udpIdleTimeout',
    ]

    returnables = [
        'address',
        'arp',
        'connection_limit',
        'description',
        'disabled',
        'enabled',
        'ip_idle_timeout',
        'state',
        'tcp_idle_timeout',
        'traffic_group',
        'udp_idle_timeout',
    ]

    updatables = [
        'arp',
        'connection_limit',
        'description',
        'disabled',
        'enabled',
        'ip_idle_timeout',
        'traffic_group',
        'tcp_idle_timeout',
        'udp_idle_timeout',
    ]


class ApiParameters(Parameters):
    @property
    def connection_limit(self):
        if self._values['connection_limit'] is None:
            return None
        return int(self._values['connection_limit'])

    @property
    def enabled(self):
        if 'enabled' in self._values:
            return True
        return False

    @property
    def disabled(self):
        if 'disabled' in self._values:
            return True
        return False


class ModuleParameters(Parameters):

    def _validate_timeout_limit(self, limit):
        if limit is None:
            return None
        if limit in ['indefinite', '4294967295']:
            return 'indefinite'
        if 0 <= int(limit) <= 4294967295:
            return str(limit)
        raise F5ModuleError(
            "Valid 'maximum_age' must be in range 0 - 4294967295, or 'indefinite'."
        )

    def _validate_conn_limit(self, limit):
        if limit is None:
            return None
        if 0 <= int(limit) <= 65535:
            return int(limit)
        raise F5ModuleError(
            "Valid 'connection_limit' must be in range 0 - 65535."
        )

    @property
    def address(self):
        if self._values['address'] is None:
            return None
        if len(self._values['address'].split('%')) > 1:
            address, rd = self._values['address'].split('%')
            if is_valid_ip(address):
                result = '{0}%{1}'.format(compress_address(address), rd)
                return result
        else:
            if is_valid_ip(self._values['address']):
                return self._values['address']
        raise F5ModuleError(
            "The provided address: {0} is not a valid IP address".format(self._values['address'])
        )

    @property
    def arp(self):
        result = flatten_boolean(self._values['arp'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def connection_limit(self):
        if self._values['connection_limit'] is None:
            return None
        return int(self._validate_conn_limit(self._values['connection_limit']))

    @property
    def description(self):
        if self._values['description'] is None:
            return None
        if self._values['description'] in ['', 'none']:
            return ''
        return self._values['description']

    @property
    def disabled(self):
        if self._values['state'] == 'disabled':
            return True

    @property
    def enabled(self):
        if self._values['state'] in ['enabled', 'present']:
            return True

    @property
    def ip_idle_timeout(self):
        return self._validate_timeout_limit(self._values['ip_idle_timeout'])

    @property
    def state(self):
        if self.enabled is True and self._values['state'] != 'present':
            return 'enabled'
        elif self.disabled is True:
            return 'disabled'
        else:
            return self._values['state']

    @property
    def tcp_idle_timeout(self):
        return self._validate_timeout_limit(self._values['tcp_idle_timeout'])

    @property
    def traffic_group(self):
        if self._values['traffic_group'] is None:
            return None
        return fq_name(self.partition, self._values['traffic_group'])

    @property
    def udp_idle_timeout(self):
        return self._validate_timeout_limit(self._values['udp_idle_timeout'])


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
    def _change_limit_value(self, value):
        if value == 4294967295:
            return 'indefinite'
        else:
            return value

    @property
    def arp(self):
        return flatten_boolean(self._values['arp'])

    @property
    def ip_idle_timeout(self):
        if self._values['ip_idle_timeout'] is None:
            return None
        return self._change_limit_value(self._values['ip_idle_timeout'])

    @property
    def tcp_idle_timeout(self):
        if self._values['tcp_idle_timeout'] is None:
            return None
        return self._change_limit_value(self._values['tcp_idle_timeout'])

    @property
    def udp_idle_timeout(self):
        if self._values['udp_idle_timeout'] is None:
            return None
        return self._change_limit_value(self._values['udp_idle_timeout'])


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
    def description(self):
        return cmp_str_with_none(self.want.description, self.have.description)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state in ['present', 'enabled', 'disabled']:
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)

        if self.module._diff and self.have:
            result['diff'] = self.make_diff()

        result.update(dict(changed=changed))
        self._announce_deprecations(result)

        return result

    def _grab_attr(self, item):
        result = dict()
        updatables = Parameters.updatables
        for k in updatables:
            if getattr(item, k) is not None:
                result[k] = getattr(item, k)
        return result

    def make_diff(self):
        result = dict(before=self._grab_attr(self.have), after=self._grab_attr(self.want))
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

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

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        if not self.exists():
            raise F5ModuleError("Failed to create the SNAT pool")
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the SNAT pool")
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/snat-translation/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/snat-translation/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/snat-translation/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/snat-translation/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/snat-translation/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
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


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            address=dict(
                aliases=['ip']
            ),
            arp=dict(
                type='bool'
            ),
            connection_limit=dict(
                type='int'
            ),
            description=dict(),
            ip_idle_timeout=dict(),
            name=dict(required=True),
            partition=dict(
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            state=dict(
                default='present',
                choices=['absent', 'present', 'enabled', 'disabled']
            ),
            tcp_idle_timeout=dict(),
            traffic_group=dict(),
            udp_idle_timeout=dict()
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['state', 'present', ['address', 'name']],
            ['state', 'enabled', ['address', 'name']],
            ['state', 'disabled', ['address', 'name']],
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
