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
---
module: docker_config

short_description: Manage docker configs.

version_added: "2.8"

description:
     - Create and remove Docker configs in a Swarm environment. Similar to C(docker config create) and C(docker config rm).
     - Adds to the metadata of new configs 'ansible_key', an encrypted hash representation of the data, which is then used
       in future runs to test if a config has changed. If 'ansible_key' is not present, then a config will not be updated
       unless the C(force) option is set.
     - Updates to configs are performed by removing the config and creating it again.
options:
  data:
    description:
      - The value of the config. Required when state is C(present).
    type: str
  data_is_b64:
    description:
      - If set to C(true), the data is assumed to be Base64 encoded and will be
        decoded before being used.
      - To use binary C(data), it is better to keep it Base64 encoded and let it
        be decoded by this option.
    type: bool
    default: no
  labels:
    description:
      - "A map of key:value meta data, where both the I(key) and I(value) are expected to be a string."
      - If new meta data is provided, or existing meta data is modified, the config will be updated by removing it and creating it again.
    type: dict
  force:
    description:
      - Use with state C(present) to always remove and recreate an existing config.
      - If I(true), an existing config will be replaced, even if it has not been changed.
    type: bool
    default: no
  name:
    description:
      - The name of the config.
    type: str
    required: yes
  state:
    description:
      - Set to C(present), if the config should exist, and C(absent), if it should not.
    type: str
    default: present
    choices:
      - absent
      - present

extends_documentation_fragment:
  - docker
  - docker.docker_py_2_documentation

requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 2.6.0"
  - "Docker API >= 1.30"

author:
  - Chris Houseknecht (@chouseknecht)
  - John Hu (@ushuz)
'''

EXAMPLES = '''

- name: Create config foo (from a file on the control machine)
  docker_config:
    name: foo
    # If the file is JSON or binary, Ansible might modify it (because
    # it is first decoded and later re-encoded). Base64-encoding the
    # file directly after reading it prevents this to happen.
    data: "{{ lookup('file', '/path/to/config/file') | b64encode }}"
    data_is_b64: true
    state: present

- name: Change the config data
  docker_config:
    name: foo
    data: Goodnight everyone!
    labels:
      bar: baz
      one: '1'
    state: present

- name: Add a new label
  docker_config:
    name: foo
    data: Goodnight everyone!
    labels:
      bar: baz
      one: '1'
      # Adding a new label will cause a remove/create of the config
      two: '2'
    state: present

- name: No change
  docker_config:
    name: foo
    data: Goodnight everyone!
    labels:
      bar: baz
      one: '1'
      # Even though 'two' is missing, there is no change to the existing config
    state: present

- name: Update an existing label
  docker_config:
    name: foo
    data: Goodnight everyone!
    labels:
      bar: monkey   # Changing a label will cause a remove/create of the config
      one: '1'
    state: present

- name: Force the (re-)creation of the config
  docker_config:
    name: foo
    data: Goodnight everyone!
    force: yes
    state: present

- name: Remove config foo
  docker_config:
    name: foo
    state: absent
'''

RETURN = '''
config_id:
  description:
    - The ID assigned by Docker to the config object.
  returned: success and C(state == "present")
  type: str
  sample: 'hzehrmyjigmcp2gb6nlhmjqcv'
'''

import base64
import hashlib

try:
    from docker.errors import APIError
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass

from ansible.module_utils.docker.common import AnsibleDockerClient, DockerBaseClass, compare_generic
from ansible.module_utils._text import to_native, to_bytes


class ConfigManager(DockerBaseClass):

    def __init__(self, client, results):

        super(ConfigManager, self).__init__()

        self.client = client
        self.results = results
        self.check_mode = self.client.check_mode

        parameters = self.client.module.params
        self.name = parameters.get('name')
        self.state = parameters.get('state')
        self.data = parameters.get('data')
        if self.data is not None:
            if parameters.get('data_is_b64'):
                self.data = base64.b64decode(self.data)
            else:
                self.data = to_bytes(self.data)
        self.labels = parameters.get('labels')
        self.force = parameters.get('force')
        self.data_key = None

    def __call__(self):
        if self.state == 'present':
            self.data_key = hashlib.sha224(self.data).hexdigest()
            self.present()
        elif self.state == 'absent':
            self.absent()

    def get_config(self):
        ''' Find an existing config. '''
        try:
            configs = self.client.configs(filters={'name': self.name})
        except APIError as exc:
            self.client.fail("Error accessing config %s: %s" % (self.name, to_native(exc)))

        for config in configs:
            if config['Spec']['Name'] == self.name:
                return config
        return None

    def create_config(self):
        ''' Create a new config '''
        config_id = None
        # We can't see the data after creation, so adding a label we can use for idempotency check
        labels = {
            'ansible_key': self.data_key
        }
        if self.labels:
            labels.update(self.labels)

        try:
            if not self.check_mode:
                config_id = self.client.create_config(self.name, self.data, labels=labels)
        except APIError as exc:
            self.client.fail("Error creating config: %s" % to_native(exc))

        if isinstance(config_id, dict):
            config_id = config_id['ID']

        return config_id

    def present(self):
        ''' Handles state == 'present', creating or updating the config '''
        config = self.get_config()
        if config:
            self.results['config_id'] = config['ID']
            data_changed = False
            attrs = config.get('Spec', {})
            if attrs.get('Labels', {}).get('ansible_key'):
                if attrs['Labels']['ansible_key'] != self.data_key:
                    data_changed = True
            labels_changed = not compare_generic(self.labels, attrs.get('Labels'), 'allow_more_present', 'dict')
            if data_changed or labels_changed or self.force:
                # if something changed or force, delete and re-create the config
                self.absent()
                config_id = self.create_config()
                self.results['changed'] = True
                self.results['config_id'] = config_id
        else:
            self.results['changed'] = True
            self.results['config_id'] = self.create_config()

    def absent(self):
        ''' Handles state == 'absent', removing the config '''
        config = self.get_config()
        if config:
            try:
                if not self.check_mode:
                    self.client.remove_config(config['ID'])
            except APIError as exc:
                self.client.fail("Error removing config %s: %s" % (self.name, to_native(exc)))
            self.results['changed'] = True


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        data=dict(type='str'),
        data_is_b64=dict(type='bool', default=False),
        labels=dict(type='dict'),
        force=dict(type='bool', default=False)
    )

    required_if = [
        ('state', 'present', ['data'])
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        min_docker_version='2.6.0',
        min_docker_api_version='1.30',
    )

    results = dict(
        changed=False,
    )

    ConfigManager(client, results)()
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
