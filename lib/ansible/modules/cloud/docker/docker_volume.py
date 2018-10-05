#!/usr/bin/python
# coding: utf-8
#
# Copyright 2017 Red Hat | Ansible, Alex Grönholm <alex.gronholm@nextday.fi>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = u'''
module: docker_volume
version_added: "2.4"
short_description: Manage Docker volumes
description:
  - Create/remove Docker volumes.
  - Performs largely the same function as the "docker volume" CLI subcommand.
options:
  name:
    description:
      - Name of the volume to operate on.
    required: true
    aliases:
      - volume_name

  driver:
    description:
      - Specify the type of volume. Docker provides the C(local) driver, but 3rd party drivers can also be used.
    default: local

  driver_options:
    description:
      - "Dictionary of volume settings. Consult docker docs for valid options and values:
        U(https://docs.docker.com/engine/reference/commandline/volume_create/#driver-specific-options)"

  labels:
    description:
      - List of labels to set for the volume

  force:
    description:
      - With state C(present) causes the volume to be deleted and recreated if the volume already
        exist and the driver, driver options or labels differ. This will cause any data in the existing
        volume to be lost.
    type: bool
    default: 'no'

  state:
    description:
      - C(absent) deletes the volume.
      - C(present) creates the volume, if it does not already exist.
    default: present
    choices:
      - absent
      - present

extends_documentation_fragment:
    - docker

author:
    - Alex Grönholm (@agronholm)

requirements:
    - "python >= 2.6"
    - "docker-py >= 1.10.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
       install the C(docker) Python module. Note that both modules should I(not)
       be installed at the same time. Also note that when both modules are installed
       and one of them is uninstalled, the other might no longer function and a
       reinstall of it is required."
    - "The docker server >= 1.9.0"
'''

EXAMPLES = '''
- name: Create a volume
  docker_volume:
    name: volume_one

- name: Remove a volume
  docker_volume:
    name: volume_one
    state: absent

- name: Create a volume with options
  docker_volume:
    name: volume_two
    driver_options:
      type: btrfs
      device: /dev/sda2
'''

RETURN = '''
facts:
    description: Volume inspection results for the affected volume.
    returned: success
    type: dict
    sample: {}
'''

try:
    from docker.errors import APIError
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils.docker_common import DockerBaseClass, AnsibleDockerClient
from ansible.module_utils.six import iteritems, text_type


class TaskParameters(DockerBaseClass):
    def __init__(self, client):
        super(TaskParameters, self).__init__()
        self.client = client

        self.volume_name = None
        self.driver = None
        self.driver_options = None
        self.labels = None
        self.force = None
        self.debug = None

        for key, value in iteritems(client.module.params):
            setattr(self, key, value)


class DockerVolumeManager(object):

    def __init__(self, client):
        self.client = client
        self.parameters = TaskParameters(client)
        self.check_mode = self.client.check_mode
        self.results = {
            u'changed': False,
            u'actions': []
        }
        self.diff = self.client.module._diff

        self.existing_volume = self.get_existing_volume()

        state = self.parameters.state
        if state == 'present':
            self.present()
        elif state == 'absent':
            self.absent()

    def get_existing_volume(self):
        try:
            volumes = self.client.volumes()
        except APIError as e:
            self.client.fail(text_type(e))

        if volumes[u'Volumes'] is None:
            return None

        for volume in volumes[u'Volumes']:
            if volume['Name'] == self.parameters.volume_name:
                return volume

        return None

    def has_different_config(self):
        """
        Return the list of differences between the current parameters and the existing volume.

        :return: list of options that differ
        """
        differences = []
        if self.parameters.driver and self.parameters.driver != self.existing_volume['Driver']:
            differences.append('driver')
        if self.parameters.driver_options:
            if not self.existing_volume.get('Options'):
                differences.append('driver_options')
            else:
                for key, value in iteritems(self.parameters.driver_options):
                    if (not self.existing_volume['Options'].get(key) or
                            value != self.existing_volume['Options'][key]):
                        differences.append('driver_options.%s' % key)
        if self.parameters.labels:
            existing_labels = self.existing_volume.get('Labels', {})
            all_labels = set(self.parameters.labels) | set(existing_labels)
            for label in all_labels:
                if existing_labels.get(label) != self.parameters.labels.get(label):
                    differences.append('labels.%s' % label)

        return differences

    def create_volume(self):
        if not self.existing_volume:
            if not self.check_mode:
                try:
                    resp = self.client.create_volume(self.parameters.volume_name,
                                                     driver=self.parameters.driver,
                                                     driver_opts=self.parameters.driver_options,
                                                     labels=self.parameters.labels)
                    self.existing_volume = self.client.inspect_volume(resp['Name'])
                except APIError as e:
                    self.client.fail(text_type(e))

            self.results['actions'].append("Created volume %s with driver %s" % (self.parameters.volume_name, self.parameters.driver))
            self.results['changed'] = True

    def remove_volume(self):
        if self.existing_volume:
            if not self.check_mode:
                try:
                    self.client.remove_volume(self.parameters.volume_name)
                except APIError as e:
                    self.client.fail(text_type(e))

            self.results['actions'].append("Removed volume %s" % self.parameters.volume_name)
            self.results['changed'] = True

    def present(self):
        differences = []
        if self.existing_volume:
            differences = self.has_different_config()

        if differences and self.parameters.force:
            self.remove_volume()
            self.existing_volume = None

        self.create_volume()

        if self.diff or self.check_mode or self.parameters.debug:
            self.results['diff'] = differences

        if not self.check_mode and not self.parameters.debug:
            self.results.pop('actions')

        self.results['ansible_facts'] = {u'docker_volume': self.get_existing_volume()}

    def absent(self):
        self.remove_volume()


def main():
    argument_spec = dict(
        volume_name=dict(type='str', required=True, aliases=['name']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        driver=dict(type='str', default='local'),
        driver_options=dict(type='dict', default={}),
        labels=dict(type='list'),
        force=dict(type='bool', default=False),
        debug=dict(type='bool', default=False)
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    cm = DockerVolumeManager(client)
    client.module.exit_json(**cm.results)


if __name__ == '__main__':
    main()
