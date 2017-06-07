#!/usr/bin/python
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

DOCUMENTATION = '''
---
module: ecr
short_description: Create or delete repositories in ECS.
description:
    - Create or delete repositories in ECS.
version_added: "2.3"
author: Argishti Rostamian(@WhileLoop)
requirements: [ boto3 ]
options:
    name:
        description:
            - The name of the repository
        required: True
    state:
        description:
            - The desired state of the repository
        required: True
        choices: ['present', 'absent']
    force:
        description:
          - Force delete of repository if there are images present
        required: false
        default: "false"
        choices: [ "true", "false" ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Create a repository
- name: create repository
  ecr:
    name: new_repo
    state: present
  register: ecr_output

# Delete a repository with images in it
- name: create repository
  ecr:
    name: new_repo
    state: absent
    force: yes
  register: ecr_output
'''

RETURN = '''
state:
    description: The current state of the repository
    returned: always
    type: string
repository:
    description: Details of affected repository
    returned: when repository is present
    type: complex
    contains:
        registryId:
            description: The AWS account ID associated with the registry that contains the repository.
            type: string
        repositoryArn:
            description: The Amazon Resource Name (ARN) that identifies the repository.
            type: string
        repositoryName:
            description: The name of the repository.
            type: string
        repositoryUri:
            description: The URI for the repository. You can use this URI for Docker push and pull operations.
            type: string
'''

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info, camel_dict_to_snake_dict

def get_repository(ecr, name, module):
    # If the repository is not present boto throws 'RepositoryNotFoundException'.
    try:
        return ecr.describe_repositories(repositoryNames=[name])['repositories']
    except ClientError as e:
        if e.response['Error']['Code'] == 'RepositoryNotFoundException':
            return None
        else:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

def main():
    # Get arguments.
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent', 'empty']),
        name=dict(required=True, type='str'),
        force=dict(default=False, type='bool'),
    ))
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    state = module.params['state']
    name = module.params['name']
    force = module.params['force']

    # Verify package requirements.
    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    # Create ECR client.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if region:
        ecr = boto3_conn(module, conn_type='client', resource='ecr', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    else:
        module.fail_json(msg="region must be specified")

    # Handle case present -> present.
    if state == 'present':
        repository = get_repository(ecr, name, module)
        if repository:
            module.exit_json(changed=False, repository=repository, state='present')
    # Handle case absent -> present.
        else:
            if not module.check_mode:
                try:
                    repository = ecr.create_repository(repositoryName=name)['repository']
                except ClientError as e:
                    module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))
                module.exit_json(changed=True, repository=repository, state='present')
            else:
                module.exit_json(changed=True, state='present')
    # Handle case present -> absent.
    if state == 'absent':
        repository = get_repository(ecr, name, module)
        if repository:
            if not module.check_mode:
                try:
                    repository = ecr.delete_repository(repositoryName=name, force=force)['repository']
                except ClientError as e:
                    module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))
            module.exit_json(changed=True, repository=repository, state='absent')
    # Handle case absent -> absent.
        else:
            module.exit_json(changed=False, state='absent')

if __name__ == '__main__':
    main()
