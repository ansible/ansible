#!/usr/bin/python
#
# Copyright 2016 Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: docker_network
version_added: "2.2"
short_description: Manage Docker networks
description:
  - Create/remove Docker networks and connect containers to them.
  - Performs largely the same function as the "docker network" CLI subcommand.
options:
  name:
    description:
      - Name of the network to operate on.
    required: true
    aliases:
      - network_name

  connected:
    description:
      - List of container names or container IDs to connect to a network.
    aliases:
      - containers

  driver:
    description:
      - Specify the type of network. Docker provides bridge and overlay drivers, but 3rd party drivers can also be used.
    default: bridge

  driver_options:
    description:
      - Dictionary of network settings. Consult docker docs for valid options and values.

  force:
    description:
      - With state I(absent) forces disconnecting all containers from the
        network prior to deleting the network. With state I(present) will
        disconnect all containers, delete the network and re-create the
        network.  This option is required if you have changed the IPAM or
        driver options and want an existing network to be updated to use the
        new options.
    type: bool
    default: 'no'

  appends:
    description:
      - By default the connected list is canonical, meaning containers not on the list are removed from the network.
        Use C(appends) to leave existing containers connected.
    type: bool
    default: 'no'
    aliases:
      - incremental

  ipam_driver:
    description:
      - Specify an IPAM driver.

  ipam_options:
    description:
      - Dictionary of IPAM options.

  state:
    description:
      - I(absent) deletes the network. If a network has connected containers, it
        cannot be deleted. Use the C(force) option to disconnect all containers
        and delete the network.
      - I(present) creates the network, if it does not already exist with the
        specified parameters, and connects the list of containers provided via
        the connected parameter. Containers not on the list will be disconnected.
        An empty list will leave no containers connected to the network. Use the
        C(appends) option to leave existing containers connected. Use the C(force)
        options to force re-creation of the network.
    default: present
    choices:
      - absent
      - present

extends_documentation_fragment:
    - docker

author:
    - "Ben Keith (@keitwb)"
    - "Chris Houseknecht (@chouseknecht)"

requirements:
    - "python >= 2.6"
    - "docker-py >= 1.7.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
       install the C(docker) Python module. Note that both modules should I(not)
       be installed at the same time."
    - "The docker server >= 1.9.0"
'''

EXAMPLES = '''
- name: Create a network
  docker_network:
    name: network_one

- name: Remove all but selected list of containers
  docker_network:
    name: network_one
    connected:
      - container_a
      - container_b
      - container_c

- name: Remove a single container
  docker_network:
    name: network_one
    connected: "{{ fulllist|difference(['container_a']) }}"

- name: Add a container to a network, leaving existing containers connected
  docker_network:
    name: network_one
    connected:
      - container_a
    appends: yes

- name: Create a network with options
  docker_network:
    name: network_two
    driver_options:
      com.docker.network.bridge.name: net2
    ipam_options:
      subnet: '172.3.26.0/16'
      gateway: 172.3.26.1
      iprange: '192.168.1.0/24'

- name: Delete a network, disconnecting all containers
  docker_network:
    name: network_one
    state: absent
    force: yes
'''

RETURN = '''
facts:
    description: Network inspection results for the affected network.
    returned: success
    type: dict
    sample: {}
'''

from ansible.module_utils.docker_common import AnsibleDockerClient, DockerBaseClass, HAS_DOCKER_PY_2, HAS_DOCKER_PY_3

try:
    from docker import utils
    if HAS_DOCKER_PY_2 or HAS_DOCKER_PY_3:
        from docker.types import IPAMPool, IPAMConfig
except:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass


class TaskParameters(DockerBaseClass):
    def __init__(self, client):
        super(TaskParameters, self).__init__()
        self.client = client

        self.network_name = None
        self.connected = None
        self.driver = None
        self.driver_options = None
        self.ipam_driver = None
        self.ipam_options = None
        self.appends = None
        self.force = None
        self.debug = None

        for key, value in client.module.params.items():
            setattr(self, key, value)


def container_names_in_network(network):
    return [c['Name'] for c in network['Containers'].values()] if network['Containers'] else []


class DockerNetworkManager(object):

    def __init__(self, client):
        self.client = client
        self.parameters = TaskParameters(client)
        self.check_mode = self.client.check_mode
        self.results = {
            u'changed': False,
            u'actions': []
        }
        self.diff = self.client.module._diff

        self.existing_network = self.get_existing_network()

        if not self.parameters.connected and self.existing_network:
            self.parameters.connected = container_names_in_network(self.existing_network)

        state = self.parameters.state
        if state == 'present':
            self.present()
        elif state == 'absent':
            self.absent()

    def get_existing_network(self):
        networks = self.client.networks(names=[self.parameters.network_name])
        # check if a user is trying to find network by its Id
        if not networks:
            networks = self.client.networks(ids=[self.parameters.network_name])
        if not networks:
            return None
        else:
            return networks[0]

    def has_different_config(self, net):
        '''
        Evaluates an existing network and returns a tuple containing a boolean
        indicating if the configuration is different and a list of differences.

        :param net: the inspection output for an existing network
        :return: (bool, list)
        '''
        different = False
        differences = []
        if self.parameters.driver and self.parameters.driver != net['Driver']:
            different = True
            differences.append('driver')
        if self.parameters.driver_options:
            if not net.get('Options'):
                different = True
                differences.append('driver_options')
            else:
                for key, value in self.parameters.driver_options.items():
                    if not (key in net['Options']) or value != net['Options'][key]:
                        different = True
                        differences.append('driver_options.%s' % key)
        if self.parameters.ipam_driver:
            if not net.get('IPAM') or net['IPAM']['Driver'] != self.parameters.ipam_driver:
                different = True
                differences.append('ipam_driver')
        if self.parameters.ipam_options:
            if not net.get('IPAM') or not net['IPAM'].get('Config'):
                different = True
                differences.append('ipam_options')
            else:
                for key, value in self.parameters.ipam_options.items():
                    camelkey = None
                    for net_key in net['IPAM']['Config'][0]:
                        if key == net_key.lower():
                            camelkey = net_key
                            break
                    if not camelkey:
                        # key not found
                        different = True
                        differences.append('ipam_options.%s' % key)
                    elif net['IPAM']['Config'][0].get(camelkey) != value:
                        # key has different value
                        different = True
                        differences.append('ipam_options.%s' % key)
        return different, differences

    def create_network(self):
        if not self.existing_network:
            ipam_pools = []
            if self.parameters.ipam_options:
                if HAS_DOCKER_PY_2 or HAS_DOCKER_PY_3:
                    ipam_pools.append(IPAMPool(**self.parameters.ipam_options))
                else:
                    ipam_pools.append(utils.create_ipam_pool(**self.parameters.ipam_options))

            if HAS_DOCKER_PY_2 or HAS_DOCKER_PY_3:
                ipam_config = IPAMConfig(driver=self.parameters.ipam_driver,
                                         pool_configs=ipam_pools)
            else:
                ipam_config = utils.create_ipam_config(driver=self.parameters.ipam_driver,
                                                       pool_configs=ipam_pools)

            if not self.check_mode:
                resp = self.client.create_network(self.parameters.network_name,
                                                  driver=self.parameters.driver,
                                                  options=self.parameters.driver_options,
                                                  ipam=ipam_config)

                self.existing_network = self.client.inspect_network(resp['Id'])
            self.results['actions'].append("Created network %s with driver %s" % (self.parameters.network_name, self.parameters.driver))
            self.results['changed'] = True

    def remove_network(self):
        if self.existing_network:
            self.disconnect_all_containers()
            if not self.check_mode:
                self.client.remove_network(self.parameters.network_name)
            self.results['actions'].append("Removed network %s" % (self.parameters.network_name,))
            self.results['changed'] = True

    def is_container_connected(self, container_name):
        return container_name in container_names_in_network(self.existing_network)

    def connect_containers(self):
        for name in self.parameters.connected:
            if not self.is_container_connected(name):
                if not self.check_mode:
                    self.client.connect_container_to_network(name, self.parameters.network_name)
                self.results['actions'].append("Connected container %s" % (name,))
                self.results['changed'] = True

    def disconnect_missing(self):
        if not self.existing_network:
            return
        containers = self.existing_network['Containers']
        if not containers:
            return
        for c in containers.values():
            name = c['Name']
            if name not in self.parameters.connected:
                self.disconnect_container(name)

    def disconnect_all_containers(self):
        containers = self.client.inspect_network(self.parameters.network_name)['Containers']
        if not containers:
            return
        for cont in containers.values():
            self.disconnect_container(cont['Name'])

    def disconnect_container(self, container_name):
        if not self.check_mode:
            self.client.disconnect_container_from_network(container_name, self.parameters.network_name)
        self.results['actions'].append("Disconnected container %s" % (container_name,))
        self.results['changed'] = True

    def present(self):
        different = False
        differences = []
        if self.existing_network:
            different, differences = self.has_different_config(self.existing_network)

        if self.parameters.force or different:
            self.remove_network()
            self.existing_network = None

        self.create_network()
        self.connect_containers()
        if not self.parameters.appends:
            self.disconnect_missing()

        if self.diff or self.check_mode or self.parameters.debug:
            self.results['diff'] = differences

        if not self.check_mode and not self.parameters.debug:
            self.results.pop('actions')

        self.results['ansible_facts'] = {u'docker_network': self.get_existing_network()}

    def absent(self):
        self.remove_network()


def main():
    argument_spec = dict(
        network_name=dict(type='str', required=True, aliases=['name']),
        connected=dict(type='list', default=[], aliases=['containers']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        driver=dict(type='str', default='bridge'),
        driver_options=dict(type='dict', default={}),
        force=dict(type='bool', default=False),
        appends=dict(type='bool', default=False, aliases=['incremental']),
        ipam_driver=dict(type='str', default=None),
        ipam_options=dict(type='dict', default={}),
        debug=dict(type='bool', default=False)
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    cm = DockerNetworkManager(client)
    client.module.exit_json(**cm.results)


if __name__ == '__main__':
    main()
