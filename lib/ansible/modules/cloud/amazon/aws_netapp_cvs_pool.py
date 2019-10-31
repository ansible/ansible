#!/usr/bin/python

# (c) 2019, NetApp Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""AWS Cloud Volumes Services - Manage Pools"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: aws_netapp_cvs_pool

short_description: NetApp AWS Cloud Volumes Service Manage Pools.
extends_documentation_fragment:
    - netapp.awscvs
version_added: '2.9'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
    - Create, Update, Delete Pool on AWS Cloud Volumes Service.

options:
    state:
        description:
        - Whether the specified pool should exist or not.
        choices: ['present', 'absent']
        required: true
        type: str
    region:
        description:
        - The region to which the Pool is associated.
        required: true
        type: str
    name:
        description:
        - pool name ( The human readable name of the Pool )
        - name can be used for create, update and delete operations
        required: true
        type: str
    serviceLevel:
        description:
        - The service level of the Pool
        - can be used with pool create, update operations
        choices: ['basic', 'standard', 'extreme']
        type: str
    sizeInBytes:
        description:
        - Size of the Pool in bytes
        - can be used with pool create, update operations
        - minimum value is 4000000000000 bytes
        type: int
    vendorID:
        description:
        - A vendor ID for the Pool. E.g. an ID allocated by a vendor service for the Pool.
        - can be used with pool create, update operations
        - must be unique
        type: str
    from_name:
        description:
        - rename the existing pool name ( The human readable name of the Pool )
        - I(from_name) is the existing name, and I(name) the new name
        - can be used with update operation
        type: str
'''

EXAMPLES = """
- name: Create a new Pool
  aws_netapp_cvs_pool:
    state: present
    name: TestPoolBB12
    serviceLevel: extreme
    sizeInBytes: 4000000000000
    vendorID: ansiblePoolTestVendorBB12
    region: us-east-1
    api_url: cds-aws-bundles.netapp.com
    api_key: MyAPiKey
    secret_key: MySecretKey

- name: Delete a Pool
  aws_netapp_cvs_pool:
    state: absent
    name: TestPoolBB7
    region: us-east-1
    api_url: cds-aws-bundles.netapp.com
    api_key: MyAPiKey
    secret_key: MySecretKey

- name: Update a Pool
  aws_netapp_cvs_pool:
    state: present
    from_name: TestPoolBB12
    name: Mynewpool7
    vendorID: ansibleVendorMynewpool15
    serviceLevel: extreme
    sizeInBytes: 4000000000000
    region: us-east-1
    api_url: cds-aws-bundles.netapp.com
    api_key: MyAPiKey
    secret_key: MySecretKey

"""

RETURN = '''
'''

import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp_module import NetAppModule
from ansible.module_utils.netapp import AwsCvsRestAPI


class NetAppAWSCVS(object):
    '''Class  for  Pool operations '''

    def __init__(self):
        """
        Parse arguments, setup state variables,
        """
        self.argument_spec = netapp_utils.aws_cvs_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=True, choices=['present', 'absent']),
            region=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str'),
            serviceLevel=dict(required=False, choices=['basic', 'standard', 'extreme'], type='str'),
            sizeInBytes=dict(required=False, type='int'),
            vendorID=dict(required=False, type='str'),
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.restApi = AwsCvsRestAPI(self.module)
        self.sizeInBytes_min_value = 4000000000000

    def get_aws_netapp_cvs_pool(self, name=None):
        """
        Returns Pool object if exists else Return None
        """
        pool_info = None

        if name is None:
            name = self.parameters['name']

        pools, error = self.restApi.get('Pools')

        if error is None and pools is not None:
            for pool in pools:
                if 'name' in pool and pool['region'] == self.parameters['region']:
                    if pool['name'] == name:
                        pool_info = pool
                        break

        return pool_info

    def create_aws_netapp_cvs_pool(self):
        """
        Create a pool
        """
        api = 'Pools'

        for key in ['serviceLevel', 'sizeInBytes', 'vendorID']:
            if key not in self.parameters.keys() or self.parameters[key] is None:
                self.module.fail_json(changed=False, msg="Mandatory key '%s' required" % (key))

        pool = {
            "name": self.parameters['name'],
            "region": self.parameters['region'],
            "serviceLevel": self.parameters['serviceLevel'],
            "sizeInBytes": self.parameters['sizeInBytes'],
            "vendorID": self.parameters['vendorID']
        }

        response, error = self.restApi.post(api, pool)
        if error is not None:
            self.module.fail_json(changed=False, msg=error)

    def update_aws_netapp_cvs_pool(self, update_pool_info, pool_id):
        """
        Update a pool
        """
        api = 'Pools/' + pool_id

        pool = {
            "name": update_pool_info['name'],
            "region": self.parameters['region'],
            "serviceLevel": update_pool_info['serviceLevel'],
            "sizeInBytes": update_pool_info['sizeInBytes'],
            "vendorID": update_pool_info['vendorID']
        }

        response, error = self.restApi.put(api, pool)
        if error is not None:
            self.module.fail_json(changed=False, msg=error)

    def delete_aws_netapp_cvs_pool(self, pool_id):
        """
        Delete a pool
        """
        api = 'Pools/' + pool_id
        data = None
        response, error = self.restApi.delete(api, data)

        if error is not None:
            self.module.fail_json(changed=False, msg=error)

    def apply(self):
        """
        Perform pre-checks, call functions and exit
        """
        update_required = False
        cd_action = None

        if 'sizeInBytes' in self.parameters.keys() and self.parameters['sizeInBytes'] < self.sizeInBytes_min_value:
            self.module.fail_json(changed=False, msg="sizeInBytes should be greater than  or equal to %d" % (self.sizeInBytes_min_value))

        current = self.get_aws_netapp_cvs_pool()
        if self.parameters.get('from_name'):
            existing = self.get_aws_netapp_cvs_pool(self.parameters['from_name'])
            rename = self.na_helper.is_rename_action(existing, current)
            if rename is None:
                self.module.fail_json(changed=False, msg="unable to rename pool: '%s' does not exist" % self.parameters['from_name'])
            if rename:
                current = existing
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)

        if cd_action is None and self.parameters['state'] == 'present':
            keys_to_check = ['name', 'vendorID', 'sizeInBytes', 'serviceLevel']
            update_pool_info, update_required = self.na_helper.compare_and_update_values(current, self.parameters, keys_to_check)

            if update_required is True:
                self.na_helper.changed = True
                cd_action = 'update'

        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if cd_action == 'update':
                    self.update_aws_netapp_cvs_pool(update_pool_info, current['poolId'])
                elif cd_action == 'create':
                    self.create_aws_netapp_cvs_pool()
                elif cd_action == 'delete':
                    self.delete_aws_netapp_cvs_pool(current['poolId'])

        self.module.exit_json(changed=self.na_helper.changed)


def main():
    '''Main Function'''
    aws_cvs_netapp_pool = NetAppAWSCVS()
    aws_cvs_netapp_pool.apply()


if __name__ == '__main__':
    main()
