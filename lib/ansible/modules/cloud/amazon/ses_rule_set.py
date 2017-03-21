#!/usr/bin/python

# -*- coding: utf-8 -*-
#
# (c) 2017, Ben Tomasik <ben@tomasik.io>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: ses_rule_set
short_description: Manages SES inbound receipt rule sets
description:
    - The M(ses_rule_set) module allows you to create, delete, and manage SES receipt rule sets
version_added: 2.4
author:
  - "Ben Tomasik (@tomislacker)"
requirements: [ "boto3","botocore" ]
options:
  name:
    description:
      - The name of the receipt rule set
    required: True
  state:
    description:
      - Whether to create or destroy the receipt rule set
    required: False
    default: present
    choices: ["absent", "present"]
  is_active:
    description:
      - Whether or not to set this rule set as the active one
    required: False
    default: False
extends_documentation_fragment: aws
"""

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.
---
- name: Create default rule set and activate it if not already
  ses_rule_set:
    name: default-rule-set
    is_active: yes

- name: Create some arbitrary rule set but do not activate it
  ses_rule_set:
    name: arbitrary-rule-set
"""

RETURN = """
changed:
  description: if a SES rule set has been created and/or activated, or deleted
  returned: always
  type: bool
  sample:
    changed: true
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO3
from ansible.module_utils.ec2 import ec2_argument_spec
from ansible.module_utils.ec2 import get_aws_connection_info
from ansible.module_utils.ec2 import boto3_conn


def rule_set_exists(ses_client, name):
    rule_sets = ses_client.list_receipt_rule_sets()['RuleSets']
    return any([s for s in rule_sets if s['Name'].lower() == name.lower()])


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        is_active=dict(type='bool', default=False),
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    name = module.params.get('name').lower()
    state = module.params.get('state').lower()
    is_active = module.params.get('is_active')
    check_mode = module.check_mode
    changed = False

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install it')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg='region must be specified')

    try:
        client = boto3_conn(module, conn_type='client', resource='ses',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.ValidationError) as e:
        module.fail_json(msg=str(e))

    if state == 'absent':
        # Remove the rule set if present
        if rule_set_exists(client, name):
            changed = True

            if not check_mode:
                try:
                    client.delete_receipt_rule_set(
                        RuleSetName=name)
                except botocore.exceptions.ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                     **camel_dict_to_snake_dict(e.response))
                except botocore.exceptions.ParamValidationError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc())

    elif state == 'present':
        # Add rule set if missing
        if not rule_set_exists(client, name):
            changed = True

            if not check_mode:
                try:
                    client.create_receipt_rule_set(
                        RuleSetName=name)
                except botocore.exceptions.ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                     **camel_dict_to_snake_dict(e.response))
                except botocore.exceptions.ParamValidationError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc())

        # Set active if requested
        if is_active:
            # First determine if it's the active rule set
            try:
                active_name = client.describe_active_receipt_rule_set()['Metadata']['Name'].lower()
            except KeyError:
                # Metadata was not set meaning there is no active rule set
                active_name = ""

            if name != active_name:
                changed = True

                if not check_mode:
                    try:
                        client.set_active_receipt_rule_set(
                            RuleSetName=name)
                    except botocore.exceptions.ClientError as e:
                        module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                         **camel_dict_to_snake_dict(e.response))
                    except botocore.exceptions.ParamValidationError as e:
                        module.fail_json(msg=e.message, exception=traceback.format_exc())

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
