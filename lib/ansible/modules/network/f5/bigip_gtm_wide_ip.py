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
---
module: bigip_gtm_wide_ip
short_description: Manages F5 BIG-IP GTM wide ip
description:
  - Manages F5 BIG-IP GTM wide ip.
version_added: 2.0
options:
  pool_lb_method:
    description:
      - Specifies the load balancing method used to select a pool in this wide
        IP. This setting is relevant only when multiple pools are configured
        for a wide IP.
      - The C(round_robin) value is deprecated and will be removed in Ansible 2.9.
      - The C(global_availability) value is deprecated and will be removed in Ansible 2.9.
    required: True
    aliases: ['lb_method']
    choices:
      - round-robin
      - ratio
      - topology
      - global-availability
      - global_availability
      - round_robin
    version_added: 2.5
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
        is enabled.
      - When C(absent), ensures that the Wide IP has been removed.
      - When C(disabled), ensures that the Wide IP exists and is disabled.
    default: present
    choices:
      - present
      - absent
      - disabled
      - enabled
    version_added: 2.4
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
  pools:
    description:
      - The pools that you want associated with the Wide IP.
      - If C(ratio) is not provided when creating a new Wide IP, it will default
        to 1.
    suboptions:
      name:
        description:
          - The name of the pool to include.
        required: True
      ratio:
        description:
          - Ratio for the pool.
          - The system uses this number with the Ratio load balancing method.
    version_added: 2.5
  irules:
    version_added: 2.6
    description:
      - List of rules to be applied.
      - If you want to remove all existing iRules, specify a single empty value; C("").
        See the documentation for an example.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Set lb method
  bigip_gtm_wide_ip:
    server: lb.mydomain.com
    user: admin
    password: secret
    pool_lb_method: round-robin
    name: my-wide-ip.example.com
  delegate_to: localhost

- name: Add iRules to the Wide IP
  bigip_gtm_wide_ip:
    server: lb.mydomain.com
    user: admin
    password: secret
    pool_lb_method: round-robin
    name: my-wide-ip.example.com
    irules:
      - irule1
      - irule2
  delegate_to: localhost

- name: Remove one iRule from the Virtual Server
  bigip_gtm_wide_ip:
    server: lb.mydomain.com
    user: admin
    password: secret
    pool_lb_method: round-robin
    name: my-wide-ip.example.com
    irules:
      - irule1
  delegate_to: localhost

- name: Remove all iRules from the Virtual Server
  bigip_gtm_wide_ip:
    server: lb.mydomain.com
    user: admin
    password: secret
    pool_lb_method: round-robin
    name: my-wide-ip.example.com
    irules: ""
  delegate_to: localhost

- name: Assign a pool with ratio to the Wide IP
  bigip_gtm_wide_ip:
    server: lb.mydomain.com
    user: admin
    password: secret
    pool_lb_method: round-robin
    name: my-wide-ip.example.com
    pools:
      - name: pool1
        ratio: 100
  delegate_to: localhost
'''

RETURN = r'''
lb_method:
  description: The new load balancing method used by the wide IP.
  returned: changed
  type: string
  sample: topology
state:
  description: The new state of the wide IP.
  returned: changed
  type: string
  sample: disabled
irules:
  description: iRules set on the Wide IP.
  returned: changed
  type: list
  sample: ['/Common/irule1', '/Common/irule2']
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import is_valid_fqdn
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
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import is_valid_fqdn
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'poolLbMode': 'pool_lb_method',
        'rules': 'irules',
    }

    updatables = [
        'pool_lb_method', 'state', 'pools', 'irules', 'enabled', 'disabled'
    ]

    returnables = [
        'name', 'pool_lb_method', 'state', 'pools', 'irules'
    ]

    api_attributes = [
        'poolLbMode', 'enabled', 'disabled', 'pools', 'rules'
    ]


class ApiParameters(Parameters):
    @property
    def disabled(self):
        if self._values['disabled'] is True:
            return True
        return False

    @property
    def enabled(self):
        if self._values['enabled'] is True:
            return True
        return False

    @property
    def pools(self):
        result = []
        if self._values['pools'] is None:
            return None
        pools = sorted(self._values['pools'], key=lambda x: x['order'])
        for item in pools:
            pool = dict()
            pool.update(item)
            name = '/{0}/{1}'.format(item['partition'], item['name'])
            del pool['nameReference']
            del pool['order']
            del pool['name']
            del pool['partition']
            pool['name'] = name
            result.append(pool)
        return result


class ModuleParameters(Parameters):
    @property
    def pool_lb_method(self):
        if self._values['pool_lb_method'] is None:
            return None
        lb_method = str(self._values['pool_lb_method'])
        if lb_method == 'global_availability':
            if self._values['__warnings'] is None:
                self._values['__warnings'] = []
            self._values['__warnings'].append(
                dict(
                    msg='The provided pool_lb_method is deprecated',
                    version='2.4'
                )
            )
            lb_method = 'global-availability'
        elif lb_method == 'round_robin':
            if self._values['__warnings'] is None:
                self._values['__warnings'] = []
            self._values['__warnings'].append(
                dict(
                    msg='The provided pool_lb_method is deprecated',
                    version='2.4'
                )
            )
            lb_method = 'round-robin'
        return lb_method

    @property
    def type(self):
        if self._values['type'] is None:
            return None
        return str(self._values['type'])

    @property
    def name(self):
        if self._values['name'] is None:
            return None
        if not is_valid_fqdn(self._values['name']):
            raise F5ModuleError(
                "The provided name must be a valid FQDN"
            )
        return self._values['name']

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
        else:
            return None

    @property
    def disabled(self):
        if self._values['state'] == 'disabled':
            return True
        elif self._values['state'] in ['present', 'enabled']:
            return False
        else:
            return None

    @property
    def pools(self):
        result = []
        if self._values['pools'] is None:
            return None
        for item in self._values['pools']:
            pool = dict()
            if 'name' not in item:
                raise F5ModuleError(
                    "'name' is a required key for items in the list of pools."
                )
            if 'ratio' in item:
                pool['ratio'] = item['ratio']
            pool['name'] = fq_name(self.partition, item['name'])
            result.append(pool)
        return result

    @property
    def irules(self):
        results = []
        if self._values['irules'] is None:
            return None
        if len(self._values['irules']) == 1 and self._values['irules'][0] == '':
            return ''
        for irule in self._values['irules']:
            result = fq_name(self.partition, irule)
            results.append(result)
        return results


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


class UsableChanges(Changes):
    @property
    def irules(self):
        if self._values['irules'] is None:
            return None
        if self._values['irules'] == '':
            return []
        return self._values['irules']


class ReportableChanges(Changes):
    @property
    def pool_lb_method(self):
        result = dict(
            lb_method=self._values['pool_lb_method'],
            pool_lb_method=self._values['pool_lb_method'],
        )
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

    def to_tuple(self, items):
        result = []
        for x in items:
            tmp = [(str(k), str(v)) for k, v in iteritems(x)]
            result += tmp
        return result

    def _diff_complex_items(self, want, have):
        if want == [] and have is None:
            return None
        if want is None:
            return None
        w = self.to_tuple(want)
        h = self.to_tuple(have)
        if set(w).issubset(set(h)):
            return None
        else:
            return want

    @property
    def state(self):
        if self.want.state == 'disabled' and self.have.enabled:
            return self.want.state
        elif self.want.state in ['present', 'enabled'] and self.have.disabled:
            return self.want.state

    @property
    def pools(self):
        result = self._diff_complex_items(self.want.pools, self.have.pools)
        return result

    @property
    def irules(self):
        if self.want.irules is None:
            return None
        if self.want.irules == '' and self.have.irules is None:
            return None
        if self.want.irules == '' and len(self.have.irules) > 0:
            return []
        if sorted(set(self.want.irules)) != sorted(set(self.have.irules)):
            return self.want.irules


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

    def exec_module(self):
        if self.version_is_less_than_12():
            manager = self.get_manager('untyped')
        else:
            manager = self.get_manager('typed')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'typed':
            return TypedManager(**self.kwargs)
        elif type == 'untyped':
            return UntypedManager(**self.kwargs)

    def version_is_less_than_12(self):
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.0.0'):
            return True
        else:
            return False


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
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
            return self.update()
        else:
            return self.create()

    def create(self):
        if self.want.pool_lb_method is None:
            raise F5ModuleError(
                "The 'pool_lb_method' option is required when state is 'present'"
            )
        self._set_changed_options()
        if self.module.check_mode:
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
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.module.check_mode:
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
        params = self.changes.api_params()
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
        return ApiParameters(params=result)

    def create_on_device(self):
        params = self.changes.api_params()
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
    def __init__(self, *args, **kwargs):
        super(TypedManager, self).__init__(**kwargs)
        if self.want.type is None:
            raise F5ModuleError(
                "The 'type' option is required for BIG-IP instances "
                "greater than or equal to 12.x"
            )
        type_map = dict(
            a='a_s',
            aaaa='aaaas',
            cname='cnames',
            mx='mxs',
            naptr='naptrs',
            srv='srvs'
        )
        self.collection = type_map[self.want.type]

    def exists(self):
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.collection)
        resource = getattr(collection, self.want.type)
        result = resource.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_on_device(self):
        params = self.changes.api_params()
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def read_current_from_device(self):
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = result.attrs
        return ApiParameters(params=result)

    def create_on_device(self):
        params = self.changes.api_params()
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.collection)
        resource = getattr(collection, self.want.type)
        resource.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove_from_device(self):
        wideips = self.client.api.tm.gtm.wideips
        collection = getattr(wideips, self.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if result:
            result.delete()


class ArgumentSpec(object):
    def __init__(self):
        lb_method_choices = [
            'round-robin', 'topology', 'ratio', 'global-availability',

            # TODO(Remove in Ansible 2.9)
            'round_robin', 'global_availability'
        ]
        self.supports_check_mode = True
        argument_spec = dict(
            pool_lb_method=dict(
                choices=lb_method_choices,
                aliases=['lb_method']
            ),
            name=dict(
                required=True,
                aliases=['wide_ip']
            ),
            type=dict(
                choices=[
                    'a', 'aaaa', 'cname', 'mx', 'naptr', 'srv'
                ]
            ),
            state=dict(
                default='present',
                choices=['absent', 'present', 'enabled', 'disabled']
            ),
            pools=dict(
                type='list',
                options=dict(
                    name=dict(required=True),
                    ratio=dict(type='int')
                )
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            irules=dict(
                type='list',
            ),
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
    except F5ModuleError as e:
        cleanup_tokens(client)
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
