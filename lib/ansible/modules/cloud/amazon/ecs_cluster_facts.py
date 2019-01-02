#!/usr/bin/python

# Copyright: (c) 2018, Rob White (@wimnat)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ecs_cluster_facts
short_description: Get AWS ECS cluster facts.
description:
    - Get AWS ECS cluster facts as well as facts of the ec2 instances assigned to those clusters.
version_added: "2.8"
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  clusters:
    description:
      - A list of up to 100 cluster names or full cluster Amazon Resource Name (ARN) entries. If you do not specify a cluster, the default cluster is assumed.
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Query for facts of the default cluster
- ecs_cluster_facts:

# Query for facts of the cluster 'mycluster1' and 'mycluster2'
- ecs_cluster_facts:
    clusters:
      - mycluster1
      - mycluster2

'''

RETURN = '''
active_services_count:
  description: The number of services that are running on the cluster in an ACTIVE state. You can view these services with ListServices.
  returned: always
  type: int
  sample: 5
cluster_arn:
  description: The Amazon Resource Name (ARN) that identifies the cluster.
  returned: always
  type: string
  sample: arn:aws:ecs:us-west-2:172139249013:cluster/test-cluster-mfshcdok
cluster_name:
  description: A user-generated string that you use to identify your cluster.
  returned: always
  type: string
  sample: test-cluster-mfshcdok
instances:
  description: A list of dicts that contain detail about each instance of the cluster.
  returned: always
  type: string
  sample: []
pending_tasks_count:
  description: The number of tasks in the cluster that are in the PENDING state.
  returned: always
  type: int
  sample: 0
registered_container_instances_count: 
  description: The number of container instances registered into the cluster.
  returned: always
  type: int
  sample: 5
running_tasks_count:
  description: The number of tasks in the cluster that are in the RUNNING state.
  returned: always
  type: int
  sample: 15
statistics:
  description: Additional information about your clusters that are separated by launch type.
  returned: always
  type: list
  sample: []
status:
  description: The status of the cluster. The valid values are ACTIVE or INACTIVE.
  returned: always
  type: string
  sample: ACTIVE
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

# Non-ansible imports
try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass


def _get_ecs_clusters(connection, module, clusters):
    """
    Get one or more ECS cluster facts based on name. If not found, return None.

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param clusters: A list of ECS clusters to describe
    :return: boto3 ECS cluster dict or None if not found
    """

    try:
        response = connection.describe_clusters(clusters=clusters)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)

    if len(response['failures']) > 0:
        module.fail_json(msg="One or more clusters could not be found.", failures=response['failures'])
    else:
        return response['clusters']


def _list_ecs_cluster_instances(connection, module, cluster_name):
    """
    Get a list of container instances of a particular ECS cluster

    :param connection: AWS boto3 ecs connection
    :param module: Ansible module
    :param cluster_name: name of ECS cluster to lookup instances for
    :return: full list of instance ARNs attached to the cluster
    """

    try:
        ecs_cluster_instances_paginator = connection.get_paginator('list_container_instances')
        return ecs_cluster_instances_paginator.paginate(cluster=cluster_name).build_full_result()['containerInstanceArns']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


def _describe_ecs_cluster_instance(connection, module, cluster_name, instance_arn):
    """
    Describe an ECS cluster instance by ARN. This will only ever return one instance result.

    :param connection: AWS boto3 ecs connection
    :param module: Ansible module
    :param cluster_name: ECS cluster name
    :param instance_arn: ECS instance ARN
    :return: the first (and should be only) result - a dict containing ECS cluster instance detail
    """

    try:
        return connection.describe_container_instances(cluster=cluster_name, containerInstances=[instance_arn])['containerInstances'][0]
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)


def get_cluster_facts(connection, module):
    """
    Get one or more ECS cluster facts based on name. As well as cluster facts it will also
    get facts of the underlying cluster instances.

    :param connection: AWS boto3 ecs connection
    :param module: Ansible module
    """

    list_of_clusters = _get_ecs_clusters(connection, module, module.params.get('clusters'))

    # For each cluster, get the list of instances and then describe each one appending to the result
    for cluster in list_of_clusters:
        cluster['instances'] = []
        cluster_instance_arn_list = _list_ecs_cluster_instances(connection, module, cluster['clusterName'])
        for cluster_instance_arn in cluster_instance_arn_list:
            cluster['instances'].append(_describe_ecs_cluster_instance(connection, module, cluster['clusterName'], cluster_instance_arn))

    # Snake case the cluster results
    list_of_snaked_clusters = list()
    for cluster in list_of_clusters:
        list_of_snaked_clusters.append(camel_dict_to_snake_dict(cluster))

    module.exit_json(clusters=list_of_snaked_clusters)
    

def main():

    argument_spec = (
        dict(
            clusters=dict(type='list', default=[])
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    connection = module.client('ecs')

    get_cluster_facts(connection, module)

if __name__ == '__main__':
    main()
