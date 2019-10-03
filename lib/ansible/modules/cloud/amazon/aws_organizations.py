#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Kamil Potrec <kamilpotrec@googlemail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: aws_organizations
short_description: Manages AWS Organization
description:
  - Creates and deletes AWS OrganizationalUnits
version_added: "2.10"
author:
  - Kamil Potrec (@p0tr3c)
options:
  name:
    description:
      - Name of the organizational unit
    required: true
    type: str
  state:
    description:
      - State of the organizational unit
    default: present
    type: str
    choices:
      - present
      - absent
extends_documentation_fragment:
  - aws
  - ec2
requirements:
  - boto3
  - botocore
"""

EXAMPLES = """
- name: Create organizational unit
  aws_organizations:
    name: Prod
    state: present

- name: Delete organizational unit
  aws_organizations:
    name: Prod
    state: absent
"""

RETURN = """
name:
  description: Name of the organizational unit
  returned: always
  type: str
  sample: Prod
state:
  description: State of the organization unit
  returned: always
  type: str
  sample: present
ou:
  description: The Organization Unit details
  returned: always
  type: dict
  sample:
    {
        "Arn": "arn:aws:organizations::account:ou/o-id/ou-id",
        "Id": "ou-id",
        "Name": "Prod"
    }
"""

try:
    import boto3
    import botocore.exceptions
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    # handled by AnsibleAWSModule
    pass

from ansible.module_utils.ec2 import AWSRetry, boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list, camel_dict_to_snake_dict
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils._text import to_native


class AwsOrganizations():
    def __init__(self, module):
        self.module = module
        try:
            self.client = self.module.client('organizations')
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to connect to AWS")
        self.aws_org_root = self.get_root()

    def _get_boto_paginator(self, api):
        return self.client.get_paginator(api)

    def get_children_ous(self, parent_id, recursive=False):
        paginator = self._get_boto_paginator('list_organizational_units_for_parent')
        children_ous = []
        for page in paginator.paginate(ParentId=parent_id):
            if recursive:
                for ou in page['OrganizationalUnits']:
                    children_ous.append(dict(
                        ou,
                        OrganizationalUnits=self.get_children_ous(ou['Id'], recursive=True),
                        Accounts=self.get_children_accounts(ou['Id'])
                    ))
            else:
                children_ous += page['OrganizationalUnits']
        return children_ous

    def get_children_accounts(self, parent_id):
        paginator = self._get_boto_paginator('list_accounts_for_parent')
        children_accounts = []
        for page in paginator.paginate(ParentId=parent_id):
            children_accounts += page['Accounts']
        return children_accounts

    def get_ou_by_id(self, ou_id):
        try:
            ou = self.client.describe_organizational_unit(OrganizationalUnitId=ou_id)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to describe organizational unit")
        else:
            if ou is None:
                self.module.fail_json(msg="Organizational unit does not exist")
            else:
                return ou['OrganizationalUnit']

    def get_ou_id(self, name):
        ou = self.get_ou(name)
        if ou is None:
            self.module.fail_json(msg="Organizational unit does not exist")
        else:
            return ou['Id']

    def get_parent_tree(self, parent_name):
        parent_ou = self.get_ou(parent_name)
        if parent_ou is None:
            self.module.fail_json(msg="Organizational unit does not exist")
        org_tree = dict(
            parent_ou,
            OrganizationalUnits=self.get_children_ous(parent_ou['Id'], recursive=True),
            Accounts=self.get_children_accounts(parent_ou['Id'])
        )
        return org_tree

    def get_org_tree(self):
        org_tree = dict(
            self.aws_org_root,
            OrganizationalUnits=self.get_children_ous(self.aws_org_root['Id'], recursive=True),
            Accounts=self.get_children_accounts(self.aws_org_root['Id'])
        )
        return org_tree

    def get_root(self):
        try:
            root_ids = self.client.list_roots().get('Roots')
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to list roots")
        if len(root_ids) > 1:
            self.module.fail_json(msg="Multiple roots not supported")
        return root_ids[0]

    def get_root_id(self):
        return self.aws_org_root['Id']

    def _get_ou(self, name, parent):
        paginator = self._get_boto_paginator("list_organizational_units_for_parent")
        children_ous = []
        for page in paginator.paginate(ParentId=parent):
            children_ous += page['OrganizationalUnits']
        ou = list(filter(lambda f: f['Name'] == name, children_ous))
        if len(ou) == 1:
            return ou[0]
        elif len(ou) == 0:
            return None
        else:
            self.module.fail_json(msg="None unique organizational unit names within a parent are not supported")

    def get_ou(self, name):
        ou_name = name.rstrip('/').lstrip('/')
        ou_path = ou_name.split('/')
        ou_parent = self.get_root_id()
        for n in ou_path:
            ou = self._get_ou(n, ou_parent)
            if ou is None:
                return ou
            ou_parent = ou['Id']
        return dict(ou)

    def _create_ou(self, name, parent_id):
        try:
            ou = self.client.create_organizational_unit(ParentId=parent_id, Name=name)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to create organizational unit")
        else:
            return ou['OrganizationalUnit']

    def create_ou(self, name):
        ou_name = name.rstrip('/').lstrip('/')
        ou_path = ou_name.split('/')
        if len(ou_path) == 1:
            parent_id = self.get_root_id()
        else:
            ou_parent_path = ou_path[:-1]
            parent_ou = self.get_ou('/'.join(ou_parent_path))
            if parent_ou is None:
                self.module.fail_json(msg="Parent organizational unit does not exist")
            else:
                parent_id = parent_ou['Id']
        return self._create_ou(ou_path[-1], parent_id)

    def delete_ou(self, ou_id):
        try:
            res = self.client.delete_organizational_unit(OrganizationalUnitId=ou_id)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg="Failed to delete organizational unit")
        else:
            return True


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    client = AwsOrganizations(module)

    result = dict(
        name=module.params.get('name'),
        ou=dict(),
        changed=False,
        state='absent',
    )

    ou = client.get_ou(module.params.get('name'))
    if ou is None:
        result['state'] = 'absent'
    else:
        result['state'] = 'present'
        result['ou'] = ou

    if module.params.get('state') == 'absent':
        if ou is None:
            result['changed'] = False
        else:
            if client.delete_ou(ou['Id']):
                result['changed'] = True
                result['state'] = 'absent'
    elif module.params.get('state') == 'present':
        if ou is None:
            ou = client.create_ou(module.params.get('name'))
            if ou is not None:
                result['changed'] = True
                result['ou'] = ou
            else:
                module.fail_json(msg="Failed to create organizational unit")

    module.exit_json(**result)


if __name__ == '__main__':
    main()
