#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_telemetry_agent
version_added: "2.9"
author: "Samer Deeb (@samerd)"
short_description: Manage telemetry agent on Mellanox ONYX network devices
description:
  - This module provides declarative management of telemetry agent
    on Mellanox ONYX network devices.
options:
  name:
    description:
      - Name of the of the telemetry agent docker container.
    required: true
  state:
    description:
      - State of the telemetry agent agent docker container.
    default: present
    choices: ['present', 'absent']
  install_mode:
    description:
      - Install mode of the telemetry agent, can be pull from docker hub
        or fetch an image from given location, required if I(state)
        is C(present).
    choices: ['pull', 'fetch']
  location:
    description:
      - location of the docker image, required if I(install_mode) is C(fetch).
    suboptions:
      server:
        description:
          - name of IP address of the server storing the image.
        required: true
      protocol:
        description:
          - protocol for fetching the image from the server.
        choices: ['http', 'https', 'ftp', 'tftp', 'scp', 'sftp']
        required: true
      path:
        description:
          - Image absolute path within the server.
        required: true
      image:
        description:
          - Image name, the default is telemetry-agent.
        default: telemetry-agent
      version:
        description:
          - Image version.
        required: true
      username:
        description:
          - username used to fetch the image.
      password:
        description:
          - password used to fetch the image.
"""

EXAMPLES = """
- name: create telemetry agent docker
  onyx_telemetry_agent:
    name: my_telemetry
    install_mode: pull

- name: remove telemetry agent docker
  onyx_telemetry_agent:
    name: my_telemetry
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - no docker shutdown
    - docker pull mellanox/telemetry_agent:latest
    - docker start mellanox/telemetry_agent latest my_agent now-and-init privileged network sdk
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxTelemetryAgentModule(BaseOnyxModule):
    IMAGE_FILE = "ANSIBLE_DOCKER_IMAGE.img"

    def init_module(self):
        """ module initialization
        """
        location_spec = dict(
            server=dict(required=True),
            protocol=dict(
                choices=['http', 'https', 'ftp', 'tftp', 'scp', 'sftp'],
                required=True),
            path=dict(required=True),
            image=dict(default='telemetry-agent'),
            version=dict(required=True),
            username=dict(),
            password=dict())

        element_spec = dict(
            name=dict(required=True),
            install_mode=dict(choices=['pull', 'fetch']),
            location=dict(type='dict', options=location_spec),
            state=dict(choices=['present', 'absent'], default='present'))

        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            required_if=[
                ["state", "present", ["install_mode"]],
                ["install_mode", "fetch", ["location"]]],
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)

    def _get_dockers_state(self):
        return show_cmd(self._module, "show docker")

    def _get_docker_containers(self):
        return show_cmd(self._module, "show docker containers")

    def load_current_config(self):
        # called in base class in run function
        self._current_config = dict()
        dockers_state = self._get_dockers_state()
        if not dockers_state:
            self._current_config['docker_enabled'] = False
            return
        docker_enabled = dockers_state.get('Dockers state')
        self._current_config['docker_enabled'] = (docker_enabled == 'enabled')
        if not self._current_config['docker_enabled']:
            return
        docker_containers = self._get_docker_containers()
        if not docker_containers:
            return
        for container in docker_containers:
            if not container:
                continue
            container_data = container.get(self._required_config['name'])
            if container_data:
                container_data = container_data[0]
                self._current_config['docker_image'] = container_data['image']
                self._current_config['docker_image_version'] = \
                    container_data['version']
                break

    def generate_commands(self):
        state = self._required_config.get("state")
        if state == 'present':
            self._generate_docker_commands()
            if self._required_config.get("install_mode") == "pull":
                self._generate_pull_container_commands()
            else:
                self._generate_fetch_container_commands()
        else:
            self._generate_remove_container_commands()

    def _generate_remove_container_commands(self):
        image = self._current_config.get('docker_image')
        if image:
            self._commands.append(
                'docker no start %s' % self._required_config['name'])

    def _generate_docker_commands(self):
        if not self._current_config['docker_enabled']:
            self._commands.append('no docker shutdown')

    def _generate_start_container_commands(self, image_name, image_version,
                                           container_name):
        self._commands.append(
            'docker start %s %s %s now-and-init privileged network sdk' %
            (image_name, image_version, container_name))
        self._commands.append(
            'docker copy-sdk %s to /' % container_name)

    def _check_container_exists(self, image, version):
        current_image = self._current_config.get('docker_image')
        current_version = self._current_config.get('docker_image_version')
        if not current_image:
            return False
        if current_image != image:
            msg = 'found a container with same name, but with different '\
                'image: %s instead of %s' % (current_image, image)
            self._module.fail_json(msg=msg)
        return (current_version == version)

    def _generate_pull_container_commands(self):
        image_name = 'mellanox/telemetry-agent'
        image_version = 'latest'
        if self._check_container_exists(image_name, image_version):
            return
        container_name = self._required_config['name']
        self._commands.append('docker pull mellanox/telemetry-agent:latest')
        self._generate_start_container_commands(
            image_name, image_version, container_name)

    def _generate_fetch_container_commands(self):
        location = self._required_config.get('location')
        image_name = location.get('image')
        image_version = location.get('version')
        if self._check_container_exists(image_name, image_version):
            return
        url_prefix = ''
        username = location.get('username')
        password = location.get('password')
        protocol = location.get('protocol')
        image_path = location.get('path')

        server = location.get('server')
        if username:
            url_prefix = "%s@" % username
            if password:
                url_prefix = "%s:%s@" % (username, password)
        url = "%s://%s%s%s" % (protocol, url_prefix, server, image_path)

        container_name = self._required_config['name']
        self._commands.append(
            'image fetch %s %s' % (url, self.IMAGE_FILE))
        self._commands.append(
            'docker load %s' % self.IMAGE_FILE)
        self._generate_start_container_commands(
            image_name, image_version, container_name)


def main():
    """ main entry point for module execution
    """
    OnyxTelemetryAgentModule.main()


if __name__ == '__main__':
    main()
