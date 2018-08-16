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
module: docker_secret

short_description: Manage docker secrets.

version_added: "2.4"

description:
     - Create and remove Docker secrets in a Swarm environment. Similar to `docker secret create` and `docker secret rm`.
     - Adds to the metadata of new secrets 'ansible_key', an encrypted hash representation of the data, which is then used
     - in future runs to test if a secret has changed.
     - If 'ansible_key is not present, then a secret will not be updated unless the C(force) option is set.
     - Updates to secrets are performed by removing the secret and creating it again.
options:
  data:
    description:
      - String. The value of the secret. Required when state is C(present).
    required: false
  labels:
    description:
      - "A map of key:value meta data, where both the I(key) and I(value) are expected to be a string."
      - If new meta data is provided, or existing meta data is modified, the secret will be updated by removing it and creating it again.
    required: false
  force:
    description:
      - Use with state C(present) to always remove and recreate an existing secret.
      - If I(true), an existing secret will be replaced, even if it has not changed.
    default: false
    type: bool
  name:
    description:
      - The name of the secret.
    required: true
  state:
    description:
      - Set to C(present), if the secret should exist, and C(absent), if it should not.
    required: false
    default: present
    choices:
      - absent
      - present

extends_documentation_fragment:
    - docker

requirements:
  - "docker-py >= 2.1.0"
  - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
     module has been superseded by L(docker,https://pypi.org/project/docker/)
     (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
     Version 2.1.0 or newer is only available with the C(docker) module."
  - "Docker API >= 1.25"

author:
  - Chris Houseknecht (@chouseknecht)
'''

EXAMPLES = '''

- name: Create secret foo
  docker_secret:
    name: foo
    data: Hello World!
    state: present

- name: Change the secret data
  docker_secret:
    name: foo
    data: Goodnight everyone!
    labels:
      bar: baz
      one: '1'
    state: present

- name: Add a new label
  docker_secret:
    name: foo
    data: Goodnight everyone!
    labels:
      bar: baz
      one: '1'
      # Adding a new label will cause a remove/create of the secret
      two: '2'
    state: present

- name: No change
  docker_secret:
    name: foo
    data: Goodnight everyone!
    labels:
      bar: baz
      one: '1'
      # Even though 'two' is missing, there is no change to the existing secret
    state: present

- name: Update an existing label
  docker_secret:
    name: foo
    data: Goodnight everyone!
    labels:
      bar: monkey   # Changing a label will cause a remove/create of the secret
      one: '1'
    state: present

- name: Force the removal/creation of the secret
  docker_secret:
    name: foo
    data: Goodnight everyone!
    force: yes
    state: present

- name: Remove secret foo
  docker_secret:
    name: foo
    state: absent
'''

RETURN = '''
secret_id:
  description:
    - The ID assigned by Docker to the secret object.
  returned: success
  type: string
  sample: 'hzehrmyjigmcp2gb6nlhmjqcv'
'''

import hashlib

try:
    from docker.errors import APIError
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils.docker_common import AnsibleDockerClient, DockerBaseClass
from ansible.module_utils._text import to_native, to_bytes


class SecretManager(DockerBaseClass):

    def __init__(self, client, results):

        super(SecretManager, self).__init__()

        self.client = client
        self.results = results
        self.check_mode = self.client.check_mode

        parameters = self.client.module.params
        self.name = parameters.get('name')
        self.state = parameters.get('state')
        self.data = parameters.get('data')
        self.labels = parameters.get('labels')
        self.force = parameters.get('force')
        self.data_key = None

    def __call__(self):
        if self.state == 'present':
            self.data_key = hashlib.sha224(to_bytes(self.data)).hexdigest()
            self.present()
        elif self.state == 'absent':
            self.absent()

    def get_secret(self):
        ''' Find an existing secret. '''
        try:
            secrets = self.client.secrets(filters={'name': self.name})
        except APIError as exc:
            self.client.fail("Error accessing secret %s: %s" % (self.name, to_native(exc)))

        for secret in secrets:
            if secret['Spec']['Name'] == self.name:
                return secret
        return None

    def create_secret(self):
        ''' Create a new secret '''
        secret_id = None
        # We can't see the data after creation, so adding a label we can use for idempotency check
        labels = {
            'ansible_key': self.data_key
        }
        if self.labels:
            labels.update(self.labels)

        try:
            if not self.check_mode:
                secret_id = self.client.create_secret(self.name, self.data, labels=labels)
        except APIError as exc:
            self.client.fail("Error creating secret: %s" % to_native(exc))

        if isinstance(secret_id, dict):
            secret_id = secret_id['ID']

        return secret_id

    def present(self):
        ''' Handles state == 'present', creating or updating the secret '''
        secret = self.get_secret()
        if secret:
            self.results['secret_id'] = secret['ID']
            data_changed = False
            attrs = secret.get('Spec', {})
            if attrs.get('Labels', {}).get('ansible_key'):
                if attrs['Labels']['ansible_key'] != self.data_key:
                    data_changed = True
            labels_changed = False
            if self.labels and attrs.get('Labels'):
                # check if user requested a label change
                for label in attrs['Labels']:
                    if self.labels.get(label) and self.labels[label] != attrs['Labels'][label]:
                        labels_changed = True
                # check if user added a label
            labels_added = False
            if self.labels:
                if attrs.get('Labels'):
                    for label in self.labels:
                        if label not in attrs['Labels']:
                            labels_added = True
                else:
                    labels_added = True
            if data_changed or labels_added or labels_changed or self.force:
                # if something changed or force, delete and re-create the secret
                self.absent()
                secret_id = self.create_secret()
                self.results['changed'] = True
                self.results['secret_id'] = secret_id
        else:
            self.results['changed'] = True
            self.results['secret_id'] = self.create_secret()

    def absent(self):
        ''' Handles state == 'absent', removing the secret '''
        secret = self.get_secret()
        if secret:
            try:
                if not self.check_mode:
                    self.client.remove_secret(secret['ID'])
            except APIError as exc:
                self.client.fail("Error removing secret %s: %s" % (self.name, to_native(exc)))
            self.results['changed'] = True


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', choices=['absent', 'present'], default='present'),
        data=dict(type='str', no_log=True),
        labels=dict(type='dict'),
        force=dict(type='bool', default=False)
    )

    required_if = [
        ('state', 'present', ['data'])
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if
    )

    results = dict(
        changed=False,
        secret_id=''
    )

    SecretManager(client, results)()
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
