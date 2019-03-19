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
module: bigip_remote_role
short_description: Manage remote roles on a BIG-IP
description:
  - Manages remote roles on a BIG-IP. Remote roles are used in situations where
    user authentication is handled off-box. Local access control to the BIG-IP
    is controlled by the defined remote role. Where-as authentication (and by
    extension, assignment to the role) is handled off-box.
version_added: 2.7
options:
  name:
    description:
      - Specifies the name of the remote role.
    type: str
    required: True
  line_order:
    description:
      - Specifies the order of the line in the file C(/config/bigip/auth/remoterole).
      - The LDAP and Active Directory servers read this file line by line.
      - The order of the information is important; therefore, F5 recommends that
        you set the first line at 1000. This allows you, in the future, to insert
        lines before the first line.
      - When creating a new remote role, this parameter is required.
    type: int
  attribute_string:
    description:
      - Specifies the user account attributes saved in the group, in the format
        C(cn=, ou=, dc=).
      - When creating a new remote role, this parameter is required.
    type: str
  remote_access:
    description:
      - Enables or disables remote access for the specified group of remotely
        authenticated users.
      - When creating a new remote role, if this parameter is not specified, the default
        is C(yes).
    type: bool
  assigned_role:
    description:
      - Specifies the authorization (level of access) for the account.
      - When creating a new remote role, if this parameter is not provided, the
        default is C(none).
      - The C(partition_access) parameter controls which partitions the account can
        access.
      - The chosen role may affect the partitions that one is allowed to specify.
        Specifically, roles such as C(administrator), C(auditor) and C(resource-administrator)
        required a C(partition_access) of C(all).
      - A set of pre-existing roles ship with the system. They are C(none), C(guest),
        C(operator), C(application-editor), C(manager), C(certificate-manager),
        C(irule-manager), C(user-manager), C(resource-administrator), C(auditor),
        C(administrator), C(firewall-manager).
    type: str
  partition_access:
    description:
      - Specifies the accessible partitions for the account.
      - This parameter supports the reserved names C(all) and C(Common), as well as
        specific partitions a user may access.
      - Users who have access to a partition can operate on objects in that partition,
        as determined by the permissions conferred by the user's C(assigned_role).
      - When creating a new remote role, if this parameter is not specified, the default
        is C(all).
    type: str
  terminal_access:
    description:
      - Specifies terminal-based accessibility for remote accounts not already
        explicitly assigned a user role.
      - Common values for this include C(tmsh) and C(none), however custom values
        may also be specified.
      - When creating a new remote role, if this parameter is not specified, the default
        is C(none).
    type: str
  state:
    description:
      - When C(present), guarantees that the remote role exists.
      - When C(absent), removes the remote role from the system.
    type: str
    choices:
      - absent
      - present
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a remote role
  bigip_remote_role:
    name: foo
    group_name: ldap_group
    line_order: 1
    attribute_string: memberOf=cn=ldap_group,cn=ldap.group,ou=ldap
    remote_access: enabled
    assigned_role: administrator
    partition_access: all
    terminal_access: none
    state: present
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
attribute_string:
  description: The new attribute string of the resource.
  returned: changed
  type: str
  sample: "memberOf=cn=ldap_group,cn=ldap.group,ou=ldap"
terminal_access:
  description: The terminal setting of the remote role.
  returned: changed
  type: str
  sample: tmsh
line_order:
  description: Order of the remote role for LDAP and Active Directory servers.
  returned: changed
  type: int
  sample: 1000
assigned_role:
  description: System role that this remote role is associated with.
  returned: changed
  type: str
  sample: administrator
partition_access:
  description: Partition that the role has access to.
  returned: changed
  type: str
  sample: all
remote_access:
  description: Whether remote access is allowed or not.
  returned: changed
  type: bool
  sample: no
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.common import transform_name
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.common import transform_name


class Parameters(AnsibleF5Parameters):
    api_map = {
        'attribute': 'attribute_string',
        'console': 'terminal_access',
        'lineOrder': 'line_order',
        'role': 'assigned_role',
        'userPartition': 'partition_access',
        'deny': 'remote_access'
    }

    api_attributes = [
        'attribute',
        'console',
        'lineOrder',
        'role',
        'deny',
        'userPartition',
    ]

    returnables = [
        'attribute_string',
        'terminal_access',
        'line_order',
        'assigned_role',
        'partition_access',
        'remote_access',
    ]

    updatables = [
        'attribute_string',
        'terminal_access',
        'line_order',
        'assigned_role',
        'partition_access',
        'remote_access',
    ]

    role_map = {
        'application-editor': 'applicationeditor',
        'none': 'noaccess',
        'certificate-manager': 'certificatemanager',
        'irule-manager': 'irulemanager',
        'user-manager': 'usermanager',
        'resource-administrator': 'resourceadmin',
        'firewall-manager': 'firewallmanager'
    }


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def partition(self):
        return 'Common'

    @property
    def assigned_role(self):
        if self._values['assigned_role'] is None:
            return None
        return self.role_map.get(self._values['assigned_role'], self._values['assigned_role'])

    @property
    def terminal_access(self):
        if self._values['terminal_access'] in [None, 'tmsh']:
            return self._values['terminal_access']
        elif self._values['terminal_access'] == 'none':
            return 'disable'
        return self._values['terminal_access']

    @property
    def partition_access(self):
        if self._values['partition_access'] is None:
            return None
        if self._values['partition_access'] == 'all':
            return 'All'
        return self._values['partition_access']

    @property
    def remote_access(self):
        result = flatten_boolean(self._values['remote_access'])
        if result == 'yes':
            return 'disabled'
        elif result == 'no':
            return 'enabled'


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
    def assigned_role(self):
        if self._values['assigned_role'] is None:
            return None
        rmap = dict((v, k) for k, v in iteritems(self.role_map))
        return rmap.get(self._values['assigned_role'], self._values['assigned_role'])

    @property
    def terminal_access(self):
        if self._values['terminal_access'] in [None, 'tmsh']:
            return self._values['terminal_access']
        elif self._values['terminal_access'] == 'disabled':
            return 'none'
        return self._values['terminal_access']


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
        uri = "https://{0}:{1}/mgmt/tm/auth/remote-role/role-info/{2}".format(
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
        if self.want.partition_access is None:
            self.want.update({'partition_access': 'all'})
        if self.want.remote_access is None:
            self.want.update({'remote_access': True})
        if self.want.assigned_role is None:
            self.want.update({'assigned_role': 'none'})
        if self.want.terminal_access is None:
            self.want.update({'terminal_access': 'none'})
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        uri = "https://{0}:{1}/mgmt/tm/auth/remote-role/role-info/".format(
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

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/auth/remote-role/role-info/{2}".format(
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
                if 'Once configured [All] partition, remote user group cannot' in response['message']:
                    raise F5ModuleError(
                        "The specified 'attribute_string' is already used in the 'all' partition."
                    )
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/auth/remote-role/role-info/{2}".format(
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
        uri = "https://{0}:{1}/mgmt/tm/auth/remote-role/role-info/{2}".format(
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
            name=dict(required=True),
            line_order=dict(type='int'),
            attribute_string=dict(),
            remote_access=dict(type='bool'),
            assigned_role=dict(),
            partition_access=dict(),
            terminal_access=dict(),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
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
