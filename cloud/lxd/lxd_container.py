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
          - A config dictionary for creating a container.
            See https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-1
          - Required when the container is not created yet and the state is
            not absent.
          - If the container already exists and its metadata obtained from
            GET /1.0/containers/<name>
            https://github.com/lxc/lxd/blob/master/doc/rest-api.md#10containersname
            are different, they this module tries to apply the configurations.
            The following keys in config will be compared and applied.
              - architecture
              - config
                  - The key starts with 'volatile.' are ignored for comparison.
              - devices
              - ephemeral
              - profiles
          - Not all config values are supported to apply the existing container.
            Maybe you need to delete and recreate a container.
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
    timeout:
        description:
          - A timeout of one LXC REST API call.
          - This is also used as a timeout for waiting until IPv4 addresses
            are set to the all network interfaces in the container after
            starting or restarting.
        required: false
        default: 30
    wait_for_ipv4_addresses:
        description:
          - If this is true, the lxd_module waits until IPv4 addresses
            are set to the all network interfaces in the container after
            starting or restarting.
        required: false
        default: false
    force_stop:
        description:
          - If this is true, the lxd_module forces to stop the container
            when it stops or restarts the container.
        required: false
        default: false
    unix_socket_path:
        description:
          - The unix domain socket path for the LXD server.
        required: false
        default: /var/lib/lxd/unix.socket
requirements:
  - 'requests_unixsocket'
notes:
  - Containers must have a unique name. If you attempt to create a container
    with a name that already existed in the users namespace the module will
    simply return as "unchanged".
  - There are two ways to can run commands in containers, using the command
    module or using the ansible lxd connection plugin bundled in Ansible >=
    2.1, the later requires python to be installed in the container which can
    be done with the command module.
  - You can copy a file from the host to the container
    with the Ansible `copy` and `template` module and the `lxd` connection plugin.
    See the example below.
  - You can copy a file in the creatd container to the localhost
    with `command=lxc file pull container_name/dir/filename filename`.
    See the first example below.
"""

EXAMPLES = """
- hosts: localhost
  connection: local
  tasks:
    - name: Create a started container
      lxd_container:
        name: mycontainer
        state: started
        config:
          source:
            type: image
            mode: pull
            server: https://images.linuxcontainers.org
            protocol: lxd
            alias: "ubuntu/xenial/amd64"
          profiles: ["default"]
    - name: Install python in the created container "mycontainer"
      command: lxc exec mycontainer -- apt install -y python
    - name: Copy /etc/hosts in the created container "mycontainer" to localhost with name "mycontainer-hosts"
      command: lxc file pull mycontainer/etc/hosts mycontainer-hosts


# Note your container must be in the inventory for the below example.
#
# [containers]
# mycontainer ansible_connection=lxd
#
- hosts:
    - mycontainer
  tasks:
    - template: src=foo.j2 dest=/etc/bar

- hosts: localhost
  connection: local
  tasks:
    - name: Create a stopped container
      lxd_container:
        name: mycontainer
        state: stopped
        config:
          source:
            type: image
            mode: pull
            server: https://images.linuxcontainers.org
            protocol: lxd
            alias: "ubuntu/xenial/amd64"
          profiles: ["default"]

- hosts: localhost
  connection: local
  tasks:
    - name: Restart a container
      lxd_container:
        name: mycontainer
        state: restarted
        config:
          source:
            type: image
            mode: pull
            server: https://images.linuxcontainers.org
            protocol: lxd
            alias: "ubuntu/xenial/amd64"
          profiles: ["default"]
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
    actions:
      description: list of actions performed for the container
      returned: success
      type: list
      sample: ["create", "start"]
"""

from ansible.compat.six.moves.urllib.parse import quote

try:
    import requests_unixsocket
    from requests.exceptions import ConnectionError
except ImportError:
    HAS_REQUETS_UNIXSOCKET = False
else:
    HAS_REQUETS_UNIXSOCKET = True

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
        self.timeout = self.module.params['timeout']
        self.wait_for_ipv4_addresses = self.module.params['wait_for_ipv4_addresses']
        self.force_stop = self.module.params['force_stop']
        self.addresses = None
        self.unix_socket_path = self.module.params['unix_socket_path']
        self.base_url = 'http+unix://{0}'.format(quote(self.unix_socket_path, safe=''))
        self.session = requests_unixsocket.Session()
        self.logs = []
        self.actions = []

    def _path_to_url(self, path):
        return self.base_url + path

    def _send_request(self, method, path, json=None, ok_error_codes=None):
        try:
            url = self._path_to_url(path)
            resp = self.session.request(method, url, json=json, timeout=self.timeout)
            resp_json = resp.json()
            self.logs.append({
                'type': 'sent request',
                'request': {'method': method, 'url': url, 'json': json, 'timeout': self.timeout},
                'response': {'json': resp_json}
            })
            resp_type = resp_json.get('type', None)
            if resp_type == 'error':
                if ok_error_codes is not None and resp_json['error_code'] in ok_error_codes:
                    return resp_json
                self.module.fail_json(
                    msg='error response',
                    request={'method': method, 'url': url, 'json': json, 'timeout': self.timeout},
                    response={'json': resp_json},
                    logs=self.logs
                )
            return resp_json
        except ConnectionError:
            self.module.fail_json(msg='cannot connect to the LXD server', unix_socket_path=self.unix_socket_path)

    def _operate_and_wait(self, method, path, json=None):
        resp_json = self._send_request(method, path, json=json)
        if resp_json['type'] == 'async':
            path = '{0}/wait?timeout={1}'.format(resp_json['operation'], self.timeout)
            resp_json = self._send_request('GET', path)
            if resp_json['metadata']['status'] != 'Success':
                url = self._path_to_url(path)
                self.module.fail_json(
                    msg='error response for waiting opearation',
                    request={'method': method, 'url': url, 'json': json, 'timeout': self.timeout},
                    response={'json': resp_json},
                    logs=self.logs
                )
        return resp_json

    def _get_container_json(self):
        return self._send_request(
            'GET', '/1.0/containers/{0}'.format(self.container_name),
            ok_error_codes=[404]
        )

    def _get_container_state_json(self):
        return self._send_request(
            'GET', '/1.0/containers/{0}/state'.format(self.container_name),
            ok_error_codes=[404]
        )

    @staticmethod
    def _container_json_to_module_state(resp_json):
        if resp_json['type'] == 'error':
            return 'absent'
        return ANSIBLE_LXD_STATES[resp_json['metadata']['status']]

    def _change_state(self, action, force_stop=False):
        json={'action': action, 'timeout': self.timeout}
        if force_stop:
            json['force'] = True
        return self._operate_and_wait('PUT', '/1.0/containers/{0}/state'.format(self.container_name), json)

    def _create_container(self):
        config = self.config.copy()
        config['name'] = self.container_name
        self._operate_and_wait('POST', '/1.0/containers', config)
        self.actions.append('creat')

    def _start_container(self):
        self._change_state('start')
        self.actions.append('start')

    def _stop_container(self):
        self._change_state('stop', self.force_stop)
        self.actions.append('stop')

    def _restart_container(self):
        self._change_state('restart', self.force_stop)
        self.actions.append('restart')

    def _delete_container(self):
        return self._operate_and_wait('DELETE', '/1.0/containers/{0}'.format(self.container_name))
        self.actions.append('delete')

    def _freeze_container(self):
        self._change_state('freeze')
        self.actions.append('freeze')

    def _unfreeze_container(self):
        self._change_state('unfreeze')
        self.actions.append('unfreez')

    def _container_ipv4_addresses(self, ignore_devices=['lo']):
        resp_json = self._get_container_state_json()
        network = resp_json['metadata']['network'] or {}
        network = dict((k, v) for k, v in network.items() if k not in ignore_devices) or {}
        addresses = dict((k, [a['address'] for a in v['addresses'] if a['family'] == 'inet']) for k, v in network.items()) or {}
        return addresses

    @staticmethod
    def _has_all_ipv4_addresses(addresses):
        return len(addresses) > 0 and all([len(v) > 0 for v in addresses.itervalues()])

    def _get_addresses(self):
        due = datetime.datetime.now() + datetime.timedelta(seconds=self.timeout)
        while datetime.datetime.now() < due:
            time.sleep(1)
            addresses = self._container_ipv4_addresses()
            if self._has_all_ipv4_addresses(addresses):
                self.addresses = addresses
                return

        state_changed = len(self.actions) > 0
        self.module.fail_json(
            failed=True,
            msg='timeout for getting IPv4 addresses',
            changed=state_changed,
            actions=self.actions,
            logs=self.logs)

    def _started(self):
        if self.old_state == 'absent':
            self._create_container()
            self._start_container()
        else:
            if self.old_state == 'frozen':
                self._unfreeze_container()
            elif self.old_state == 'stopped':
                self._start_container()
            if self._needs_to_apply_configs():
                self._apply_configs()
        if self.wait_for_ipv4_addresses:
            self._get_addresses()

    def _stopped(self):
        if self.old_state == 'absent':
            self._create_container()
        else:
            if self.old_state == 'stopped':
                if self._needs_to_apply_configs():
                    self._start_container()
                    self._apply_configs()
                    self._stop_container()
            else:
                if self.old_state == 'frozen':
                    self._unfreeze_container()
                if self._needs_to_apply_configs():
                    self._apply_configs()
                self._stop_container()

    def _restarted(self):
        if self.old_state == 'absent':
            self._create_container()
            self._start_container()
        else:
            if self.old_state == 'frozen':
                self._unfreeze_container()
            if self._needs_to_apply_configs():
                self._apply_configs()
            self._restart_container()
        if self.wait_for_ipv4_addresses:
            self._get_addresses()

    def _destroyed(self):
        if self.old_state != 'absent':
            if self.old_state == 'frozen':
                self._unfreeze_container()
            self._stop_container()
            self._delete_container()

    def _frozen(self):
        if self.old_state == 'absent':
            self._create_container()
            self._start_container()
            self._freeze_container()
        else:
            if self.old_state == 'stopped':
                self._start_container()
            if self._needs_to_apply_configs():
                self._apply_configs()
            self._freeze_container()

    def _needs_to_change_config(self, key):
        if key not in self.config:
            return False
        if key == 'config':
            old_configs = dict((k, v) for k, v in self.old_container_json['metadata'][key].items() if k.startswith('volatile.'))
        else:
            old_configs = self.old_container_json['metadata'][key]
        return self.config[key] != old_configs

    def _needs_to_apply_configs(self):
        return (
            self._needs_to_change_config('architecture') or
            self._needs_to_change_config('config') or
            self._needs_to_change_config('ephemeral') or
            self._needs_to_change_config('devices') or
            self._needs_to_change_config('profiles')
        )

    def _apply_configs(self):
        old_metadata = self.old_container_json['metadata']
        json = {
            'architecture': old_metadata['architecture'],
            'config': old_metadata['config'],
            'devices': old_metadata['devices'],
            'profiles': old_metadata['profiles']
        }
        if self._needs_to_change_config('architecture'):
            json['architecture'] = self.config['architecture']
        if self._needs_to_change_config('config'):
            for k, v in self.config['config'].items():
                json['config'][k] = v
        if self._needs_to_change_config('ephemeral'):
            json['ephemeral'] = self.config['ephemeral']
        if self._needs_to_change_config('devices'):
            json['devices'] = self.config['devices']
        if self._needs_to_change_config('profiles'):
            json['profiles'] = self.config['profiles']
        self._operate_and_wait('PUT', '/1.0/containers/{0}'.format(self.container_name), json)
        self.actions.append('apply_configs')

    def run(self):
        """Run the main method."""

        self.old_container_json = self._get_container_json()
        self.old_state = self._container_json_to_module_state(self.old_container_json)

        action = getattr(self, LXD_ANSIBLE_STATES[self.state])
        action()

        state_changed = len(self.actions) > 0
        result_json = {
            'changed': state_changed,
            'old_state': self.old_state,
            'logs': self.logs,
            'actions': self.actions
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
            timeout=dict(
                type='int',
                default=30
            ),
            wait_for_ipv4_addresses=dict(
                type='bool',
                default=False
            ),
            force_stop=dict(
                type='bool',
                default=False
            ),
            unix_socket_path=dict(
                type='str',
                default='/var/lib/lxd/unix.socket'
            )
        ),
        supports_check_mode=False,
    )

    if not HAS_REQUETS_UNIXSOCKET:
        module.fail_json(
            msg='The `requests_unixsocket` module is not importable. Check the requirements.'
        )

    lxd_manage = LxdContainerManagement(module=module)
    lxd_manage.run()


# import module bits
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
