# -*- coding: utf-8 -*-
# Copyright (c) 2018, Stefan Heitmueller <stefan.heitmueller@gmx.com>
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    name: docker_swarm
    plugin_type: inventory
    version_added: '2.8'
    authors:
      - Stefan Heitmüller (@morph027) <stefan.heitmueller@gmx.com>
    short_description: Ansible dynamic inventory plugin for Docker swarm nodes.
    requirements:
        - python >= 2.7
        - Docker SDK for Python > 1.10.0
    extends_documentation_fragment:
        - constructed
    description:
        - Reads inventories from the Docker swarm API.
        - Uses a YAML configuration file docker_swarm.[yml|yaml].
    options:
        plugin:
            description: The name of this plugin, it should always be set to 'docker_swarm' for this plugin to recognize it as it's own.
            type: str
            required: true
            choices: docker_swarm
        host:
            description: Socket of a Docker swarm manager node (tcp,unix).
            type: str
            required: true
        verbose_output:
            description: Toggle to (not) include all available nodes metadata (e.g. Platform, Architecture, OS, EngineVersion)
            type: bool
            default: yes
        tls:
            description: Connect using TLS without verifying the authenticity of the Docker host server.
            type: bool
            default: no
        tls_verify:
            description: Toggle if connecting using TLS with or without verifying the authenticity of the Docker host server.
            type: bool
            default: no
        key_path:
            description: Path to the client's TLS key file.
            type: path
        cacert_path:
            description: Use a CA certificate when performing server verification by providing the path to a CA certificate file.
            type: path
        cert_path:
            description: Path to the client's TLS certificate file.
            type: path
        tls_hostname:
            description: When verifying the authenticity of the Docker Host server, provide the expected name of the server.
            type: str
'''

EXAMPLES = '''
# Minimal example using local docker
plugin: docker_swarm
host: unix://var/run/docker.sock

# Minimal example using remote docker
plugin: docker_swarm
host: tcp://my-docker-host:2375

# Example using remote docker with unverified TLS
plugin: docker_swarm
host: tcp://my-docker-host:2376
tls: yes

# Example using remote docker with verified TLS and client certificate verification
plugin: docker_swarm
host: tcp://my-docker-host:2376
tls_verify: yes
cacert_path: /somewhere/ca.pem
key_path: /somewhere/key.pem
cert_path: /somewhere/cert.pem

# Example using constructed features to create groups and set ansible_host
plugin: docker_swarm
host: tcp://my-docker-host:2375
strict: False
keyed_groups:
  # add e.g. x86_64 hosts to an arch_x86_64 group
  - prefix: arch
    key: 'Description.Platform.Architecture'
  # add e.g. linux hosts to an os_linux group
  - prefix: os
    key: 'Description.Platform.OS'
  # create a group per node label
  # e.g. a node labeled w/ "production" ends up in group "label_production"
  # hint: labels containing special characters will be converted to safe names
  - key: 'Spec.Labels'
    prefix: label
'''

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.parsing.utils.addresses import parse_address

try:
    import docker
    HAS_DOCKER = True
except ImportError:
    HAS_DOCKER = False


class InventoryModule(BaseInventoryPlugin, Constructable):
    ''' Host inventory parser for ansible using Docker swarm as source. '''

    NAME = 'docker_swarm'

    def _get_tls_config(self, **kwargs):
        try:
            tls_config = docker.tls.TLSConfig(**kwargs)
            return tls_config
        except Exception as e:
            raise AnsibleError('Unable to setup TLS, this was the original exception: %s' % to_native(e))

    def _get_tls_connect_params(self):
        if self.get_option('tls') and self.get_option('cert_path') and self.get_option('key_path'):
            # TLS with certs and no host verification
            tls_config = self._get_tls_config(client_cert=(self.get_option('cert_path'), self.get_option('key_path')),
                                              verify=False)
            return tls_config

        if self.get_option('tls'):
            # TLS with no certs and not host verification
            tls_config = self._get_tls_config(verify=False)
            return tls_config

        if self.get_option('tls_verify') and self.get_option('cert_path') and self.get_option('key_path'):
            # TLS with certs and host verification
            if self.get_option('cacert_path'):
                tls_config = self._get_tls_config(client_cert=(self.get_option('cert_path'), self.get_option('key_path')),
                                                  ca_cert=self.get_option('cacert_path'),
                                                  verify=True,
                                                  assert_hostname=self.get_option('tls_hostname'))
            else:
                tls_config = self._get_tls_config(client_cert=(self.get_option('cert_path'), self.get_option('key_path')),
                                                  verify=True,
                                                  assert_hostname=self.get_option('tls_hostname'))

            return tls_config

        if self.get_option('tls_verify') and self.get_option('cacert_path'):
            # TLS with cacert only
            tls_config = self._get_tls_config(ca_cert=self.get_option('cacert_path'),
                                              assert_hostname=self.get_option('tls_hostname'),
                                              verify=True)
            return tls_config

        if self.get_option('tls_verify'):
            # TLS with verify and no certs
            tls_config = self._get_tls_config(verify=True,
                                              assert_hostname=self.get_option('tls_hostname'))
            return tls_config

        # No TLS
        return None

    def _populate(self):
        self.client = docker.DockerClient(base_url=self.get_option('host'), tls=self._get_tls_connect_params())
        self.inventory.add_group('all')
        self.inventory.add_group('manager')
        self.inventory.add_group('worker')
        self.inventory.add_group('leader')
        try:
            self.nodes = self.client.nodes.list()
            for self.node in self.nodes:
                self.node_attrs = self.client.nodes.get(self.node.id).attrs
                self.inventory.add_host(self.node_attrs['ID'])
                self.inventory.add_host(self.node_attrs['ID'], group=self.node_attrs['Spec']['Role'])
                self.inventory.set_variable(self.node_attrs['ID'], 'ansible_host', self.node_attrs['Status']['Addr'])
                if self.get_option('verbose_output', True):
                    self.inventory.set_variable(self.node_attrs['ID'], 'docker_swarm_node_attributes', self.node_attrs)
                if 'ManagerStatus' in self.node_attrs:
                    if self.node_attrs['ManagerStatus'].get('Leader'):
                        self.inventory.set_variable(self.node_attrs['ID'], 'ansible_host',
                                                    parse_address(self.node_attrs['ManagerStatus']['Addr'])[0])
                        self.inventory.add_host(self.node_attrs['ID'], group='leader')
                # Use constructed if applicable
                strict = self.get_option('strict')
                # Composed variables
                self._set_composite_vars(self.get_option('compose'), self.node_attrs, self.node_attrs['ID'], strict=strict)
                # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
                self._add_host_to_composed_groups(self.get_option('groups'), self.node_attrs, self.node_attrs['ID'], strict=strict)
                # Create groups based on variable values and add the corresponding hosts to it
                self._add_host_to_keyed_groups(self.get_option('keyed_groups'), self.node_attrs, self.node_attrs['ID'], strict=strict)
        except Exception as e:
            raise AnsibleError('Unable to fetch hosts from Docker swarm API, this was the original exception: %s' % to_native(e))

    def verify_file(self, path):
        """Return the possibly of a file being consumable by this plugin."""
        return (
            super(InventoryModule, self).verify_file(path) and
            path.endswith((self.NAME + ".yaml", self.NAME + ".yml")))

    def parse(self, inventory, loader, path, cache=True):
        if not HAS_DOCKER:
            raise AnsibleError('The Docker swarm dynamic inventory plugin requires the Docker SDK for Python: https://github.com/docker/docker-py.')
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)
        self._populate()
