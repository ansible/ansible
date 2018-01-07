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
module: bigip_gtm_server
short_description: Manages F5 BIG-IP GTM servers
description:
  - Manage BIG-IP server configuration. This module is able to manipulate the server
    definitions in a BIG-IP.
version_added: "2.5"
options:
  name:
    description:
      - The name of the server.
    required: True
  state:
    description:
      - The server state. If C(absent), an attempt to delete the server will be made.
        This will only succeed if this server is not in use by a virtual server.
        C(present) creates the server and enables it. If C(enabled), enable the server
        if it exists. If C(disabled), create the server if needed, and set state to
        C(disabled).
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
  datacenter:
    description:
      - Data center the server belongs to. When creating a new GTM server, this value
        is required.
  devices:
    description:
      - Lists the self IP addresses and translations for each device. When creating a
        new GTM server, this value is required. This list is a complex list that
        specifies a number of keys. There are several supported keys.
      - The C(name) key specifies a name for the device. The device name must
        be unique per server. This key is required.
      - The C(address) key contains an IP address, or list of IP addresses, for the
        destination server. This key is required.
      - The C(translation) key contains an IP address to translate the C(address)
        value above to. This key is optional.
      - Specifying duplicate C(name) fields is a supported means of providing device
        addresses. In this scenario, the addresses will be assigned to the C(name)'s list
        of addresses.
  server_type:
    description:
      - Specifies the server type. The server type determines the metrics that the
        system can collect from the server. When creating a new GTM server, the default
        value C(bigip) is used.
    choices:
      - alteon-ace-director
      - cisco-css
      - cisco-server-load-balancer
      - generic-host
      - radware-wsd
      - windows-nt-4.0
      - bigip
      - cisco-local-director-v2
      - extreme
      - generic-load-balancer
      - sun-solaris
      - cacheflow
      - cisco-local-director-v3
      - foundry-server-iron
      - netapp
      - windows-2000-server
  link_discovery:
    description:
      - Specifies whether the system auto-discovers the links for this server. When
        creating a new GTM server, if this parameter is not specified, the default
        value C(disabled) is used.
      - If you set this parameter to C(enabled) or C(enabled-no-delete), you must
        also ensure that the C(virtual_server_discovery) parameter is also set to
        C(enabled) or C(enabled-no-delete).
    choices:
      - enabled
      - disabled
      - enabled-no-delete
  virtual_server_discovery:
    description:
      - Specifies whether the system auto-discovers the virtual servers for this server.
        When creating a new GTM server, if this parameter is not specified, the default
        value C(disabled) is used.
    choices:
      - enabled
      - disabled
      - enabled-no-delete
  partition:
    description:
      - Device partition to manage resources on.
    required: False
    default: 'Common'
    version_added: 2.5
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as
    pip install f5-sdk.
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Robert Teller
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create server "GTM_Server"
  bigip_gtm_server:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: GTM_Server
    datacenter: /Common/New York
    server_type: bigip
    link_discovery: disabled
    virtual_server_discovery: disabled
    devices:
      - {'name': 'server_1', 'address': '1.1.1.1'}
      - {'name': 'server_2', 'address': '2.2.2.1', 'translation':'192.168.2.1'}
      - {'name': 'server_2', 'address': '2.2.2.2'}
      - {'name': 'server_3', 'addresses': [{'address':'3.3.3.1'},{'address':'3.3.3.2'}]}
      - {'name': 'server_4', 'addresses': [{'address':'4.4.4.1','translation':'192.168.14.1'}, {'address':'4.4.4.2'}]}
  delegate_to: localhost

- name: Create server "GTM_Server" with expanded keys
  bigip_gtm_server:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: GTM_Server
    datacenter: /Common/New York
    server_type: bigip
    link_discovery: disabled
    virtual_server_discovery: disabled
    devices:
      - name: server_1
        address: 1.1.1.1
      - name: server_2
        address: 2.2.2.1
        translation: 192.168.2.1
      - name: server_2
        address: 2.2.2.2
      - name: server_3
        addresses:
          - address: 3.3.3.1
          - address: 3.3.3.2
      - name: server_4
        addresses:
          - address: 4.4.4.1
            translation: 192.168.14.1
          - address: 4.4.4.2
  delegate_to: localhost
'''

RETURN = r'''
link_discovery:
  description: The new C(link_discovery) configured on the remote device.
  returned: changed
  type: string
  sample: enabled
virtual_server_discovery:
  description: The new C(virtual_server_discovery) name for the trap destination.
  returned: changed
  type: string
  sample: disabled
server_type:
  description: The new type of the server.
  returned: changed
  type: string
  sample: bigip
datacenter:
  description: The new C(datacenter) which the server is part of.
  returned: changed
  type: string
  sample: datacenter01
'''

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.six import iteritems
from collections import defaultdict
from distutils.version import LooseVersion

try:
    from collections import OrderedDict
except ImportError:
    try:
        from ordereddict import OrderedDict
    except ImportError:
        pass

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'product': 'server_type',
        'virtualServerDiscovery': 'virtual_server_discovery',
        'linkDiscovery': 'link_discovery',
        'addresses': 'devices'
    }

    updatables = [
        'link_discovery', 'virtual_server_discovery', 'server_type_and_devices',
        'datacenter', 'state'
    ]

    returnables = [
        'link_discovery', 'virtual_server_discovery', 'server_type', 'datacenter',
        'enabled'
    ]

    api_attributes = [
        'linkDiscovery', 'virtualServerDiscovery', 'product', 'addresses',
        'datacenter', 'enabled', 'disabled'
    ]

    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        self._values['__warnings'] = []
        if params:
            self.update(params=params)

    def update(self, params=None):
        if params:
            for k, v in iteritems(params):
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have
                        # an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if api_attribute in self.api_map:
                result[api_attribute] = getattr(
                    self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result

    def _fqdn_name(self, value):
        if value is not None and not value.startswith('/'):
            return '/{0}/{1}'.format(self.partition, value)
        return value


class ApiParameters(Parameters):
    @property
    def devices(self):
        if self._values['devices'] is None:
            return None
        return self._values['devices']

    @property
    def server_type(self):
        if self._values['server_type'] is None:
            return None
        elif self._values['server_type'] in ['single-bigip', 'redundant-bigip']:
            return 'bigip'
        else:
            return self._values['server_type']

    @property
    def raw_server_type(self):
        if self._values['server_type'] is None:
            return None
        return self._values['server_type']

    @property
    def enabled(self):
        if self._values['enabled'] is None:
            return None
        return True

    @property
    def disabled(self):
        if self._values['disabled'] is None:
            return None
        return True


class ModuleParameters(Parameters):
    @property
    def devices(self):
        if self._values['devices'] is None:
            return None
        result = []

        for device in self._values['devices']:
            if not any(x for x in ['address', 'addresses'] if x in device):
                raise F5ModuleError(
                    "The specified device list must contain an 'address' or 'addresses' key"
                )

            if 'address' in device:
                translation = self._determine_translation(device)
                name = device['address']
                device_name = device['name']
                result.append({
                    'name': name,
                    'deviceName': device_name,
                    'translation': translation
                })
            elif 'addresses' in device:
                for address in device['addresses']:
                    translation = self._determine_translation(address)
                    name = address['address']
                    device_name = device['name']
                    result.append({
                        'name': name,
                        'deviceName': device_name,
                        'translation': translation
                    })
        return result

    def devices_list(self):
        if self._values['devices'] is None:
            return None
        return self._values['devices']

    @property
    def enabled(self):
        if self._values['state'] in ['present', 'enabled']:
            return True
        return False

    @property
    def datacenter(self):
        if self._values['datacenter'] is None:
            return None
        return self._fqdn_name(self._values['datacenter'])

    def _determine_translation(self, device):
        if 'translation' not in device:
            return 'none'
        return device['translation']

    @property
    def state(self):
        if self._values['state'] == 'enabled':
            return 'present'
        return self._values['state']


class Changes(Parameters):
    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    @property
    def server_type(self):
        if self._values['server_type'] in ['single-bigip', 'redundant-bigip']:
            return 'bigip'
        return self._values['server_type']


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

    def _discovery_constraints(self):
        if self.want.virtual_server_discovery is None:
            virtual_server_discovery = self.have.virtual_server_discovery
        else:
            virtual_server_discovery = self.want.virtual_server_discovery

        if self.want.link_discovery is None:
            link_discovery = self.have.link_discovery
        else:
            link_discovery = self.want.link_discovery

        if link_discovery in ['enabled', 'enabled-no-delete'] and virtual_server_discovery == 'disabled':
            raise F5ModuleError(
                "Virtual server discovery must be enabled if link discovery is enabled"
            )

    def _devices_changed(self):
        if self.want.devices is None and self.want.server_type is None:
            return None
        if self.want.devices is None:
            devices = self.have.devices
        else:
            devices = self.want.devices
        if len(devices) == 0:
            raise F5ModuleError(
                "A GTM server must have at least one device associated with it."
            )
        want = [OrderedDict(sorted(d.items())) for d in devices]
        have = [OrderedDict(sorted(d.items())) for d in self.have.devices]
        if want != have:
            return True
        return False

    def _server_type_changed(self):
        if self.want.server_type is None:
            self.want.update({'server_type': self.have.server_type})
        if self.want.server_type != self.have.server_type:
            return True
        return False

    @property
    def link_discovery(self):
        self._discovery_constraints()
        if self.want.link_discovery != self.have.link_discovery:
            return self.want.link_discovery

    @property
    def virtual_server_discovery(self):
        self._discovery_constraints()
        if self.want.virtual_server_discovery != self.have.virtual_server_discovery:
            return self.want.virtual_server_discovery

    def _handle_current_server_type_and_devices(self, devices_change, server_change):
        result = {}
        if devices_change:
            result['devices'] = self.want.devices
        if server_change:
            result['server_type'] = self.want.server_type
        return result

    def _handle_legacy_server_type_and_devices(self, devices_change, server_change):
        result = {}
        if server_change and devices_change:
            result['devices'] = self.want.devices
            if len(self.want.devices) > 1 and self.want.server_type == 'bigip':
                if self.have.raw_server_type != 'redundant-bigip':
                    result['server_type'] = 'redundant-bigip'
            elif self.want.server_type == 'bigip':
                if self.have.raw_server_type != 'single-bigip':
                    result['server_type'] = 'single-bigip'
            else:
                result['server_type'] = self.want.server_type

        elif devices_change:
            result['devices'] = self.want.devices
            if len(self.want.devices) > 1 and self.have.server_type == 'bigip':
                if self.have.raw_server_type != 'redundant-bigip':
                    result['server_type'] = 'redundant-bigip'
            elif self.have.server_type == 'bigip':
                if self.have.raw_server_type != 'single-bigip':
                    result['server_type'] = 'single-bigip'
            else:
                result['server_type'] = self.want.server_type

        elif server_change:
            if len(self.have.devices) > 1 and self.want.server_type == 'bigip':
                if self.have.raw_server_type != 'redundant-bigip':
                    result['server_type'] = 'redundant-bigip'
            elif self.want.server_type == 'bigip':
                if self.have.raw_server_type != 'single-bigip':
                    result['server_type'] = 'single-bigip'
            else:
                result['server_type'] = self.want.server_type
        return result

    @property
    def server_type_and_devices(self):
        """Compares difference between server type and devices list

        These two parameters are linked with each other and, therefore, must be
        compared together to ensure that the correct setting is sent to BIG-IP

        :return:
        """
        devices_change = self._devices_changed()
        server_change = self._server_type_changed()
        if not devices_change and not server_change:
            return None
        tmos_version = self.client.api.tmos_version
        if LooseVersion(tmos_version) >= LooseVersion('13.0.0'):
            result = self._handle_current_server_type_and_devices(
                devices_change, server_change
            )
            return result
        else:
            result = self._handle_legacy_server_type_and_devices(
                devices_change, server_change
            )
            return result

    @property
    def state(self):
        if self.want.state == 'disabled' and self.have.enabled:
            return dict(disabled=True)
        elif self.want.state in ['present', 'enabled'] and self.have.disabled:
            return dict(enabled=True)


class ModuleManager(object):
    def __init__(self, client):
        self.client = client

    def exec_module(self):
        if not self.gtm_provisioned():
            raise F5ModuleError(
                "GTM must be provisioned to use this module."
            )
        if self.version_is_less_than('13.0.0'):
            manager = self.get_manager('v1')
        else:
            manager = self.get_manager('v2')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'v1':
            return V1Manager(self.client)
        elif type == 'v2':
            return V2Manager(self.client)

    def version_is_less_than(self, version):
        tmos_version = self.client.api.tmos_version
        if LooseVersion(tmos_version) < LooseVersion(version):
            return True
        else:
            return False

    def gtm_provisioned(self):
        resource = self.client.api.tm.sys.dbs.db.load(
            name='provisioned.cpu.gtm'
        )
        if int(resource.value) == 0:
            return False
        return True


class BaseManager(object):
    def __init__(self, client):
        self.client = client
        self.want = ModuleParameters(params=self.client.module.params)
        self.want.update(dict(client=client))
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        diff.client = self.client
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
            self.changes = UsableChanges(changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ['present', 'enabled', 'disabled']:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        reportable = ReportableChanges(self.changes.to_return())
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

    def _check_link_discovery_requirements(self):
        if self.want.link_discovery in ['enabled', 'enabled-no-delete'] and self.want.virtual_server_discovery == 'disabled':
            raise F5ModuleError(
                "Virtual server discovery must be enabled if link discovery is enabled"
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        if self.want.state == 'disabled':
            self.want.update({'disabled': True})
        elif self.want.state in ['present', 'enabled']:
            self.want.update({'enabled': True})
        self._set_changed_options()

        if self.want.devices is None:
            raise F5ModuleError(
                "You must provide an initial device."
            )
        self._assign_creation_defaults()

        if self.client.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the server")

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.gtm.servers.server.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def read_current_from_device(self):
        resource = self.client.api.tm.gtm.servers.server.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(result)

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.gtm.servers.server.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the server")
        return True

    def remove_from_device(self):
        resource = self.client.api.tm.gtm.servers.server.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.delete()

    def exists(self):
        result = self.client.api.tm.gtm.servers.server.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result


class V1Manager(BaseManager):
    def _assign_creation_defaults(self):
        if self.want.server_type is None:
            if len(self.want.devices) == 0:
                raise F5ModuleError(
                    "You must provide at least one device."
                )
            elif len(self.want.devices) == 1:
                self.want.update({'server_type': 'single-bigip'})
            else:
                self.want.update({'server_type': 'redundant-bigip'})
        else:
            if len(self.want.devices) == 1:
                self.want.update({'server_type': 'single-bigip'})
            else:
                self.want.update({'server_type': 'redundant-bigip'})
        if self.want.link_discovery is None:
            self.want.update({'link_discovery': 'disabled'})
        if self.want.virtual_server_discovery is None:
            self.want.update({'virtual_server_discovery': 'disabled'})
        self._check_link_discovery_requirements()


class V2Manager(BaseManager):
    def _assign_creation_defaults(self):
        if self.want.server_type is None:
            self.want.update({'server_type': 'bigip'})
        if self.want.link_discovery is None:
            self.want.update({'link_discovery': 'disabled'})
        if self.want.virtual_server_discovery is None:
            self.want.update({'virtual_server_discovery': 'disabled'})
        self._check_link_discovery_requirements()


class ArgumentSpec(object):
    def __init__(self):
        self.states = ['absent', 'present', 'enabled', 'disabled']
        self.server_types = [
            'alteon-ace-director', 'cisco-css', 'cisco-server-load-balancer',
            'generic-host', 'radware-wsd', 'windows-nt-4.0', 'bigip',
            'cisco-local-director-v2', 'extreme', 'generic-load-balancer',
            'sun-solaris', 'cacheflow', 'cisco-local-director-v3',
            'foundry-server-iron', 'netapp', 'standalone-bigip',
            'redundant-bigip', 'windows-2000-server'
        ]
        self.supports_check_mode = True
        self.argument_spec = dict(
            state=dict(
                default='present',
                choices=self.states,
            ),
            name=dict(required=True),
            server_type=dict(
                choices=self.server_types,
                aliases=['product']
            ),
            datacenter=dict(),
            link_discovery=dict(
                choices=['enabled', 'disabled', 'enabled-no-delete']
            ),
            virtual_server_discovery=dict(
                choices=['enabled', 'disabled', 'enabled-no-delete']
            ),
            devices=dict(
                type='list'
            )
        )
        self.f5_product_name = 'bigip'


def cleanup_tokens(client):
    try:
        resource = client.api.shared.authz.tokens_s.token.load(
            name=client.api.icrs.token
        )
        resource.delete()
    except Exception:
        pass


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
