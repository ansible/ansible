#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_api_gateway
short_description: Manage AWS API Gateway APIs
description:
     - Allows for the management of API Gateway APIs
     - Normally you should give the api_id since there is no other
       stable guaranteed unique identifier for the API.  If you do
       not give api_id then a new API will be create each time
       this is run.
     - Beware that there are very hard limits on the rate that
       you can call API Gateway's REST API.  You may need to patch
       your boto.  See U(https://github.com/boto/boto3/issues/876)
       and discuss with your AWS rep.
     - swagger_file and swagger_text are passed directly on to AWS
       transparently whilst swagger_dict is an ansible dict which is
       converted to JSON before the API definitions are uploaded.
version_added: '2.4'
requirements: [ boto3 ]
options:
  api_id:
    description:
      - The ID of the API you want to manage.
    type: str
  state:
    description: Create or delete API Gateway.
    default: present
    choices: [ 'present', 'absent' ]
    type: str
  swagger_file:
    description:
      - JSON or YAML file containing swagger definitions for API.
        Exactly one of swagger_file, swagger_text or swagger_dict must
        be present.
    type: path
    aliases: ['src', 'api_file']
  swagger_text:
    description:
      - Swagger definitions for API in JSON or YAML as a string direct
        from playbook.
    type: str
  swagger_dict:
    description:
      - Swagger definitions API ansible dictionary which will be
        converted to JSON and uploaded.
    type: json
  stage:
    description:
      - The name of the stage the API should be deployed to.
    type: str
  deploy_desc:
    description:
      - Description of the deployment - recorded and visible in the
        AWS console.
    default: Automatic deployment by Ansible.
    type: str
  cache_enabled:
    description:
      - Enable API GW caching of backend responses. Defaults to false.
    type: bool
    default: false
    version_added: '2.10'
  cache_size:
    description:
      - Size in GB of the API GW cache, becomes effective when cache_enabled is true.
    choices: ['0.5', '1.6', '6.1', '13.5', '28.4', '58.2', '118', '237']
    type: str
    default: '0.5'
    version_added: '2.10'
  stage_variables:
    description:
      - ENV variables for the stage. Define a dict of key values pairs for variables.
    type: dict
    version_added: '2.10'
  stage_canary_settings:
    description:
      - Canary settings for the deployment of the stage.
      - 'Dict with following settings:'
      - 'percentTraffic: The percent (0-100) of traffic diverted to a canary deployment.'
      - 'deploymentId: The ID of the canary deployment.'
      - 'stageVariableOverrides: Stage variables overridden for a canary release deployment.'
      - 'useStageCache: A Boolean flag to indicate whether the canary deployment uses the stage cache or not.'
      - See docs U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/apigateway.html#APIGateway.Client.create_stage)
    type: dict
    version_added: '2.10'
  tracing_enabled:
    description:
      - Specifies whether active tracing with X-ray is enabled for the API GW stage.
    type: bool
    version_added: '2.10'
  endpoint_type:
    description:
      - Type of endpoint configuration, use C(EDGE) for an edge optimized API endpoint,
      - C(REGIONAL) for just a regional deploy or PRIVATE for a private API.
      - This will flag will only be used when creating a new API Gateway setup, not for updates.
    choices: ['EDGE', 'REGIONAL', 'PRIVATE']
    type: str
    default: EDGE
    version_added: '2.10'
author:
    - 'Michael De La Rue (@mikedlr)'
extends_documentation_fragment:
    - aws
    - ec2
notes:
   - A future version of this module will probably use tags or another
     ID so that an API can be create only once.
   - As an early work around an intermediate version will probably do
     the same using a tag embedded in the API name.

'''

EXAMPLES = '''
- name: Setup AWS API Gateway setup on AWS and deploy API definition
  aws_api_gateway:
    swagger_file: my_api.yml
    stage: production
    cache_enabled: true
    cache_size: '1.6'
    tracing_enabled: true
    endpoint_type: EDGE
    state: present

- name: Update API definition to deploy new version
  aws_api_gateway:
    api_id: 'abc123321cba'
    swagger_file: my_api.yml
    deploy_desc: Make auth fix available.
    cache_enabled: true
    cache_size: '1.6'
    endpoint_type: EDGE
    state: present

- name: Update API definitions and settings and deploy as canary
  aws_api_gateway:
    api_id: 'abc123321cba'
    swagger_file: my_api.yml
    cache_enabled: true
    cache_size: '6.1'
    canary_settings: { percentTraffic: 50.0, deploymentId: '123', useStageCache: True }
    state: present
'''

RETURN = '''
api_id:
    description: API id of the API endpoint created
    returned: success
    type: str
    sample: '0ln4zq7p86'
configure_response:
    description: AWS response from the API configure call
    returned: success
    type: dict
    sample: { api_key_source: "HEADER", created_at: "2020-01-01T11:37:59+00:00", id: "0ln4zq7p86" }
deploy_response:
    description: AWS response from the API deploy call
    returned: success
    type: dict
    sample: { created_date: "2020-01-01T11:36:59+00:00", id: "rptv4b", description: "Automatic deployment by Ansible." }
resource_actions:
    description: Actions performed against AWS API
    returned: always
    type: list
    sample: ["apigateway:CreateRestApi", "apigateway:CreateDeployment", "apigateway:PutRestApi"]
'''

import json

try:
    import botocore
except ImportError:
    # HAS_BOTOCORE taken care of in AnsibleAWSModule
    pass

import traceback
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (AWSRetry, camel_dict_to_snake_dict)


def main():
    argument_spec = dict(
        api_id=dict(type='str', required=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        swagger_file=dict(type='path', default=None, aliases=['src', 'api_file']),
        swagger_dict=dict(type='json', default=None),
        swagger_text=dict(type='str', default=None),
        stage=dict(type='str', default=None),
        deploy_desc=dict(type='str', default="Automatic deployment by Ansible."),
        cache_enabled=dict(type='bool', default=False),
        cache_size=dict(type='str', default='0.5', choices=['0.5', '1.6', '6.1', '13.5', '28.4', '58.2', '118', '237']),
        stage_variables=dict(type='dict', default={}),
        stage_canary_settings=dict(type='dict', default={}),
        tracing_enabled=dict(type='bool', default=False),
        endpoint_type=dict(type='str', default='EDGE', choices=['EDGE', 'REGIONAL', 'PRIVATE'])
    )

    mutually_exclusive = [['swagger_file', 'swagger_dict', 'swagger_text']]  # noqa: F841

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        mutually_exclusive=mutually_exclusive,
    )

    api_id = module.params.get('api_id')
    state = module.params.get('state')   # noqa: F841
    swagger_file = module.params.get('swagger_file')
    swagger_dict = module.params.get('swagger_dict')
    swagger_text = module.params.get('swagger_text')
    endpoint_type = module.params.get('endpoint_type')

    client = module.client('apigateway')

    changed = True   # for now it will stay that way until we can sometimes avoid change
    conf_res = None
    dep_res = None
    del_res = None

    if state == "present":
        if api_id is None:
            api_id = create_empty_api(module, client, endpoint_type)
        api_data = get_api_definitions(module, swagger_file=swagger_file,
                                       swagger_dict=swagger_dict, swagger_text=swagger_text)
        conf_res, dep_res = ensure_api_in_correct_state(module, client, api_id, api_data)
    if state == "absent":
        del_res = delete_rest_api(module, client, api_id)

    exit_args = {"changed": changed, "api_id": api_id}

    if conf_res is not None:
        exit_args['configure_response'] = camel_dict_to_snake_dict(conf_res)
    if dep_res is not None:
        exit_args['deploy_response'] = camel_dict_to_snake_dict(dep_res)
    if del_res is not None:
        exit_args['delete_response'] = camel_dict_to_snake_dict(del_res)

    module.exit_json(**exit_args)


def get_api_definitions(module, swagger_file=None, swagger_dict=None, swagger_text=None):
    apidata = None
    if swagger_file is not None:
        try:
            with open(swagger_file) as f:
                apidata = f.read()
        except OSError as e:
            msg = "Failed trying to read swagger file {0}: {1}".format(str(swagger_file), str(e))
            module.fail_json(msg=msg, exception=traceback.format_exc())
    if swagger_dict is not None:
        apidata = json.dumps(swagger_dict)
    if swagger_text is not None:
        apidata = swagger_text

    if apidata is None:
        module.fail_json(msg='module error - no swagger info provided')
    return apidata


def create_empty_api(module, client, endpoint_type):
    """
    creates a new empty API ready to be configured. The description is
    temporarily set to show the API as incomplete but should be
    updated when the API is configured.
    """
    desc = "Incomplete API creation by ansible aws_api_gateway module"
    try:
        awsret = create_api(client, name="ansible-temp-api", description=desc, endpoint_type=endpoint_type)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="creating API")
    return awsret["id"]


def delete_rest_api(module, client, api_id):
    """
    Deletes entire REST API setup
    """
    try:
        delete_response = delete_api(client, api_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="deleting API {0}".format(api_id))
    return delete_response


def ensure_api_in_correct_state(module, client, api_id, api_data):
    """Make sure that we have the API configured and deployed as instructed.

    This function first configures the API correctly uploading the
    swagger definitions and then deploys those.  Configuration and
    deployment should be closely tied because there is only one set of
    definitions so if we stop, they may be updated by someone else and
    then we deploy the wrong configuration.
    """

    configure_response = None
    try:
        configure_response = configure_api(client, api_id, api_data=api_data)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        module.fail_json_aws(e, msg="configuring API {0}".format(api_id))

    deploy_response = None

    stage = module.params.get('stage')
    if stage:
        try:
            deploy_response = create_deployment(client, api_id, **module.params)
        except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
            msg = "deploying api {0} to stage {1}".format(api_id, stage)
            module.fail_json_aws(e, msg)

    return configure_response, deploy_response


retry_params = {"tries": 10, "delay": 5, "backoff": 1.2}


@AWSRetry.backoff(**retry_params)
def create_api(client, name=None, description=None, endpoint_type=None):
    return client.create_rest_api(name="ansible-temp-api", description=description, endpointConfiguration={'types': [endpoint_type]})


@AWSRetry.backoff(**retry_params)
def delete_api(client, api_id):
    return client.delete_rest_api(restApiId=api_id)


@AWSRetry.backoff(**retry_params)
def configure_api(client, api_id, api_data=None, mode="overwrite"):
    return client.put_rest_api(restApiId=api_id, mode=mode, body=api_data)


@AWSRetry.backoff(**retry_params)
def create_deployment(client, rest_api_id, **params):
    canary_settings = params.get('stage_canary_settings')

    if canary_settings and len(canary_settings) > 0:
        result = client.create_deployment(
            restApiId=rest_api_id,
            stageName=params.get('stage'),
            description=params.get('deploy_desc'),
            cacheClusterEnabled=params.get('cache_enabled'),
            cacheClusterSize=params.get('cache_size'),
            variables=params.get('stage_variables'),
            canarySettings=canary_settings,
            tracingEnabled=params.get('tracing_enabled')
        )
    else:
        result = client.create_deployment(
            restApiId=rest_api_id,
            stageName=params.get('stage'),
            description=params.get('deploy_desc'),
            cacheClusterEnabled=params.get('cache_enabled'),
            cacheClusterSize=params.get('cache_size'),
            variables=params.get('stage_variables'),
            tracingEnabled=params.get('tracing_enabled')
        )

    return result


if __name__ == '__main__':
    main()
