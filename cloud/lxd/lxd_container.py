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
    type:
        choices:
          - container
          - profile
        description:
          - The resource type.
        required: false
        default: container
    architecture:
        description:
          - The archiecture for the container (e.g. "x86_64" or "i686").
            See https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-1
        required: false
    config:
        description:
          - >
            The config for the container (e.g. {"limits.cpu": "2"}).
            See https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-1
          - If the container already exists and its "config" value in metadata
            obtained from
            GET /1.0/containers/<name>
            https://github.com/lxc/lxd/blob/master/doc/rest-api.md#10containersname
            are different, they this module tries to apply the configurations.
          - The key starts with 'volatile.' are ignored for this comparison.
          - Not all config values are supported to apply the existing container.
            Maybe you need to delete and recreate a container.
        required: false
    devices:
        description:
          - >
            The devices for the container
            (e.g. { "rootfs": { "path": "/dev/kvm", "type": "unix-char" }).
            See https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-1
        required: false
    ephemeral:
        description:
          - Whether or not the container is ephemeral (e.g. true or false).
            See https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-1
        required: false
    source:
        description:
          - >
            The source for the container
            (e.g. { "type": "image",
                    "mode": "pull",
                    "server": "https://images.linuxcontainers.org",
                    "protocol": "lxd",
                    "alias": "ubuntu/xenial/amd64" }).
            See https://github.com/lxc/lxd/blob/master/doc/rest-api.md#post-1
        required: false
    new_name:
        description:
          - A new name of a profile.
          - If this parameter is specified a profile will be renamed to this name.
        required: false
    state:
        choices:
          - present
          - started
          - stopped
          - restarted
          - absent
          - frozen
        description:
          - Define the state of a container or profile.
          - Valid choices for type=container are started, stopped, restarted,
            absent, or frozen.
          - Valid choices for type=profile are present or absent.
        required: false
        default: started
    timeout:
        description:
          - A timeout for changing the state of the container.
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
    url:
        description:
          - The unix domain socket path or the https URL for the LXD server.
        required: false
        default: unix:/var/lib/lxd/unix.socket
    key_file:
        description:
          - The client certificate key file path.
        required: false
        default: >
          '{}/.config/lxc/client.key'.format(os.environ['HOME'])
    cert_file:
        description:
          - The client certificate file path.
        required: false
        default: >
          '{}/.config/lxc/client.crt'.format(os.environ['HOME'])
    trust_password:
        description:
          - The client trusted password.
          - You need to set this password on the LXD server before
            running this module using the following command.
            lxc config set core.trust_password <some random password>
            See https://www.stgraber.org/2016/04/18/lxd-api-direct-interaction/
          - If trust_password is set, this module send a request for
            authentication before sending any requests.
        required: false
    debug:
        description:
          - If this flag is true, the logs key are added to the result object
            which keeps all the requests and responses for calling APIs.
        required: false
        default: false
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
        source:
          type: image
          mode: pull
          server: https://images.linuxcontainers.org
          protocol: lxd
          alias: "ubuntu/xenial/amd64"
        profiles: ["default"]

# An example for connecting to the LXD server using https
- hosts: localhost
  connection: local
  tasks:
  - name: create macvlan profile
    lxd_container:
      url: https://127.0.0.1:8443
      # These cert_file and key_file values are equal to the default values.
      #cert_file: "{{ lookup('env', 'HOME') }}/.config/lxc/client.crt"
      #key_file: "{{ lookup('env', 'HOME') }}/.config/lxc/client.key"
      trust_password: mypassword
      type: profile
      name: macvlan
      state: present
      config: {}
      description: 'my macvlan profile'
      devices:
        eth0:
          nictype: macvlan
          parent: br0
          type: nic
"""

RETURN="""
lxd_container:
  description: container information
  returned: success
  type: object
  contains:
    addresses:
      description: Mapping from the network device name to a list of IPv4 addresses in the container
      returned: when state is started or restarted
      type: object
      sample: {"eth0": ["10.155.92.191"]}
    old_state:
      description: The old state of the container
      returned: when state is started or restarted
      sample: "stopped"
    logs:
      descriptions: The logs of requests and responses.
      returned: when the debug parameter is true and any requests were sent.
    actions:
      description: List of actions performed for the container.
      returned: success
      type: list
      sample: ["create", "start"]
"""

import os

try:
    import json
except ImportError:
    import simplejson as json

# httplib/http.client connection using unix domain socket
import socket
import ssl
try:
    from httplib import HTTPConnection, HTTPSConnection
except ImportError:
    # Python 3
    from http.client import HTTPConnection, HTTPSConnection

class UnixHTTPConnection(HTTPConnection):
    def __init__(self, path, timeout=None):
        HTTPConnection.__init__(self, 'localhost', timeout=timeout)
        self.path = path

    def connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.path)
        self.sock = sock

from ansible.module_utils.urls import generic_urlparse
try:
    from urlparse import urlparse
except ImportError:
    # Python 3
    from url.parse import urlparse

# LXD_ANSIBLE_STATES is a map of states that contain values of methods used
# when a particular state is evoked.
LXD_ANSIBLE_STATES = {
    'started': '_started',
    'stopped': '_stopped',
    'restarted': '_restarted',
    'absent': '_destroyed',
    'frozen': '_frozen'
}

# PROFILE_STATES is a list for states supported for type=profiles
PROFILES_STATES = [
    'present', 'absent'
]

# ANSIBLE_LXD_STATES is a map of states of lxd containers to the Ansible
# lxc_container module state parameter value.
ANSIBLE_LXD_STATES = {
    'Running': 'started',
    'Stopped': 'stopped',
    'Frozen': 'frozen',
}

# CONFIG_PARAMS is a map from a resource type to config attribute names.
CONFIG_PARAMS = {
    'container': ['architecture', 'config', 'devices', 'ephemeral', 'profiles', 'source'],
    'profile': ['config', 'description', 'devices']
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
        self.name = self.module.params['name']
        self.type = self.module.params['type']
        self._build_config()

        self.state = self.module.params['state']
        if self.type == 'container':
            self._check_argument_choices('state', self.state, LXD_ANSIBLE_STATES.keys())
        elif self.type == 'profile':
            self._check_argument_choices('state', self.state, PROFILES_STATES)

        self.new_name = self.module.params.get('new_name', None)
        self.timeout = self.module.params['timeout']
        self.wait_for_ipv4_addresses = self.module.params['wait_for_ipv4_addresses']
        self.force_stop = self.module.params['force_stop']
        self.addresses = None
        self.url = self.module.params['url']
        self.key_file = self.module.params.get('key_file', None)
        self.cert_file = self.module.params.get('cert_file', None)
        self.trust_password = self.module.params.get('trust_password', None)
        self.debug = self.module.params['debug']
        if self.url.startswith('https:'):
            parts = generic_urlparse(urlparse(self.url))
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(self.cert_file, keyfile=self.key_file)
            self.connection = HTTPSConnection(parts.get('netloc'), context=ctx)
        elif self.url.startswith('unix:'):
            unix_socket_path = self.url[len('unix:'):]
            self.connection = UnixHTTPConnection(unix_socket_path)
        else:
            self.module.fail_json(msg='URL scheme must be unix: or https:')
        self.logs = []
        self.actions = []

    def _check_argument_choices(self, name, value, choices):
        if value not in choices:
            choices_str=",".join([str(c) for c in choices])
            msg="value of %s must be one of: %s, got: %s" % (name, choices_str, value)
            self.module.fail_json(msg=msg)

    def _build_config(self):
        self.config = {}
        for attr in CONFIG_PARAMS[self.type]:
            param_val = self.module.params.get(attr, None)
            if param_val is not None:
                self.config[attr] = param_val

    def _authenticate(self):
        body_json = {'type': 'client', 'password': self.trust_password}
        self._send_request('POST', '/1.0/certificates', body_json=body_json)

    def _send_request(self, method, url, body_json=None, ok_error_codes=None):
        try:
            body = json.dumps(body_json)
            self.connection.request(method, url, body=body)
            resp = self.connection.getresponse()
            resp_json = json.loads(resp.read())
            self.logs.append({
                'type': 'sent request',
                'request': {'method': method, 'url': url, 'json': body_json, 'timeout': self.timeout},
                'response': {'json': resp_json}
            })
            resp_type = resp_json.get('type', None)
            if resp_type == 'error':
                if ok_error_codes is not None and resp_json['error_code'] in ok_error_codes:
                    return resp_json
                fail_params = {
                    'msg': self._get_err_from_resp_json(resp_json),
                }
                if self.debug:
                    fail_params['logs'] = self.logs
                self.module.fail_json(**fail_params)
            return resp_json
        except socket.error as e:
            if self.url is None:
                self.module.fail_json(
                    msg='cannot connect to the LXD server',
                    unix_socket_path=self.unix_socket_path, error=e
                )
            else:
                self.module.fail_json(
                    msg='cannot connect to the LXD server',
                    url=self.url, key_file=self.key_file, cert_file=self.cert_file,
                    error=e
                )

    @staticmethod
    def _get_err_from_resp_json(resp_json):
        metadata = resp_json.get('metadata', None)
        if metadata is not None:
            err = metadata.get('err', None)
        if err is None:
            err = resp_json.get('error', None)
        return err

    def _operate_and_wait(self, method, path, body_json=None):
        resp_json = self._send_request(method, path, body_json=body_json)
        if resp_json['type'] == 'async':
            url = '{0}/wait'.format(resp_json['operation'])
            resp_json = self._send_request('GET', url)
            if resp_json['metadata']['status'] != 'Success':
                fail_params = {
                    'msg': self._get_err_from_resp_json(resp_json),
                }
                if self.debug:
                    fail_params['logs'] = self.logs
                self.module.fail_json(**fail_params)
        return resp_json

    def _get_container_json(self):
        return self._send_request(
            'GET', '/1.0/containers/{0}'.format(self.name),
            ok_error_codes=[404]
        )

    def _get_container_state_json(self):
        return self._send_request(
            'GET', '/1.0/containers/{0}/state'.format(self.name),
            ok_error_codes=[404]
        )

    @staticmethod
    def _container_json_to_module_state(resp_json):
        if resp_json['type'] == 'error':
            return 'absent'
        return ANSIBLE_LXD_STATES[resp_json['metadata']['status']]

    def _change_state(self, action, force_stop=False):
        body_json={'action': action, 'timeout': self.timeout}
        if force_stop:
            body_json['force'] = True
        return self._operate_and_wait('PUT', '/1.0/containers/{0}/state'.format(self.name), body_json=body_json)

    def _create_container(self):
        config = self.config.copy()
        config['name'] = self.name
        self._operate_and_wait('POST', '/1.0/containers', config)
        self.actions.append('create')

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
        return self._operate_and_wait('DELETE', '/1.0/containers/{0}'.format(self.name))
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
        fail_params = {
            'msg': 'timeout for getting IPv4 addresses',
            'changed': state_changed,
            'actions': self.actions
        }
        if self.debug:
            fail_params['logs'] = self.logs
        self.module.fail_json(**fail_params)

    def _started(self):
        if self.old_state == 'absent':
            self._create_container()
            self._start_container()
        else:
            if self.old_state == 'frozen':
                self._unfreeze_container()
            elif self.old_state == 'stopped':
                self._start_container()
            if self._needs_to_apply_container_configs():
                self._apply_container_configs()
        if self.wait_for_ipv4_addresses:
            self._get_addresses()

    def _stopped(self):
        if self.old_state == 'absent':
            self._create_container()
        else:
            if self.old_state == 'stopped':
                if self._needs_to_apply_container_configs():
                    self._start_container()
                    self._apply_container_configs()
                    self._stop_container()
            else:
                if self.old_state == 'frozen':
                    self._unfreeze_container()
                if self._needs_to_apply_container_configs():
                    self._apply_container_configs()
                self._stop_container()

    def _restarted(self):
        if self.old_state == 'absent':
            self._create_container()
            self._start_container()
        else:
            if self.old_state == 'frozen':
                self._unfreeze_container()
            if self._needs_to_apply_container_configs():
                self._apply_container_configs()
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
            if self._needs_to_apply_container_configs():
                self._apply_container_configs()
            self._freeze_container()

    def _needs_to_change_container_config(self, key):
        if key not in self.config:
            return False
        if key == 'config':
            old_configs = dict((k, v) for k, v in self.old_container_json['metadata'][key].items() if not k.startswith('volatile.'))
        else:
            old_configs = self.old_container_json['metadata'][key]
        return self.config[key] != old_configs

    def _needs_to_apply_container_configs(self):
        return (
            self._needs_to_change_container_config('architecture') or
            self._needs_to_change_container_config('config') or
            self._needs_to_change_container_config('ephemeral') or
            self._needs_to_change_container_config('devices') or
            self._needs_to_change_container_config('profiles')
        )

    def _apply_container_configs(self):
        old_metadata = self.old_container_json['metadata']
        body_json = {
            'architecture': old_metadata['architecture'],
            'config': old_metadata['config'],
            'devices': old_metadata['devices'],
            'profiles': old_metadata['profiles']
        }
        if self._needs_to_change_container_config('architecture'):
            body_json['architecture'] = self.config['architecture']
        if self._needs_to_change_container_config('config'):
            for k, v in self.config['config'].items():
                body_json['config'][k] = v
        if self._needs_to_change_container_config('ephemeral'):
            body_json['ephemeral'] = self.config['ephemeral']
        if self._needs_to_change_container_config('devices'):
            body_json['devices'] = self.config['devices']
        if self._needs_to_change_container_config('profiles'):
            body_json['profiles'] = self.config['profiles']
        self._operate_and_wait('PUT', '/1.0/containers/{0}'.format(self.name), body_json=body_json)
        self.actions.append('apply_container_configs')

    def _get_profile_json(self):
        return self._send_request(
            'GET', '/1.0/profiles/{0}'.format(self.name),
            ok_error_codes=[404]
        )

    @staticmethod
    def _profile_json_to_module_state(resp_json):
        if resp_json['type'] == 'error':
            return 'absent'
        return 'present'

    def _update_profile(self):
        if self.state == 'present':
            if self.old_state == 'absent':
                if self.new_name is None:
                    self._create_profile()
                else:
                    self.module.fail_json(
                        msg='new_name must not be set when the profile does not exist and the specified state is present',
                        changed=False)
            else:
                if self.new_name is not None and self.new_name != self.name:
                    self._rename_profile()
                if self._needs_to_apply_profile_configs():
                    self._apply_profile_configs()
        elif self.state == 'absent':
            if self.old_state == 'present':
                if self.new_name is None:
                    self._delete_profile()
                else:
                    self.module.fail_json(
                        msg='new_name must not be set when the profile exists and the specified state is absent',
                        changed=False)

    def _create_profile(self):
        config = self.config.copy()
        config['name'] = self.name
        self._send_request('POST', '/1.0/profiles', config)
        self.actions.append('create')

    def _rename_profile(self):
        config = {'name': self.new_name}
        self._send_request('POST', '/1.0/profiles/{}'.format(self.name), config)
        self.actions.append('rename')
        self.name = self.new_name

    def _needs_to_change_profile_config(self, key):
        if key not in self.config:
            return False
        old_configs = self.old_profile_json['metadata'].get(key, None)
        return self.config[key] != old_configs

    def _needs_to_apply_profile_configs(self):
        return (
            self._needs_to_change_profile_config('config') or
            self._needs_to_change_profile_config('description') or
            self._needs_to_change_profile_config('devices')
        )

    def _apply_profile_configs(self):
        config = self.old_profile_json.copy()
        for k, v in self.config.iteritems():
            config[k] = v
        self._send_request('PUT', '/1.0/profiles/{}'.format(self.name), config)
        self.actions.append('apply_profile_configs')

    def _delete_profile(self):
        self._send_request('DELETE', '/1.0/profiles/{}'.format(self.name))
        self.actions.append('delete')

    def run(self):
        """Run the main method."""

        if self.trust_password is not None:
            self._authenticate()

        if self.type == 'container':
            self.old_container_json = self._get_container_json()
            self.old_state = self._container_json_to_module_state(self.old_container_json)
            action = getattr(self, LXD_ANSIBLE_STATES[self.state])
            action()
        elif self.type == 'profile':
            self.old_profile_json = self._get_profile_json()
            self.old_state = self._profile_json_to_module_state(self.old_profile_json)
            self._update_profile()

        state_changed = len(self.actions) > 0
        result_json = {
            'changed': state_changed,
            'old_state': self.old_state,
            'actions': self.actions
        }
        if self.debug:
            result_json['logs'] = self.logs
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
            new_name=dict(
                type='str',
            ),
            type=dict(
                type='str',
                choices=CONFIG_PARAMS.keys(),
                default='container'
            ),
            architecture=dict(
                type='str',
            ),
            config=dict(
                type='dict',
            ),
            description=dict(
                type='str',
            ),
            devices=dict(
                type='dict',
            ),
            ephemeral=dict(
                type='bool',
            ),
            profiles=dict(
                type='list',
            ),
            source=dict(
                type='dict',
            ),
            state=dict(
                choices=list(set(LXD_ANSIBLE_STATES.keys()) | set(PROFILES_STATES)),
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
            url=dict(
                type='str',
                default='unix:/var/lib/lxd/unix.socket'
            ),
            key_file=dict(
                type='str',
                default='{}/.config/lxc/client.key'.format(os.environ['HOME'])
            ),
            cert_file=dict(
                type='str',
                default='{}/.config/lxc/client.crt'.format(os.environ['HOME'])
            ),
            trust_password=dict(
                type='str',
            ),
            debug=dict(
                type='bool',
                default=False
            )
        ),
        supports_check_mode=False,
    )

    lxd_manage = LxdContainerManagement(module=module)
    lxd_manage.run()

# import module bits
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
