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
        - The plugin sets standard host variables C(ansible_host), C(ansible_port), C(ansible_user) and C(ansible_ssh_private_key).
        - The plugin stores the Docker Machine 'env' output variables in I(dm_) prefixed host variables.

    options:
        plugin:
            description: token that ensures this is a source file for the C(docker_machine) plugin.
            required: yes
            choices: ['docker_machine']
        daemon_required:
            description: when true, hosts for which Docker Machine cannot output Docker daemon connection environment variables will be skipped.
            type: bool
            default: yes
        running_required:
            description: when true, hosts which Docker Machine indicates are in a state other than C(running) will be skipped.
            type: bool
            default: yes
        verbose_output:
            description: when true, include all available nodes metadata (e.g. Image, Region, Size) as a JSON object.
            type: bool
            default: yes
'''

EXAMPLES = '''
# Minimal example
plugin: docker_machine

# Example using constructed features to create a group per Docker Machine driver
# (https://docs.docker.com/machine/drivers/), e.g.:
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

# Example using compose to override the default SSH behaviour of asking the user to accept the remote host key
compose:
  ansible_ssh_common_args: '"-o StrictHostKeyChecking=accept-new"'
'''

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.module_utils._text import to_text
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.utils.display import Display

import json
import re
import subprocess

display = Display()


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    ''' Host inventory parser for ansible using Docker machine as source. '''

    NAME = 'docker_machine'

    def _run_command(self, args):
        command = ['docker-machine']
        command.extend(args)
        display.debug('Executing command {0}'.format(command))
        try:
            result = subprocess.check_output(command)
        except Exception as e:
            display.warning('Exception {0} caught while executing command {1}, this was the original exception: {2}'.format(type(e).__name__, command, e))
            raise e

        return result.decode('utf-8').strip()

    def _get_docker_daemon_variables(self, id):
        '''
        Capture settings from Docker Machine that would be needed to connect to the remote Docker daemon installed on
        the Docker Machine remote host. Note: passing '--shell=sh' is a workaround for 'Error: Unknown shell'.
        '''
        try:
            env_lines = self._run_command(['env', '--shell=sh', id]).splitlines()
        except Exception:
            # This can happen when the machine is created but provisioning is incomplete
            return None

        # example output of docker-machine env --shell=sh:
        #   export DOCKER_TLS_VERIFY="1"
        #   export DOCKER_HOST="tcp://134.209.204.160:2376"
        #   export DOCKER_CERT_PATH="/root/.docker/machine/machines/routinator"
        #   export DOCKER_MACHINE_NAME="routinator"
        #   # Run this command to configure your shell:
        #   # eval $(docker-machine env --shell=bash routinator)

        # capture any of the DOCKER_xxx variables that were output and create Ansible host vars
        # with the same name and value but with a dm_ name prefix.
        vars = []
        for line in env_lines:
            match = re.search('(DOCKER_[^=]+)="([^"]+)"', line)
            if match:
                env_var_name = match.group(1)
                env_var_value = match.group(2)
                vars.append((env_var_name, env_var_value))

        return vars

    def _get_machine_names(self):
        # Filter out machines that are not in the Running state as we probably can't do anything useful actions
        # with them.
        ls_command = ['ls', '-q']
        if self.get_option('running_required'):
            ls_command.extend(['--filter', 'state=Running'])

        try:
            ls_lines = self._run_command(ls_command)
        except Exception:
            return None

        return ls_lines.splitlines()

    def _inspect_docker_machine_host(self, node):
        try:
            inspect_lines = self._run_command(['inspect', self.node])
        except Exception:
            return None

        return json.loads(inspect_lines)

    def _should_skip_host(self, id, env_var_tuples):
        if not env_var_tuples:
            if self.get_option('daemon_required'):
                display.warning('Unable to fetch Docker daemon env vars from Docker Machine for host {0}: host will be skipped'.format(id))
                return True
            else:
                display.warning('Unable to fetch Docker daemon env vars from Docker Machine for host {0}: host will lack dm_DOCKER_xxx variables'.format(id))
        return False

    def _populate(self):
        try:
            for self.node in self._get_machine_names():
                self.node_attrs = self._inspect_docker_machine_host(self.node)
                if not self.node_attrs:
                    continue

                id = self.node_attrs['Driver']['MachineName']

                # query `docker-machine env` to obtain remote Docker daemon connection settings in the form of commands
                # that could be used to set environment variables to influence a local Docker client:
                env_var_tuples = self._get_docker_daemon_variables(id)
                if self._should_skip_host(id, env_var_tuples):
                    continue

                # add an entry in the inventory for this host
                self.inventory.add_host(id)

                # set standard Ansible remote host connection settings to details captured from `docker-machine`
                # see: https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html
                self.inventory.set_variable(id, 'ansible_host', self.node_attrs['Driver']['IPAddress'])
                self.inventory.set_variable(id, 'ansible_port', self.node_attrs['Driver']['SSHPort'])
                self.inventory.set_variable(id, 'ansible_user', self.node_attrs['Driver']['SSHUser'])
                self.inventory.set_variable(id, 'ansible_ssh_private_key_file', self.node_attrs['Driver']['SSHKeyPath'])

                # set variables based on Docker Machine tags
                tags = self.node_attrs['Driver'].get('Tags') or ''
                self.inventory.set_variable(id, 'dm_tags', tags)

                # set variables based on Docker Machine env variables
                for kv in env_var_tuples:
                    self.inventory.set_variable(id, 'dm_{0}'.format(kv[0]), kv[1])

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
