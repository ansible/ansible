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
module: ec2_vol_facts
short_description: Gather facts about ec2 volumes in AWS
description:
    - Gather facts about ec2 volumes in AWS
version_added: "2.1"
author: "Rob White (@wimnat)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html) for possible filters.
    required: false
    default: null
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Gather facts about all volumes
- ec2_vol_facts:

# Gather facts about a particular volume using volume ID
- ec2_vol_facts:
    filters:
      volume-id: vol-00112233

# Gather facts about any volume with a tag key Name and value Example
- ec2_vol_facts:
    filters:
      "tag:Name": Example

# Gather facts about any volume that is attached
- ec2_vol_facts:
    filters:
      attachment.status: attached

'''

# TODO: Disabled the RETURN as it was breaking docs building. Someone needs to
# fix this
RETURN = '''# '''

try:
    import boto.ec2
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import connect_to_aws, ec2_argument_spec, get_aws_connection_info


def get_volume_info(volume):

    attachment = volume.attach_data

    volume_info = {
                    'create_time': volume.create_time,
                    'id': volume.id,
                    'iops': volume.iops,
                    'size': volume.size,
                    'snapshot_id': volume.snapshot_id,
                    'status': volume.status,
                    'type': volume.type,
                    'zone': volume.zone,
                    'region': volume.region.name,
                    'attachment_set': {
                        'attach_time': attachment.attach_time,
                        'device': attachment.device,
                        'instance_id': attachment.instance_id,
                        'status': attachment.status
                    },
                    'tags': volume.tags
                }
    
    return volume_info

def list_ec2_volumes(connection, module):

    filters = module.params.get("filters")
    volume_dict_array = []

    try:
        all_volumes = connection.get_all_volumes(filters=filters)
    except BotoServerError as e:
        module.fail_json(msg=e.message)

    for volume in all_volumes:
        volume_dict_array.append(get_volume_info(volume))

    module.exit_json(volumes=volume_dict_array)


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
        except (boto.exception.NoAuthHandlerFound, StandardError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_volumes(connection, module)


if __name__ == '__main__':
    main()
