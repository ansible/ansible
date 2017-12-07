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
module: ec2_vol_facts
short_description: Gather facts about ec2 volumes in AWS
description:
    - Gather facts about ec2 volumes in AWS
version_added: "2.1"
author: "Rob White (@wimnat)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
        See U(http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html) for possible filters.
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

import traceback

try:
    import boto.ec2
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import connect_to_aws, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils._text import to_native


def get_volume_info(volume):

    attachment = volume.attach_data

    volume_info = {
        'create_time': volume.create_time,
        'id': volume.id,
        'encrypted': volume.encrypted,
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
            filters=dict(default=None, type='dict')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, Exception) as e:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_volumes(connection, module)


if __name__ == '__main__':
    main()
