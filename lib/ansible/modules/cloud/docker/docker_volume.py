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
  volume_name:
    description:
      - Name of the volume to operate on.
    type: str
    required: yes
    aliases:
      - name

  driver:
    description:
      - Specify the type of volume. Docker provides the C(local) driver, but 3rd party drivers can also be used.
    type: str
    default: local

  driver_options:
    description:
      - "Dictionary of volume settings. Consult docker docs for valid options and values:
        U(https://docs.docker.com/engine/reference/commandline/volume_create/#driver-specific-options)"
    type: dict

  labels:
    description:
      - Dictionary of label key/values to set for the volume
    type: dict

  force:
    description:
      - With state C(present) causes the volume to be deleted and recreated if the volume already
        exist and the driver, driver options or labels differ. This will cause any data in the existing
        volume to be lost.
      - Deprecated. Will be removed in Ansible 2.12. Set I(recreate) to C(options-changed) instead
        for the same behavior of setting I(force) to C(yes).
    type: bool
    default: no

  recreate:
    version_added: "2.8"
    description:
      - Controls when a volume will be recreated when I(state) is C(present). Please
        note that recreating an existing volume will cause **any data in the existing volume
        to be lost!** The volume will be deleted and a new volume with the same name will be
        created.
      - The value C(always) forces the volume to be always recreated.
      - The value C(never) makes sure the volume will not be recreated.
      - The value C(options-changed) makes sure the volume will be recreated if the volume
        already exist and the driver, driver options or labels differ.
    type: str
    default: never
    choices:
    - always
    - never
    - options-changed

  state:
    description:
      - C(absent) deletes the volume.
      - C(present) creates the volume, if it does not already exist.
    type: str
    default: present
    choices:
      - absent
      - present

extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation

author:
  - Alex Grönholm (@agronholm)

requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 1.10.0 (use L(docker-py,https://pypi.org/project/docker-py/) for Python 2.6)"
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
volume:
    description:
    - Volume inspection results for the affected volume.
    - Note that facts are part of the registered vars since Ansible 2.8. For compatibility reasons, the facts
      are also accessible directly as C(docker_volume). Note that the returned fact will be removed in Ansible 2.12.
    returned: success
    type: dict
    sample: {}
'''

import traceback

try:
    from docker.errors import DockerException, APIError
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass

from ansible.module_utils.docker.common import (
    DockerBaseClass,
    AnsibleDockerClient,
    DifferenceTracker,
    RequestException,
)
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
        self.recreate = None
        self.debug = None

        for key, value in iteritems(client.module.params):
            setattr(self, key, value)

        if self.force is not None:
            if self.recreate != 'never':
                client.fail('Cannot use the deprecated "force" '
                            'option when "recreate" is set. Please stop '
                            'using the force option.')
            client.module.warn('The "force" option of docker_volume has been deprecated '
                               'in Ansible 2.8. Please use the "recreate" '
                               'option, which provides the same functionality as "force".')
            self.recreate = 'options-changed' if self.force else 'never'


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
        self.diff_tracker = DifferenceTracker()
        self.diff_result = dict()

        self.existing_volume = self.get_existing_volume()

        state = self.parameters.state
        if state == 'present':
            self.present()
        elif state == 'absent':
            self.absent()

        if self.diff or self.check_mode or self.parameters.debug:
            if self.diff:
                self.diff_result['before'], self.diff_result['after'] = self.diff_tracker.get_before_after()
            self.results['diff'] = self.diff_result

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
        differences = DifferenceTracker()
        if self.parameters.driver and self.parameters.driver != self.existing_volume['Driver']:
            differences.add('driver', parameter=self.parameters.driver, active=self.existing_volume['Driver'])
        if self.parameters.driver_options:
            if not self.existing_volume.get('Options'):
                differences.add('driver_options',
                                parameter=self.parameters.driver_options,
                                active=self.existing_volume.get('Options'))
            else:
                for key, value in iteritems(self.parameters.driver_options):
                    if (not self.existing_volume['Options'].get(key) or
                            value != self.existing_volume['Options'][key]):
                        differences.add('driver_options.%s' % key,
                                        parameter=value,
                                        active=self.existing_volume['Options'].get(key))
        if self.parameters.labels:
            existing_labels = self.existing_volume.get('Labels', {})
            for label in self.parameters.labels:
                if existing_labels.get(label) != self.parameters.labels.get(label):
                    differences.add('labels.%s' % label,
                                    parameter=self.parameters.labels.get(label),
                                    active=existing_labels.get(label))

        return differences

    def create_volume(self):
        if not self.existing_volume:
            if not self.check_mode:
                try:
                    params = dict(
                        driver=self.parameters.driver,
                        driver_opts=self.parameters.driver_options,
                    )

                    if self.parameters.labels is not None:
                        params['labels'] = self.parameters.labels

                    resp = self.client.create_volume(self.parameters.volume_name, **params)
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
        differences = DifferenceTracker()
        if self.existing_volume:
            differences = self.has_different_config()

        self.diff_tracker.add('exists', parameter=True, active=self.existing_volume is not None)
        if (not differences.empty and self.parameters.recreate == 'options-changed') or self.parameters.recreate == 'always':
            self.remove_volume()
            self.existing_volume = None

        self.create_volume()

        if self.diff or self.check_mode or self.parameters.debug:
            self.diff_result['differences'] = differences.get_legacy_docker_diffs()
            self.diff_tracker.merge(differences)

        if not self.check_mode and not self.parameters.debug:
            self.results.pop('actions')

        volume_facts = self.get_existing_volume()
        self.results['ansible_facts'] = {u'docker_volume': volume_facts}
        self.results['volume'] = volume_facts

    def absent(self):
        self.diff_tracker.add('exists', parameter=False, active=self.existing_volume is not None)
        self.remove_volume()


def main():
    argument_spec = dict(
        volume_name=dict(type='str', required=True, aliases=['name']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        driver=dict(type='str', default='local'),
        driver_options=dict(type='dict', default={}),
        labels=dict(type='dict'),
        force=dict(type='bool', removed_in_version='2.12'),
        recreate=dict(type='str', default='never', choices=['always', 'never', 'options-changed']),
        debug=dict(type='bool', default=False)
    )

    option_minimal_versions = dict(
        labels=dict(docker_py_version='1.10.0', docker_api_version='1.23'),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='1.10.0',
        min_docker_api_version='1.21',
        # "The docker server >= 1.9.0"
        option_minimal_versions=option_minimal_versions,
    )

    try:
        cm = DockerVolumeManager(client)
        client.module.exit_json(**cm.results)
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
