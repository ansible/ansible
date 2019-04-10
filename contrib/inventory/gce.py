#!/usr/bin/env python

# Copyright: (c) 2013, Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

'''
GCE external inventory script
=================================

Generates inventory that Ansible can understand by making API requests
Google Compute Engine via the libcloud library.  Full install/configuration
instructions for the gce* modules can be found in the comments of
ansible/test/gce_tests.py.

When run against a specific host, this script returns the following variables
based on the data obtained from the libcloud Node object:
 - gce_uuid
 - gce_id
 - gce_image
 - gce_machine_type
 - gce_private_ip
 - gce_public_ip
 - gce_name
 - gce_description
 - gce_status
 - gce_zone
 - gce_tags
 - gce_metadata
 - gce_network
 - gce_subnetwork

When run in --list mode, instances are grouped by the following categories:
 - zone:
   zone group name examples are us-central1-b, europe-west1-a, etc.
 - instance tags:
   An entry is created for each tag.  For example, if you have two instances
   with a common tag called 'foo', they will both be grouped together under
   the 'tag_foo' name.
 - network name:
   the name of the network is appended to 'network_' (e.g. the 'default'
   network will result in a group named 'network_default')
 - machine type
   types follow a pattern like n1-standard-4, g1-small, etc.
 - running status:
   group name prefixed with 'status_' (e.g. status_running, status_stopped,..)
 - image:
   when using an ephemeral/scratch disk, this will be set to the image name
   used when creating the instance (e.g. debian-7-wheezy-v20130816).  when
   your instance was created with a root persistent disk it will be set to
   'persistent_disk' since there is no current way to determine the image.

Examples:
  Execute uname on all instances in the us-central1-a zone
  $ ansible -i gce.py us-central1-a -m shell -a "/bin/uname -a"

  Use the GCE inventory script to print out instance specific information
  $ contrib/inventory/gce.py --host my_instance

Author: Eric Johnson <erjohnso@google.com>
Contributors: Matt Hite <mhite@hotmail.com>, Tom Melendez <supertom@google.com>,
              John Roach <johnroach1985@gmail.com>
Version: 0.0.4
'''

try:
    import pkg_resources
except ImportError:
    # Use pkg_resources to find the correct versions of libraries and set
    # sys.path appropriately when there are multiversion installs.  We don't
    # fail here as there is code that better expresses the errors where the
    # library is used.
    pass

USER_AGENT_PRODUCT = "Ansible-gce_inventory_plugin"
USER_AGENT_VERSION = "v2"

import sys
import os
import argparse

from time import time

from ansible.module_utils.six.moves import configparser

import logging
logging.getLogger('libcloud.common.google').addHandler(logging.NullHandler())

import json

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    _ = Provider.GCE
except Exception:
    sys.exit("GCE inventory script requires libcloud >= 0.13")


class CloudInventoryCache(object):
    def __init__(self, cache_name='ansible-cloud-cache', cache_path='/tmp',
                 cache_max_age=300):
        cache_dir = os.path.expanduser(cache_path)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.cache_path_cache = os.path.join(cache_dir, cache_name)

        self.cache_max_age = cache_max_age

    def is_valid(self, max_age=None):
        ''' Determines if the cache files have expired, or if it is still valid '''

        if max_age is None:
            max_age = self.cache_max_age

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + max_age) > current_time:
                return True

        return False

    def get_all_data_from_cache(self, filename=''):
        ''' Reads the JSON inventory from the cache file. Returns Python dictionary. '''

        data = ''
        if not filename:
            filename = self.cache_path_cache
        with open(filename, 'r') as cache:
            data = cache.read()
        return json.loads(data)

    def write_to_cache(self, data, filename=''):
        ''' Writes data to file as JSON.  Returns True. '''
        if not filename:
            filename = self.cache_path_cache
        json_data = json.dumps(data)
        with open(filename, 'w') as cache:
            cache.write(json_data)
        return True


class GceInventory(object):
    def __init__(self):
        # Cache object
        self.cache = None
        # dictionary containing inventory read from disk
        self.inventory = {}

        # Read settings and parse CLI arguments
        self.parse_cli_args()
        self.config = self.get_config()
        self.drivers = self.get_gce_drivers()
        self.ip_type = self.get_inventory_options()
        if self.ip_type:
            self.ip_type = self.ip_type.lower()

        # Cache management
        start_inventory_time = time()
        cache_used = False
        if self.args.refresh_cache or not self.cache.is_valid():
            self.do_api_calls_update_cache()
        else:
            self.load_inventory_from_cache()
            cache_used = True
            self.inventory['_meta']['stats'] = {'use_cache': True}
        self.inventory['_meta']['stats'] = {
            'inventory_load_time': time() - start_inventory_time,
            'cache_used': cache_used
        }

        # Just display data for specific host
        if self.args.host:
            print(self.json_format_dict(
                self.inventory['_meta']['hostvars'][self.args.host],
                pretty=self.args.pretty))
        else:
            # Otherwise, assume user wants all instances grouped
            zones = self.parse_env_zones()
            print(self.json_format_dict(self.inventory,
                                        pretty=self.args.pretty))
        sys.exit(0)

    def get_config(self):
        """
        Reads the settings from the gce.ini file.

        Populates a ConfigParser object with defaults and
        attempts to read an .ini-style configuration from the filename
        specified in GCE_INI_PATH. If the environment variable is
        not present, the filename defaults to gce.ini in the current
        working directory.
        """
        gce_ini_default_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "gce.ini")
        gce_ini_path = os.environ.get('GCE_INI_PATH', gce_ini_default_path)

        # Create a ConfigParser.
        # This provides empty defaults to each key, so that environment
        # variable configuration (as opposed to INI configuration) is able
        # to work.
        config = configparser.ConfigParser(defaults={
            'gce_service_account_email_address': '',
            'gce_service_account_pem_file_path': '',
            'gce_project_id': '',
            'gce_zone': '',
            'libcloud_secrets': '',
            'instance_tags': '',
            'inventory_ip_type': '',
            'cache_path': '~/.ansible/tmp',
            'cache_max_age': '300'
        })
        if 'gce' not in config.sections():
            config.add_section('gce')
        if 'inventory' not in config.sections():
            config.add_section('inventory')
        if 'cache' not in config.sections():
            config.add_section('cache')

        config.read(gce_ini_path)

        #########
        # Section added for processing ini settings
        #########

        # Set the instance_states filter based on config file options
        self.instance_states = []
        if config.has_option('gce', 'instance_states'):
            states = config.get('gce', 'instance_states')
            # Ignore if instance_states is an empty string.
            if states:
                self.instance_states = states.split(',')

        # Set the instance_tags filter, env var overrides config from file
        # and cli param overrides all
        if self.args.instance_tags:
            self.instance_tags = self.args.instance_tags
        else:
            self.instance_tags = os.environ.get(
                'GCE_INSTANCE_TAGS', config.get('gce', 'instance_tags'))
        if self.instance_tags:
            self.instance_tags = self.instance_tags.split(',')

        # Caching
        cache_path = config.get('cache', 'cache_path')
        cache_max_age = config.getint('cache', 'cache_max_age')
        # TOOD(supertom): support project-specific caches
        cache_name = 'ansible-gce.cache'
        self.cache = CloudInventoryCache(cache_path=cache_path,
                                         cache_max_age=cache_max_age,
                                         cache_name=cache_name)
        return config

    def get_inventory_options(self):
        """Determine inventory options. Environment variables always
        take precedence over configuration files."""
        ip_type = self.config.get('inventory', 'inventory_ip_type')
        # If the appropriate environment variables are set, they override
        # other configuration
        ip_type = os.environ.get('INVENTORY_IP_TYPE', ip_type)
        return ip_type

    def get_gce_drivers(self):
        """Determine the GCE authorization settings and return a list of
        libcloud drivers.
        """
        # Attempt to get GCE params from a configuration file, if one
        # exists.
        secrets_path = self.config.get('gce', 'libcloud_secrets')
        secrets_found = False

        try:
            import secrets
            args = list(secrets.GCE_PARAMS)
            kwargs = secrets.GCE_KEYWORD_PARAMS
            secrets_found = True
        except Exception:
            pass

        if not secrets_found and secrets_path:
            if not secrets_path.endswith('secrets.py'):
                err = "Must specify libcloud secrets file as "
                err += "/absolute/path/to/secrets.py"
                sys.exit(err)
            sys.path.append(os.path.dirname(secrets_path))
            try:
                import secrets
                args = list(getattr(secrets, 'GCE_PARAMS', []))
                kwargs = getattr(secrets, 'GCE_KEYWORD_PARAMS', {})
                secrets_found = True
            except Exception:
                pass

        if not secrets_found:
            args = [
                self.config.get('gce', 'gce_service_account_email_address'),
                self.config.get('gce', 'gce_service_account_pem_file_path')
            ]
            kwargs = {'project': self.config.get('gce', 'gce_project_id'),
                      'datacenter': self.config.get('gce', 'gce_zone')}

        # If the appropriate environment variables are set, they override
        # other configuration; process those into our args and kwargs.
        args[0] = os.environ.get('GCE_EMAIL', args[0])
        args[1] = os.environ.get('GCE_PEM_FILE_PATH', args[1])
        args[1] = os.environ.get('GCE_CREDENTIALS_FILE_PATH', args[1])

        kwargs['project'] = os.environ.get('GCE_PROJECT', kwargs['project'])
        kwargs['datacenter'] = os.environ.get('GCE_ZONE', kwargs['datacenter'])

        gce_drivers = []
        projects = kwargs['project'].split(',')
        for project in projects:
            kwargs['project'] = project
            gce = get_driver(Provider.GCE)(*args, **kwargs)
            gce.connection.user_agent_append(
                '%s/%s' % (USER_AGENT_PRODUCT, USER_AGENT_VERSION),
            )
            gce_drivers.append(gce)
        return gce_drivers

    def parse_env_zones(self):
        '''returns a list of comma separated zones parsed from the GCE_ZONE environment variable.
        If provided, this will be used to filter the results of the grouped_instances call'''
        import csv
        reader = csv.reader([os.environ.get('GCE_ZONE', "")], skipinitialspace=True)
        zones = [r for r in reader]
        return [z for z in zones[0]]

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(
            description='Produce an Ansible Inventory file based on GCE')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                            help='Get all information about an instance')
        parser.add_argument('--instance-tags', action='store',
                            help='Only include instances with this tags, separated by comma')
        parser.add_argument('--pretty', action='store_true', default=False,
                            help='Pretty format (default: False)')
        parser.add_argument(
            '--refresh-cache', action='store_true', default=False,
            help='Force refresh of cache by making API requests (default: False - use cache files)')
        self.args = parser.parse_args()

    def node_to_dict(self, inst):
        md = {}

        if inst is None:
            return {}

        if 'items' in inst.extra['metadata']:
            for entry in inst.extra['metadata']['items']:
                md[entry['key']] = entry['value']

        net = inst.extra['networkInterfaces'][0]['network'].split('/')[-1]
        subnet = None
        if 'subnetwork' in inst.extra['networkInterfaces'][0]:
            subnet = inst.extra['networkInterfaces'][0]['subnetwork'].split('/')[-1]
        # default to exernal IP unless user has specified they prefer internal
        if self.ip_type == 'internal':
            ssh_host = inst.private_ips[0]
        else:
            ssh_host = inst.public_ips[0] if len(inst.public_ips) >= 1 else inst.private_ips[0]

        return {
            'gce_uuid': inst.uuid,
            'gce_id': inst.id,
            'gce_image': inst.image,
            'gce_machine_type': inst.size,
            'gce_private_ip': inst.private_ips[0],
            'gce_public_ip': inst.public_ips[0] if len(inst.public_ips) >= 1 else None,
            'gce_name': inst.name,
            'gce_description': inst.extra['description'],
            'gce_status': inst.extra['status'],
            'gce_zone': inst.extra['zone'].name,
            'gce_tags': inst.extra['tags'],
            'gce_metadata': md,
            'gce_network': net,
            'gce_subnetwork': subnet,
            # Hosts don't have a public name, so we add an IP
            'ansible_ssh_host': ssh_host
        }

    def load_inventory_from_cache(self):
        ''' Loads inventory from JSON on disk. '''

        try:
            self.inventory = self.cache.get_all_data_from_cache()
            hosts = self.inventory['_meta']['hostvars']
        except Exception as e:
            print(
                "Invalid inventory file %s.  Please rebuild with -refresh-cache option."
                % (self.cache.cache_path_cache))
            raise

    def do_api_calls_update_cache(self):
        ''' Do API calls and save data in cache. '''
        zones = self.parse_env_zones()
        data = self.group_instances(zones)
        self.cache.write_to_cache(data)
        self.inventory = data

    def list_nodes(self):
        all_nodes = []
        params, more_results = {'maxResults': 500}, True
        while more_results:
            for driver in self.drivers:
                driver.connection.gce_params = params
                all_nodes.extend(driver.list_nodes())
                more_results = 'pageToken' in params
        return all_nodes

    def group_instances(self, zones=None):
        '''Group all instances'''
        groups = {}
        meta = {}
        meta["hostvars"] = {}

        for node in self.list_nodes():

            # This check filters on the desired instance states defined in the
            # config file with the instance_states config option.
            #
            # If the instance_states list is _empty_ then _ALL_ states are returned.
            #
            # If the instance_states list is _populated_ then check the current
            # state against the instance_states list
            if self.instance_states and not node.extra['status'] in self.instance_states:
                continue

            # This check filters on the desired instance tags defined in the
            # config file with the instance_tags config option, env var GCE_INSTANCE_TAGS,
            # or as the cli param --instance-tags.
            #
            # If the instance_tags list is _empty_ then _ALL_ instances are returned.
            #
            # If the instance_tags list is _populated_ then check the current
            # instance tags against the instance_tags list. If the instance has
            # at least one tag from the instance_tags list, it is returned.
            if self.instance_tags and not set(self.instance_tags) & set(node.extra['tags']):
                continue

            name = node.name

            meta["hostvars"][name] = self.node_to_dict(node)

            zone = node.extra['zone'].name

            # To avoid making multiple requests per zone
            # we list all nodes and then filter the results
            if zones and zone not in zones:
                continue

            if zone in groups:
                groups[zone].append(name)
            else:
                groups[zone] = [name]

            tags = node.extra['tags']
            for t in tags:
                if t.startswith('group-'):
                    tag = t[6:]
                else:
                    tag = 'tag_%s' % t
                if tag in groups:
                    groups[tag].append(name)
                else:
                    groups[tag] = [name]

            net = node.extra['networkInterfaces'][0]['network'].split('/')[-1]
            net = 'network_%s' % net
            if net in groups:
                groups[net].append(name)
            else:
                groups[net] = [name]

            machine_type = node.size
            if machine_type in groups:
                groups[machine_type].append(name)
            else:
                groups[machine_type] = [name]

            image = node.image or 'persistent_disk'
            if image in groups:
                groups[image].append(name)
            else:
                groups[image] = [name]

            status = node.extra['status']
            stat = 'status_%s' % status.lower()
            if stat in groups:
                groups[stat].append(name)
            else:
                groups[stat] = [name]

            for private_ip in node.private_ips:
                groups[private_ip] = [name]

            if len(node.public_ips) >= 1:
                for public_ip in node.public_ips:
                    groups[public_ip] = [name]

        groups["_meta"] = meta

        return groups

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


# Run the script
if __name__ == '__main__':
    GceInventory()
