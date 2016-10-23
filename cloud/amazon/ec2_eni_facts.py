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

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (AnsibleAWSError,
        ansible_dict_to_boto3_filter_list, boto3_conn,
        boto3_tag_list_to_ansible_dict, camel_dict_to_snake_dict,
        connect_to_aws, ec2_argument_spec, get_aws_connection_info)


def list_ec2_snapshots_boto3(connection, module):

    if module.params.get("filters") is None:
        filters = []
    else:
        filters = ansible_dict_to_boto3_filter_list(module.params.get("filters"))

    try:
        network_interfaces_result = connection.describe_network_interfaces(Filters=filters)
    except (ClientError, NoCredentialsError) as e:
        module.fail_json(msg=e.message)

    # Turn the boto3 result in to ansible_friendly_snaked_names
    snaked_network_interfaces_result = camel_dict_to_snake_dict(network_interfaces_result)
    for network_interfaces in snaked_network_interfaces_result['network_interfaces']:
        network_interfaces['tag_set'] = boto3_tag_list_to_ansible_dict(network_interfaces['tag_set'])

    module.exit_json(**snaked_network_interfaces_result)


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

    if hasattr(interface, 'publicDnsName'):
        interface_info['association'] = {'public_ip_address': interface.publicIp,
                                         'public_dns_name': interface.publicDnsName,
                                         'ip_owner_id': interface.ipOwnerId
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

    if HAS_BOTO3:
        region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

        if region:
            connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
        else:
            module.fail_json(msg="region must be specified")

        list_ec2_snapshots_boto3(connection, module)
    else:
        region, ec2_url, aws_connect_params = get_aws_connection_info(module)

        if region:
            try:
                connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
            except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
                module.fail_json(msg=str(e))
        else:
            module.fail_json(msg="region must be specified")

        list_eni(connection, module)


if __name__ == '__main__':
    main()
