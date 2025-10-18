# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: generator
    version_added: "2.6"
    short_description: Uses Jinja2 to construct hosts and groups from patterns
    description:
        - Uses a YAML configuration file with a valid YAML or C(.config) extension to define var expressions and group conditionals
        - Create a template pattern that describes each host, and then use independent configuration layers
        - Every element of every layer is combined to create a host for every layer combination
        - Parent groups can be defined with reference to hosts and other groups using the same template variables
    options:
      plugin:
         description: token that ensures this is a source file for the 'generator' plugin.
         required: True
         choices: ['ansible.builtin.generator', 'generator']
      hosts:
        description:
          - The C(name) key is a template used to generate
            hostnames based on the C(layers) option. Each variable in the name is expanded to create a
            cartesian product of all possible layer combinations.
          - The C(parents) are a list of parent groups that the host belongs to. Each C(parent) item
            contains a C(name) key, again expanded from the template, and an optional C(parents) key
            that lists its parents.
          - Parents can also contain C(vars), which is a dictionary of vars that
            is then always set for that variable. This can provide easy access to the group name. E.g
            set an C(application) variable that is set to the value of the C(application) layer name.
      layers:
        description:
          - A dictionary of layers, with the key being the layer name, used as a variable name in the C(host)
            C(name) and C(parents) keys. Each layer value is a list of possible values for that layer.
      use_extra_vars:
        version_added: '2.21'
        description:
          - Merge extra vars into the available variables for composition (highest precedence).
        type: bool
        default: false
        ini:
          - section: inventory_plugins
            key: use_extra_vars
          - section: inventory_plugin_generator
            key: use_extra_vars
        env:
          - name: ANSIBLE_INVENTORY_USE_EXTRA_VARS
          - name: ANSIBLE_GENERATOR_USE_EXTRA_VARS
"""

EXAMPLES = """
    # inventory.config file in YAML format
    # remember to enable this inventory plugin in the ansible.cfg before using
    # View the output using `ansible-inventory -i inventory.config --list`
    plugin: ansible.builtin.generator
    hosts:
        name: "{{ operation }}_{{ application }}_{{ environment }}_runner"
        parents:
          - name: "{{ operation }}_{{ application }}_{{ environment }}"
            parents:
              - name: "{{ operation }}_{{ application }}"
                parents:
                  - name: "{{ operation }}"
                  - name: "{{ application }}"
              - name: "{{ application }}_{{ environment }}"
                parents:
                  - name: "{{ application }}"
                    vars:
                      application: "{{ application }}"
                  - name: "{{ environment }}"
                    vars:
                      environment: "{{ environment }}"
          - name: runner
    layers:
        operation:
            - build
            - launch
        environment:
            - dev
            - test
            - prod
        application:
            - web
            - api
"""

import os

from itertools import product

from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.utils.vars import load_extra_vars


class InventoryModule(BaseInventoryPlugin):
    """ constructs groups and vars using Jinja2 template expressions """

    NAME = 'generator'

    # implicit trust behavior is already added by the YAML parser invoked by the loader

    def __init__(self):

        super(InventoryModule, self).__init__()

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)

            if not ext or ext in ['.config'] + C.YAML_FILENAME_EXTENSIONS:
                valid = True

        return valid

    def template(self, pattern, variables):
        # Allow pass-through of data structures for templating later (if applicable).
        # This limitation was part of the original plugin implementation and was updated to maintain feature parity with the new templating API.
        if not isinstance(pattern, str):
            return pattern

        return self.templar.copy_with_new_env(available_variables=variables).template(pattern)

    def add_parents(self, inventory, child, parents, template_vars):
        for parent in parents:
            groupname = self.template(parent.get('name'), template_vars)
            if not groupname:
                raise AnsibleParserError(f"Element {child} has a parent with no name.")
            if groupname not in inventory.groups:
                inventory.add_group(groupname)
            group = inventory.groups[groupname]
            for (k, v) in parent.get('vars', {}).items():
                group.set_variable(k, self.template(v, template_vars))
            inventory.add_child(groupname, child)
            self.add_parents(inventory, groupname, parent.get('parents', []), template_vars)

    def parse(self, inventory, loader, path, cache=False):
        """ parses the inventory file """

        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)

        config = self._read_config_data(path)
        if self.get_option('use_extra_vars'):
            extra_vars = load_extra_vars(loader)
        else:
            extra_vars = {}
        template_inputs = product(*config['layers'].values())
        for item in template_inputs:
            template_vars = dict()
            template_vars.update(extra_vars)
            for i, key in enumerate(config['layers'].keys()):
                template_vars[key] = item[i]
            host = self.template(config['hosts']['name'], template_vars)
            inventory.add_host(host)
            self.add_parents(inventory, host, config['hosts'].get('parents', []), template_vars)
