# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: aws_rds
    plugin_type: inventory
    short_description: rds instance source
    description:
        - Get instances and clusters from Amazon Web Services RDS.
        - Uses a YAML configuration file that ends with aws_rds.(yml|yaml).
    options:
        regions:
          description: A list of regions in which to describe RDS instances and clusters. Available regions are listed here
              U(https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html)
          default: []
        filters:
          description: A dictionary of filter value pairs. Available filters are listed here
              U(https://docs.aws.amazon.com/cli/latest/reference/rds/describe-db-instances.html#options). If you filter by
              db-cluster-id and I(include_clusters) is True it will apply to clusters as well.
          default: {}
        strict_permissions:
          description: By default if an AccessDenied exception is encountered this plugin will fail. You can set strict_permissions to
              False in the inventory config file which will allow the restrictions to be gracefully skipped.
          type: bool
          default: True
        include_clusters:
          description: Whether or not to query for Aurora clusters as well as instances
          type: bool
          default: False
        statuses:
          description: A list of desired states for instances/clusters to be added to inventory. Set to ['all'] as a shorthand to find everything.
          type: list
          default:
              - creating
              - available
    extends_documentation_fragment:
        - inventory_cache
        - constructed
        - aws_credentials
    requirements:
        - boto3
        - botocore
    author: Sloane Hertel (@s-hertel)
'''

EXAMPLES = '''
plugin: aws_rds
regions:
  - us-east-1
  - ca-central-1
keyed_groups:
  - key: 'db_parameter_groups|json_query("[].db_parameter_group_name")'
    prefix: rds_parameter_group
  - key: engine
    prefix: rds
  - key: tags
  - key: region
'''

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.module_utils.aws.core import is_boto3_error_code
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, boto3_tag_list_to_ansible_dict
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

try:
    import boto3
    import botocore
except ImportError:
    raise AnsibleError('The RDS dynamic inventory plugin requires boto3 and botocore.')


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = 'aws_rds'

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.credentials = {}
        self.boto_profile = None

    def _boto3_conn(self, regions):
        '''
            :param regions: A list of regions to create a boto3 client

            Generator that yields a boto3 client and the region
        '''
        for region in regions:
            try:
                connection = boto3.session.Session(profile_name=self.boto_profile).client('rds', region, **self.credentials)
            except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                if self.boto_profile:
                    try:
                        connection = boto3.session.Session(profile_name=self.boto_profile).client('rds', region)
                    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                        raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
                else:
                    raise AnsibleError("Insufficient credentials found: %s" % to_native(e))
            yield connection, region

    def _get_hosts_by_region(self, connection, filters, strict):

        def _add_tags_for_hosts(connection, hosts, strict):
            for host in hosts:
                if 'DBInstanceArn' in host:
                    resource_arn = host['DBInstanceArn']
                else:
                    resource_arn = host['DBClusterArn']

                try:
                    tags = connection.list_tags_for_resource(ResourceName=resource_arn)['TagList']
                except is_boto3_error_code('AccessDenied') as e:
                    if not strict:
                        tags = []
                    else:
                        raise e
                host['Tags'] = tags

        def wrapper(f, *args, **kwargs):
            try:
                results = f(*args, **kwargs)
                if 'DBInstances' in results:
                    results = results['DBInstances']
                else:
                    results = results['DBClusters']
                _add_tags_for_hosts(connection, results, strict)
            except is_boto3_error_code('AccessDenied') as e:  # pylint: disable=duplicate-except
                if not strict:
                    results = []
                else:
                    raise AnsibleError("Failed to query RDS: {0}".format(to_native(e)))
            except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:  # pylint: disable=duplicate-except
                raise AnsibleError("Failed to query RDS: {0}".format(to_native(e)))
            return results
        return wrapper

    def _get_all_hosts(self, regions, instance_filters, cluster_filters, strict, statuses, gather_clusters=False):
        '''
           :param regions: a list of regions in which to describe hosts
           :param instance_filters: a list of boto3 filter dictionaries
           :param cluster_filters: a list of boto3 filter dictionaries
           :param strict: a boolean determining whether to fail or ignore 403 error codes
           :param statuses: a list of statuses that the returned hosts should match
           :return A list of host dictionaries
        '''
        all_instances = []
        all_clusters = []
        for connection, region in self._boto3_conn(regions):
            paginator = connection.get_paginator('describe_db_instances')
            all_instances.extend(
                self._get_hosts_by_region(connection, instance_filters, strict)
                (paginator.paginate(Filters=instance_filters).build_full_result)
            )
            if gather_clusters:
                all_clusters.extend(
                    self._get_hosts_by_region(connection, cluster_filters, strict)
                    (connection.describe_db_clusters, **{'Filters': cluster_filters})
                )
        sorted_hosts = list(
            sorted(all_instances, key=lambda x: x['DBInstanceIdentifier']) +
            sorted(all_clusters, key=lambda x: x['DBClusterIdentifier'])
        )
        return self.find_hosts_with_valid_statuses(sorted_hosts, statuses)

    def find_hosts_with_valid_statuses(self, hosts, statuses):
        if 'all' in statuses:
            return hosts
        valid_hosts = []
        for host in hosts:
            if host.get('DBInstanceStatus') in statuses:
                valid_hosts.append(host)
            elif host.get('Status') in statuses:
                valid_hosts.append(host)
        return valid_hosts

    def _populate(self, hosts):
        group = 'aws_rds'
        self.inventory.add_group(group)
        if hosts:
            self._add_hosts(hosts=hosts, group=group)
            self.inventory.add_child('all', group)

    def _populate_from_source(self, source_data):
        hostvars = source_data.pop('_meta', {}).get('hostvars', {})
        for group in source_data:
            if group == 'all':
                continue
            else:
                self.inventory.add_group(group)
                hosts = source_data[group].get('hosts', [])
                for host in hosts:
                    self._populate_host_vars([host], hostvars.get(host, {}), group)
                self.inventory.add_child('all', group)

    def _get_hostname(self, host):
        if host.get('DBInstanceIdentifier'):
            return host['DBInstanceIdentifier']
        else:
            return host['DBClusterIdentifier']

    def _format_inventory(self, hosts):
        results = {'_meta': {'hostvars': {}}}
        group = 'aws_rds'
        results[group] = {'hosts': []}
        for host in hosts:
            hostname = self._get_hostname(host)
            results[group]['hosts'].append(hostname)
            h = self.inventory.get_host(hostname)
            results['_meta']['hostvars'][h.name] = h.vars
        return results

    def _add_hosts(self, hosts, group):
        '''
            :param hosts: a list of hosts to be added to a group
            :param group: the name of the group to which the hosts belong
        '''
        for host in hosts:
            hostname = self._get_hostname(host)
            host = camel_dict_to_snake_dict(host, ignore_list=['Tags'])
            host['tags'] = boto3_tag_list_to_ansible_dict(host.get('tags', []))

            # Allow easier grouping by region
            if 'availability_zone' in host:
                host['region'] = host['availability_zone'][:-1]
            elif 'availability_zones' in host:
                host['region'] = host['availability_zones'][0][:-1]

            self.inventory.add_host(hostname, group=group)
            for hostvar, hostval in host.items():
                self.inventory.set_variable(hostname, hostvar, hostval)

            # Use constructed if applicable
            strict = self.get_option('strict')
            # Composed variables
            self._set_composite_vars(self.get_option('compose'), host, hostname, strict=strict)
            # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
            self._add_host_to_composed_groups(self.get_option('groups'), host, hostname, strict=strict)
            # Create groups based on variable values and add the corresponding hosts to it
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host, hostname, strict=strict)

    def _set_credentials(self):
        '''
            :param config_data: contents of the inventory config file
        '''
        self.boto_profile = self.get_option('aws_profile')
        aws_access_key_id = self.get_option('aws_access_key')
        aws_secret_access_key = self.get_option('aws_secret_key')
        aws_security_token = self.get_option('aws_security_token')

        if not self.boto_profile and not (aws_access_key_id and aws_secret_access_key):
            session = botocore.session.get_session()
            if session.get_credentials() is not None:
                aws_access_key_id = session.get_credentials().access_key
                aws_secret_access_key = session.get_credentials().secret_key
                aws_security_token = session.get_credentials().token

        if not self.boto_profile and not (aws_access_key_id and aws_secret_access_key):
            raise AnsibleError("Insufficient boto credentials found. Please provide them in your "
                               "inventory configuration file or set them as environment variables.")

        if aws_access_key_id:
            self.credentials['aws_access_key_id'] = aws_access_key_id
        if aws_secret_access_key:
            self.credentials['aws_secret_access_key'] = aws_secret_access_key
        if aws_security_token:
            self.credentials['aws_session_token'] = aws_security_token

    def verify_file(self, path):
        '''
            :param loader: an ansible.parsing.dataloader.DataLoader object
            :param path: the path to the inventory config file
            :return the contents of the config file
        '''
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('aws_rds.yml', 'aws_rds.yaml')):
                return True
        return False

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)

        config_data = self._read_config_data(path)
        self._set_credentials()

        # get user specifications
        regions = self.get_option('regions')
        filters = self.get_option('filters')
        strict_permissions = self.get_option('strict_permissions')
        statuses = self.get_option('statuses')
        include_clusters = self.get_option('include_clusters')
        instance_filters = ansible_dict_to_boto3_filter_list(filters)
        cluster_filters = []
        if 'db-cluster-id' in filters and include_clusters:
            cluster_filters = ansible_dict_to_boto3_filter_list({'db-cluster-id': filters['db-cluster-id']})

        cache_key = self.get_cache_key(path)
        # false when refresh_cache or --flush-cache is used
        if cache:
            # get the user-specified directive
            cache = self.get_option('cache')

        # Generate inventory
        formatted_inventory = {}
        cache_needs_update = False
        if cache:
            try:
                results = self._cache[cache_key]
            except KeyError:
                # if cache expires or cache file doesn't exist
                cache_needs_update = True
            else:
                self._populate_from_source(results)

        if not cache or cache_needs_update:
            results = self._get_all_hosts(regions, instance_filters, cluster_filters, strict_permissions, statuses, include_clusters)
            self._populate(results)
            formatted_inventory = self._format_inventory(results)

        # If the cache has expired/doesn't exist or if refresh_inventory/flush cache is used
        # when the user is using caching, update the cached inventory
        if cache_needs_update or (not cache and self.get_option('cache')):
            self._cache[cache_key] = formatted_inventory
