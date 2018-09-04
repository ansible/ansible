# Copyright (c) 2012, Marco Vito Moscaritolo <marco@agavee.com>
# Copyright (c) 2013, Jesse Keating <jesse.keating@rackspace.com>
# Copyright (c) 2015, Hewlett-Packard Development Company, L.P.
# Copyright (c) 2016, Rackspace Australia
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: openstack
    plugin_type: inventory
    authors:
      - Marco Vito Moscaritolo <marco@agavee.com>
      - Jesse Keating <jesse.keating@rackspace.com>
    short_description: OpenStack inventory source
    extends_documentation_fragment:
        - inventory_cache
        - constructed
    description:
        - Get inventory hosts from OpenStack clouds
        - Uses openstack.(yml|yaml) YAML configuration file to configure the inventory plugin
        - Uses standard clouds.yaml YAML configuration file to configure cloud credentials
    options:
        show_all:
            description: toggles showing all vms vs only those with a working IP
            type: bool
            default: 'no'
        inventory_hostname:
            description: |
                What to register as the inventory hostname.
                If set to 'uuid' the uuid of the server will be used and a
                group will be created for the server name.
                If set to 'name' the name of the server will be used unless
                there are more than one server with the same name in which
                case the 'uuid' logic will be used.
                Default is to do 'name', which is the opposite of the old
                openstack.py inventory script's option use_hostnames)
            type: string
            choices:
                - name
                - uuid
            default: "name"
        expand_hostvars:
            description: |
                Run extra commands on each host to fill in additional
                information about the host. May interrogate cinder and
                neutron and can be expensive for people with many hosts.
                (Note, the default value of this is opposite from the default
                old openstack.py inventory script's option expand_hostvars)
            type: bool
            default: 'no'
        private:
            description: |
                Use the private interface of each server, if it has one, as
                the host's IP in the inventory. This can be useful if you are
                running ansible inside a server in the cloud and would rather
                communicate to your servers over the private network.
            type: bool
            default: 'no'
        only_clouds:
            description: |
                List of clouds from clouds.yaml to use, instead of using
                the whole list.
            type: list
            default: []
        fail_on_errors:
            description: |
                Causes the inventory to fail and return no hosts if one cloud
                has failed (for example, bad credentials or being offline).
                When set to False, the inventory will return as many hosts as
                it can from as many clouds as it can contact. (Note, the
                default value of this is opposite from the old openstack.py
                inventory script's option fail_on_errors)
            type: bool
            default: 'no'
        clouds_yaml_path:
            description: |
                Override path to clouds.yaml file. If this value is given it
                will be searched first. The default path for the
                ansible inventory adds /etc/ansible/openstack.yaml and
                /etc/ansible/openstack.yml to the regular locations documented
                at https://docs.openstack.org/os-client-config/latest/user/configuration.html#config-files
            type: string
        compose:
            description: Create vars from jinja2 expressions.
            type: dictionary
            default: {}
        groups:
            description: Add hosts to group based on Jinja2 conditionals.
            type: dictionary
            default: {}
'''

EXAMPLES = '''
# file must be named openstack.yaml or openstack.yml
# Make the plugin behave like the default behavior of the old script
plugin: openstack
expand_hostvars: yes
fail_on_errors: yes
'''

import collections

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

try:
    # Due to the name shadowing we should import other way
    import importlib
    sdk = importlib.import_module('openstack')
    sdk_inventory = importlib.import_module('openstack.cloud.inventory')
    client_config = importlib.import_module('openstack.config.loader')
    HAS_SDK = True
except ImportError:
    HAS_SDK = False


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    ''' Host inventory provider for ansible using OpenStack clouds. '''

    NAME = 'openstack'

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)

        cache_key = self._get_cache_prefix(path)

        # file is config file
        self._config_data = self._read_config_data(path)

        msg = ''
        if not self._config_data:
            msg = 'File empty. this is not my config file'
        elif 'plugin' in self._config_data and self._config_data['plugin'] != self.NAME:
            msg = 'plugin config file, but not for us: %s' % self._config_data['plugin']
        elif 'plugin' not in self._config_data and 'clouds' not in self._config_data:
            msg = "it's not a plugin configuration nor a clouds.yaml file"
        elif not HAS_SDK:
            msg = "openstacksdk is required for the OpenStack inventory plugin. OpenStack inventory sources will be skipped."

        if msg:
            raise AnsibleParserError(msg)

        # The user has pointed us at a clouds.yaml file. Use defaults for
        # everything.
        if 'clouds' in self._config_data:
            self._config_data = {}

        if cache:
            cache = self.get_option('cache')
        source_data = None
        if cache:
            try:
                source_data = self.cache.get(cache_key)
            except KeyError:
                pass

        if not source_data:
            clouds_yaml_path = self._config_data.get('clouds_yaml_path')
            if clouds_yaml_path:
                config_files = (clouds_yaml_path +
                                client_config.CONFIG_FILES)
            else:
                config_files = None

            # TODO(mordred) Integrate shade's logging with ansible's logging
            sdk.enable_logging()

            cloud_inventory = sdk_inventory.OpenStackInventory(
                config_files=config_files,
                private=self._config_data.get('private', False))
            only_clouds = self._config_data.get('only_clouds', [])
            if only_clouds and not isinstance(only_clouds, list):
                raise ValueError(
                    'OpenStack Inventory Config Error: only_clouds must be'
                    ' a list')
            if only_clouds:
                new_clouds = []
                for cloud in cloud_inventory.clouds:
                    if cloud.name in only_clouds:
                        new_clouds.append(cloud)
                cloud_inventory.clouds = new_clouds

            expand_hostvars = self._config_data.get('expand_hostvars', False)
            fail_on_errors = self._config_data.get('fail_on_errors', False)

            source_data = cloud_inventory.list_hosts(
                expand=expand_hostvars, fail_on_cloud_config=fail_on_errors)

            self.cache.set(cache_key, source_data)

        self._populate_from_source(source_data)

    def _populate_from_source(self, source_data):
        groups = collections.defaultdict(list)
        firstpass = collections.defaultdict(list)
        hostvars = {}

        use_server_id = (
            self._config_data.get('inventory_hostname', 'name') != 'name')
        show_all = self._config_data.get('show_all', False)

        for server in source_data:
            if 'interface_ip' not in server and not show_all:
                continue
            firstpass[server['name']].append(server)

        for name, servers in firstpass.items():
            if len(servers) == 1 and not use_server_id:
                self._append_hostvars(hostvars, groups, name, servers[0])
            else:
                server_ids = set()
                # Trap for duplicate results
                for server in servers:
                    server_ids.add(server['id'])
                if len(server_ids) == 1 and not use_server_id:
                    self._append_hostvars(hostvars, groups, name, servers[0])
                else:
                    for server in servers:
                        self._append_hostvars(
                            hostvars, groups, server['id'], server,
                            namegroup=True)

        self._set_variables(hostvars, groups)

    def _set_variables(self, hostvars, groups):

        # set vars in inventory from hostvars
        for host in hostvars:

            # create composite vars
            self._set_composite_vars(
                self._config_data.get('compose'), hostvars, host)

            # actually update inventory
            for key in hostvars[host]:
                self.inventory.set_variable(host, key, hostvars[host][key])

            # constructed groups based on conditionals
            self._add_host_to_composed_groups(
                self._config_data.get('groups'), hostvars, host)

        for group_name, group_hosts in groups.items():
            self.inventory.add_group(group_name)
            for host in group_hosts:
                self.inventory.add_child(group_name, host)

    def _get_groups_from_server(self, server_vars, namegroup=True):
        groups = []

        region = server_vars['region']
        cloud = server_vars['cloud']
        metadata = server_vars.get('metadata', {})

        # Create a group for the cloud
        groups.append(cloud)

        # Create a group on region
        if region:
            groups.append(region)

        # And one by cloud_region
        groups.append("%s_%s" % (cloud, region))

        # Check if group metadata key in servers' metadata
        if 'group' in metadata:
            groups.append(metadata['group'])

        for extra_group in metadata.get('groups', '').split(','):
            if extra_group:
                groups.append(extra_group.strip())

        groups.append('instance-%s' % server_vars['id'])
        if namegroup:
            groups.append(server_vars['name'])

        for key in ('flavor', 'image'):
            if 'name' in server_vars[key]:
                groups.append('%s-%s' % (key, server_vars[key]['name']))

        for key, value in iter(metadata.items()):
            groups.append('meta-%s_%s' % (key, value))

        az = server_vars.get('az', None)
        if az:
            # Make groups for az, region_az and cloud_region_az
            groups.append(az)
            groups.append('%s_%s' % (region, az))
            groups.append('%s_%s_%s' % (cloud, region, az))
        return groups

    def _append_hostvars(self, hostvars, groups, current_host,
                         server, namegroup=False):
        hostvars[current_host] = dict(
            ansible_ssh_host=server['interface_ip'],
            ansible_host=server['interface_ip'],
            openstack=server)
        self.inventory.add_host(current_host)

        for group in self._get_groups_from_server(server, namegroup=namegroup):
            groups[group].append(current_host)

    def verify_file(self, path):

        if super(InventoryModule, self).verify_file(path):
            for fn in ('openstack', 'clouds'):
                for suffix in ('yaml', 'yml'):
                    maybe = '{fn}.{suffix}'.format(fn=fn, suffix=suffix)
                    if path.endswith(maybe):
                        return True
        return False
