#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ec2_eni_facts
short_description: Gather facts about ec2 ENI interfaces in AWS
description:
    - Gather facts about ec2 ENI interfaces in AWS
version_added: "2.0"
author: "Rob White (@wimnat)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeNetworkInterfaces.html) for possible filters.
    required: false
    default: null

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all ENIs
- ec2_eni_facts:

# Gather facts about a particular ENI
- ec2_eni_facts:
    filters:
      network-interface-id: eni-xxxxxxx

'''

try:
    import boto.ec2
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

def get_eni_info(interface):

    # Private addresses
    private_addresses = []
    for ip in interface.private_ip_addresses:
        private_addresses.append({ 'private_ip_address': ip.private_ip_address, 'primary_address': ip.primary })

    interface_info = {'id': interface.id,
                      'subnet_id': interface.subnet_id,
                      'vpc_id': interface.vpc_id,
                      'description': interface.description,
                      'owner_id': interface.owner_id,
                      'status': interface.status,
                      'mac_address': interface.mac_address,
                      'private_ip_address': interface.private_ip_address,
                      'source_dest_check': interface.source_dest_check,
                      'groups': dict((group.id, group.name) for group in interface.groups),
                      'private_ip_addresses': private_addresses
                      }

    if interface.attachment is not None:
        interface_info['attachment'] = {'attachment_id': interface.attachment.id,
                                        'instance_id': interface.attachment.instance_id,
                                        'device_index': interface.attachment.device_index,
                                        'status': interface.attachment.status,
                                        'attach_time': interface.attachment.attach_time,
                                        'delete_on_termination': interface.attachment.delete_on_termination,
                                        }

    return interface_info


def list_eni(connection, module):

    filters = module.params.get("filters")
    interface_dict_array = []

    try:
        all_eni = connection.get_all_network_interfaces(filters=filters)
    except BotoServerError as e:
        module.fail_json(msg=e.message)

    for interface in all_eni:
        interface_dict_array.append(get_eni_info(interface))

    module.exit_json(interfaces=interface_dict_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters = dict(default=None, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError), e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    list_eni(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
