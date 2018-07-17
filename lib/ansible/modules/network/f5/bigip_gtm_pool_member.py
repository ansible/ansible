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
module: bigip_gtm_pool_member
short_description: Manage GTM pool member settings
description:
  - Manages a variety of settings on GTM pool members. The settings that can be
    adjusted with this module are much more broad that what can be done in the
    C(bigip_gtm_pool) module. The pool module is intended to allow you to adjust
    the member order in the pool, not the various settings of the members. The
    C(bigip_gtm_pool_member) module should be used to adjust all of the other
    settings.
version_added: 2.6
options:
  virtual_server:
    description:
      - Specifies the name of the GTM virtual server which is assigned to the specified
        C(server).
    required: True
  server_name:
    description:
      - Specifies the GTM server which contains the C(virtual_server).
    required: True
  type:
    description:
      - The type of GTM pool that the member is in.
    choices:
      - a
      - aaaa
      - cname
      - mx
      - naptr
      - srv
    required: True
  pool:
    description:
      - Name of the GTM pool.
    required: True
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
  member_order:
    description:
      - Specifies the order in which the member will appear in the pool.
      - The system uses this number with load balancing methods that involve prioritizing
        pool members, such as the Ratio load balancing method.
      - When creating a new member using this module, if the C(member_order) parameter
        is not specified, it will default to C(0) (first member in the pool).
  monitor:
    description:
      - Specifies the monitor assigned to this pool member.
      - Pool members only support a single monitor.
      - If the C(port) of the C(gtm_virtual_server) is C(*), the accepted values of this
        parameter will be affected.
      - When creating a new pool member, if this parameter is not specified, the default
        of C(default) will be used.
      - To remove the monitor from the pool member, use the value C(none).
      - For pool members created on different partitions, you can also specify the full
        path to the Common monitor. For example, C(/Common/tcp).
  ratio:
    description:
      - Specifies the weight of the pool member for load balancing purposes.
  description:
    description:
      - The description of the pool member.
  limits:
    description:
      - Specifies resource thresholds or limit requirements at the pool member level.
      - When you enable one or more limit settings, the system then uses that data to take
        members in and out of service.
      - You can define limits for any or all of the limit settings. However, when a
        member does not meet the resource threshold limit requirement, the system marks
        the member as unavailable and directs load-balancing traffic to another resource.
    suboptions:
      bits_enabled:
        description:
          - Whether the bits limit it enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      packets_enabled:
        description:
          - Whether the packets limit it enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      connections_enabled:
        description:
          - Whether the current connections limit it enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      bits_limit:
        description:
          - Specifies the maximum allowable data throughput rate, in bits per second,
            for the member.
          - If the network traffic volume exceeds this limit, the system marks the
            member as unavailable.
      packets_limit:
        description:
          - Specifies the maximum allowable data transfer rate, in packets per second,
            for the member.
          - If the network traffic volume exceeds this limit, the system marks the
            member as unavailable.
      connections_limit:
        description:
          - Specifies the maximum number of concurrent connections, combined, for all of
            the member.
          - If the connections exceed this limit, the system marks the server as
            unavailable.
  state:
    description:
      - Pool member state. When C(present), ensures that the pool member is
        created and enabled. When C(absent), ensures that the pool member is
        removed from the system. When C(enabled) or C(disabled), ensures
        that the pool member is enabled or disabled (respectively) on the remote
        device.
      - It is recommended that you use the C(members) parameter of the C(bigip_gtm_pool)
        module when adding and removing members and it provides an easier way of
        specifying order. If this is not possible, then the C(state) parameter here
        should be used.
      - Remember that the order of the members will be affected if you add or remove them
        using this method. To some extent, this can be controlled using the C(member_order)
        parameter.
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a ...
  bigip_gtm_pool_member:
    name: foo
    password: secret
    server: lb.mydomain.com
    state: present
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
  type: string
  sample: Foo is bar
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
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
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'limitMaxBps': 'bits_limit',
        'limitMaxBpsStatus': 'bits_enabled',
        'limitMaxConnections': 'connections_limit',
        'limitMaxConnectionsStatus': 'connections_enabled',
        'limitMaxPps': 'packets_limit',
        'limitMaxPpsStatus': 'packets_enabled',
        'memberOrder': 'member_order'
    }

    api_attributes = [
        'disabled',
        'enabled',
        'limitMaxBps',
        'limitMaxBpsStatus',
        'limitMaxConnections',
        'limitMaxConnectionsStatus',
        'limitMaxPps',
        'limitMaxPpsStatus',
        'memberOrder',
        'monitor',
        'ratio',
        'description',
    ]

    returnables = [
        'bits_enabled',
        'bits_limit',
        'connections_enabled',
        'connections_limit',
        'disabled',
        'enabled',
        'member_order',
        'monitor',
        'packets_enabled',
        'packets_limit',
        'ratio',
        'description',
    ]

    updatables = [
        'bits_enabled',
        'bits_limit',
        'connections_enabled',
        'connections_limit',
        'enabled',
        'member_order',
        'monitor',
        'packets_limit',
        'packets_enabled',
        'ratio',
        'description',
    ]

    @property
    def ratio(self):
        if self._values['ratio'] is None:
            return None
        return int(self._values['ratio'])


class ApiParameters(Parameters):
    @property
    def enabled(self):
        if 'enabled' in self._values:
            return True
        else:
            return False

    @property
    def disabled(self):
        if 'disabled' in self._values:
            return True
        return False

    @property
    def monitor(self):
        if self._values['monitor'] is None:
            return None
        # The value of this parameter in the API includes an extra space
        return self._values['monitor'].strip()


class ModuleParameters(Parameters):
    def _get_limit_value(self, type):
        if self._values['limits'] is None:
            return None
        if self._values['limits'][type] is None:
            return None
        return int(self._values['limits'][type])

    def _get_limit_status(self, type):
        if self._values['limits'] is None:
            return None
        if self._values['limits'][type] is None:
            return None
        if self._values['limits'][type]:
            return 'enabled'
        return 'disabled'

    @property
    def name(self):
        result = '{0}:{1}'.format(self.server_name, self.virtual_server)
        return result

    @property
    def type(self):
        if self._values['type'] is None:
            return None
        return str(self._values['type'])

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
    def enabled(self):
        if self._values['state'] == 'enabled':
            return True
        elif self._values['state'] == 'disabled':
            return False
        else:
            return None

    @property
    def disabled(self):
        if self._values['state'] == 'enabled':
            return False
        elif self._values['state'] == 'disabled':
            return True
        else:
            return None

    @property
    def bits_limit(self):
        return self._get_limit_value('bits_limit')

    @property
    def packets_limit(self):
        return self._get_limit_value('packets_limit')

    @property
    def connections_limit(self):
        return self._get_limit_value('connections_limit')

    @property
    def bits_enabled(self):
        return self._get_limit_status('bits_enabled')

    @property
    def packets_enabled(self):
        return self._get_limit_status('packets_enabled')

    @property
    def connections_enabled(self):
        return self._get_limit_status('connections_enabled')

    @property
    def monitor(self):
        if self._values['monitor'] is None:
            return None
        elif self._values['monitor'] in ['default', '']:
            return 'default'
        return fq_name(self.partition, self._values['monitor'])


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
    def enabled(self):
        if self.want.state == 'enabled' and self.have.disabled:
            result = dict(
                enabled=True,
                disabled=False
            )
            return result
        elif self.want.state == 'disabled' and self.have.enabled:
            result = dict(
                enabled=False,
                disabled=True
            )
            return result


class ModuleManager(object):
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

    def should_update(self):
        result = self._update_changed_options()
        if result:
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
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource = resource.load(
            name=self.want.pool,
            partition=self.want.partition
        )
        result = resource.members_s.member.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

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
        if self.want.state == 'disabled':
            self.want.update({'disabled': True})
        elif self.want.state in ['present', 'enabled']:
            self.want.update({'enabled': True})
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource = resource.load(
            name=self.want.pool,
            partition=self.want.partition
        )
        resource.members_s.member.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource = resource.load(
            name=self.want.pool,
            partition=self.want.partition
        )
        resource = resource.members_s.member.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource = resource.load(
            name=self.want.pool,
            partition=self.want.partition
        )
        resource = resource.members_s.member.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource = resource.load(
            name=self.want.pool,
            partition=self.want.partition
        )
        resource = resource.members_s.member.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.types = [
            'a', 'aaaa', 'cname', 'mx', 'naptr', 'srv'
        ]
        argument_spec = dict(
            pool=dict(required=True),
            server_name=dict(required=True),
            virtual_server=dict(required=True),
            type=dict(
                choices=self.types,
                required=True
            ),
            member_order=dict(type='int'),
            monitor=dict(),
            ratio=dict(type='int'),
            description=dict(),
            limits=dict(
                type='dict',
                options=dict(
                    bits_enabled=dict(type='bool'),
                    packets_enabled=dict(type='bool'),
                    connections_enabled=dict(type='bool'),
                    bits_limit=dict(type='int'),
                    packets_limit=dict(type='int'),
                    connections_limit=dict(type='int')
                )
            ),
            state=dict(
                default='present',
                choices=['present', 'absent', 'disabled', 'enabled']
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
