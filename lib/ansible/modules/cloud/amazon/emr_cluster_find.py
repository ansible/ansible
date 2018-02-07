#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: emr_cluster_find
short_description:  Find AWS Elastic Map Reduce
version_added: "2.6"
description:
  - return a list of Cluster EMR based on name and state
  - results can be sorted
  - It depends on boto3
options:
  region:
    description:
      - region where this module will find EMR
  state:
    description:
      - looking for EMR according with this Status,
        can be one of these (starting|bootstrapping|running|waiting|terminating|terminated)
    required: true
  name_regex:
    description:
      - regexp used by matched the EMR Cluster Name
        if this option is blank, all cluster will be matched
  limit:
    description:
      - limit the number of occours is return
  sort_order:
    description:
      - define results order is ascending or descending, default is ascending
author:
  - Wellington Moreira Ramos (@wmaramos)
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: Looking for EMR based on status and name
  emr_cluster_find:
    name_regex: '^emr-test-name'
    region: us-east-1
    state: running

- name: Looking for EMR based on name
  emr_cluster_find:
    name_regex: '`emr-test-name`' # in this case regexp will be *.emr-test-name.*
    region: us-east-1

- name: Return all EMR with status RUNNING
  emr_cluster_find:
    status: running
    region: us-east-1
'''

RETURN = '''
# For more information see http://boto3.readthedocs.io/en/latest/reference/services/emr.html#EMR.Client.list_clusters
---
results:
  description: dictionary containg all cluster settings see link above for more information
  returned: success
  type: complex
  contains:
    id:
      description: The Cluster ID from EMR
      type: str
      sample: j-12CK7ZJ37B5YA
    name:
      description: name of EMR Cluster
      type: str
      sample: emr-test-name
    status:
      description: details about the current status of the cluster
      type: dict
'''

try:
    from botocore.exception import ClientError
except ImportError:
    pass  # will be picked up from imported HAS_BOTO3

import re
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, get_aws_connection_info
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict


def find_emr_clusters(client, module):
    name_regex = module.params.get('name_regex')
    state = module.params.get('state').upper()
    limit = module.params.get('limit')
    sort_order = module.params.get('sort_order')

    resource = client.list_clusters(ClusterStates=[state])

    resource = camel_dict_to_snake_dict(resource)

    if name_regex:
        results = [emr for emr in resource['clusters'] if re.compile(name_regex).match(emr['name'])]
    else:
        results = [emr for emr in resource['clusters']]

    results.sort(key=lambda e: e['status']['timeline']['creation_date_time'], reverse=(sort_order == 'descending'))

    if limit:
        results = results[:int(limit)]

    return results


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name_regex=dict(required=False),
            state=dict(required=True),
            limit=dict(required=False, type='int'),
            sort_order=dict(required=False, default='ascending', choices=['ascending', 'descending']),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='emr', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    results = find_emr_clusters(client, module)
    module.exit_json(changed=True, results=results)

if __name__ == '__main__':
    main()
