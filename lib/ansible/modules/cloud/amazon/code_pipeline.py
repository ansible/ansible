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
module: code_pipeline
short_description: Create or delete AWS CodePipeline
notes:
    - for details of the parameters and returns see U(http://boto3.readthedocs.io/en/latest/reference/services/codepipeline.html)
description:
    - Create or delete a CodePipeline on AWS.
version_added: "2.6"
author:
    - Stefan Horning (@stefanhorning) <horning@mediapeers.com>
requirements: [ json, botocore, boto3 ]
options:
    name:
      descritpion:
        - Name of the pipeline
      required: true
    role_arn:
      descritpion:
        - ARN of the IAM role to use when executing the pipeline
      required: true
    artifact_store:
      description:
        - Location information where articacts are stored (on S3). Dictionary with fields: type: <str>, location: <str>, encrypion_key: { id: <str>, type: <str> }
      required: true
    stages:
      description:
        - List of stages to perfoem in the CodePipeline. List of dictionaries
      required: true
    version:
      description:
        - Version number of the pipeline. This number is automatically incremented when a pipeline is updated.
      required: false
      default: 1
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- code_pipeline:
    name: my_deploy_pipeline
    role_arn: arn:aws:iam::123456:role/AWS-CodePipeline-Service
    artifact_store:
      type: S3
      locatation: my_s3_codepipline_bucket
    stages:
      - { name: 'Step 1', actions: [{name: 'fetch'}] }
      - { name: 'Step 2', actions: [{name: 'build'}] }
    version: 2
'''

RETURN = '''

'''

import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict, boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3

def create_pipeline(client, name, role_arn, artifact_store, stages, version, module):
    pipeline_dict = { 'name': name, 'roleArn': role_arn, 'artifactStore': artifact_store, 'stages': stages }
    if version:
        pipeline_dict['version'] = version
    try:
        resp = client.create_pipeline(pipeline=pipeline_dict)
        return resp
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable create pipeline".format(name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to create pipeline".format(name, to_native(e)),
                         exception=traceback.format_exc())


def update_pipeline(client, pipeline_dict, module):
    try:
        resp = client.update_pipeline(pipeline=pipeline_dict)
        return resp
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable update pipeline".format(name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to update pipeline".format(name, to_native(e)),
                         exception=traceback.format_exc())


def delete_pipeline(client, name, module):
    try:
        resp = client.delete_pipeline(name=name)
        return resp
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable delete pipeline".format(name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to delete pipeline".format(name, to_native(e)),
                         exception=traceback.format_exc())


def describe_pipeline(client, name, version, module):
    pipeline = {}
    try:
        if type(version) is int:
            pipeline = client.get_pipeline(name=name, version=version)
            return pipeline
        else:
            pipeline = client.get_pipeline(name=name)
            return pipeline
    except botocore.exceptions.ClientError as e:
        return pipeline
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Error when calling client.get_pipeline".format(name, to_native(e)),
                         exception=traceback.format_exc())

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, type='str'),
        role_arn=dict(required=True, type='str'),
        artifact_store=dict(required=True, type='dict'),
        stages=dict(required=True, type='list'),
        version=dict(required=False, type='int'),
        state=dict(choices=['present', 'absent'],
                   default='present'),
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client_conn = boto3_conn(module, conn_type='client', resource='codepipeline', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    state = module.params.get('state')
    changed = False

    # Determine if the CodePipeline exists
    found_code_pipeline = describe_pipeline(client=client_conn, name=module.params['name'], version=module.params['version'], module=module)
    pipeline_result = {}

    if state == 'present':
        if 'pipeline' in found_code_pipeline:
            pipeline_result = update_pipeline(client=client_conn, pipeline_dict=found_code_pipeline['pipeline'], module=module)
            changed = True
        else:
            pipeline_result = create_pipeline(client=client_conn,
                                            name=module.params['name'],
                                            role_arn=module.params['role_arn'],
                                            artifact_store=module.params['artifact_store'],
                                            stages=module.params['stages'],
                                            version=module.params['version'],
                                            module=module)
            changed = True
    elif state == 'absent':
        if found_code_pipeline:
            pipeline_result = delete_pipeline(client=client_conn, name=module.params['name'], module=module)
            changed = True

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(pipeline_result))

if __name__ == '__main__':
    main()
