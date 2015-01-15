#!/usr/bin/env python

'''
EC2 external inventory script
=================================

Generates inventory that Ansible can understand by making API request to
AWS EC2 using the Boto library.

NOTE: This script assumes Ansible is being executed where the environment
variables needed for Boto have already been set:
    export AWS_ACCESS_KEY_ID='AK123'
    export AWS_SECRET_ACCESS_KEY='abc123'

This script also assumes there is an ec2.ini file alongside it.  To specify a
different path to ec2.ini, define the EC2_INI_PATH environment variable:

    export EC2_INI_PATH=/path/to/my_ec2.ini

If you're using eucalyptus you need to set the above variables and
you need to define:

    export EC2_URL=http://hostname_of_your_cc:port/services/Eucalyptus

For more details, see: http://docs.pythonboto.org/en/latest/boto_config_tut.html

When run against a specific host, this script returns the following variables:
 - ec2_ami_launch_index
 - ec2_architecture
 - ec2_association
 - ec2_attachTime
 - ec2_attachment
 - ec2_attachmentId
 - ec2_client_token
 - ec2_deleteOnTermination
 - ec2_description
 - ec2_deviceIndex
 - ec2_dns_name
 - ec2_eventsSet
 - ec2_group_name
 - ec2_hypervisor
 - ec2_id
 - ec2_image_id
 - ec2_instanceState
 - ec2_instance_type
 - ec2_ipOwnerId
 - ec2_ip_address
 - ec2_item
 - ec2_kernel
 - ec2_key_name
 - ec2_launch_time
 - ec2_monitored
 - ec2_monitoring
 - ec2_networkInterfaceId
 - ec2_ownerId
 - ec2_persistent
 - ec2_placement
 - ec2_platform
 - ec2_previous_state
 - ec2_private_dns_name
 - ec2_private_ip_address
 - ec2_publicIp
 - ec2_public_dns_name
 - ec2_ramdisk
 - ec2_reason
 - ec2_region
 - ec2_requester_id
 - ec2_root_device_name
 - ec2_root_device_type
 - ec2_security_group_ids
 - ec2_security_group_names
 - ec2_shutdown_state
 - ec2_sourceDestCheck
 - ec2_spot_instance_request_id
 - ec2_state
 - ec2_state_code
 - ec2_state_reason
 - ec2_status
 - ec2_subnet_id
 - ec2_tenancy
 - ec2_virtualization_type
 - ec2_vpc_id

These variables are pulled out of a boto.ec2.instance object. There is a lack of
consistency with variable spellings (camelCase and underscores) since this
just loops through all variables the object exposes. It is preferred to use the
ones with underscores when multiple exist.

In addition, if an instance has AWS Tags associated with it, each tag is a new
variable named:
 - ec2_tag_[Key] = [Value]

Security groups are comma-separated in 'ec2_security_group_ids' and
'ec2_security_group_names'.
'''

# (c) 2012, Peter Sankauskas
#
# This file is part of Ansible,
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

######################################################################

import sys
import os
import argparse
import re
from time import time
import boto
from boto import ec2
from boto import rds
from boto import route53
import ConfigParser
from collections import defaultdict

try:
    import json
except ImportError:
    import simplejson as json


class Ec2Inventory(object):
    def _empty_inventory(self):
        return {"_meta" : {"hostvars" : {}}}

    def __init__(self):
        ''' Main execution path '''

        # Inventory grouped by instance IDs, tags, security groups, regions,
        # and availability zones
        self.inventory = self._empty_inventory()

        # Index of hostname (address) to instance ID
        self.index = {}

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif not self.is_cache_valid():
            self.do_api_calls_update_cache()

        # Data to print
        if self.args.host:
            data_to_print = self.get_host_info()

        elif self.args.list:
            # Display list of instances for inventory
            if self.inventory == self._empty_inventory():
                data_to_print = self.get_inventory_from_cache()
            else:
                data_to_print = self.json_format_dict(self.inventory, True)

        print data_to_print


    def is_cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_index):
                    return True

        return False


    def read_settings(self):
        ''' Reads the settings from the ec2.ini file '''

        config = ConfigParser.SafeConfigParser()
        ec2_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ec2.ini')
        ec2_ini_path = os.environ.get('EC2_INI_PATH', ec2_default_ini_path)
        config.read(ec2_ini_path)

        # is eucalyptus?
        self.eucalyptus_host = None
        self.eucalyptus = False
        if config.has_option('ec2', 'eucalyptus'):
            self.eucalyptus = config.getboolean('ec2', 'eucalyptus')
        if self.eucalyptus and config.has_option('ec2', 'eucalyptus_host'):
            self.eucalyptus_host = config.get('ec2', 'eucalyptus_host')

        # Regions
        self.regions = []
        configRegions = config.get('ec2', 'regions')
        configRegions_exclude = config.get('ec2', 'regions_exclude')
        if (configRegions == 'all'):
            if self.eucalyptus_host:
                self.regions.append(boto.connect_euca(host=self.eucalyptus_host).region.name)
            else:
                for regionInfo in ec2.regions():
                    if regionInfo.name not in configRegions_exclude:
                        self.regions.append(regionInfo.name)
        else:
            self.regions = configRegions.split(",")

        # Destination addresses
        self.destination_variable = config.get('ec2', 'destination_variable')
        self.vpc_destination_variable = config.get('ec2', 'vpc_destination_variable')

        # Route53
        self.route53_enabled = config.getboolean('ec2', 'route53')
        self.route53_excluded_zones = []
        if config.has_option('ec2', 'route53_excluded_zones'):
            self.route53_excluded_zones.extend(
                config.get('ec2', 'route53_excluded_zones', '').split(','))

        # Include RDS instances?
        self.rds_enabled = True
        if config.has_option('ec2', 'rds'):
            self.rds_enabled = config.getboolean('ec2', 'rds')

        # Return all EC2 and RDS instances (if RDS is enabled)
        if config.has_option('ec2', 'all_instances'):
            self.all_instances = config.getboolean('ec2', 'all_instances')
        else:
            self.all_instances = False
        if config.has_option('ec2', 'all_rds_instances') and self.rds_enabled:
            self.all_rds_instances = config.getboolean('ec2', 'all_rds_instances')
        else:
            self.all_rds_instances = False

        # Cache related
        cache_dir = os.path.expanduser(config.get('ec2', 'cache_path'))
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        self.cache_path_cache = cache_dir + "/ansible-ec2.cache"
        self.cache_path_index = cache_dir + "/ansible-ec2.index"
        self.cache_max_age = config.getint('ec2', 'cache_max_age')

        # Configure nested groups instead of flat namespace.
        if config.has_option('ec2', 'nested_groups'):
            self.nested_groups = config.getboolean('ec2', 'nested_groups')
        else:
            self.nested_groups = False

        # Do we need to just include hosts that match a pattern?
        try:
            pattern_include = config.get('ec2', 'pattern_include')
            if pattern_include and len(pattern_include) > 0:
                self.pattern_include = re.compile(pattern_include)
            else:
                self.pattern_include = None
        except ConfigParser.NoOptionError, e:
            self.pattern_include = None

        # Do we need to exclude hosts that match a pattern?
        try:
            pattern_exclude = config.get('ec2', 'pattern_exclude');
            if pattern_exclude and len(pattern_exclude) > 0:
                self.pattern_exclude = re.compile(pattern_exclude)
            else:
                self.pattern_exclude = None
        except ConfigParser.NoOptionError, e:
            self.pattern_exclude = None

        # Instance filters (see boto and EC2 API docs)
        self.ec2_instance_filters = defaultdict(list)
        if config.has_option('ec2', 'instance_filters'):
            for x in config.get('ec2', 'instance_filters', '').split(','):
                filter_key, filter_value = x.split('=')
                self.ec2_instance_filters[filter_key].append(filter_value)

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on EC2')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                           help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                           help='Force refresh of cache by making API requests to EC2 (default: False - use cache files)')
        self.args = parser.parse_args()


    def do_api_calls_update_cache(self):
        ''' Do API calls to each region, and save data in cache files '''

        if self.route53_enabled:
            self.get_route53_records()

        for region in self.regions:
            self.get_instances_by_region(region)
            if self.rds_enabled:
                self.get_rds_instances_by_region(region)

        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)


    def get_instances_by_region(self, region):
        ''' Makes an AWS EC2 API call to the list of instances in a particular
        region '''

        try:
            if self.eucalyptus:
                conn = boto.connect_euca(host=self.eucalyptus_host)
                conn.APIVersion = '2010-08-31'
            else:
                conn = ec2.connect_to_region(region)

            # connect_to_region will fail "silently" by returning None if the region name is wrong or not supported
            if conn is None:
                print("region name: %s likely not supported, or AWS is down.  connection to region failed." % region)
                sys.exit(1)

            reservations = []
            if self.ec2_instance_filters:
                for filter_key, filter_values in self.ec2_instance_filters.iteritems():
                    reservations.extend(conn.get_all_instances(filters = { filter_key : filter_values }))
            else:
                reservations = conn.get_all_instances()

            for reservation in reservations:
                for instance in reservation.instances:
                    self.add_instance(instance, region)

        except boto.exception.BotoServerError, e:
            if  not self.eucalyptus:
                print "Looks like AWS is down again:"
            print e
            sys.exit(1)

    def get_rds_instances_by_region(self, region):
        ''' Makes an AWS API call to the list of RDS instances in a particular
        region '''

        try:
            conn = rds.connect_to_region(region)
            if conn:
                instances = conn.get_all_dbinstances()
                for instance in instances:
                    self.add_rds_instance(instance, region)
        except boto.exception.BotoServerError, e:
            if not e.reason == "Forbidden":
                print "Looks like AWS RDS is down: "
                print e
                sys.exit(1)

    def get_instance(self, region, instance_id):
        ''' Gets details about a specific instance '''
        if self.eucalyptus:
            conn = boto.connect_euca(self.eucalyptus_host)
            conn.APIVersion = '2010-08-31'
        else:
            conn = ec2.connect_to_region(region)

        # connect_to_region will fail "silently" by returning None if the region name is wrong or not supported
        if conn is None:
            print("region name: %s likely not supported, or AWS is down.  connection to region failed." % region)
            sys.exit(1)

        reservations = conn.get_all_instances([instance_id])
        for reservation in reservations:
            for instance in reservation.instances:
                return instance

    def add_instance(self, instance, region):
        ''' Adds an instance to the inventory and index, as long as it is
        addressable '''

        # Only want running instances unless all_instances is True
        if not self.all_instances and instance.state != 'running':
            return

        # Select the best destination address
        if instance.subnet_id:
            dest = getattr(instance, self.vpc_destination_variable)
        else:
            dest =  getattr(instance, self.destination_variable)

        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return

        # if we only want to include hosts that match a pattern, skip those that don't
        if self.pattern_include and not self.pattern_include.match(dest):
            return

        # if we need to exclude hosts that match a pattern, skip those
        if self.pattern_exclude and self.pattern_exclude.match(dest):
            return

        # Add to index
        self.index[dest] = [region, instance.id]

        # Inventory: Group by instance ID (always a group of 1)
        self.inventory[instance.id] = [dest]
        if self.nested_groups:
            self.push_group(self.inventory, 'instances', instance.id)

        # Inventory: Group by region
        if self.nested_groups:
            self.push_group(self.inventory, 'regions', region)
        else:
            self.push(self.inventory, region, dest)

        # Inventory: Group by availability zone
        self.push(self.inventory, instance.placement, dest)
        if self.nested_groups:
            self.push_group(self.inventory, region, instance.placement)

        # Inventory: Group by instance type
        type_name = self.to_safe('type_' + instance.instance_type)
        self.push(self.inventory, type_name, dest)
        if self.nested_groups:
            self.push_group(self.inventory, 'types', type_name)

        # Inventory: Group by key pair
        if instance.key_name:
            key_name = self.to_safe('key_' + instance.key_name)
            self.push(self.inventory, key_name, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'keys', key_name)

        # Inventory: Group by VPC
        if instance.vpc_id:
            self.push(self.inventory, self.to_safe('vpc_id_' + instance.vpc_id), dest)

        # Inventory: Group by security group
        try:
            for group in instance.groups:
                key = self.to_safe("security_group_" + group.name)
                self.push(self.inventory, key, dest)
                if self.nested_groups:
                    self.push_group(self.inventory, 'security_groups', key)
        except AttributeError:
            print 'Package boto seems a bit older.'
            print 'Please upgrade boto >= 2.3.0.'
            sys.exit(1)

        # Inventory: Group by tag keys
        for k, v in instance.tags.iteritems():
            key = self.to_safe("tag_" + k + "=" + v)
            self.push(self.inventory, key, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'tags', self.to_safe("tag_" + k))
                self.push_group(self.inventory, self.to_safe("tag_" + k), key)

        # Inventory: Group by Route53 domain names if enabled
        if self.route53_enabled:
            route53_names = self.get_instance_route53_names(instance)
            for name in route53_names:
                self.push(self.inventory, name, dest)
                if self.nested_groups:
                    self.push_group(self.inventory, 'route53', name)

        # Global Tag: instances without tags
        if len(instance.tags) == 0:
            self.push(self.inventory, 'tag_none', dest)
            
        # Global Tag: tag all EC2 instances
        self.push(self.inventory, 'ec2', dest)

        self.inventory["_meta"]["hostvars"][dest] = self.get_host_info_dict_from_instance(instance)


    def add_rds_instance(self, instance, region):
        ''' Adds an RDS instance to the inventory and index, as long as it is
        addressable '''

        # Only want available instances unless all_rds_instances is True
        if not self.all_rds_instances and instance.status != 'available':
            return

        # Select the best destination address
        #if instance.subnet_id:
            #dest = getattr(instance, self.vpc_destination_variable)
        #else:
            #dest =  getattr(instance, self.destination_variable)
        dest = instance.endpoint[0]

        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return

        # Add to index
        self.index[dest] = [region, instance.id]

        # Inventory: Group by instance ID (always a group of 1)
        self.inventory[instance.id] = [dest]
        if self.nested_groups:
            self.push_group(self.inventory, 'instances', instance.id)

        # Inventory: Group by region
        if self.nested_groups:
            self.push_group(self.inventory, 'regions', region)
        else:
            self.push(self.inventory, region, dest)

        # Inventory: Group by availability zone
        self.push(self.inventory, instance.availability_zone, dest)
        if self.nested_groups:
            self.push_group(self.inventory, region, instance.availability_zone)

        # Inventory: Group by instance type
        type_name = self.to_safe('type_' + instance.instance_class)
        self.push(self.inventory, type_name, dest)
        if self.nested_groups:
            self.push_group(self.inventory, 'types', type_name)

        # Inventory: Group by security group
        try:
            if instance.security_group:
                key = self.to_safe("security_group_" + instance.security_group.name)
                self.push(self.inventory, key, dest)
                if self.nested_groups:
                    self.push_group(self.inventory, 'security_groups', key)

        except AttributeError:
            print 'Package boto seems a bit older.'
            print 'Please upgrade boto >= 2.3.0.'
            sys.exit(1)

        # Inventory: Group by engine
        self.push(self.inventory, self.to_safe("rds_" + instance.engine), dest)
        if self.nested_groups:
            self.push_group(self.inventory, 'rds_engines', self.to_safe("rds_" + instance.engine))

        # Inventory: Group by parameter group
        self.push(self.inventory, self.to_safe("rds_parameter_group_" + instance.parameter_group.name), dest)
        if self.nested_groups:
            self.push_group(self.inventory, 'rds_parameter_groups', self.to_safe("rds_parameter_group_" + instance.parameter_group.name))

        # Global Tag: all RDS instances
        self.push(self.inventory, 'rds', dest)

        self.inventory["_meta"]["hostvars"][dest] = self.get_host_info_dict_from_instance(instance)


    def get_route53_records(self):
        ''' Get and store the map of resource records to domain names that
        point to them. '''

        r53_conn = route53.Route53Connection()
        all_zones = r53_conn.get_zones()

        route53_zones = [ zone for zone in all_zones if zone.name[:-1]
                          not in self.route53_excluded_zones ]

        self.route53_records = {}

        for zone in route53_zones:
            rrsets = r53_conn.get_all_rrsets(zone.id)

            for record_set in rrsets:
                record_name = record_set.name

                if record_name.endswith('.'):
                    record_name = record_name[:-1]

                for resource in record_set.resource_records:
                    self.route53_records.setdefault(resource, set())
                    self.route53_records[resource].add(record_name)


    def get_instance_route53_names(self, instance):
        ''' Check if an instance is referenced in the records we have from
        Route53. If it is, return the list of domain names pointing to said
        instance. If nothing points to it, return an empty list. '''

        instance_attributes = [ 'public_dns_name', 'private_dns_name',
                                'ip_address', 'private_ip_address' ]

        name_list = set()

        for attrib in instance_attributes:
            try:
                value = getattr(instance, attrib)
            except AttributeError:
                continue

            if value in self.route53_records:
                name_list.update(self.route53_records[value])

        return list(name_list)


    def get_host_info_dict_from_instance(self, instance):
        instance_vars = {}
        for key in vars(instance):
            value = getattr(instance, key)
            key = self.to_safe('ec2_' + key)

            # Handle complex types
            # state/previous_state changed to properties in boto in https://github.com/boto/boto/commit/a23c379837f698212252720d2af8dec0325c9518
            if key == 'ec2__state':
                instance_vars['ec2_state'] = instance.state or ''
                instance_vars['ec2_state_code'] = instance.state_code
            elif key == 'ec2__previous_state':
                instance_vars['ec2_previous_state'] = instance.previous_state or ''
                instance_vars['ec2_previous_state_code'] = instance.previous_state_code
            elif type(value) in [int, bool]:
                instance_vars[key] = value
            elif type(value) in [str, unicode]:
                instance_vars[key] = value.strip()
            elif type(value) == type(None):
                instance_vars[key] = ''
            elif key == 'ec2_region':
                instance_vars[key] = value.name
            elif key == 'ec2__placement':
                instance_vars['ec2_placement'] = value.zone
            elif key == 'ec2_tags':
                for k, v in value.iteritems():
                    key = self.to_safe('ec2_tag_' + k)
                    instance_vars[key] = v
            elif key == 'ec2_groups':
                group_ids = []
                group_names = []
                for group in value:
                    group_ids.append(group.id)
                    group_names.append(group.name)
                instance_vars["ec2_security_group_ids"] = ','.join([str(i) for i in group_ids])
                instance_vars["ec2_security_group_names"] = ','.join([str(i) for i in group_names])
            else:
                pass
                # TODO Product codes if someone finds them useful
                #print key
                #print type(value)
                #print value

        return instance_vars

    def get_host_info(self):
        ''' Get variables about a specific host '''

        if len(self.index) == 0:
            # Need to load index from cache
            self.load_index_from_cache()

        if not self.args.host in self.index:
            # try updating the cache
            self.do_api_calls_update_cache()
            if not self.args.host in self.index:
                # host might not exist anymore
                return self.json_format_dict({}, True)

        (region, instance_id) = self.index[self.args.host]

        instance = self.get_instance(region, instance_id)
        return self.json_format_dict(self.get_host_info_dict_from_instance(instance), True)

    def push(self, my_dict, key, element):
        ''' Push an element onto an array that may not have been defined in
        the dict '''
        group_info = my_dict.setdefault(key, [])
        if isinstance(group_info, dict):
            host_list = group_info.setdefault('hosts', [])
            host_list.append(element)
        else:
            group_info.append(element)

    def push_group(self, my_dict, key, element):
        ''' Push a group as a child of another group. '''
        parent_group = my_dict.setdefault(key, {})
        if not isinstance(parent_group, dict):
            parent_group = my_dict[key] = {'hosts': parent_group}
        child_groups = parent_group.setdefault('children', [])
        if element not in child_groups:
            child_groups.append(element)

    def get_inventory_from_cache(self):
        ''' Reads the inventory from the cache file and returns it as a JSON
        object '''

        cache = open(self.cache_path_cache, 'r')
        json_inventory = cache.read()
        return json_inventory


    def load_index_from_cache(self):
        ''' Reads the index from the cache file sets self.index '''

        cache = open(self.cache_path_index, 'r')
        json_index = cache.read()
        self.index = json.loads(json_index)


    def write_to_cache(self, data, filename):
        ''' Writes data in JSON format to a file '''

        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()


    def to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be
        used as Ansible groups '''

        return re.sub("[^A-Za-z0-9\-]", "_", word)


    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


# Run the script
Ec2Inventory()

