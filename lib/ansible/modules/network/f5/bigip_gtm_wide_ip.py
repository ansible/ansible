#!/usr/bin/python
# -*- coding: utf-8 -*-
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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
---
module: bigip_gtm_wide_ip
short_description: Manages F5 BIG-IP GTM wide ip.
description:
  - Manages F5 BIG-IP GTM wide ip.
version_added: "2.0"
options:
  lb_method:
    description:
      - Specifies the load balancing method used to select a pool in this wide
        IP. This setting is relevant only when multiple pools are configured
        for a wide IP.
    required: True
    choices:
      - round-robin
      - ratio
      - topology
      - global-availability
  name:
    description:
      - Wide IP name. This name must be formatted as a fully qualified
        domain name (FQDN). You can also use the alias C(wide_ip) but this
        is deprecated and will be removed in a future Ansible version.
    required: True
    aliases:
      - wide_ip
  type:
    description:
      - Specifies the type of wide IP. GTM wide IPs need to be keyed by query
        type in addition to name, since pool members need different attributes
        depending on the response RDATA they are meant to supply. This value
        is required if you are using BIG-IP versions >= 12.0.0.
    choices:
      - a
      - aaaa
      - cname
      - mx
      - naptr
      - srv
    version_added: 2.4
  state:
    description:
      - When C(present) or C(enabled), ensures that the Wide IP exists and
        is enabled. When C(absent), ensures that the Wide IP has been
        removed. When C(disabled), ensures that the Wide IP exists and is
        disabled.
    default: present
    choices:
      - present
      - absent
      - disabled
      - enabled
    version_added: 2.4
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Set lb method
  bigip_gtm_wide_ip:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      lb_method: "round-robin"
      name: "my-wide-ip.example.com"
  delegate_to: localhost
'''

RETURN = '''
lb_method:
    description: The new load balancing method used by the wide IP.
    returned: changed
    type: string
    sample: "topology"
state:
    description: The new state of the wide IP.
    returned: changed
    type: string
    sample: "disabled"
'''

import re

from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iControlUnexpectedHTTPError
)
from distutils.version import LooseVersion


class Parameters(AnsibleF5Parameters):
    updatables = ['lb_method']
    returnables = ['name', 'lb_method', 'state']
    api_attributes = ['poolLbMode', 'enabled', 'disabled']

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

    @property
    def lb_method(self):
        deprecated = [
            'return_to_dns', 'null', 'static_persist', 'vs_capacity',
            'least_conn', 'lowest_rtt', 'lowest_hops', 'packet_rate', 'cpu',
            'hit_ratio', 'qos', 'bps', 'drop_packet', 'explicit_ip',
            'connection_rate', 'vs_score'
        ]
        if self._values['lb_method'] is None:
            return None
        lb_method = str(self._values['lb_method'])
        if lb_method in deprecated:
            raise F5ModuleError(
                "The provided lb_method is not supported"
            )
        elif lb_method == 'global_availability':
            if self._values['__warnings'] is None:
                self._values['__warnings'] = []
            self._values['__warnings'].append(
                dict(
                    msg='The provided lb_method is deprecated',
                    version='2.4'
                )
            )
            lb_method = 'global-availability'
        elif lb_method == 'round_robin':
            if self._values['__warnings'] is None:
                self._values['__warnings'] = []
            self._values['__warnings'].append(
                dict(
                    msg='The provided lb_method is deprecated',
                    version='2.4'
                )
            )
            lb_method = 'round-robin'
        return lb_method

    @lb_method.setter
    def lb_method(self, value):
        self._values['lb_method'] = value

    @property
    def collection(self):
        type_map = dict(
            a='a_s',
            aaaa='aaaas',
            cname='cnames',
            mx='mxs',
            naptr='naptrs',
            srv='srvs'
        )
        if self._values['type'] is None:
            return None
        wideip_type = self._values['type']
        return type_map[wideip_type]

    @property
    def type(self):
        if self._values['type'] is None:
            return None
        return str(self._values['type'])

    @property
    def name(self):
        if self._values['name'] is None:
            return None
        if not re.search(r'.*\..*\..*', self._values['name']):
            raise F5ModuleError(
                "The provided name must be a valid FQDN"
            )
        return self._values['name']

    @property
    def poolLbMode(self):
        return self.lb_method

    @poolLbMode.setter
    def poolLbMode(self, value):
        self.lb_method = value

    @property
    def state(self):
        if self._values['state'] == 'enabled':
            return 'present'
        return self._values['state']

    @property
    def enabled(self):
        if self._values['state'] == 'disabled':
            return False
        elif self._values['state'] in ['present', 'enabled']:
            return True
        elif self._values['enabled'] is True:
            return True
        else:
            return None

    @property
    def disabled(self):
        if self._values['state'] == 'disabled':
            return True
        elif self._values['state'] in ['present', 'enabled']:
            return False
        elif self._values['disabled'] is True:
            return True
        else:
            return None


class ModuleManager(object):
    def __init__(self, client):
        self.client = client

    def exec_module(self):
        if self.version_is_less_than_12():
            manager = self.get_manager('untyped')
        else:
            manager = self.get_manager('typed')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'typed':
            return TypedManager(self.client)
        elif type == 'untyped':
            return UntypedManager(self.client)

    def version_is_less_than_12(self):
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.0.0'):
            return True
        else:
            return False


class BaseManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Parameters(changed)

    def _update_changed_options(self):
        changed = {}
        for key in Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1

        if self.want.state == 'disabled' and self.have.enabled:
            changed['state'] = self.want.state
        elif self.want.state in ['present', 'enabled'] and self.have.disabled:
            changed['state'] = self.want.state

        if changed:
            self.changes = Parameters(changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ["present", "disabled"]:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations()
        return result

    def _announce_deprecations(self):
        warnings = []
        if self.want:
            warnings += self.want._values.get('__warnings', [])
        if self.have:
            warnings += self.have._values.get('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.want.lb_method is None:
            raise F5ModuleError(
                "The 'lb_method' option is required when state is 'present'"
            )
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        self._set_changed_options()
        if self.client.check_mode:
            return True
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

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the Wide IP")
        return True


class UntypedManager(BaseManager):
    def exists(self):
        return self.client.api.tm.gtm.wideips.wideip.exists(
            name=self.want.name,
            partition=self.want.partition
        )

    def update_on_device(self):
        params = self.want.api_params()
        result = self.client.api.tm.gtm.wideips.wipeip.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def read_current_from_device(self):
        resource = self.client.api.tm.gtm.wideips.wideip.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return Parameters(result)

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.gtm.wideips.wideip.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove_from_device(self):
        result = self.client.api.tm.gtm.wideips.wideip.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if result:
            result.delete()


class TypedManager(BaseManager):
    def __init__(self, client):
        super(TypedManager, self).__init__(client)
        if self.want.type is None:
            raise F5ModuleError(
                "The 'type' option is required for BIG-IP instances "
                "greater than or equal to 12.x"
            )

    def exists(self):
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_on_device(self):
        params = self.want.api_params()
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def read_current_from_device(self):
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = result.attrs
        return Parameters(result)

    def create_on_device(self):
        params = self.want.api_params()
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove_from_device(self):
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if result:
            result.delete()


class ArgumentSpec(object):
    def __init__(self):
        deprecated = [
            'return_to_dns', 'null', 'round_robin', 'static_persist',
            'global_availability', 'vs_capacity', 'least_conn', 'lowest_rtt',
            'lowest_hops', 'packet_rate', 'cpu', 'hit_ratio', 'qos', 'bps',
            'drop_packet', 'explicit_ip', 'connection_rate', 'vs_score'
        ]
        supported = [
            'round-robin', 'topology', 'ratio', 'global-availability'
        ]
        lb_method_choices = deprecated + supported
        self.supports_check_mode = True
        self.argument_spec = dict(
            lb_method=dict(
                required=False,
                choices=lb_method_choices,
                default=None
            ),
            name=dict(
                required=True,
                aliases=['wide_ip']
            ),
            type=dict(
                required=False,
                default=None,
                choices=[
                    'a', 'aaaa', 'cname', 'mx', 'naptr', 'srv'
                ]
            ),
            state=dict(
                required=False,
                default='present',
                choices=['absent', 'present', 'enabled', 'disabled']
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

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
