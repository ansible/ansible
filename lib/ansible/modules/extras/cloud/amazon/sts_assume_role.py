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
module: sts_assume_role 
short_description: assume a role in AWS account and obtain temporary credentials.
description:
    - call AWS STS (Security Token Service) to assume a role in AWS account and obtain temporary credentials. This module has a dependency on python-boto.
      For details on base AWS API reference http://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
version_added: "1.7"
options:
  role_arn:
    description:
      - The Amazon Resource Name (ARN) of the role that the caller is assuming (http://docs.aws.amazon.com/IAM/latest/UserGuide/Using_Identifiers.html#Identifiers_ARNs) 
    required: true
    aliases: []
  role_session_name:
    description:
      - Name of the role's session - will be used by CloudTrail
    required: true
    aliases: []
  policy:
    description:
      - Supplemental policy to use in addition to assumed role's policies. 
    required: false
    default: null
    aliases: []
  duration_seconds:
    description:
      - The duration, in seconds, of the role session. The value can range from 900 seconds (15 minutes) to 3600 seconds (1 hour). By default, the value is set to 3600 seconds. 
    required: false
    default: null
    aliases: []
  external_id:
    description:
      - A unique identifier that is used by third parties to assume a role in their customers' accounts. 
    required: false
    default: null
    aliases: []
  mfa_serial_number:
    description:
      - he identification number of the MFA device that is associated with the user who is making the AssumeRole call. 
    required: false
    default: null
    aliases: []
  mfa_token:
    description:
      - The value provided by the MFA device, if the trust policy of the role being assumed requires MFA. 
    required: false
    default: null
    aliases: []

author: Boris Ekelchik
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Basic example of assuming a role
tasks:
- name: assume a role in account 123456789012
  sts_assume_role: role_arn="arn:aws:iam::123456789012:role/someRole" session_name="someRoleSession"

- name: display temporary credentials
  debug: "temporary credentials for the assumed role are {{ ansible_temp_credentials }}"
  
- name: use temporary credentials for tagging an instance in account 123456789012 
  ec2_tag: resource=i-xyzxyz01 region=us-west-1 state=present
    args:
      aws_access_key: "{{ ansible_temp_credentials.access_key }}"
      aws_secret_key: "{{ ansible_temp_credentials.secret_key }}"
      security_token: "{{ ansible_temp_credentials.session_token }}"
    
      tags:
        Test: value
'''

import sys
import time

try:
    import boto.sts
    
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def sts_connect(module):

    """ Return an STS connection"""

    region, ec2_url, boto_params = get_aws_connection_info(module)

    # If we have a region specified, connect to its endpoint.
    if region:
        try:
            sts = connect_to_aws(boto.sts, region, **boto_params)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg=str(e))
    # Otherwise, no region so we fallback to connect_sts method
    else:
        try:
            sts = boto.connect_sts(**boto_params)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg=str(e))


    return sts

def assumeRole():
    data = sts.assume_role()
    return data

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            role_arn = dict(required=True),
            role_session_name = dict(required=True),
            duraction_seconds = dict(),
            external_id = dict(),
            policy = dict(),
            mfa_serial_number = dict(),
            mfa_token = dict(),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    role_arn = module.params.get('role_arn')
    role_session_name = module.params.get('role_session_name')
    policy = module.params.get('policy')
    duraction_seconds = module.params.get('duraction_seconds')
    external_id = module.params.get('external_id')
    mfa_serial_number = module.params.get('mfa_serial_number')
    mfa_token = module.params.get('mfa_token')
  
    sts = sts_connect(module)
    
    temp_credentials = {}
    
    try:
        temp_credentials = sts.assume_role(role_arn, role_session_name, policy, duraction_seconds,
                                           external_id, mfa_serial_number, mfa_token).credentials.__dict__
    except boto.exception.BotoServerError, e:
        module.fail_json(msg='Unable to assume role {0}, error: {1}'.format(role_arn, e))
    result = dict(changed=False, ansible_facts=dict(ansible_temp_credentials=temp_credentials))

    module.exit_json(**result)
    
# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
