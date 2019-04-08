# -*- coding: utf-8 -*-
# Copyright (c) 2019, Ximon Eighteen <ximon.eighteen@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: docker_machine
    plugin_type: inventory
    short_description: Docker Machine inventory source
    requirements:
        - L(Docker Machine,https://docs.docker.com/machine/)
    extends_documentation_fragment:
        - inventory_cache
        - constructed
    description:
        - Get inventory hosts from Docker Machine.
        - Uses a YAML configuration file that ends with docker_machine.(yml|yaml).
        - The plugin returns an I(all) group of nodes and one group per driver (e.g. digitalocean).
        - The plugin sets standard host variables C(ansible_host), C(ansible_port), C(ansible_user) and C(ansible_ssh_private_key).
        - The plugin also sets standard host variable I(ansible_ssh_common_args) to C(-o StrictHostKeyChecking=no).
        - The plugin also stores the Docker Machine 'env' variables in I(dm_) prefixed host variables.

    options:
        plugin:
          description: token that ensures this is a source file for the C(docker_machine) plugin.
          required: yes
          choices: ['docker_machine']
        verbose_output:
            description: Toggle to (not) include all available nodes metadata (e.g. Image, Region, Size) as a JSON object.
            type: bool
            default: yes
        split_tags:
          description: for keyed_groups add two variables as if the tag were actually a key value pair separated by a colon, instead of just a single value.
          type: bool
          default: no
        split_separator:
          description: for keyed_groups when splitting tags this is the separator to split the tag value on.
          type: str
          default: ":"
'''

EXAMPLES = '''
# Minimal example
plugin: docker_machine

# Example using constructed features to create a group per Docker Machine L(driver,https://docs.docker.com/machine/drivers/), e.g.:
#   $ docker-machine create --driver digitalocean ... mymachine
#   $ ansible-inventory -i ./path/to/docker-machine.yml --host=mymachine
#   {
#     ...
#     "digitalocean": {
#       "hosts": [
#           "mymachine"
#       ]
#     ...
#   }
strict: no
keyed_groups:
  - separator: ''
    key: docker_machine_node_attributes.DriverName

# Example grouping hosts by Digital Machine tag
strict: no
keyed_groups:
  - prefix: tag
    key: 'dm_tags'

# Example using tag splitting where the Docker Machine was created with a tag containing a ':' in the value.
# When using multiple tags this is perhaps more useful than 'dm_tags' as it will create a separate variable
# per key:value pair encoded in the tag value, e.g.
#   $ docker-machine create --driver digitalocean ... --digitalocean-tags 'mycolon:separatedtagvalue,myother:tagvalue' mymachine
#   $ docker-machine inspect mymachine --format '{{ .Driver.Tags }}'
#   mycolon:separatedtagvalue,myother:tagvalue
#   $ ansible-inventory -i ./path/to/docker-machine.yml --host=mymachine
#   {
#     ...
#     "dm_tags": "mycolon:separatedtagvalue,myother:Tag",
#     "dm_tag_mycolon": "separatedtagvalue",
#     "dm_tag_myother": "tagvalue",
#     ...
#   }
strict: no
split_tags: yes
split_separator: ":"
keyed_groups:
  - prefix: gantry_component
    key: 'dm_tag_gantry_component'

# Example using compose to override the default SSH behaviour of asking the user to accept the remote host key
compose:
  ansible_ssh_common_args: '"-o StrictHostKeyChecking=accept-new"'
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

    def _set_docker_daemon_variables(self, id):
        '''
        Capture settings from Docker Machine that would be needed to connect to the remote Docker daemon installed on
        the Docker Machine remote host. Note: passing '--shell=sh' is a workaround for 'Error: Unknown shell'.
        '''
        env_out = self._run_command('env', '--shell=sh', id)

        # example output of docker-machine env --shell=sh:
        #   export DOCKER_TLS_VERIFY="1"
        #   export DOCKER_HOST="tcp://134.209.204.160:2376"
        #   export DOCKER_CERT_PATH="/root/.docker/machine/machines/routinator"
        #   export DOCKER_MACHINE_NAME="routinator"
        #   # Run this command to configure your shell:
        #   # eval $(docker-machine env --shell=bash routinator)

        # capture any of the DOCKER_xxx variables that were output and create Ansible host vars
        # with the same name and value but with a dm_ name prefix.
        for line in env_out.splitlines():
            match = re.search('(DOCKER_[^=]+)="([^"]+)"', line)
            if match:
                env_var_name = match.group(1)
                env_var_value = match.group(2)
                self.inventory.set_variable(id, 'dm_{0}'.format(env_var_name), env_var_value)

    def _set_tag_variables(self, id):
        tags = self.node_attrs['Driver'].get('Tags') or ''
        self.inventory.set_variable(id, 'dm_tags', tags)

        if tags:
            split_tags = self.get_option('split_tags')
            split_separator = self.get_option('split_separator')

            kv_pairs = [kv_pair.strip() for kv_pair in tags.split(',') if kv_pair.strip()]
            for kv_pair in kv_pairs:
                if split_tags and split_separator in kv_pair:
                    k, v = kv_pair.split(split_separator)
                    self.inventory.set_variable(id, 'dm_tag_{0}'.format(k), v)
                else:
                    self.inventory.set_variable(id, 'dm_tag_{0}'.format(kv_pair))

    def _populate(self):
        self.inventory.add_group('all')

        try:
            self.nodes = self._run_command('ls', '-q').splitlines()
            for self.node in self.nodes:
                self.node_attrs = json.loads(self._run_command('inspect', self.node))

                id = self.node_attrs['Driver']['MachineName']
                self.inventory.add_host(id)
                self.inventory.add_host(id, group='all')

                # Find out more about the following variables at: https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html
                self.inventory.set_variable(id, 'ansible_host', self.node_attrs['Driver']['IPAddress'])
                self.inventory.set_variable(id, 'ansible_port', self.node_attrs['Driver']['SSHPort'])
                self.inventory.set_variable(id, 'ansible_user', self.node_attrs['Driver']['SSHUser'])
                self.inventory.set_variable(id, 'ansible_ssh_private_key_file', self.node_attrs['Driver']['SSHKeyPath'])

                self._set_docker_daemon_variables(id)

                self._set_tag_variables(id)

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
            raise AnsibleError('Unable to fetch hosts from Docker Machine, this was the original exception: %s' %
                               to_native(e))

    def verify_file(self, path):
        """Return the possibility of a file being consumable by this plugin."""
        return (
            super(InventoryModule, self).verify_file(path) and
            path.endswith((self.NAME + '.yaml', self.NAME + '.yml')))

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)
        self._populate()
