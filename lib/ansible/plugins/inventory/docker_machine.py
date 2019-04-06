# -*- coding: utf-8 -*-
# Copyright (c) 2019, Ximon Eighteen <ximon.eighteen@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: docker_machine
    plugin_type: inventory
    short_description: Docker machine inventory source
    requirements:
        - L(Docker Machine,https://docs.docker.com/machine/)
    extends_documentation_fragment:
        - inventory_cache
        - constructed
    description:
        - Get inventory hosts from Docker Machine.
        - Uses a YAML configuration file that ends with docker_machine.(yml|yaml).
        - The plugin returns an I(all) group of nodes and one group per driver (e.g. digitalocean).
        - The plugin sets standard host variables I(ansible_host), I(ansible_port), I(ansible_user) and I(ansible_ssh_private_key).
        - The plugin also sets standard host variable I(ansible_ssh_common_args) to '-o StrictHostKeyChecking=no'.
        - The plugin also stores the Docker Machine 'env' variables in I(dm_) prefixed host variables.

    options:
        plugin:
          description: token that ensures this is a source file for the C(docker_machine) plugin.
          required: True
          choices: ['docker_machine']
        verbose_output:
            description: Toggle to (not) include all available nodes metadata (e.g. Image, Region, Size) as a JSON object.
            type: bool
            default: yes
        split_tags:
          description: for keyed_groups add two variables as if the tag were actually a key value pair separated by a colon, instead of just a single value.
          required: False
          type: bool
          default: no
        split_separator:
          description: for keyed_groups when splitting tags this is the separator to split the tag value on.
          required: False
          type: str
          default: ":"
'''

EXAMPLES = '''
# Minimal example
plugin: docker_machine

# Example using constructed features to create groups
# keyed_groups may be used to create custom groups
strict: False
keyed_groups:
  - prefix: tag
    key: 'dm_tags'

# Example using tag splitting where the tag is like 'dm_tag_gantry_component:routinator'
strict: False
split_tags: True
split_separator: ":"
keyed_groups:
  - prefix: gantry_component
    key: 'dm_tag_gantry_component'
'''

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.module_utils._text import to_text
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

import json
import re
import subprocess


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    ''' Host inventory parser for ansible using Docker machine as source. '''

    NAME = 'docker_machine'

    def _run_command(self, *args):
        return subprocess.check_output(["docker-machine"] + list(args)).decode('utf-8').strip()

    def _populate(self):
        self.inventory.add_group('all')

        try:
            self.nodes = self._run_command('ls', '-q').splitlines()
            for self.node in self.nodes:
                self.node_attrs = json.loads(self._run_command('inspect', self.node))

                id = self.node_attrs['Driver']['MachineName']
                self.inventory.add_host(id)
                self.inventory.add_group(self.node_attrs['DriverName'])
                self.inventory.add_host(id, group=self.node_attrs['DriverName'])
                self.inventory.add_host(id, group='all')

                # Find out more about the following variables at: https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html
                self.inventory.set_variable(id, 'ansible_host', self.node_attrs['Driver']['IPAddress'])
                self.inventory.set_variable(id, 'ansible_port', self.node_attrs['Driver']['SSHPort'])
                self.inventory.set_variable(id, 'ansible_user', self.node_attrs['Driver']['SSHUser'])
                self.inventory.set_variable(id, 'ansible_ssh_common_args', '-o StrictHostKeyChecking=no')
                self.inventory.set_variable(id, 'ansible_ssh_private_key_file', self.node_attrs['Driver']['SSHKeyPath'])

                # pass '--shell=bash' to workaround 'Error: Unknown shell
                env_out = self._run_command('env', '--shell=bash', id)

                # example output of docker-machine env
                #   export DOCKER_TLS_VERIFY="1"
                #   export DOCKER_HOST="tcp://134.209.204.160:2376"
                #   export DOCKER_CERT_PATH="/root/.docker/machine/machines/routinator"
                #   export DOCKER_MACHINE_NAME="routinator"
                #   # Run this command to configure your shell:
                #   # eval $(docker-machine env --shell=bash routinator)

                for env_var_name in ['DOCKER_TLS_VERIFY', 'DOCKER_HOST', 'DOCKER_CERT_PATH', 'DOCKER_MACHINE_NAME']:
                    env_var_value = re.search('{0}="([^"]+)"'.format(env_var_name), env_out).group(1)
                    self.inventory.set_variable(id, 'dm_{0}'.format(env_var_name), env_var_value)

                # Capture any tags
                split_tags = self.get_option('split_tags')
                split_separator = self.get_option('split_separator')
                tags = self.node_attrs['Driver']['Tags']
                for kv_pair in tags.split(','):
                    if split_tags and split_separator in kv_pair:
                        k, v = kv_pair.split(split_separator)
                        self.inventory.set_variable(id, 'dm_tag_{0}'.format(k), v)
                    else:
                        self.inventory.set_variable(id, 'dm_tag_{0}'.format(kv_pair))

                if self.get_option('verbose_output'):
                    self.inventory.set_variable(id, 'docker_machine_node_attributes', self.node_attrs)

                # Use constructed if applicable
                strict = self.get_option('strict')

                # Composed variables
                self._set_composite_vars(self.get_option('compose'), self.node_attrs, id, strict=strict)

                # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
                self._add_host_to_composed_groups(self.get_option('groups'), self.node_attrs, id, strict=strict)

                # Create groups based on variable values and add the corresponding hosts to it
                self._add_host_to_keyed_groups(self.get_option('keyed_groups'), self.node_attrs, id, strict=strict)

        except Exception as e:
            raise AnsibleError('Unable to fetch hosts from Docker machine, this was the original exception: %s' %
                               to_native(e))

    def verify_file(self, path):
        """Return the possibility of a file being consumable by this plugin."""
        return (
            super(InventoryModule, self).verify_file(path) and
            path.endswith((self.NAME + '.yaml', self.NAME + '.yml')))

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        config = self._read_config_data(path)
        self._populate()
