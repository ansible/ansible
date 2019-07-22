#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_tunnel
short_description: Manage tunnels on a BIG-IP
description:
  - Manages tunnels on a BIG-IP. Tunnels are usually based upon a tunnel profile which
    defines both default arguments and constraints for the tunnel.
  - Due to this, this module exposes a number of settings that may or may not be related
    to the type of tunnel you are working with. It is important that you take this into
    consideration when declaring your tunnel config.
  - If a specific tunnel does not support the parameter you are considering, the documentation
    of the parameter will usually make mention of this. Otherwise, when configuring that
    parameter on the device, the device will notify you.
version_added: 2.7
options:
  name:
    description:
      - Specifies the name of the tunnel.
    type: str
    required: True
  description:
    description:
      - Description of the tunnel.
    type: str
  profile:
    description:
      - Specifies the profile to associate with the tunnel for handling traffic.
      - Depending on your selection, other settings become available or disappear.
      - This parameter may not be changed after it is set.
    type: str
  key:
    description:
      - When applied to a GRE tunnel, this value specifies an optional field in the GRE header,
        used to authenticate the source of the packet.
      - When applied to a VXLAN or Geneve tunnel, this value specifies the Virtual Network
        Identifier (VNI).
      - When applied to an NVGRE tunnel, this value specifies the Virtual Subnet Identifier (VSID).
      - When creating a new tunnel, if this parameter is supported by the tunnel profile but not
        specified, the default value is C(0).
    type: int
  local_address:
    description:
      - Specifies the IP address of the local endpoint of the tunnel.
    type: str
  remote_address:
    description:
      - Specifies the IP address of the remote endpoint of the tunnel.
      - For C(dslite), C(fec) (when configuring the FEC tunnel for receiving traffic only),
        C(v6rd) (configured as a border relay), or C(map), the tunnel must have an unspecified
        remote address (any).
    type: str
  secondary_address:
    description:
      - Specifies a non-floating IP address for the tunnel, to be used with host-initiated traffic.
    type: str
  mtu:
    description:
      - Specifies the maximum transmission unit (MTU) of the tunnel.
      - When creating a new tunnel, if this parameter is supported by the tunnel profile but not
        specified, the default value is C(0).
      - The valid range is from C(0) to C(65515).
    type: int
  use_pmtu:
    description:
      - Enables or disables the tunnel to use the PMTU (Path MTU) information provided by ICMP
        NeedFrag error messages.
      - If C(yes) and the tunnel C(mtu) is set to C(0), the tunnel will use the PMTU information.
      - If C(yes) and the tunnel C(mtu) is fixed to a non-zero value, the tunnel will use the
        minimum of PMTU and MTU.
      - If C(no), the tunnel will use fixed MTU or calculate its MTU using tunnel encapsulation
        configurations.
    type: bool
  tos:
    description:
      - Specifies the Type of Service (TOS) value to insert in the encapsulating header of
        transmitted packets.
      - When creating a new tunnel, if this parameter is supported by the tunnel profile but not
        specified, the default value is C(preserve).
      - When C(preserve), the system copies the TOS value from the inner header to the outer header.
      - You may also specify a numeric value. The possible values are from C(0) to C(255).
    type: str
  auto_last_hop:
    description:
      - Allows you to configure auto last hop on a per-tunnel basis.
      - When creating a new tunnel, if this parameter is supported by the tunnel profile but not
        specified, the default is C(default).
      - When C(default), means that the system uses the global auto-lasthop setting to send back
        the request.
      - When C(enabled), allows the system to send return traffic to the MAC address that transmitted
        the request, even if the routing table points to a different network or interface. As a
        result, the system can send return traffic to clients even when there is no matching route.
    type: str
    choices:
      - default
      - enabled
      - disabled
  traffic_group:
    description:
      - Specifies the traffic group to associate with the tunnel.
      - This value cannot be changed after it is set. This is a limitation of BIG-IP.
    type: str
  mode:
    description:
      - Specifies how the tunnel carries traffic.
      - When creating a new tunnel, if this parameter is supported by the tunnel profile but not
        specified, the default is C(bidirectional).
      - When C(bidirectional), specifies that the tunnel carries both inbound and outbound traffic.
      - When C(inbound), specifies that the tunnel carries only incoming traffic.
      - When C(outbound), specifies that the tunnel carries only outgoing traffic.
    type: str
    choices:
      - bidirectional
      - inbound
      - outbound
  transparent:
    description:
      - Specifies that the tunnel operates in transparent mode.
      - When C(yes), you can inspect and manipulate the encapsulated traffic flowing through the BIG-IP
        system.
      - A transparent tunnel terminates a tunnel while presenting the illusion that the tunnel transits
        the device unmodified (that is, the BIG-IP system appears as if it were an intermediate router
        that simply routes IP traffic through the device).
    type: bool
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the tunnel exists.
      - When C(absent), ensures the tunnel is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a VXLAN tunnel
  bigip_tunnel:
    name: openshift-tunnel
    local_address: 192.1681.240
    key: 0
    secondary_address: 192.168.1.100
    mtu: 0
    use_pmtu: yes
    tos: preserve
    auto_last_hop: default
    traffic_group: traffic-group-1
    state: present
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
param1:
  description: The new param1 value of the resource.
  returned: changed
  type: bool
  sample: true
param2:
  description: The new param2 value of the resource.
  returned: changed
  type: str
  sample: Foo is bar
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import transform_name
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import transform_name


class Parameters(AnsibleF5Parameters):
    api_map = {
        'autoLasthop': 'auto_last_hop',
        'localAddress': 'local_address',
        'remoteAddress': 'remote_address',
        'secondaryAddress': 'secondary_address',
        'usePmtu': 'use_pmtu',
        'trafficGroup': 'traffic_group',
    }

    api_attributes = [
        'autoLasthop',
        'description',
        'key',
        'mtu',
        'profile',
        'transparent',
        'usePmtu',
        'tos',
        'secondaryAddress',
        'remoteAddress',
        'mode',
        'localAddress',
        'trafficGroup',
    ]

    returnables = [
        'auto_last_hop',
        'local_address',
        'mode',
        'remote_address',
        'secondary_address',
        'description',
        'key',
        'mtu',
        'profile',
        'transparent',
        'use_pmtu',
        'tos',
        'traffic_group',
    ]

    updatables = [
        'auto_last_hop',
        'local_address',
        'mode',
        'remote_address',
        'profile',
        'secondary_address',
        'description',
        'key',
        'mtu',
        'transparent',
        'use_pmtu',
        'tos',
        'traffic_group',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def transparent(self):
        result = flatten_boolean(self._values['transparent'])
        if result == 'yes':
            return 'enabled'
        elif result == 'no':
            return 'disabled'

    @property
    def use_pmtu(self):
        result = flatten_boolean(self._values['use_pmtu'])
        if result == 'yes':
            return 'enabled'
        elif result == 'no':
            return 'disabled'

    @property
    def profile(self):
        if self._values['profile'] is None:
            return None
        return fq_name(self.partition, self._values['profile'])

    @property
    def traffic_group(self):
        if self._values['traffic_group'] is None:
            return None
        elif self._values['traffic_group'] in ['', 'none']:
            return ''
        return fq_name(self.partition, self._values['traffic_group'])


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
    @property
    def transparent(self):
        result = flatten_boolean(self._values['transparent'])
        return result

    @property
    def use_pmtu(self):
        result = flatten_boolean(self._values['use_pmtu'])
        return result


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
    def profile(self):
        if self.want.profile is None:
            return None
        if self.want.profile != self.have.profile:
            raise F5ModuleError(
                "'profile' cannot be changed after it is set."
            )

    @property
    def traffic_group(self):
        if self.want.traffic_group is None:
            return None
        if self.want.traffic_group in ['', None] and self.have.traffic_group is None:
            return None
        if self.want.traffic_group != self.have.traffic_group:
            raise F5ModuleError(
                "'traffic_group' cannot be changed after it is set."
            )


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
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
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/net/tunnels/tunnel/{2}".format(
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

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/net/tunnels/tunnel/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response['selfLink']

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/net/tunnels/tunnel/{2}".format(
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

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/tunnels/tunnel/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/tunnels/tunnel/{2}".format(
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
            name=dict(required='true'),
            profile=dict(),
            description=dict(),
            key=dict(type='int'),
            local_address=dict(),
            remote_address=dict(),
            secondary_address=dict(),
            mtu=dict(type='int'),
            use_pmtu=dict(type='bool'),
            tos=dict(),
            auto_last_hop=dict(
                choices=['default', 'enabled', 'disabled']
            ),
            traffic_group=dict(),
            mode=dict(
                choices=['bidirectional', 'inbound', 'outbound']
            ),
            transparent=dict(type='bool'),
            state=dict(
                default='present',
                choices=['present', 'absent']
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
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
