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
module: aws_codebuild
short_description: Create or delete an AWS CodeBuild project
notes:
    - for details of the parameters and returns see U(http://boto3.readthedocs.io/en/latest/reference/services/codebuild.html)
description:
    - Create or delete a CodeBuild projects on AWS, used for building code artifacts from source code.
version_added: "2.7"
author:
    - Stefan Horning (@stefanhorning) <horning@mediapeers.com>
requirements: [ botocore, boto3 ]
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
        suboptions:
            type:
                description:
                    - "The type of the source. Allows one of these: CODECOMMIT, CODEPIPELINE, GITHUB, S3, BITBUCKET, GITHUB_ENTERPRISE"
                required: true
            location:
                description:
                    - Information about the location of the source code to be built. For type CODEPIPELINE location should not be specified.
                required: false
            git_clone_depth:
                description:
                    - When using git you can specify the clone depth as an integer here.
                required: false
            buildspec:
                description:
                    - The build spec declaration to use for the builds in this build project. Leave empty if part of the code project.
                required: false
            insecure_ssl:
                description:
                    - Enable this flag to ignore SSL warnings while connecting to the project source code.
                required: false
    artifacts:
        description:
            - Information about the build output artifacts for the build project.
        required: true
        suboptions:
            type:
                description:
                    - "The type of build output for artifacts. Can be one of the following: CODEPIPELINE, NO_ARTIFACTS, S3"
                required: true
            location:
                description:
                    - Information about the build output artifact location. When choosing type S3, set the bucket name here.
                required: false
            path:
                description:
                    - Along with namespace_type and name, the pattern that AWS CodeBuild will use to name and store the output artifacts.
                    - Used for path in S3 bucket when type is S3
                required: false
            namespace_type:
                description:
                    - Along with path and name, the pattern that AWS CodeBuild will use to determine the name and location to store the output artifacts
                    - Accepts BUILD_ID and NONE
                    - "See docs here: http://boto3.readthedocs.io/en/latest/reference/services/codebuild.html#CodeBuild.Client.create_project"
                required: false
            name:
                description:
                    - Along with path and namespace_type, the pattern that AWS CodeBuild will use to name and store the output artifact
                required: false
            packaging:
                description:
                    - The type of build output artifact to create on S3, can be NONE for creating a folder or ZIP for a ZIP file
                required: false
    cache:
        description:
            - Caching params to speed up following builds.
        required: false
        suboptions:
            type:
                description:
                    - Cache type. Can be NO_CACHE or S3.
                required: true
            location:
                description:
                    - Caching location on S3.
                required: true
    environment:
        description:
            - Information about the build environment for the build project.
        required: true
        suboptions:
            type:
                description:
                    - The type of build environment to use for the project. Usually LINUX_CONTAINER
                required: true
            image:
                description:
                    - The ID of the Docker image to use for this build project.
                required: true
            compute_type:
                description:
                    - Information about the compute resources the build project will use.
                    - "Available values include: BUILD_GENERAL1_SMALL, BUILD_GENERAL1_MEDIUM, BUILD_GENERAL1_LARGE"
                required: true
            environment_variables:
                description:
                    - A set of environment variables to make available to builds for the build project. List of dictionaries with name and value fields.
                    - "Example: { name: 'MY_ENV_VARIABLE', value: 'test' }"
                required: false
            privileged_mode:
                description:
                    - Enables running the Docker daemon inside a Docker container. Set to true only if the build project is be used to build Docker images.
                required: false
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
        description:
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
        # Possible values: BITBUCKET, CODECOMMIT, CODEPIPELINE, GITHUB, S3
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
    region: us-east-1
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
      sample: my_project
    arn:
      description: ARN of the CodeBuild project
      returned: always
      type: string
      sample: arn:aws:codebuild:us-east-1:123123123:project/vod-api-app-builder
    description:
      description: A description of the build project
      returned: always
      type: string
      sample: My nice little proejct
    source:
      description: Information about the build input source code.
      returned: always
      type: complex
      contains:
        type:
          description: The type of the repository
          returned: always
          type: string
          sample: CODEPIPELINE
        location:
          description: Location identifier, depending on the source type.
          returned: when configured
          type: string
        git_clone_depth:
          description: The git clone depth
          returned: when configured
          type: int
        build_spec:
          description: The build spec declaration to use for the builds in this build project.
          returned: always
          type: string
        auth:
          desription: Information about the authorization settings for AWS CodeBuild to access the source code to be built.
          returned: when configured
          type: complex
        insecure_ssl:
          description: True if set to ignore SSL warnings.
          returned: when configured
          type: bool
    artifacts:
      description: Information about the output of build artifacts
      returned: always
      type: complex
      contains:
        type:
          description: The type of build artifact.
          returned: always
          type: string
          sample: CODEPIPELINE
        location:
          description: Output location for build artifacts
          returned: when configured
          type: string
        # and more... see http://boto3.readthedocs.io/en/latest/reference/services/codebuild.html#CodeBuild.Client.create_project
    cache:
      description: Cache settings for the build project.
      returned: when configured
      type: complex
    environment:
      description: Environment settings for the build
      returned: always
      type: complex
    service_role:
      description: IAM role to be used during build to access other AWS services.
      returned: always
      type: string
      sample: arn:aws:iam::123123123:role/codebuild-service-role
    timeout_in_minutes:
      description: The timeout of a build in minutes
      returned: always
      type: int
      sample: 60
    tags:
      description: Tags added to the project
      returned: when configured
      type: list
    created:
      description: Timestamp of the create time of the project
      returned: always
      type: string
      sample: 2018-04-17T16:56:03.245000+02:00
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
    clean_params = dict((k, v) for k, v in params.items() if v is not None)
    clean_params.pop('region', None)
    clean_params.pop('state', None)
    clean_params.pop('validate_certs', None)
    formatted_params = snake_dict_to_camel_dict(clean_params)

    # Check if project with that name aleady exists and if so update existing:
    found = describe_project(client=client, name=name, module=module)
    changed = False

    if 'name' in found:
        found_project = found
        resp = update_project(client=client, params=formatted_params, module=module)
        updated_project = resp['project']

        # Prep both dicts for sensible change comparison:
        found_project.pop('lastModified')
        updated_project.pop('lastModified')
        if 'tags' not in updated_project:
            updated_project['tags'] = []

        if updated_project != found_project:
            changed = True
        return resp, changed
    # Or create new project:
    try:
        resp = client.create_project(**formatted_params)
        changed = True
        return resp, changed
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
    found = describe_project(client=client, name=name, module=module)
    changed = False
    if 'name' in found:
        # Mark as changed when a project with that name existed before calling delete
        changed = True
    try:
        resp = client.delete_project(name=name)
        return resp, changed
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
        if len(projects) > 0:
            project = projects[0]
        return project
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Client error when describing project {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Error when calling client.batch_get_projects {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc())


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        description=dict(),
        source=dict(required=True, type='dict'),
        artifacts=dict(required=True, type='dict'),
        cache=dict(type='dict'),
        environment=dict(type='dict'),
        service_role=dict(),
        timeout_in_minutes=dict(type='int', default=60),
        encryption_key=dict(),
        tags=dict(type='list'),
        vpc_config=dict(type='dict'),
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
        project_result, changed = create_or_update_project(
            client=client_conn,
            params=module.params,
            module=module)
    elif state == 'absent':
        project_result, changed = delete_project(client=client_conn, name=module.params['name'], module=module)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(project_result))

if __name__ == '__main__':
    main()
