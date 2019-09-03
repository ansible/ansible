# -*- coding: utf-8 -*-
# Copyright (c) 2018, Stefan Heitmueller <stefan.heitmueller@gmx.com>
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    name: gitlab_runners
    plugin_type: inventory
    version_added: '2.8'
    authors:
      - Stefan Heitmüller (stefan.heitmueller@gmx.com)
    short_description: Ansible dynamic inventory plugin for GitLab runners.
    requirements:
        - python >= 2.7
        - python-gitlab > 1.8.0
    extends_documentation_fragment:
        - constructed
    description:
        - Reads inventories from the GitLab API.
        - Uses a YAML configuration file gitlab_runners.[yml|yaml].
    options:
        plugin:
            description: The name of this plugin, it should always be set to 'gitlab_runners' for this plugin to recognize it as it's own.
            type: str
            required: true
            choices:
              - gitlab_runners
        server_url:
            description: The URL of the GitLab server, with protocol (i.e. http or https).
            type: str
            required: true
            default: https://gitlab.com
        api_token:
            description: GitLab token for logging in.
            type: str
            aliases:
              - private_token
              - access_token
        filter:
            description: filter runners from GitLab API
            type: str
            choices: ['active', 'paused', 'online', 'specific', 'shared']
        verbose_output:
            description: Toggle to (not) include all available nodes metadata
            type: bool
            default: yes
'''

EXAMPLES = '''
# gitlab_runners.yml
plugin: gitlab_runners
host: https://gitlab.com

# Example using constructed features to create groups and set ansible_host
plugin: gitlab_runners
host: https://gitlab.com
strict: False
keyed_groups:
  # add e.g. amd64 hosts to an arch_amd64 group
  - prefix: arch
    key: 'architecture'
  # add e.g. linux hosts to an os_linux group
  - prefix: os
    key: 'platform'
  # create a group per runner tag
  # e.g. a runner tagged w/ "production" ends up in group "label_production"
  # hint: labels containing special characters will be converted to safe names
  - key: 'tag_list'
    prefix: tag
'''

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils._text import to_native
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable

try:
    import gitlab
    HAS_GITLAB = True
except ImportError:
    HAS_GITLAB = False


class InventoryModule(BaseInventoryPlugin, Constructable):
    ''' Host inventory parser for ansible using GitLab API as source. '''

    NAME = 'gitlab_runners'

    def _populate(self):
        gl = gitlab.Gitlab(self.get_option('server_url'), private_token=self.get_option('api_token'))
        self.inventory.add_group('gitlab_runners')
        try:
            if self.get_option('filter'):
                runners = gl.runners.all(scope=self.get_option('filter'))
            else:
                runners = gl.runners.all()
            for runner in runners:
                host = str(runner['id'])
                ip_address = runner['ip_address']
                host_attrs = vars(gl.runners.get(runner['id']))['_attrs']
                self.inventory.add_host(host, group='gitlab_runners')
                self.inventory.set_variable(host, 'ansible_host', ip_address)
                if self.get_option('verbose_output', True):
                    self.inventory.set_variable(host, 'gitlab_runner_attributes', host_attrs)

                # Use constructed if applicable
                strict = self.get_option('strict')
                # Composed variables
                self._set_composite_vars(self.get_option('compose'), host_attrs, host, strict=strict)
                # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
                self._add_host_to_composed_groups(self.get_option('groups'), host_attrs, host, strict=strict)
                # Create groups based on variable values and add the corresponding hosts to it
                self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host_attrs, host, strict=strict)
        except Exception as e:
            raise AnsibleParserError('Unable to fetch hosts from GitLab API, this was the original exception: %s' % to_native(e))

    def verify_file(self, path):
        """Return the possibly of a file being consumable by this plugin."""
        return (
            super(InventoryModule, self).verify_file(path) and
            path.endswith((self.NAME + ".yaml", self.NAME + ".yml")))

    def parse(self, inventory, loader, path, cache=True):
        if not HAS_GITLAB:
            raise AnsibleError('The GitLab runners dynamic inventory plugin requires python-gitlab: https://python-gitlab.readthedocs.io/en/stable/')
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)
        self._populate()
