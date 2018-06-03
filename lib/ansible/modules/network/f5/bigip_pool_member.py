#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# Copyright (c) 2013 Matt Hite <mhite@hotmail.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_pool_member
short_description: Manages F5 BIG-IP LTM pool members
description:
  - Manages F5 BIG-IP LTM pool members via iControl SOAP API.
version_added: 1.4
options:
  name:
    description:
      - Name of the node to create, or re-use, when creating a new pool member.
      - This parameter is optional and, if not specified, a node name will be
        created automatically from either the specified C(address) or C(fqdn).
    version_added: 2.6
  state:
    description:
      - Pool member state.
    required: True
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
      - forced_offline
  pool:
    description:
      - Pool name. This pool must exist.
    required: True
  partition:
    description:
      - Partition
    default: Common
  address:
    description:
      - IP address of the pool member. This can be either IPv4 or IPv6. When creating a
        new pool member, one of either C(address) or C(fqdn) must be provided. This
        parameter cannot be updated after it is set.
    aliases:
      - ip
      - host
    version_added: 2.2
  fqdn:
    description:
      - FQDN name of the pool member. This can be any name that is a valid RFC 1123 DNS
        name. Therefore, the only characters that can be used are "A" to "Z",
        "a" to "z", "0" to "9", the hyphen ("-") and the period (".").
      - FQDN names must include at lease one period; delineating the host from
        the domain. ex. C(host.domain).
      - FQDN names must end with a letter or a number.
      - When creating a new pool member, one of either C(address) or C(fqdn) must be
        provided. This parameter cannot be updated after it is set.
    aliases:
      - hostname
    version_added: 2.6
  port:
    description:
      - Pool member port.
      - This value cannot be changed after it has been set.
    required: True
  connection_limit:
    description:
      - Pool member connection limit. Setting this to 0 disables the limit.
  description:
    description:
      - Pool member description.
  rate_limit:
    description:
      - Pool member rate limit (connections-per-second). Setting this to 0
        disables the limit.
  ratio:
    description:
      - Pool member ratio weight. Valid values range from 1 through 100.
        New pool members -- unless overridden with this value -- default
        to 1.
  preserve_node:
    description:
      - When state is C(absent) attempts to remove the node that the pool
        member references.
      - The node will not be removed if it is still referenced by other pool
        members. If this happens, the module will not raise an error.
      - Setting this to C(yes) disables this behavior.
    type: bool
    version_added: 2.1
  priority_group:
    description:
      - Specifies a number representing the priority group for the pool member.
      - When adding a new member, the default is 0, meaning that the member has no priority.
      - To specify a priority, you must activate priority group usage when you
        create a new pool or when adding or removing pool members. When activated,
        the system load balances traffic according to the priority group number
        assigned to the pool member.
      - The higher the number, the higher the priority, so a member with a priority
        of 3 has higher priority than a member with a priority of 1.
    version_added: 2.5
  fqdn_auto_populate:
    description:
      - Specifies whether the system automatically creates ephemeral nodes using
        the IP addresses returned by the resolution of a DNS query for a node
        defined by an FQDN.
      - When C(enabled), the system generates an ephemeral node for each IP address
        returned in response to a DNS query for the FQDN of the node. Additionally,
        when a DNS response indicates the IP address of an ephemeral node no longer
        exists, the system deletes the ephemeral node.
      - When C(disabled), the system resolves a DNS query for the FQDN of the node
        with the single IP address associated with the FQDN.
      - When creating a new pool member, the default for this parameter is C(yes).
      - This parameter is ignored when C(reuse_nodes) is C(yes).
    type: bool
    version_added: 2.6
  reuse_nodes:
    description:
      - Reuses node definitions if requested.
    default: yes
    type: bool
    version_added: 2.6
  session_state:
    description:
      - Set new session availability status for pool member.
      - This parameter is deprecated and will be removed in Ansible 2.7. Use C(state)
        C(enabled) or C(disabled).
    version_added: 2.0
    choices:
      - enabled
      - disabled
  monitor_state:
    description:
      - Set monitor availability status for pool member.
      - This parameter is deprecated and will be removed in Ansible 2.7. Use C(state)
        C(enabled) or C(disabled).
    version_added: 2.0
    choices:
      - enabled
      - disabled
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Add pool member
  bigip_pool_member:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    pool: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
    description: web server
    connection_limit: 100
    rate_limit: 50
    ratio: 2
  delegate_to: localhost

- name: Modify pool member ratio and description
  bigip_pool_member:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    pool: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
    ratio: 1
    description: nginx server
  delegate_to: localhost

- name: Remove pool member from pool
  bigip_pool_member:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
    pool: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
  delegate_to: localhost

- name: Force pool member offline
  bigip_pool_member:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: forced_offline
    pool: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
  delegate_to: localhost

- name: Create members with priority groups
  bigip_pool_member:
    server: lb.mydomain.com
    user: admin
    password: secret
    pool: my-pool
    partition: Common
    host: "{{ item.address }}"
    name: "{{ item.name }}"
    priority_group: "{{ item.priority_group }}"
    port: 80
  delegate_to: localhost
  loop:
    - host: 1.1.1.1
      name: web1
      priority_group: 4
    - host: 2.2.2.2
      name: web2
      priority_group: 3
    - host: 3.3.3.3
      name: web3
      priority_group: 2
    - host: 4.4.4.4
      name: web4
      priority_group: 1
'''

RETURN = '''
rate_limit:
  description: The new rate limit, in connections per second, of the pool member.
  returned: changed
  type: int
  sample: 100
connection_limit:
  description: The new connection limit of the pool member
  returned: changed
  type: int
  sample: 1000
description:
  description: The new description of pool member.
  returned: changed
  type: string
  sample: My pool member
ratio:
  description: The new pool member ratio weight.
  returned: changed
  type: int
  sample: 50
priority_group:
  description: The new priority group.
  returned: changed
  type: int
  sample: 3
fqdn_auto_populate:
  description: Whether FQDN auto population was set on the member or not.
  returned: changed
  type: bool
  sample: True
fqdn:
  description: The FQDN of the pool member.
  returned: changed
  type: string
  sample: foo.bar.com
address:
  description: The address of the pool member.
  returned: changed
  type: string
  sample: 1.2.3.4
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
    from library.module_utils.network.f5.common import is_valid_hostname
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
    from ansible.module_utils.network.f5.common import is_valid_hostname
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False

try:
    import netaddr
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'rateLimit': 'rate_limit',
        'connectionLimit': 'connection_limit',
        'priorityGroup': 'priority_group',
    }

    api_attributes = [
        'rateLimit', 'connectionLimit', 'description', 'ratio', 'priorityGroup',
        'address', 'fqdn', 'session', 'state'
    ]

    returnables = [
        'rate_limit', 'connection_limit', 'description', 'ratio', 'priority_group',
        'fqdn_auto_populate', 'session', 'state', 'fqdn', 'address'
    ]

    updatables = [
        'rate_limit', 'connection_limit', 'description', 'ratio', 'priority_group',
        'fqdn_auto_populate', 'state'
    ]


class ModuleParameters(Parameters):
    @property
    def full_name(self):
        delimiter = ':'
        try:
            addr = netaddr.IPAddress(self.full_name_dict['name'])
            if addr.version == 6:
                delimiter = '.'
        except netaddr.AddrFormatError:
            pass
        return '{0}{1}{2}'.format(self.full_name_dict['name'], delimiter, self.port)

    @property
    def full_name_dict(self):
        if self._values['name'] is None:
            name = self._values['address'] if self._values['address'] else self._values['fqdn']
        else:
            name = self._values['name']
        return dict(
            name=name,
            port=self.port
        )

    @property
    def node_name(self):
        return self.full_name_dict['name']

    @property
    def fqdn_name(self):
        return self._values['fqdn']

    @property
    def fqdn(self):
        result = {}
        if self.fqdn_auto_populate:
            result['autopopulate'] = 'enabled'
        else:
            result['autopopulate'] = 'disabled'
        if self._values['fqdn'] is None:
            return result
        if not is_valid_hostname(self._values['fqdn']):
            raise F5ModuleError(
                "The specified 'fqdn' is not a valid hostname."
            )
        result['tmName'] = self._values['fqdn']
        return result

    @property
    def pool(self):
        return fq_name(self.want.partition, self._values['pool'])

    @property
    def port(self):
        if 0 > int(self._values['port']) or int(self._values['port']) > 65535:
            raise F5ModuleError(
                "Valid ports must be in range 0 - 65535"
            )
        return int(self._values['port'])

    @property
    def state(self):
        # TODO(Remove all of this state craziness in 2.7)
        if self.session_state is not None or self.monitor_state is not None:
            if self._values['state'] in ['enabled', 'disabled', 'forced_offline']:
                self._values['__warnings'].append([{
                    'msg': "'session_state' is deprecated and will be ignored in favor of 'state'.",
                    'version': '2.7'
                }])
                return self._values['state']
            else:
                if self.session_state is not None:
                    self._values['__warnings'].append([{
                        'msg': "'session_state' is deprecated and will be removed in the future. Use 'state'.",
                        'version': '2.7'
                    }])
                elif self.monitor_state is not None:
                    self._values['__warnings'].append([{
                        'msg': "'monitor_state' is deprecated and will be removed in the future. Use 'state'.",
                        'version': '2.7'
                    }])

                if self.session_state == 'enabled' and self.monitor_state == 'enabled':
                    return 'enabled'
                elif self.session_state == 'disabled' and self.monitor_state == 'enabled':
                    return 'disabled'
                else:
                    return 'forced_offline'
        return self._values['state']

    @property
    def address(self):
        if self._values['address'] is None:
            return None
        elif self._values['address'] == 'any6':
            return 'any6'
        try:
            addr = netaddr.IPAddress(self._values['address'])
            return str(addr)
        except netaddr.AddrFormatError:
            raise F5ModuleError(
                "The specified 'address' value is not a valid IP address."
            )


class ApiParameters(Parameters):
    @property
    def allow(self):
        if self._values['allow'] is None:
            return ''
        if self._values['allow'][0] == 'All':
            return 'all'
        allow = self._values['allow']
        result = list(set([str(x) for x in allow]))
        result = sorted(result)
        return result

    @property
    def rate_limit(self):
        if self._values['rate_limit'] is None:
            return None
        if self._values['rate_limit'] == 'disabled':
            return 0
        return int(self._values['rate_limit'])

    @property
    def state(self):
        if self._values['state'] in ['user-up', 'unchecked', 'fqdn-up-no-addr'] and self._values['session'] in ['user-enabled']:
            return 'present'
        elif self._values['state'] in ['down', 'up'] and self._values['session'] == 'monitor-enabled':
            return 'present'
        elif self._values['state'] in ['user-down'] and self._values['session'] in ['user-disabled']:
            return 'forced_offline'
        else:
            return 'disabled'


class NodeApiParameters(Parameters):
    pass


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
    def ssl_cipher_suite(self):
        default = ':'.join(sorted(Parameters._ciphers.split(':')))
        if self._values['ssl_cipher_suite'] == default:
            return 'default'
        else:
            return self._values['ssl_cipher_suite']

    @property
    def fqdn_auto_populate(self):
        if self._values['fqdn'] is None:
            return None
        if 'autopopulate' in self._values['fqdn']:
            if self._values['fqdn']['autopopulate'] == 'enabled':
                return True
            return False

    @property
    def fqdn(self):
        if self._values['fqdn'] is None:
            return None
        if 'tmName' in self._values['fqdn']:
            return self._values['fqdn']['tmName']

    @property
    def state(self):
        if self._values['state'] in ['user-up', 'unchecked', 'fqdn-up-no-addr'] and self._values['session'] in ['user-enabled']:
            return 'present'
        elif self._values['state'] in ['down', 'up'] and self._values['session'] == 'monitor-enabled':
            return 'present'
        elif self._values['state'] in ['user-down'] and self._values['session'] in ['user-disabled']:
            return 'forced_offline'
        else:
            return 'disabled'


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
    def state(self):
        if self.want.state == self.have.state:
            return None
        if self.want.state == 'forced_offline':
            return {
                'state': 'user-down',
                'session': 'user-disabled'
            }
        elif self.want.state == 'disabled':
            return {
                'state': 'user-up',
                'session': 'user-disabled'
            }
        elif self.want.state in ['present', 'enabled']:
            return {
                'state': 'user-up',
                'session': 'user-enabled'
            }


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
            if state in ['present', 'present', 'enabled', 'disabled', 'forced_offline']:
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

    def exists(self):
        try:
            pool = self.client.api.tm.ltm.pools.pool.load(
                name=self.want.pool,
                partition=self.want.partition
            )
        except Exception:
            raise F5ModuleError('The specified pool does not exist')
        result = pool.members_s.members.exists(
            name=self.want.full_name,
            partition=self.want.partition
        )
        return result

    def node_exists(self):
        resource = self.client.api.tm.ltm.nodes.node.exists(
            name=self.want.node_name,
            partition=self.want.partition
        )
        return resource

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
        if not self.want.preserve_node:
            self.remove_node_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def _set_host_by_name(self):
        try:
            netaddr.IPAddress(self.want.name)
            self.want.update({
                'fqdn': None,
                'address': self.want.name
            })
        except netaddr.AddrFormatError:
            if not is_valid_hostname(self.want.name):
                raise F5ModuleError(
                    "'name' is neither a valid IP address or FQDN name."
                )
            self.want.update({
                'fqdn': self.want.name,
                'address': None
            })

    def _update_api_state_attributes(self):
        if self.want.state == 'forced_offline':
            self.want.update({
                'state': 'user-down',
                'session': 'user-disabled',

                # TODO(Remove in 2.7)
                'session_state': None,
                'monitor_state': None
            })
        elif self.want.state == 'disabled':
            self.want.update({
                'state': 'user-up',
                'session': 'user-disabled',

                # TODO(Remove in 2.7)
                'session_state': None,
                'monitor_state': None
            })
        elif self.want.state in ['present', 'enabled']:
            self.want.update({
                'state': 'user-up',
                'session': 'user-enabled',

                # TODO(Remove in 2.7)
                'session_state': None,
                'monitor_state': None
            })

    def _update_address_with_existing_nodes(self):
        try:
            have = self.read_current_node_from_device(self.want.node_name)

            if self.want.fqdn_auto_populate and self.want.reuse_nodes:
                self.module.warn("'fqdn_auto_populate' is discarded in favor of the re-used node's auto-populate setting.")
            self.want.update({
                'fqdn_auto_populate': True if have.fqdn['autopopulate'] == 'enabled' else False
            })
            if 'tmName' in have.fqdn:
                self.want.update({
                    'fqdn': have.fqdn['tmName'],
                    'address': 'any6'
                })
            else:
                self.want.update({
                    'address': have.address
                })
        except Exception:
            return None

    def create(self):
        if self.want.reuse_nodes:
            self._update_address_with_existing_nodes()
        if self.want.name and not any(x for x in [self.want.address, self.want.fqdn_name]):
            self._set_host_by_name()

        self._update_api_state_attributes()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        pool = self.client.api.tm.ltm.pools.pool.load(
            name=self.want.pool,
            partition=self.want.partition
        )
        pool.members_s.members.create(
            name=self.want.full_name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        pool = self.client.api.tm.ltm.pools.pool.load(
            name=self.want.pool,
            partition=self.want.partition
        )
        resource = pool.members_s.members.load(
            name=self.want.full_name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        elif not self.want.preserve_node and self.node_exists():
            return self.remove_node_from_device()
        return False

    def remove_from_device(self):
        pool = self.client.api.tm.ltm.pools.pool.load(
            name=self.want.pool,
            partition=self.want.partition
        )
        resource = pool.members_s.members.load(
            name=self.want.full_name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def remove_node_from_device(self):
        resource = self.client.api.tm.ltm.nodes.node.load(
            name=self.want.node_name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        pool = self.client.api.tm.ltm.pools.pool.load(
            name=self.want.pool,
            partition=self.want.partition
        )
        resource = pool.members_s.members.load(
            name=self.want.full_name,
            partition=self.want.partition
        )
        return ApiParameters(params=resource.attrs)

    def read_current_node_from_device(self, node):
        resource = self.client.api.tm.ltm.nodes.node.load(
            name=node,
            partition=self.want.partition
        )
        return NodeApiParameters(params=resource.attrs)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            pool=dict(required=True),
            address=dict(aliases=['host', 'ip']),
            fqdn=dict(
                aliases=['hostname']
            ),
            name=dict(),
            port=dict(type='int', required=True),
            connection_limit=dict(type='int'),
            description=dict(),
            rate_limit=dict(type='int'),
            ratio=dict(type='int'),
            preserve_node=dict(type='bool'),
            priority_group=dict(type='int'),
            state=dict(
                default='present',
                choices=['absent', 'present', 'enabled', 'disabled', 'forced_offline']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            fqdn_auto_populate=dict(type='bool'),
            reuse_nodes=dict(type='bool', default=True),

            # Deprecated params
            # TODO(Remove in 2.7)
            session_state=dict(
                choices=['enabled', 'disabled'],
                removed_in_version=2.7,
            ),
            monitor_state=dict(
                choices=['enabled', 'disabled'],
                removed_in_version=2.7,
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['address', 'fqdn']
        ]
        self.required_one_of = [
            ['name', 'address', 'fqdn'],
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
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
