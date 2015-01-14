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

DOCUMENTATION = """
---
module: elasticache
short_description: Manage cache clusters in Amazon Elasticache.
description:
  - Manage cache clusters in Amazon Elasticache.
  - Returns information about the specified cache cluster.
version_added: "1.4"
requirements: [ "boto" ]
author: Jim Dalton
options:
  state:
    description:
      - C(absent) or C(present) are idempotent actions that will create or destroy a cache cluster as needed. C(rebooted) will reboot the cluster, resulting in a momentary outage.
    choices: ['present', 'absent', 'rebooted']
    required: true
  name:
    description:
      - The cache cluster identifier
    required: true
  engine:
    description:
      - Name of the cache engine to be used (memcached or redis)
    required: false
    default: memcached
  cache_engine_version:
    description:
      - The version number of the cache engine
    required: false
    default: 1.4.14
  node_type:
    description:
      - The compute and memory capacity of the nodes in the cache cluster
    required: false
    default: cache.m1.small
  num_nodes:
    description:
      - The initial number of cache nodes that the cache cluster will have
    required: false
  cache_port:
    description:
      - The port number on which each of the cache nodes will accept connections
    required: false
    default: 11211
  security_group_ids:
    description:
      - A list of vpc security group names to associate with this cache cluster. Only use if inside a vpc
    required: false
    default: ['default']
    version_added: "1.6"
  cache_security_groups:
    description:
      - A list of cache security group names to associate with this cache cluster
    required: false
    default: ['default']
  zone:
    description:
      - The EC2 Availability Zone in which the cache cluster will be created
    required: false
    default: None
  wait:
    description:
      - Wait for cache cluster result before returning
    required: false
    default: yes
    choices: [ "yes", "no" ]
  hard_modify:
    description:
      - Whether to destroy and recreate an existing cache cluster if necessary in order to modify its state
    required: false
    default: no
    choices: [ "yes", "no" ]
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used. 
    required: false
    default: None
    aliases: ['ec2_secret_key', 'secret_key']
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: None
    aliases: ['ec2_access_key', 'access_key']
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    aliases: ['aws_region', 'ec2_region']

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

import sys
import os
import time

try:
    import boto
    from boto.elasticache.layer1 import ElastiCacheConnection
    from boto.regioninfo import RegionInfo
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)


class ElastiCacheManager(object):
    """Handles elasticache creation and destruction"""

    EXIST_STATUSES = ['available', 'creating', 'rebooting', 'modifying']

    def __init__(self, module, name, engine, cache_engine_version, node_type,
                 num_nodes, cache_port, cache_security_groups, security_group_ids, zone, wait,
                 hard_modify, aws_access_key, aws_secret_key, region):
        self.module = module
        self.name = name
        self.engine = engine
        self.cache_engine_version = cache_engine_version
        self.node_type = node_type
        self.num_nodes = num_nodes
        self.cache_port = cache_port
        self.cache_security_groups = cache_security_groups
        self.security_group_ids = security_group_ids
        self.zone = zone
        self.wait = wait
        self.hard_modify = hard_modify

        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region = region

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

        try:
            response = self.conn.create_cache_cluster(cache_cluster_id=self.name,
                                                      num_cache_nodes=self.num_nodes,
                                                      cache_node_type=self.node_type,
                                                      engine=self.engine,
                                                      engine_version=self.cache_engine_version,
                                                      cache_security_group_names=self.cache_security_groups,
                                                      security_group_ids=self.security_group_ids,
                                                      preferred_availability_zone=self.zone,
                                                      port=self.cache_port)
        except boto.exception.BotoServerError, e:
            self.module.fail_json(msg=e.message)
        cache_cluster_data = response['CreateCacheClusterResponse']['CreateCacheClusterResult']['CacheCluster']
        self._refresh_data(cache_cluster_data)

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
            response = self.conn.delete_cache_cluster(cache_cluster_id=self.name)
        except boto.exception.BotoServerError, e:
            self.module.fail_json(msg=e.message)
        cache_cluster_data = response['DeleteCacheClusterResponse']['DeleteCacheClusterResult']['CacheCluster']
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
            response = self.conn.modify_cache_cluster(cache_cluster_id=self.name,
                                                  num_cache_nodes=self.num_nodes,
                                                  cache_node_ids_to_remove=nodes_to_remove,
                                                  cache_security_group_names=self.cache_security_groups,
                                                  security_group_ids=self.security_group_ids,
                                                  apply_immediately=True,
                                                  engine_version=self.cache_engine_version)
        except boto.exception.BotoServerError, e:
            self.module.fail_json(msg=e.message)

        cache_cluster_data = response['ModifyCacheClusterResponse']['ModifyCacheClusterResult']['CacheCluster']
        self._refresh_data(cache_cluster_data)

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
            response = self.conn.reboot_cache_cluster(cache_cluster_id=self.name,
                                                      cache_node_ids_to_reboot=cache_node_ids)
        except boto.exception.BotoServerError, e:
            self.module.fail_json(msg=e.message)

        cache_cluster_data = response['RebootCacheClusterResponse']['RebootCacheClusterResult']['CacheCluster']
        self._refresh_data(cache_cluster_data)

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
            time.sleep(1)
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
        for key, value in modifiable_data.iteritems():
            if self.data[key] != value:
                return True

        # Check cache security groups
        cache_security_groups = []
        for sg in self.data['CacheSecurityGroups']:
            cache_security_groups.append(sg['CacheSecurityGroupName'])
            if set(cache_security_groups) - set(self.cache_security_groups):
                return True

        # check vpc security groups
        vpc_security_groups = []
        security_groups = self.data['SecurityGroups'] or []
        for sg in security_groups:
            vpc_security_groups.append(sg['SecurityGroupId'])
            if set(vpc_security_groups) - set(self.security_group_ids):
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
        for key, value in unmodifiable_data.iteritems():
            if getattr(self, key) != value:
                return True
        return False

    def _get_elasticache_connection(self):
        """Get an elasticache connection"""
        try:
            endpoint = "elasticache.%s.amazonaws.com" % self.region
            connect_region = RegionInfo(name=self.region, endpoint=endpoint)
            return ElastiCacheConnection(aws_access_key_id=self.aws_access_key,
                                         aws_secret_access_key=self.aws_secret_key,
                                         region=connect_region)
        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg=e.message)

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
                response = self.conn.describe_cache_clusters(cache_cluster_id=self.name,
                                                             show_cache_node_info=True)
            except boto.exception.BotoServerError:
                self.data = None
                self.status = 'gone'
                return
            cache_cluster_data = response['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters'][0]
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
            return None

        if not self.hard_modify:
            msg = "'%s' requires removal of cache nodes. 'hard_modify' must be set to true to proceed."
            self.module.fail_json(msg=msg % self.name)

        cache_node_ids = [cn['CacheNodeId'] for cn in self.data['CacheNodes']]
        return cache_node_ids[-num_nodes_to_remove:]



def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            state={'required': True, 'choices': ['present', 'absent', 'rebooted']},
            name={'required': True},
            engine={'required': False, 'default': 'memcached'},
            cache_engine_version={'required': False, 'default': '1.4.14'},
            node_type={'required': False, 'default': 'cache.m1.small'},
            num_nodes={'required': False, 'default': None, 'type': 'int'},
            cache_port={'required': False, 'default': 11211, 'type': 'int'},
            cache_security_groups={'required': False, 'default': ['default'],
                                   'type': 'list'},
            security_group_ids={'required': False, 'default': [],
                                   'type': 'list'},
            zone={'required': False, 'default': None},
            wait={'required': False, 'type' : 'bool', 'default': True},
            hard_modify={'required': False, 'type': 'bool', 'default': False}
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    ec2_url, aws_access_key, aws_secret_key, region = get_ec2_creds(module)

    name = module.params['name']
    state = module.params['state']
    engine = module.params['engine']
    cache_engine_version = module.params['cache_engine_version']
    node_type = module.params['node_type']
    num_nodes = module.params['num_nodes']
    cache_port = module.params['cache_port']
    cache_security_groups = module.params['cache_security_groups']
    security_group_ids = module.params['security_group_ids']
    zone = module.params['zone']
    wait = module.params['wait']
    hard_modify = module.params['hard_modify']

    if state == 'present' and not num_nodes:
        module.fail_json(msg="'num_nodes' is a required parameter. Please specify num_nodes > 0")

    if not region:
        module.fail_json(msg=str("Either region or EC2_REGION environment variable must be set."))

    elasticache_manager = ElastiCacheManager(module, name, engine,
                                             cache_engine_version, node_type,
                                             num_nodes, cache_port,
                                             cache_security_groups,
                                             security_group_ids, zone, wait,
                                             hard_modify, aws_access_key,
                                             aws_secret_key, region)

    if state == 'present':
        elasticache_manager.ensure_present()
    elif state == 'absent':
        elasticache_manager.ensure_absent()
    elif state == 'rebooted':
        elasticache_manager.ensure_rebooted()

    facts_result = dict(changed=elasticache_manager.changed,
                        elasticache=elasticache_manager.get_info())

    module.exit_json(**facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
