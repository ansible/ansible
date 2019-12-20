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
module: aws_organization_units
short_description: Manages AWS Organizations Units
description:
  - Creates and deletes AWS OrganizationalUnits.
version_added: "2.10"
author:
  - Kamil Potrec (@p0tr3c)
options:
  name:
    description:
      - Name of the organizational unit
        This can be full OU path such as "Prod/IT/Service_Desk".
        The lookup always starts from the root node, as the names are not unique within the organization tree.
      - Mutually exclusive with c(arn)
    required: true
    type: str
  arn:
    description:
      - ARN of the organizational unit
      - ARN can be used to delete OU but not create
      - Mutually exclusive with c(name)
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
  description:
    - Name of the organizational unit.
      If the parent OU does not exist the module will fail with warning message.
  returned: always
  type: str
  sample: Prod
arn:
  description:
    - ARN of the organizational unit.
      If the parent OU does not exist the module will fail with warning message.
  returned: always
  type: str
  sample: Prod
state:
  description: State of the organization unit.
  returned: always
  type: str
  sample: present
ou:
  description: The Organization Unit details.
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
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    # handled by AnsibleAWSModule
    pass

from ansible.module_utils.ec2 import AWSRetry, boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list, camel_dict_to_snake_dict
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils._text import to_native

class ParameterValidationException(Exception):
    pass

class UnknownConditionException(Exception):
    pass

class OrganizationalUnitDependencyException(Exception):
    pass

class AwsOrganizationalUnit():
    def __init__(self, name=None, arn=None):
        self.arn = arn
        self.client = boto3.client("organizations")
        self.root = self.get_aws_organization_root()
        if arn:
            self.name = name
            self.ou = self.get_aws_organizational_unit_by_arn(self.arn)
        elif name:
            self.name = name.strip("/")
            self.ou = self.get_aws_organizational_unit_by_name(self.name)
        else:
            raise ParameterValidationException

    def get_aws_organization_root(self):
        roots = self.client.list_roots()
        if len(roots.get("Roots")) != 1:
            raise UnknownConditionException
        return roots.get("Roots")[0]

    def get_aws_organizational_unit_for_parent(self, ou_name, parent_id):
        paginator = self.client.get_paginator("list_organizational_units_for_parent")
        for page in paginator.paginate(ParentId=parent_id):
            for child_ou in page["OrganizationalUnits"]:
                if child_ou["Name"] == ou_name:
                    return child_ou
        return None

    def get_aws_organizational_unit_by_name(self, name):
        parent_ou_id = self.root["Id"]
        for ou in name.split("/"):
            parent_ou = self.get_aws_organizational_unit_for_parent(ou, parent_ou_id)
            if parent_ou is None:
                return None
            parent_ou_id = parent_ou["Id"]
        return parent_ou

    def get_aws_organizational_unit_by_arn(self, arn):
        if arn.startswith("arn:aws:organizations::"):
            ou_id = arn.split("/")[-1]
        else:
            raise ParameterValidationException
        try:
            parent_ou = self.client.describe_organizational_unit(OrganizationalUnitId=ou_id)
        except ClientError as e:
            if "OrganizationalUnitNotFoundException" in e.response["Error"]["Message"]:
                return None
            else:
                raise e
        return parent_ou["OrganizationalUnit"]

    def has_children(self):
        if self.ou is None:
            return False
        paginator = self.client.get_paginator("list_children")
        for child_type in ["ACCOUNT", "ORGANIZATIONAL_UNIT"]:
            for page in paginator.paginate(ParentId=self.ou["Id"], ChildType=child_type):
                if len(page["Children"]) > 0:
                    return True
        return False

    def delete_aws_organizational_unit(self):
        if self.ou is None:
            return True
        if self.has_children():
            raise OrganizationalUnitDependencyException
        self.client.delete_organizational_unit(OrganizationalUnitId=self.ou["Id"])
        return True

    def create_aws_organizational_unit(self):
        if self.ou is not None:
            return True
        if self.name is None:
            raise ParameterValidationException
        parent_name = self.name.rsplit("/", 1)[0]
        ou_name = self.name.split("/")[-1]
        if parent_name != ou_name:
            parent_ou = self.get_aws_organizational_unit_by_name(parent_name)
            if parent_ou is None:
                raise ParentOrganizationalUnitDoesNotExist
            parent_id = parent_ou["Id"]
        else:
            parent_id = self.root["Id"]
        self.ou = self.client.create_organizational_unit(ParentId=parent_id, Name=ou_name)
        return self.ou


def main():
    argument_spec = dict(
        name=dict(type='str'),
        arn=dict(type='str'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['name', 'arn']],
        required_one_of=[['name', 'arn']]
    )

    result = dict(
        name=module.params.get('name'),
        ou=dict(),
        changed=False,
        state='absent',
    )

    ou_name = module.params.get('name')
    ou_arn = module.params.get('arn')
    ou_state = module.params.get('state')

    if ou_arn:
        try:
            client = AwsOrganizationalUnit(arn=ou_arn)
        except ParameterValidationException as e:
            module.fail_json(msg="Invalid ARN format")
        except (BotoCoreError, ClientError) as e:
            module.fail_json(msg="Boto failure")
    else:
        client = AwsOrganizationalUnit(name=ou_name)

    if client.ou is None:
        result['state'] = 'absent'
    else:
        result['state'] = 'present'
        result['ou'] = client.ou

    if ou_state == 'absent':
        if client.ou is None:
            result['changed'] = False
        else:
            result['changed'] = True
            if not module.check_mode:
                try:
                    if client.delete_aws_organizational_unit():
                        result['state'] = 'absent'
                except (BotoCoreError, ClientError, OrganizationalUnitDependencyException) as e:
                    module.fail_json(msg="Failed to delete organizational unit")
    elif ou_state == 'present':
        if client.ou is None:
            result['changed'] = True
            if not module.check_mode:
                try:
                    result['ou'] = client.create_aws_organizational_unit()
                except (BotoCoreError, ClientError, ParentOrganizationalUnitDoesNotExist) as e:
                    module.fail_json(msg="Failed to create organizational unit")
    module.exit_json(**result)


if __name__ == '__main__':
    main()
