#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: code_build
short_description: Create or delete AWS CodeBuild
notes:
    - for details of the parameters and returns see U(http://boto3.readthedocs.io/en/latest/reference/services/codebuild.html)
description:
    - Create or delete a CodeBuild projects on AWS.
version_added: "2.6"
author:
    - Stefan Horning (@stefanhorning) <horning@mediapeers.com>
requirements: [ json, botocore, boto3 ]
options:
    name:
        description:
            - Name of the CodeBuild project
        required: true
    description:
        description:
            - Descriptive text of the CodeBuild project
        required: false
    source:
        description:
            - Configure service and location for the build input source.
        required: true
    artifacts:
        description:
            - Information about the build output artifacts for the build project.
        required: true
    cache:
        description:
            - Caching params to speed up following builds.
        required: false
    environment:
        description:
            - Information about the build environment for the build project.
        required: true
    service_role:
        description:
            - The ARN of the AWS IAM role that enables AWS CodeBuild to interact with dependent AWS services on behalf of the AWS account.
        required: false
    timeout_in_minutes:
         description:
            - How long CodeBuild should wait until timing out any build that has not been marked as completed.
        default: 60
        required: false
    encryption_key:
        decription:
            - The AWS Key Management Service (AWS KMS) customer master key (CMK) to be used for encrypting the build output artifacts.
        required: false
    tags:
        description:
            - A set of tags for the build project.
        required: false
    vpc_config:
        description:
            - The VPC config enables AWS CodeBuild to access resources in an Amazon VPC.
        required: false
    state:
        description:
            - Create or remove code build project.
        default: 'present'
        choices: ['present', 'absent']
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- code_build:
    name: my_project
    description: My nice little project
    service_role: "arn:aws:iam::123123:role/service-role/code-build-service-role"
    source:
        type: CODEPIPELINE
        buildspec: ''
    artifacts:
        namespaceType: NONE
        packaging: NONE
        type: CODEPIPELINE
        name: my_project
    environment:
        computeType: BUILD_GENERAL1_SMALL
        privilegedMode: "true"
        image: "aws/codebuild/docker:17.09.0"
        type: LINUX_CONTAINER
        environmentVariables:
            - { name: 'PROFILE', value: 'staging' }
    encryption_key: "arn:aws:kms:us-east-1:123123:alias/aws/s3"
    state: present
'''

RETURN = '''
project:
    description: Returns the dictionary desribing the code project configuration.
    returned: success
    type: complex
    contains:
        name:
            descriptoin: Name of the CodeBuild project
            returned: always
            type: string
'''

import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict, snake_dict_to_camel_dict, boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def create_or_update_project(client, params, module):
    resp = {}
    name = params['name']
    # Sanity check and cleanup params not needed for boto methods:
    if not isinstance(name, str):
        module.fail_json(msg="Params was missing name", exception=traceback.format_exc())
    clean_params = dict((k, v) for k, v in params.iteritems() if v is not None)
    clean_params.pop('region', None)
    clean_params.pop('state', None)
    clean_params.pop('validate_certs', None)
    formatted_params = snake_dict_to_camel_dict(clean_params)

    # Check if project with that name aleady exists and if so update existing:
    found = describe_project(client=client, name=name, module=module)

    if 'name' in found:
        found_last_modified = found['lastModified']
        resp = update_project(client=client, params=formatted_params, module=module)
        update_last_modified = resp['project']['lastModified']

        if update_last_modified > found_last_modified:
            resp['updated'] = True
        return resp
    # Or create new project:
    try:
        resp = client.create_project(**formatted_params)
        return resp
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable create project {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to create project {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc())


def update_project(client, params, module):
    name = params['name']

    try:
        resp = client.update_project(**params)
        return resp
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable update project {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to update project {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc())


def delete_project(client, name, module):
    try:
        resp = client.delete_project(name=name)
        return resp
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable delete project {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to delete project {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc())


def describe_project(client, name, module):
    project = {}
    try:
        projects = client.batch_get_projects(names=[name])['projects']
        if len(projects) > 0 and isinstance(projects[0], dict):
            project = projects[0]
        return project
    except botocore.exceptions.ClientError as e:
        return project
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Error when calling client.batch_get_projects {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc())


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, type='str'),
        description=dict(required=False, type='str'),
        source=dict(required=True, type='dict'),
        artifacts=dict(required=True, type='dict'),
        cache=dict(required=False, type='dict'),
        environment=dict(required=True, type='dict'),
        service_role=dict(required=False, type='str'),
        timeout_in_minutes=dict(required=False, type='int', default=60),
        encryption_key=dict(required=False, type='str'),
        tags=dict(required=False, type='list'),
        vpc_config=dict(required=False, type='dict'),
        state=dict(choices=['present', 'absent'], default='present')
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client_conn = boto3_conn(module, conn_type='client', resource='codebuild', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    state = module.params.get('state')
    changed = False

    if state == 'present':
        project_result = create_or_update_project(
            client=client_conn,
            params=module.params,
            module=module)
        if project_result['updated']:
            changed = True
    elif state == 'absent':
        project_result = delete_project(client=client_conn, name=module.params['name'], module=module)
        changed = True

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(project_result))

if __name__ == '__main__':
    main()
