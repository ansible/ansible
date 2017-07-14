#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2016 F5 Networks Inc.
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: bigip_snat_pool
short_description: Manage SNAT pools on a BIG-IP.
description:
  - Manage SNAT pools on a BIG-IP.
version_added: "2.3"
options:
  append:
    description:
      - When C(yes), will only add members to the SNAT pool. When C(no), will
        replace the existing member list with the provided member list.
    choices:
      - yes
      - no
    default: no
  members:
    description:
      - List of members to put in the SNAT pool. When a C(state) of present is
        provided, this parameter is required. Otherwise, it is optional.
    required: false
    default: None
    aliases: ['member']
  name:
    description: The name of the SNAT pool.
    required: True
  state:
    description:
      - Whether the SNAT pool should exist or not.
    required: false
    default: present
    choices:
      - present
      - absent
notes:
   - Requires the f5-sdk Python package on the host. This is as easy as
     pip install f5-sdk
   - Requires the netaddr Python package on the host. This is as easy as
     pip install netaddr
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Add the SNAT pool 'my-snat-pool'
  bigip_snat_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      name: "my-snat-pool"
      state: "present"
      members:
          - 10.10.10.10
          - 20.20.20.20
  delegate_to: localhost

- name: Change the SNAT pool's members to a single member
  bigip_snat_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      name: "my-snat-pool"
      state: "present"
      member: "30.30.30.30"
  delegate_to: localhost

- name: Append a new list of members to the existing pool
  bigip_snat_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      name: "my-snat-pool"
      state: "present"
      members:
          - 10.10.10.10
          - 20.20.20.20
  delegate_to: localhost

- name: Remove the SNAT pool 'my-snat-pool'
  bigip_snat_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      name: "johnd"
      state: "absent"
  delegate_to: localhost
'''

RETURN = '''
members:
    description:
      - List of members that are part of the SNAT pool.
    returned: changed and success
    type: list
    sample: "['10.10.10.10']"
'''

try:
    from f5.bigip.contexts import TransactionContextManager
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError

    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False

try:
    from netaddr import IPAddress, AddrFormatError
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5_utils import F5ModuleError, f5_argument_spec


class BigIpSnatPoolManager(object):
    def __init__(self, *args, **kwargs):
        self.changed_params = dict()
        self.params = kwargs
        self.api = None

    def apply_changes(self):
        result = dict()

        changed = self.apply_to_running_config()
        if changed:
            self.save_running_config()

        result.update(**self.changed_params)
        result.update(dict(changed=changed))
        return result

    def apply_to_running_config(self):
        try:
            self.api = self.connect_to_bigip(**self.params)
            if self.params['state'] == "present":
                return self.present()
            elif self.params['state'] == "absent":
                return self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

    def save_running_config(self):
        self.api.tm.sys.config.exec_cmd('save')

    def present(self):
        if self.params['members'] is None:
            raise F5ModuleError(
                "The members parameter must be specified"
            )

        if self.snat_pool_exists():
            return self.update_snat_pool()
        else:
            return self.ensure_snat_pool_is_present()

    def absent(self):
        changed = False
        if self.snat_pool_exists():
            changed = self.ensure_snat_pool_is_absent()
        return changed

    def connect_to_bigip(self, **kwargs):
        return ManagementRoot(kwargs['server'],
                              kwargs['user'],
                              kwargs['password'],
                              port=kwargs['server_port'])

    def read_snat_pool_information(self):
        pool = self.load_snat_pool()
        return self.format_snat_pool_information(pool)

    def format_snat_pool_information(self, pool):
        """Ensure that the pool information is in a standard format

        The SDK provides information back in a format that may change with
        the version of BIG-IP being worked with. Therefore, we need to make
        sure that the data is formatted in a way that our module expects it.

        Additionally, this takes care of minor variations between Python 2
        and Python 3.

        :param pool:
        :return:
        """
        result = dict()
        result['name'] = str(pool.name)
        if hasattr(pool, 'members'):
            result['members'] = self.format_current_members(pool)
        return result

    def format_current_members(self, pool):
        result = set()
        partition_prefix = "/{0}/".format(self.params['partition'])

        for member in pool.members:
            member = str(member.replace(partition_prefix, ''))
            result.update([member])
        return list(result)

    def load_snat_pool(self):
        return self.api.tm.ltm.snatpools.snatpool.load(
            name=self.params['name'],
            partition=self.params['partition']
        )

    def snat_pool_exists(self):
        return self.api.tm.ltm.snatpools.snatpool.exists(
            name=self.params['name'],
            partition=self.params['partition']
        )

    def update_snat_pool(self):
        params = self.get_changed_parameters()
        if params:
            self.changed_params = camel_dict_to_snake_dict(params)
            if self.params['check_mode']:
                return True
        else:
            return False
        params['name'] = self.params['name']
        params['partition'] = self.params['partition']
        self.update_snat_pool_on_device(params)
        return True

    def update_snat_pool_on_device(self, params):
        tx = self.api.tm.transactions.transaction
        with TransactionContextManager(tx) as api:
            r = api.tm.ltm.snatpools.snatpool.load(
                name=self.params['name'],
                partition=self.params['partition']
            )
            r.modify(**params)

    def get_changed_parameters(self):
        result = dict()
        current = self.read_snat_pool_information()
        if self.are_members_changed(current):
            result['members'] = self.get_new_member_list(current['members'])
        return result

    def are_members_changed(self, current):
        if self.params['members'] is None:
            return False
        if 'members' not in current:
            return True
        if set(self.params['members']) == set(current['members']):
            return False
        if not self.params['append']:
            return True

        # Checking to see if the supplied list is a subset of the current
        # list is only relevant if the `append` parameter is provided.
        new_members = set(self.params['members'])
        current_members = set(current['members'])
        if new_members.issubset(current_members):
            return False
        else:
            return True

    def get_new_member_list(self, current_members):
        result = set()

        if self.params['append']:
            result.update(set(current_members))
            result.update(set(self.params['members']))
        else:
            result.update(set(self.params['members']))
        return list(result)

    def ensure_snat_pool_is_present(self):
        params = self.get_snat_pool_creation_parameters()
        self.changed_params = camel_dict_to_snake_dict(params)
        if self.params['check_mode']:
            return True
        self.create_snat_pool_on_device(params)
        if self.snat_pool_exists():
            return True
        else:
            raise F5ModuleError("Failed to create the SNAT pool")

    def get_snat_pool_creation_parameters(self):
        members = self.get_formatted_members_list()
        return dict(
            name=self.params['name'],
            partition=self.params['partition'],
            members=members
        )

    def get_formatted_members_list(self):
        result = set()
        try:
            for ip in self.params['members']:
                address = str(IPAddress(ip))
                result.update([address])
            return list(result)
        except AddrFormatError:
            raise F5ModuleError(
                'The provided member address is not a valid IP address'
            )

    def create_snat_pool_on_device(self, params):
        tx = self.api.tm.transactions.transaction
        with TransactionContextManager(tx) as api:
            api.tm.ltm.snatpools.snatpool.create(**params)

    def ensure_snat_pool_is_absent(self):
        if self.params['check_mode']:
            return True
        self.delete_snat_pool_from_device()
        if self.snat_pool_exists():
            raise F5ModuleError("Failed to delete the SNAT pool")
        return True

    def delete_snat_pool_from_device(self):
        tx = self.api.tm.transactions.transaction
        with TransactionContextManager(tx) as api:
            pool = api.tm.ltm.snatpools.snatpool.load(
                name=self.params['name'],
                partition=self.params['partition']
            )
            pool.delete()


class BigIpSnatPoolModuleConfig(object):
    def __init__(self):
        self.argument_spec = dict()
        self.meta_args = dict()
        self.supports_check_mode = True
        self.states = ['absent', 'present']

        self.initialize_meta_args()
        self.initialize_argument_spec()

    def initialize_meta_args(self):
        args = dict(
            append=dict(
                default=False,
                type='bool',
            ),
            name=dict(required=True),
            members=dict(
                required=False,
                default=None,
                type='list',
                aliases=['member']
            ),
            state=dict(
                default='present',
                choices=self.states
            )
        )
        self.meta_args = args

    def initialize_argument_spec(self):
        self.argument_spec = f5_argument_spec()
        self.argument_spec.update(self.meta_args)

    def create(self):
        return AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=self.supports_check_mode
        )


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    if not HAS_NETADDR:
        raise F5ModuleError("The python netaddr module is required")

    config = BigIpSnatPoolModuleConfig()
    module = config.create()

    try:
        obj = BigIpSnatPoolManager(
            check_mode=module.check_mode, **module.params
        )
        result = obj.apply_changes()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
