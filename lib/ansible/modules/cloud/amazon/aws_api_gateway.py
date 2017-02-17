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
                    'version': '0.1'}

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
author:
    - 'Michael De La Rue (@mikedlr)'
extends_documentation_fragment:
    - aws
    - ec2
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

from ansible.module_utils.basic import AnsibleModule, traceback
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, camel_dict_to_snake_dict

import os

try:
    import botocore
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

try:
    import boto3 # noqua: F401
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            api_id=dict(type='str', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            swagger_file=dict(type='str', default=None, aliases=['src', 'api_file']),
            swagger_dict=dict(type='json', default=None),
            swagger_text=dict(type='str', default=None),
            stage=dict(type='str', default=None),
            deploy_desc=dict(type='str', default=None),
        )
    )

    mutually_exclusive = [['swagger_file', 'swagger_dict', 'swagger_text' ]]

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,  )   # TODO !!!`

    api_id = module.params.get('api_id')
    state = module.params.get('state')
    try:
        swagger_file = os.path.expanduser(module.params.get('swagger_file'))
    except AttributeError:
        swagger_file=None
    swagger_dict = module.params.get('swagger_dict')
    swagger_text = module.params.get('swagger_text')
    stage= module.params.get('stage')
    deploy_desc= module.params.get('deploy_desc')

#    check_mode = module.check_mode
    changed = False

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install it')

    if not HAS_BOTOCORE:
        module.fail_json(msg='Python module "botocore" is missing, please install it')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg='region must be specified')

    try:
        client = boto3_conn(module, conn_type='client', resource='apigateway',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.ValidationError) as e:
        msg="Incorrect AWS configuration"
        module.fail_json(msg=msg, exception=traceback.format_exc())
    except (botocore.exceptions.ClientError) as e:
        msg="Client side failure connecting to AWS API"
        module.fail_json(msg=msg, exception=traceback.format_exc())
    except Exception as e:
        msg="Unexpected exception configuring AWS API connection"
        module.fail_json(msg=msg, exception=traceback.format_exc())

    if not api_id:
        desc="Incomplete API creation by ansible aws_api_gateway module"
        awsret=client.create_rest_api(name="ansible-temp-api", description=desc)
        api_id=awsret["id"]

    apidata=None
    if swagger_file:
        try:
            with open(swagger_file) as f:
                apidata=f.read()
        except Exception as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc())
    if swagger_dict:
        apidata = json.dumps(swagger_dict)
    if swagger_text:
        apidata = swagger_text

    if apidata is None:
        module.fail_json(msg='module error - failed to get API data')

    try:
        create_response=client.put_rest_api(body=apidata, restApiId=api_id, mode="overwrite")
    except botocore.exceptions.ClientError as e:
        msg="Client side error configuring api {} - check definitions".format(api_id)
        module.fail_json(msg=msg, exception=traceback.format_exc())
    except botocore.exceptions.EndpointConnectionError as e:
        msg="Connectivity problem configuring api {}. Check network.".format(api_id)
        module.fail_json(msg=msg, exception=traceback.format_exc())
    except botocore.exceptions.NoCredentialsError as e:
        msg="AWS credentials missing configuring api {}. set up credentials.".format(api_id)
        module.fail_json(msg=msg, exception=traceback.format_exc())
    except Exception as e:
        msg="Unexpected exception configuring api {}".format(api_id)
        module.fail_json(msg=msg, exception=traceback.format_exc())

    changed=True

    if stage:
        if deploy_desc is None:
            deploy_desc = "Automatic deployment by Ansible."
        try:
            deploy_response=client.create_deployment(restApiId=api_id, stageName=stage,
                                                     description=deploy_desc)
        except (botocore.exceptions.ClientError) as e:
            msg="Client side error deploying api {} to stage {}".format(api_id, stage)
            module.fail_json(msg=msg, exception=traceback.format_exc())
        except botocore.exceptions.EndpointConnectionError as e:
            msg="Connectivity problem deploying api {} to stage {}".format(api_id, stage)
            module.fail_json(msg=msg, exception=traceback.format_exc())
        except Exception as e:
            msg="Unexpected exception deploying api {} to stage {}".format(api_id, stage)
            module.fail_json(msg=msg, exception=traceback.format_exc())
        module.exit_json(changed=changed, api_id=api_id,
                     create_response=camel_dict_to_snake_dict(create_response),
                     deploy_response=camel_dict_to_snake_dict(deploy_response))
    else:
            module.exit_json(changed=changed, api_id=api_id,
                     create_response=camel_dict_to_snake_dict(create_response))

if __name__ == '__main__':
    main()
