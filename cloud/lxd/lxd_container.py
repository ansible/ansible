#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Hiroaki Nakamura <hnakamur@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = """
---
module: lxd_container
short_description: Manage LXD Containers
version_added: 2.2.0
description:
  - Management of LXD containers
author: "Hiroaki Nakamura (@hnakamur)"
options:
    name:
        description:
          - Name of a container.
        required: true
    config:
        description:
          - a config dictionary for creating a container.
            See https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-1
          - required when the container is not created yet and the state is
            not absent.
        required: false
    state:
        choices:
          - started
          - stopped
          - restarted
          - absent
          - frozen
        description:
          - Define the state of a container.
        required: false
        default: started
    timeout_for_addresses:
        description:
          - a timeout of waiting for IPv4 addresses are set to the all network
            interfaces in the container after starting or restarting.
          - if this values is equal to or less than 0, ansible does not
            wait for IPv4 addresses.
        required: false
        default: 0
requirements:
  - 'lxd >= 2.0 # OS package'
  - 'python >= 2.6 # OS Package'
  - 'pylxd >= 2.0 # OS or PIP Package from https://github.com/lxc/pylxd'
notes:
  - Containers must have a unique name. If you attempt to create a container
    with a name that already existed in the users namespace the module will
    simply return as "unchanged".
  - If your distro does not have a package for "python-pylxd", which is a
    requirement for this module, it can be installed from source at
    "https://github.com/lxc/pylxd" or installed via pip using the package
    name pylxd.
"""

EXAMPLES = """
- name: Create a started container
  lxd_container:
    name: cent01
    source: { type: image, alias: centos/7/amd64 }
    state: started

- name: Create a stopped container
  lxd_container:
    name: cent01
    source: { type: image, alias: centos/7/amd64 }
    state: stopped

- name: Restart a container
  lxd_container:
    name: cent01
    source: { type: image, alias: centos/7/amd64 }
    state: restarted
"""

RETURN="""
lxd_container:
  description: container information
  returned: success
  type: object
  contains:
    addresses:
      description: mapping from the network device name to a list of IPv4 addresses in the container
      returned: when state is started or restarted
      type: object
      sample: {"eth0": ["10.155.92.191"]}
    old_state:
      description: the old state of the container
      returned: when state is started or restarted
      sample: "stopped"
    logs:
      description: list of actions performed for the container
      returned: success
      type: list
      sample: ["created", "started"]
"""

from distutils.spawn import find_executable

try:
    from pylxd.client import Client
except ImportError:
    HAS_PYLXD = False
else:
    HAS_PYLXD = True


# LXD_ANSIBLE_STATES is a map of states that contain values of methods used
# when a particular state is evoked.
LXD_ANSIBLE_STATES = {
    'started': '_started',
    'stopped': '_stopped',
    'restarted': '_restarted',
    'absent': '_destroyed',
    'frozen': '_frozen'
}

# ANSIBLE_LXD_STATES is a map of states of lxd containers to the Ansible
# lxc_container module state parameter value.
ANSIBLE_LXD_STATES = {
    'Running': 'started',
    'Stopped': 'stopped',
    'Frozen': 'frozen',
}

try:
    callable(all)
except NameError:
    # For python <2.5
    # This definition is copied from https://docs.python.org/2/library/functions.html#all
    def all(iterable):
        for element in iterable:
            if not element:
                return False
        return True

class LxdContainerManagement(object):
    def __init__(self, module):
        """Management of LXC containers via Ansible.

        :param module: Processed Ansible Module.
        :type module: ``object``
        """
        self.module = module
        self.container_name = self.module.params['name']
        self.config = self.module.params.get('config', None)
        self.state = self.module.params['state']
        self.timeout_for_addresses = self.module.params['timeout_for_addresses']
        self.addresses = None
        self.client = Client()
        self.logs = []

    def _create_container(self):
        config = self.config.copy()
        config['name'] = self.container_name
        self.client.containers.create(config, wait=True)
        # NOTE: get container again for the updated state
        self.container = self._get_container()
        self.logs.append('created')

    def _start_container(self):
        self.container.start(wait=True)
        self.logs.append('started')

    def _stop_container(self):
        self.container.stop(wait=True)
        self.logs.append('stopped')

    def _restart_container(self):
        self.container.restart(wait=True)
        self.logs.append('restarted')

    def _delete_container(self):
        self.container.delete(wait=True)
        self.logs.append('deleted')

    def _freeze_container(self):
        self.container.freeze(wait=True)
        self.logs.append('freezed')

    def _unfreeze_container(self):
        self.container.unfreeze(wait=True)
        self.logs.append('unfreezed')

    def _get_container(self):
        try:
            return self.client.containers.get(self.container_name)
        except NameError:
            return None

    @staticmethod
    def _container_to_module_state(container):
        if container is None:
            return "absent"
        else:
            return ANSIBLE_LXD_STATES[container.status]

    def _container_ipv4_addresses(self, ignore_devices=['lo']):
        container = self._get_container()
        network = container is not None and container.state().network or {}
        network = dict((k, v) for k, v in network.iteritems() if k not in ignore_devices) or {}
        addresses = dict((k, [a['address'] for a in v['addresses'] if a['family'] == 'inet']) for k, v in network.iteritems()) or {}
        return addresses

    @staticmethod
    def _has_all_ipv4_addresses(addresses):
        return len(addresses) > 0 and all([len(v) > 0 for v in addresses.itervalues()])

    def _get_addresses(self):
        if self.timeout_for_addresses <= 0:
            return
        due = datetime.datetime.now() + datetime.timedelta(seconds=self.timeout_for_addresses)
        while datetime.datetime.now() < due:
            time.sleep(1)
            addresses = self._container_ipv4_addresses()
            if self._has_all_ipv4_addresses(addresses):
                self.addresses = addresses
                return
        self._on_timeout()

    def _started(self):
        """Ensure a container is started.

        If the container does not exist the container will be created.
        """
        if self.container is None:
            self._create_container()
            self._start_container()
        else:
            if self.container.status == 'Frozen':
                self._unfreeze_container()
            if self.container.status != 'Running':
                self._start_container()
        self._get_addresses()

    def _stopped(self):
        if self.container is None:
            self._create_container()
        else:
            if self.container.status == 'Frozen':
                self._unfreeze_container()
            if self.container.status != 'Stopped':
                self._stop_container()

    def _restarted(self):
        if self.container is None:
            self._create_container()
            self._start_container()
        else:
            if self.container.status == 'Frozen':
                self._unfreeze_container()
            if self.container.status == 'Running':
                self._restart_container()
            else:
                self._start_container()
        self._get_addresses()

    def _destroyed(self):
        if self.container is not None:
            if self.container.status == 'Frozen':
                self._unfreeze_container()
            if self.container.status == 'Running':
                self._stop_container()
            self._delete_container()

    def _frozen(self):
        if self.container is None:
            self._create_container()
            self._start_container()
            self._freeze_container()
        else:
            if self.container.status != 'Frozen':
                if self.container.status != 'Running':
                    self._start_container()
                self._freeze_container()

    def _on_timeout(self):
        state_changed = len(self.logs) > 0
        self.module.fail_json(
            failed=True,
            msg='timeout for getting addresses',
            changed=state_changed,
            logs=self.logs)

    def run(self):
        """Run the main method."""

        self.container = self._get_container()
        self.old_state = self._container_to_module_state(self.container)

        action = getattr(self, LXD_ANSIBLE_STATES[self.state])
        action()

        state_changed = len(self.logs) > 0
        result_json = {
            "changed" : state_changed,
            "old_state" : self.old_state,
            "logs" : self.logs
        }
        if self.addresses is not None:
            result_json['addresses'] = self.addresses
        self.module.exit_json(**result_json)


def main():
    """Ansible Main module."""

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(
                type='str',
                required=True
            ),
            config=dict(
                type='dict',
            ),
            state=dict(
                choices=LXD_ANSIBLE_STATES.keys(),
                default='started'
            ),
            timeout_for_addresses=dict(
                type='int',
                default=0
            )
        ),
        supports_check_mode=False,
    )

    if not HAS_PYLXD:
        module.fail_json(
            msg='The `pylxd` module is not importable. Check the requirements.'
        )

    lxd_manage = LxdContainerManagement(module=module)
    lxd_manage.run()


# import module bits
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
