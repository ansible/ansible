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
module: ec2_vpc_facts
short_description: Describe vpcs given a set of filters 

'''

EXAMPLES = '''
# Simple example of filtering based on vpc_id
ec2_vpc_facts:
  region: "{{ region }}"
  filters:
    vpc-id: "{{vpc_id}}"
register: ec2_vpc_facts
'''


try:
    import json
    import botocore
    import boto3    
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def get_vpc_info(vpc):
    
   vpc_info = {'VpcId': vpc['VpcId'],
               'State': vpc['State'],
               'CidrBlock': vpc['CidrBlock'],
               'DhcpOptionsId': vpc['DhcpOptionsId'],
               'Tags': vpc['Tags'],
               'InstanceTenancy': vpc['InstanceTenancy'],
               'IsDefault': vpc['IsDefault']
               }
    
    
   return vpc_info

def list_vpcs(client, module):
    input_filters = module.params.get("filters")
    input_dryrun = module.params.get("DryRun")


    filters = []

    for key, value in input_filters.iteritems():
        filters.append({'Name': key, 'Values':[value]}) 

    all_vpcs = client.describe_vpcs(DryRun=input_dryrun, Filters=filters)
    all_vpcs_array = []
 
    for vpc in all_vpcs['Vpcs']:
        all_vpcs_array.append(get_vpc_info(vpc))
    
    module.exit_json(vpcs=all_vpcs_array)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters = dict(default=None, type='dict'),
            DryRun = dict(type='bool', default=False)
        )
    )
    
    module = AnsibleModule(argument_spec=argument_spec)

     # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='json and botocore/boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError, e:
        module.fail_json(msg="Can't authorize connection - "+str(e))

    # call your function here

    list_vpcs(connection, module)

    module.exit_json(changed=changed, vpc_facts_result=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()



