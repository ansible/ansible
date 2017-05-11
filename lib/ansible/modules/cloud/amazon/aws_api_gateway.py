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


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: aws_api_gateway
short_description: Manage AWS API Gateway APIs
description:
     - Allows for the management of API Gatway APIs
     - Normally you should give the api_id since there is no other
       stable guaranteed unique identifier for the API.  If you do
       not give api_id then a new API will be create each time
       this is run.
     - Beware that there are very hard limits on the rate that
       you can call API Gateway's REST API.  You may need to patch
       your boto.  See https://github.com/boto/boto3/issues/876
       and discuss with your AWS rep.
     - swagger_file and swagger_text are passed directly on to AWS
       transparently whilst swagger_dict is an ansible dict which is
       converted to JSON before the API definitions are uploaded.
version_added: '2.3'
requirements: [ boto3 ]
options:
  api_id:
    description:
      - The ID of the API you want to manage
    required: false
  state:
    description:
      - NOT IMPLEMENTED Create or delete API - currently we always create
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  swagger_file:
    description:
      - JSON or YAML file containing swagger definitions for API
    required: false
  swagger_text:
    description:
      - Swagger definitions for API in JSON or YAML as a string direct from playbook
    required: false
  swagger_dict:
    description:
      - Swagger definitions API ansible dictionary which will be converted to JSON and uploaded
    required: false
  stage:
    description:
      - stage API should be deployed to
    required: false
  deploy_desc:
    description:
      - Description of the deployment - recorded and visible in the AWS console.  
    required: false
author:
    - 'Michael De La Rue (@mikedlr)'
extends_documentation_fragment:
    - aws
notes:
   - a future version of this module will probably use tags or another
     ID so that an API can be create only once.
   - as an early work around an intermediate version will probably do
     the same using a tag embedded in the API name.

'''

EXAMPLES = '''
# Update API resources for development
tasks:
- name: update API
  aws_api_gateway:
    api_id: 'abc123321cba'
    state: present
    swagger_file: my_api.yml

# update definitions and deploy API to production
tasks:
- name: deploy API
  aws_api_gateway:
    api_id: 'abc123321cba'
    state: present
    swagger_file: my_api.yml
    stage: production
    deploy_desc: Make auth fix available.
'''

RETURN = '''
output:
  description: the data returned by put_restapi in boto3
  returned: success
  type: dict
  sample:
    'data':
      {
          "id": "abc123321cba",
          "name": "MY REST API",
          "createdDate": 1484233401
      }
'''

import json
from ansible.module_utils.basic import AnsibleModule, traceback
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, camel_dict_to_snake_dict, AWSRetry

from ansible.module_utils.ec2 import HAS_BOTO3

try:
    import botocore
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            api_id=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            swagger_file=dict(type='path', default=None, aliases=['src', 'api_file']),
            swagger_dict=dict(type='json', default=None),
            swagger_text=dict(type='str', default=None),
            stage=dict(type='str', default=None),
            deploy_desc=dict(type='str', default=None),
        )
    )

    mutually_exclusive = [['swagger_file', 'swagger_dict', 'swagger_text']]  # noqa: F841

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    api_id = module.params.get('api_id')
    state = module.params.get('state')   # noqa: F841
    swagger_file = module.params.get('swagger_file')
    swagger_dict = module.params.get('swagger_dict')
    swagger_text = module.params.get('swagger_text')
    stage = module.params.get('stage')
    deploy_desc = module.params.get('deploy_desc')

#    check_mode = module.check_mode
    changed = False

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install boto3')

    if not HAS_BOTOCORE:
        module.fail_json(msg='Python module "botocore" is missing, please install it')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    try:
        client = boto3_conn(module, conn_type='client', resource='apigateway',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoRegionError:
        module.fail_json(msg="Region must be specified as a parameter, in AWS_DEFAULT_REGION environment variable or in boto configuration file")
    except (botocore.exceptions.ValidationError, botocore.exceptions.ClientError) as e:
        fail_json_aws(module, e, msg="connecting to AWS")

    if not api_id:
        desc = "Incomplete API creation by ansible aws_api_gateway module"
        awsret = create_api(client, name="ansible-temp-api", description=desc)
        api_id = awsret["id"]

    apidata = None
    if swagger_file is not None:
        try:
            with open(swagger_file) as f:
                apidata = f.read()
        except Exception as e:
            module.fail_json(msg="Failed trying to read swagger file " + str(swagger_file)
                             + ":" + str(e), exception=traceback.format_exc())
    if swagger_dict is not None:
        apidata = json.dumps(swagger_dict)
    if swagger_text is not None:
        apidata = swagger_text

    if apidata is None:
        module.fail_json(msg='module error - failed to get API data')

    try:
        create_response = configure_api(client, apidata=apidata, api_id=api_id)
    except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
        fail_json_aws(module, e, msg="configuring api {}".format(api_id))

    changed = True

    if stage:
        try:
            deploy_response = create_deployment(client, api_id=api_id, stage=stage,
                                                description=deploy_desc)
        except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as e:
            msg = "deploying api {} to stage {}".format(api_id, stage)
            fail_json_aws(module, e, msg)
        module.exit_json(changed=changed, api_id=api_id,
                         create_response=camel_dict_to_snake_dict(create_response),
                         deploy_response=camel_dict_to_snake_dict(deploy_response))
    else:
            module.exit_json(changed=changed, api_id=api_id,
                             create_response=camel_dict_to_snake_dict(create_response))


retry_params = {"tries": 10, "delay": 5, "backoff": 1.2}


# There is a PR open to merge fail_json_aws this into the standard module code;
# see https://github.com/ansible/ansible/pull/23882
def fail_json_aws(module, exception, msg=None):
    """call fail_json with processed exception
    function for converting exceptions thrown by AWS SDK modules,
    botocore, boto3 and boto, into nice error messages.
    """
    last_traceback = traceback.format_exc()
    if msg is not None:
        message = '{}: {}'.format(msg, exception.message)
    else:
        message = exception.message

    try:
        response = exception.response
    except AttributeError:
        response = None

    if response is None:
        module.fail_json(msg=message, traceback=last_traceback)
    else:
        module.fail_json(msg=message, traceback=last_traceback,
                         **camel_dict_to_snake_dict(response))


@AWSRetry.backoff(**retry_params)
def create_api(client, name=None, description=None):
    return client.create_rest_api(name="ansible-temp-api", description=description)


@AWSRetry.backoff(**retry_params)
def configure_api(client, apidata=None, api_id=None, mode="overwrite"):
    return client.put_rest_api(body=apidata, restApiId=api_id, mode=mode)


@AWSRetry.backoff(**retry_params)
def create_deployment(client, api_id=None, stage=None, description=None):
    # we can also get None as an argument so we don't do this as a defult
    if description is None:
        description = "Automatic deployment by Ansible."
    return client.create_deployment(restApiId=api_id, stageName=stage, description=description)


if __name__ == '__main__':
    main()
