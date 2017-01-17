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
module: api-gateway
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
version_added: '2.2'
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
  api_file:
    description:
      - JSON or YAML file containing swagger definitions for API
    required: true
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
  lambda:
    api_id: 'abc123321cba'
    state: present
    api_file: my_api.yml

# update definitions and deploy API to production
tasks:
- name: deploy API
  lambda:
    api_id: 'abc123321cba'
    state: present
    api_file: my_api.yml
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

# Import from Python standard library

try:
    import botocore
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        api_id=dict(type='str', required=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        api_file=dict(type='str', default=None, aliases=['src']),
        stage=dict(type='str', default=None),
        deploy_desc=dict(type='str', default=None),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False,  ) #TODO !!!`

    api_id = module.params.get('api_id')
    state = module.params.get('state').lower()
    api_file = module.params.get('api_file')
    stage= module.params.get('stage')
    deploy_desc= module.params.get('deploy_desc')

#    check_mode = module.check_mode
    changed = False

    if not HAS_BOTOCORE:
        module.fail_json(msg='Python module "botocore" is missing, please install it')

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install it')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg='region must be specified')

    try:
        client = boto3_conn(module, conn_type='client', resource='apigateway',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.ValidationError) as e:
        module.fail_json(msg=str(e))

    if not api_id:
        desc="Incomplete API creation by ansible api_gateway module"
        awsret=client.create_rest_api(name="ansible-temp-api", description=desc)
        api_id=awsret["id"]

    with open(api_file) as f:
        apidata=f.read()

    create_response=client.put_rest_api(body=apidata, restApiId=api_id, mode="overwrite")

    if deploy_desc == None:
        deploy_desc = "Automatic deployment."
    if stage: 
        deploy_response=client.create_deployment(restApiId=api_id, stageName=stage,
                                                 description=deploy_desc)
    changed=True
    module.exit_json(changed=changed, api_id=api_id,
                     create_response=camel_dict_to_snake_dict(create_response),
                     deploy_response=camel_dict_to_snake_dict(deploy_response))

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
