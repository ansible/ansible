#!/usr/bin/python
#
# Copyright (c) 2017 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: elasticache
short_description: Manage cache clusters in Amazon Elasticache.
description:
  - Manage cache clusters in Amazon Elasticache.
  - Returns information about the specified cache cluster.
version_added: "1.4"
requirements: [ boto3 ]
author: "Jim Dalton (@jsdalton)"
options:
  state:
    description:
      - C(absent) or C(present) are idempotent actions that will create or destroy a cache cluster as needed. C(rebooted) will reboot the cluster,
        resulting in a momentary outage.
    choices: ['present', 'absent', 'rebooted']
    required: true
  name:
    description:
      - The cache cluster identifier
    required: true
  engine:
    description:
      - Name of the cache engine to be used.
    default: memcached
    choices: ['redis', 'memcached']
  cache_engine_version:
    description:
      - The version number of the cache engine
  node_type:
    description:
      - The compute and memory capacity of the nodes in the cache cluster
    default: cache.m1.small
  num_nodes:
    description:
      - The initial number of cache nodes that the cache cluster will have. Required when state=present.
  cache_port:
    description:
      - The port number on which each of the cache nodes will accept connections
  cache_parameter_group:
    description:
      - The name of the cache parameter group to associate with this cache cluster. If this argument is omitted, the default cache parameter group
        for the specified engine will be used.
    version_added: "2.0"
    aliases: [ 'parameter_group' ]
  cache_subnet_group:
    description:
      - The subnet group name to associate with. Only use if inside a vpc. Required if inside a vpc
    version_added: "2.0"
  security_group_ids:
    description:
      - A list of vpc security group names to associate with this cache cluster. Only use if inside a vpc
    version_added: "1.6"
  cache_security_groups:
    description:
      - A list of cache security group names to associate with this cache cluster. Must be an empty list if inside a vpc
  zone:
    description:
      - The EC2 Availability Zone in which the cache cluster will be created
  wait:
    description:
      - Wait for cache cluster result before returning
    type: bool
    default: 'yes'
  hard_modify:
    description:
      - Whether to destroy and recreate an existing cache cluster if necessary in order to modify its state
    type: bool
    default: 'no'
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Basic example
- elasticache:
    name: "test-please-delete"
    state: present
    engine: memcached
    cache_engine_version: 1.4.14
    node_type: cache.m1.small
    num_nodes: 1
    cache_port: 11211
    cache_security_groups:
      - default
    zone: us-east-1d


# Ensure cache cluster is gone
- elasticache:
    name: "test-please-delete"
    state: absent

# Reboot cache cluster
- elasticache:
    name: "test-please-delete"
    state: rebooted

"""
from time import sleep
from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, HAS_BOTO3, camel_dict_to_snake_dict

try:
    import boto3
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


class ElastiCacheManager(object):

    """Handles elasticache creation and destruction"""

    EXIST_STATUSES = ['available', 'creating', 'rebooting', 'modifying']

    def __init__(self, module, name, engine, cache_engine_version, node_type,
                 num_nodes, cache_port, cache_parameter_group, cache_subnet_group,
                 cache_security_groups, security_group_ids, zone, wait,
                 hard_modify, region, **aws_connect_kwargs):
        self.module = module
        self.name = name
        self.engine = engine.lower()
        self.cache_engine_version = cache_engine_version
        self.node_type = node_type
        self.num_nodes = num_nodes
        self.cache_port = cache_port
        self.cache_parameter_group = cache_parameter_group
        self.cache_subnet_group = cache_subnet_group
        self.cache_security_groups = cache_security_groups
        self.security_group_ids = security_group_ids
        self.zone = zone
        self.wait = wait
        self.hard_modify = hard_modify

        self.region = region
        self.aws_connect_kwargs = aws_connect_kwargs

        self.changed = False
        self.data = None
        self.status = 'gone'
        self.conn = self._get_elasticache_connection()
        self._refresh_data()

    def ensure_present(self):
        """Ensure cache cluster exists or create it if not"""
        if self.exists():
            self.sync()
        else:
            self.create()

    def ensure_absent(self):
        """Ensure cache cluster is gone or delete it if not"""
        self.delete()

    def ensure_rebooted(self):
        """Ensure cache cluster is gone or delete it if not"""
        self.reboot()

    def exists(self):
        """Check if cache cluster exists"""
        return self.status in self.EXIST_STATUSES

    def create(self):
        """Create an ElastiCache cluster"""
        if self.status == 'available':
            return
        if self.status in ['creating', 'rebooting', 'modifying']:
            if self.wait:
                self._wait_for_status('available')
            return
        if self.status == 'deleting':
            if self.wait:
                self._wait_for_status('gone')
            else:
                msg = "'%s' is currently deleting. Cannot create."
                self.module.fail_json(msg=msg % self.name)

        kwargs = dict(CacheClusterId=self.name,
                      NumCacheNodes=self.num_nodes,
                      CacheNodeType=self.node_type,
                      Engine=self.engine,
                      EngineVersion=self.cache_engine_version,
                      CacheSecurityGroupNames=self.cache_security_groups,
                      SecurityGroupIds=self.security_group_ids,
                      CacheParameterGroupName=self.cache_parameter_group,
                      CacheSubnetGroupName=self.cache_subnet_group)
        if self.cache_port is not None:
            kwargs['Port'] = self.cache_port
        if self.zone is not None:
            kwargs['PreferredAvailabilityZone'] = self.zone

        try:
            self.conn.create_cache_cluster(**kwargs)

        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg=e.message, exception=format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

        self._refresh_data()

        self.changed = True
        if self.wait:
            self._wait_for_status('available')
        return True

    def delete(self):
        """Destroy an ElastiCache cluster"""
        if self.status == 'gone':
            return
        if self.status == 'deleting':
            if self.wait:
                self._wait_for_status('gone')
            return
        if self.status in ['creating', 'rebooting', 'modifying']:
            if self.wait:
                self._wait_for_status('available')
            else:
                msg = "'%s' is currently %s. Cannot delete."
                self.module.fail_json(msg=msg % (self.name, self.status))

        try:
            response = self.conn.delete_cache_cluster(CacheClusterId=self.name)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg=e.message, exception=format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

        cache_cluster_data = response['CacheCluster']
        self._refresh_data(cache_cluster_data)

        self.changed = True
        if self.wait:
            self._wait_for_status('gone')

    def sync(self):
        """Sync settings to cluster if required"""
        if not self.exists():
            msg = "'%s' is %s. Cannot sync."
            self.module.fail_json(msg=msg % (self.name, self.status))

        if self.status in ['creating', 'rebooting', 'modifying']:
            if self.wait:
                self._wait_for_status('available')
            else:
                # Cluster can only be synced if available. If we can't wait
                # for this, then just be done.
                return

        if self._requires_destroy_and_create():
            if not self.hard_modify:
                msg = "'%s' requires destructive modification. 'hard_modify' must be set to true to proceed."
                self.module.fail_json(msg=msg % self.name)
            if not self.wait:
                msg = "'%s' requires destructive modification. 'wait' must be set to true."
                self.module.fail_json(msg=msg % self.name)
            self.delete()
            self.create()
            return

        if self._requires_modification():
            self.modify()

    def modify(self):
        """Modify the cache cluster. Note it's only possible to modify a few select options."""
        nodes_to_remove = self._get_nodes_to_remove()
        try:
            self.conn.modify_cache_cluster(CacheClusterId=self.name,
                                           NumCacheNodes=self.num_nodes,
                                           CacheNodeIdsToRemove=nodes_to_remove,
                                           CacheSecurityGroupNames=self.cache_security_groups,
                                           CacheParameterGroupName=self.cache_parameter_group,
                                           SecurityGroupIds=self.security_group_ids,
                                           ApplyImmediately=True,
                                           EngineVersion=self.cache_engine_version)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg=e.message, exception=format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

        self._refresh_data()

        self.changed = True
        if self.wait:
            self._wait_for_status('available')

    def reboot(self):
        """Reboot the cache cluster"""
        if not self.exists():
            msg = "'%s' is %s. Cannot reboot."
            self.module.fail_json(msg=msg % (self.name, self.status))
        if self.status == 'rebooting':
            return
        if self.status in ['creating', 'modifying']:
            if self.wait:
                self._wait_for_status('available')
            else:
                msg = "'%s' is currently %s. Cannot reboot."
                self.module.fail_json(msg=msg % (self.name, self.status))

        # Collect ALL nodes for reboot
        cache_node_ids = [cn['CacheNodeId'] for cn in self.data['CacheNodes']]
        try:
            self.conn.reboot_cache_cluster(CacheClusterId=self.name,
                                           CacheNodeIdsToReboot=cache_node_ids)
        except botocore.exceptions.ClientError as e:
            self.module.fail_json(msg=e.message, exception=format_exc(),
                                  **camel_dict_to_snake_dict(e.response))

        self._refresh_data()

        self.changed = True
        if self.wait:
            self._wait_for_status('available')

    def get_info(self):
        """Return basic info about the cache cluster"""
        info = {
            'name': self.name,
            'status': self.status
        }
        if self.data:
            info['data'] = self.data
        return info

    def _wait_for_status(self, awaited_status):
        """Wait for status to change from present status to awaited_status"""
        status_map = {
            'creating': 'available',
            'rebooting': 'available',
            'modifying': 'available',
            'deleting': 'gone'
        }
        if self.status == awaited_status:
            # No need to wait, we're already done
            return
        if status_map[self.status] != awaited_status:
            msg = "Invalid awaited status. '%s' cannot transition to '%s'"
            self.module.fail_json(msg=msg % (self.status, awaited_status))

        if awaited_status not in set(status_map.values()):
            msg = "'%s' is not a valid awaited status."
            self.module.fail_json(msg=msg % awaited_status)

        while True:
            sleep(1)
            self._refresh_data()
            if self.status == awaited_status:
                break

    def _requires_modification(self):
        """Check if cluster requires (nondestructive) modification"""
        # Check modifiable data attributes
        modifiable_data = {
            'NumCacheNodes': self.num_nodes,
            'EngineVersion': self.cache_engine_version
        }
        for key, value in modifiable_data.items():
            if value is not None and value and self.data[key] != value:
                return True

        # Check cache security groups
        cache_security_groups = []
        for sg in self.data['CacheSecurityGroups']:
            cache_security_groups.append(sg['CacheSecurityGroupName'])
        if set(cache_security_groups) != set(self.cache_security_groups):
            return True

        # check vpc security groups
        if self.security_group_ids:
            vpc_security_groups = []
            security_groups = self.data['SecurityGroups'] or []
            for sg in security_groups:
                vpc_security_groups.append(sg['SecurityGroupId'])
            if set(vpc_security_groups) != set(self.security_group_ids):
                return True

        return False

    def _requires_destroy_and_create(self):
        """
        Check whether a destroy and create is required to synchronize cluster.
        """
        unmodifiable_data = {
            'node_type': self.data['CacheNodeType'],
            'engine': self.data['Engine'],
            'cache_port': self._get_port()
        }
        # Only check for modifications if zone is specified
        if self.zone is not None:
            unmodifiable_data['zone'] = self.data['PreferredAvailabilityZone']
        for key, value in unmodifiable_data.items():
            if getattr(self, key) is not None and getattr(self, key) != value:
                return True
        return False

    def _get_elasticache_connection(self):
        """Get an elasticache connection"""
        region, ec2_url, aws_connect_params = get_aws_connection_info(self.module, boto3=True)
        if region:
            return boto3_conn(self.module, conn_type='client', resource='elasticache',
                              region=region, endpoint=ec2_url, **aws_connect_params)
        else:
            self.module.fail_json(msg="region must be specified")

    def _get_port(self):
        """Get the port. Where this information is retrieved from is engine dependent."""
        if self.data['Engine'] == 'memcached':
            return self.data['ConfigurationEndpoint']['Port']
        elif self.data['Engine'] == 'redis':
            # Redis only supports a single node (presently) so just use
            # the first and only
            return self.data['CacheNodes'][0]['Endpoint']['Port']

    def _refresh_data(self, cache_cluster_data=None):
        """Refresh data about this cache cluster"""

        if cache_cluster_data is None:
            try:
                response = self.conn.describe_cache_clusters(CacheClusterId=self.name, ShowCacheNodeInfo=True)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'CacheClusterNotFound':
                    self.data = None
                    self.status = 'gone'
                    return
                else:
                    self.module.fail_json(msg=e.message, exception=format_exc(),
                                          **camel_dict_to_snake_dict(e.response))
            cache_cluster_data = response['CacheClusters'][0]
        self.data = cache_cluster_data
        self.status = self.data['CacheClusterStatus']

        # The documentation for elasticache lies -- status on rebooting is set
        # to 'rebooting cache cluster nodes' instead of 'rebooting'. Fix it
        # here to make status checks etc. more sane.
        if self.status == 'rebooting cache cluster nodes':
            self.status = 'rebooting'

    def _get_nodes_to_remove(self):
        """If there are nodes to remove, it figures out which need to be removed"""
        num_nodes_to_remove = self.data['NumCacheNodes'] - self.num_nodes
        if num_nodes_to_remove <= 0:
            return []

        if not self.hard_modify:
            msg = "'%s' requires removal of cache nodes. 'hard_modify' must be set to true to proceed."
            self.module.fail_json(msg=msg % self.name)

        cache_node_ids = [cn['CacheNodeId'] for cn in self.data['CacheNodes']]
        return cache_node_ids[-num_nodes_to_remove:]


def main():
    """ elasticache ansible module """
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent', 'rebooted']),
        name=dict(required=True),
        engine=dict(default='memcached'),
        cache_engine_version=dict(default=""),
        node_type=dict(default='cache.t2.small'),
        num_nodes=dict(default=1, type='int'),
        # alias for compat with the original PR 1950
        cache_parameter_group=dict(default="", aliases=['parameter_group']),
        cache_port=dict(type='int'),
        cache_subnet_group=dict(default=""),
        cache_security_groups=dict(default=[], type='list'),
        security_group_ids=dict(default=[], type='list'),
        zone=dict(),
        wait=dict(default=True, type='bool'),
        hard_modify=dict(type='bool')
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    name = module.params['name']
    state = module.params['state']
    engine = module.params['engine']
    cache_engine_version = module.params['cache_engine_version']
    node_type = module.params['node_type']
    num_nodes = module.params['num_nodes']
    cache_port = module.params['cache_port']
    cache_subnet_group = module.params['cache_subnet_group']
    cache_security_groups = module.params['cache_security_groups']
    security_group_ids = module.params['security_group_ids']
    zone = module.params['zone']
    wait = module.params['wait']
    hard_modify = module.params['hard_modify']
    cache_parameter_group = module.params['cache_parameter_group']

    if cache_subnet_group and cache_security_groups:
        module.fail_json(msg="Can't specify both cache_subnet_group and cache_security_groups")

    if state == 'present' and not num_nodes:
        module.fail_json(msg="'num_nodes' is a required parameter. Please specify num_nodes > 0")

    elasticache_manager = ElastiCacheManager(module, name, engine,
                                             cache_engine_version, node_type,
                                             num_nodes, cache_port,
                                             cache_parameter_group,
                                             cache_subnet_group,
                                             cache_security_groups,
                                             security_group_ids, zone, wait,
                                             hard_modify, region, **aws_connect_kwargs)

    if state == 'present':
        elasticache_manager.ensure_present()
    elif state == 'absent':
        elasticache_manager.ensure_absent()
    elif state == 'rebooted':
        elasticache_manager.ensure_rebooted()

    facts_result = dict(changed=elasticache_manager.changed,
                        elasticache=elasticache_manager.get_info())

    module.exit_json(**facts_result)

if __name__ == '__main__':
    main()
