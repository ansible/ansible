#!/usr/bin/python

# Copyright 2014 Jens Carl, Hothead Games Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
author:
  - "Jens Carl (@j-carl), Hothead Games Inc."
  - "Rafael Driutti (@rafaeldriutti)"
module: redshift
version_added: "2.2"
short_description: create, delete, or modify an Amazon Redshift instance
description:
  - Creates, deletes, or modifies amazon Redshift cluster instances.
options:
  command:
    description:
      - Specifies the action to take.
    required: true
    choices: [ 'create', 'facts', 'delete', 'modify' ]
  identifier:
    description:
      - Redshift cluster identifier.
    required: true
  node_type:
    description:
      - The node type of the cluster. Must be specified when command=create.
    choices: ['ds1.xlarge', 'ds1.8xlarge', 'ds2.xlarge', 'ds2.8xlarge', 'dc1.large', 'dc1.8xlarge', 'dc2.large', 'dc2.8xlarge',
              'dw1.xlarge', 'dw1.8xlarge', 'dw2.large', 'dw2.8xlarge']
  username:
    description:
      - Master database username. Used only when command=create.
  password:
    description:
      - Master database password. Used only when command=create.
  cluster_type:
    description:
      - The type of cluster.
    choices: ['multi-node', 'single-node' ]
    default: 'single-node'
  db_name:
    description:
      - Name of the database.
  availability_zone:
    description:
      - availability zone in which to launch cluster
    aliases: ['zone', 'aws_zone']
  number_of_nodes:
    description:
      - Number of nodes. Only used when cluster_type=multi-node.
  cluster_subnet_group_name:
    description:
      - which subnet to place the cluster
    aliases: ['subnet']
  cluster_security_groups:
    description:
      - in which security group the cluster belongs
    aliases: ['security_groups']
  vpc_security_group_ids:
    description:
      - VPC security group
    aliases: ['vpc_security_groups']
  skip_final_cluster_snapshot:
    description:
      - skip a final snapshot before deleting the cluster. Used only when command=delete.
    aliases: ['skip_final_snapshot']
    default: 'no'
    version_added: "2.4"
  final_cluster_snapshot_identifier:
    description:
      - identifier of the final snapshot to be created before deleting the cluster. If this parameter is provided,
        final_cluster_snapshot_identifier must be false. Used only when command=delete.
    aliases: ['final_snapshot_id']
    version_added: "2.4"
  preferred_maintenance_window:
    description:
      - maintenance window
    aliases: ['maintance_window', 'maint_window']
  cluster_parameter_group_name:
    description:
      - name of the cluster parameter group
    aliases: ['param_group_name']
  automated_snapshot_retention_period:
    description:
      - period when the snapshot take place
    aliases: ['retention_period']
  port:
    description:
      - which port the cluster is listening
  cluster_version:
    description:
      - which version the cluster should have
    aliases: ['version']
    choices: ['1.0']
  allow_version_upgrade:
    description:
      - flag to determinate if upgrade of version is possible
    aliases: ['version_upgrade']
    default: 'yes'
  publicly_accessible:
    description:
      - if the cluster is accessible publicly or not
    default: 'no'
  encrypted:
    description:
      -  if the cluster is encrypted or not
    default: 'no'
  elastic_ip:
    description:
      - if the cluster has an elastic IP or not
  new_cluster_identifier:
    description:
      - Only used when command=modify.
    aliases: ['new_identifier']
  wait:
    description:
      - When command=create, modify or restore then wait for the database to enter the 'available' state.
        When command=delete wait for the database to be terminated.
    type: bool
    default: 'no'
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
requirements: [ 'boto3' ]
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Basic cluster provisioning example
- redshift: >
    command=create
    node_type=ds1.xlarge
    identifier=new_cluster
    username=cluster_admin
    password=1nsecure

# Cluster delete example
- redshift:
    command: delete
    identifier: new_cluster
    skip_final_cluster_snapshot: true
    wait: true
'''

RETURN = '''
cluster:
    description: dictionary containing all the cluster information
    returned: success
    type: complex
    contains:
        identifier:
            description: Id of the cluster.
            returned: success
            type: str
            sample: "new_redshift_cluster"
        create_time:
            description: Time of the cluster creation as timestamp.
            returned: success
            type: float
            sample: 1430158536.308
        status:
            description: Status of the cluster.
            returned: success
            type: str
            sample: "available"
        db_name:
            description: Name of the database.
            returned: success
            type: str
            sample: "new_db_name"
        availability_zone:
            description: Amazon availability zone where the cluster is located. "None" until cluster is available.
            returned: success
            type: str
            sample: "us-east-1b"
        maintenance_window:
            description: Time frame when maintenance/upgrade are done.
            returned: success
            type: str
            sample: "sun:09:30-sun:10:00"
        private_ip_address:
            description: Private IP address of the main node.
            returned: success
            type: str
            sample: "10.10.10.10"
        public_ip_address:
            description: Public IP address of the main node. "None" when enhanced_vpc_routing is enabled.
            returned: success
            type: str
            sample: "0.0.0.0"
        port:
            description: Port of the cluster. "None" until cluster is available.
            returned: success
            type: int
            sample: 5439
        url:
            description: FQDN of the main cluster node. "None" until cluster is available.
            returned: success
            type: str
            sample: "new-redshift_cluster.jfkdjfdkj.us-east-1.redshift.amazonaws.com"
        enhanced_vpc_routing:
            description: status of the enhanced vpc routing feature.
            returned: success
            type: bool
'''

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule
from ansible.module_utils.ec2 import ec2_argument_spec, snake_dict_to_camel_dict
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code


def _collect_facts(resource):
    """Transform cluster information to dict."""
    facts = {
        'identifier': resource['ClusterIdentifier'],
        'status': resource['ClusterStatus'],
        'username': resource['MasterUsername'],
        'db_name': resource['DBName'],
        'maintenance_window': resource['PreferredMaintenanceWindow'],
        'enhanced_vpc_routing': resource['EnhancedVpcRouting']

    }

    for node in resource['ClusterNodes']:
        if node['NodeRole'] in ('SHARED', 'LEADER'):
            facts['private_ip_address'] = node['PrivateIPAddress']
            if facts['enhanced_vpc_routing'] is False:
                facts['public_ip_address'] = node['PublicIPAddress']
            else:
                facts['public_ip_address'] = None
            break

    # Some parameters are not ready instantly if you don't wait for available
    # cluster status
    facts['create_time'] = None
    facts['url'] = None
    facts['port'] = None
    facts['availability_zone'] = None

    if resource['ClusterStatus'] != "creating":
        facts['create_time'] = resource['ClusterCreateTime']
        facts['url'] = resource['Endpoint']['Address']
        facts['port'] = resource['Endpoint']['Port']
        facts['availability_zone'] = resource['AvailabilityZone']

    return facts


def create_cluster(module, redshift):
    """
    Create a new cluster

    module: AnsibleModule object
    redshift: authenticated redshift connection object

    Returns:
    """

    identifier = module.params.get('identifier')
    node_type = module.params.get('node_type')
    username = module.params.get('username')
    password = module.params.get('password')
    d_b_name = module.params.get('db_name')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    changed = True
    # Package up the optional parameters
    params = {}
    for p in ('cluster_type', 'cluster_security_groups',
              'vpc_security_group_ids', 'cluster_subnet_group_name',
              'availability_zone', 'preferred_maintenance_window',
              'cluster_parameter_group_name',
              'automated_snapshot_retention_period', 'port',
              'cluster_version', 'allow_version_upgrade',
              'number_of_nodes', 'publicly_accessible',
              'encrypted', 'elastic_ip', 'enhanced_vpc_routing'):
        # https://github.com/boto/boto3/issues/400
        if module.params.get(p) is not None:
            params[p] = module.params.get(p)

    if d_b_name:
        params['d_b_name'] = d_b_name

    try:
        redshift.describe_clusters(ClusterIdentifier=identifier)['Clusters'][0]
        changed = False
    except is_boto3_error_code('ClusterNotFound'):
        try:
            redshift.create_cluster(ClusterIdentifier=identifier,
                                    NodeType=node_type,
                                    MasterUsername=username,
                                    MasterUserPassword=password,
                                    **snake_dict_to_camel_dict(params, capitalize_first=True))
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Failed to create cluster")
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to describe cluster")
    if wait:
        attempts = wait_timeout // 60
        waiter = redshift.get_waiter('cluster_available')
        try:
            waiter.wait(
                ClusterIdentifier=identifier,
                WaiterConfig=dict(MaxAttempts=attempts)
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Timeout waiting for the cluster creation")
    try:
        resource = redshift.describe_clusters(ClusterIdentifier=identifier)['Clusters'][0]
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe cluster")

    return(changed, _collect_facts(resource))


def describe_cluster(module, redshift):
    """
    Collect data about the cluster.

    module: Ansible module object
    redshift: authenticated redshift connection object
    """
    identifier = module.params.get('identifier')

    try:
        resource = redshift.describe_clusters(ClusterIdentifier=identifier)['Clusters'][0]
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Error describing cluster")

    return(True, _collect_facts(resource))


def delete_cluster(module, redshift):
    """
    Delete a cluster.

    module: Ansible module object
    redshift: authenticated redshift connection object
    """

    identifier = module.params.get('identifier')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    params = {}
    for p in ('skip_final_cluster_snapshot',
              'final_cluster_snapshot_identifier'):
        if p in module.params:
            # https://github.com/boto/boto3/issues/400
            if module.params.get(p) is not None:
                params[p] = module.params.get(p)

    try:
        redshift.delete_cluster(
            ClusterIdentifier=identifier,
            **snake_dict_to_camel_dict(params, capitalize_first=True)
        )
    except is_boto3_error_code('ClusterNotFound'):
        return(False, {})
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="Failed to delete cluster")

    if wait:
        attempts = wait_timeout // 60
        waiter = redshift.get_waiter('cluster_deleted')
        try:
            waiter.wait(
                ClusterIdentifier=identifier,
                WaiterConfig=dict(MaxAttempts=attempts)
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Timeout deleting the cluster")

    return(True, {})


def modify_cluster(module, redshift):
    """
    Modify an existing cluster.

    module: Ansible module object
    redshift: authenticated redshift connection object
    """

    identifier = module.params.get('identifier')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    # Package up the optional parameters
    params = {}
    for p in ('cluster_type', 'cluster_security_groups',
              'vpc_security_group_ids', 'cluster_subnet_group_name',
              'availability_zone', 'preferred_maintenance_window',
              'cluster_parameter_group_name',
              'automated_snapshot_retention_period', 'port', 'cluster_version',
              'allow_version_upgrade', 'number_of_nodes', 'new_cluster_identifier'):
        # https://github.com/boto/boto3/issues/400
        if module.params.get(p) is not None:
            params[p] = module.params.get(p)

    # enhanced_vpc_routing parameter change needs an exclusive request
    if module.params.get('enhanced_vpc_routing') is not None:
        try:
            redshift.modify_cluster(ClusterIdentifier=identifier,
                                    EnhancedVpcRouting=module.params.get('enhanced_vpc_routing'))
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't modify redshift cluster %s " % identifier)
    if wait:
        attempts = wait_timeout // 60
        waiter = redshift.get_waiter('cluster_available')
        try:
            waiter.wait(
                ClusterIdentifier=identifier,
                WaiterConfig=dict(MaxAttempts=attempts)
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e,
                                 msg="Timeout waiting for cluster enhanced vpc routing modification"
                                 )

    # change the rest
    try:
        redshift.modify_cluster(ClusterIdentifier=identifier,
                                **snake_dict_to_camel_dict(params, capitalize_first=True))
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't modify redshift cluster %s " % identifier)

    if module.params.get('new_cluster_identifier'):
        identifier = module.params.get('new_cluster_identifier')

    if wait:
        attempts = wait_timeout // 60
        waiter2 = redshift.get_waiter('cluster_available')
        try:
            waiter2.wait(
                ClusterIdentifier=identifier,
                WaiterConfig=dict(MaxAttempts=attempts)
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Timeout waiting for cluster modification")
    try:
        resource = redshift.describe_clusters(ClusterIdentifier=identifier)['Clusters'][0]
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json(e, msg="Couldn't modify redshift cluster %s " % identifier)

    return(True, _collect_facts(resource))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        command=dict(choices=['create', 'facts', 'delete', 'modify'], required=True),
        identifier=dict(required=True),
        node_type=dict(choices=['ds1.xlarge', 'ds1.8xlarge', 'ds2.xlarge',
                                'ds2.8xlarge', 'dc1.large', 'dc2.large',
                                'dc1.8xlarge', 'dw1.xlarge', 'dw1.8xlarge',
                                'dw2.large', 'dw2.8xlarge'], required=False),
        username=dict(required=False),
        password=dict(no_log=True, required=False),
        db_name=dict(required=False),
        cluster_type=dict(choices=['multi-node', 'single-node'], default='single-node'),
        cluster_security_groups=dict(aliases=['security_groups'], type='list'),
        vpc_security_group_ids=dict(aliases=['vpc_security_groups'], type='list'),
        skip_final_cluster_snapshot=dict(aliases=['skip_final_snapshot'],
                                         type='bool', default=False),
        final_cluster_snapshot_identifier=dict(aliases=['final_snapshot_id'], required=False),
        cluster_subnet_group_name=dict(aliases=['subnet']),
        availability_zone=dict(aliases=['aws_zone', 'zone']),
        preferred_maintenance_window=dict(aliases=['maintance_window', 'maint_window']),
        cluster_parameter_group_name=dict(aliases=['param_group_name']),
        automated_snapshot_retention_period=dict(aliases=['retention_period'], type='int'),
        port=dict(type='int'),
        cluster_version=dict(aliases=['version'], choices=['1.0']),
        allow_version_upgrade=dict(aliases=['version_upgrade'], type='bool', default=True),
        number_of_nodes=dict(type='int'),
        publicly_accessible=dict(type='bool', default=False),
        encrypted=dict(type='bool', default=False),
        elastic_ip=dict(required=False),
        new_cluster_identifier=dict(aliases=['new_identifier']),
        enhanced_vpc_routing=dict(type='bool', default=False),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=300),
    ))

    required_if = [
        ('command', 'delete', ['skip_final_cluster_snapshot']),
        ('command', 'create', ['node_type',
                               'username',
                               'password'])
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if
    )

    command = module.params.get('command')
    skip_final_cluster_snapshot = module.params.get('skip_final_cluster_snapshot')
    final_cluster_snapshot_identifier = module.params.get('final_cluster_snapshot_identifier')
    # can't use module basic required_if check for this case
    if command == 'delete' and skip_final_cluster_snapshot is False and final_cluster_snapshot_identifier is None:
        module.fail_json(msg="Need to specify final_cluster_snapshot_identifier if skip_final_cluster_snapshot is False")

    conn = module.client('redshift')

    changed = True
    if command == 'create':
        (changed, cluster) = create_cluster(module, conn)

    elif command == 'facts':
        (changed, cluster) = describe_cluster(module, conn)

    elif command == 'delete':
        (changed, cluster) = delete_cluster(module, conn)

    elif command == 'modify':
        (changed, cluster) = modify_cluster(module, conn)

    module.exit_json(changed=changed, cluster=cluster)


if __name__ == '__main__':
    main()
