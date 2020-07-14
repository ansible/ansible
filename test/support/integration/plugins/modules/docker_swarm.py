#!/usr/bin/python

# Copyright 2016 Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: docker_swarm
short_description: Manage Swarm cluster
version_added: "2.7"
description:
  - Create a new Swarm cluster.
  - Add/Remove nodes or managers to an existing cluster.
options:
  advertise_addr:
    description:
      - Externally reachable address advertised to other nodes.
      - This can either be an address/port combination
          in the form C(192.168.1.1:4567), or an interface followed by a
          port number, like C(eth0:4567).
      - If the port number is omitted,
          the port number from the listen address is used.
      - If I(advertise_addr) is not specified, it will be automatically
          detected when possible.
      - Only used when swarm is initialised or joined. Because of this it's not
        considered for idempotency checking.
    type: str
  default_addr_pool:
    description:
      - Default address pool in CIDR format.
      - Only used when swarm is initialised. Because of this it's not considered
        for idempotency checking.
      - Requires API version >= 1.39.
    type: list
    elements: str
    version_added: "2.8"
  subnet_size:
    description:
      - Default address pool subnet mask length.
      - Only used when swarm is initialised. Because of this it's not considered
        for idempotency checking.
      - Requires API version >= 1.39.
    type: int
    version_added: "2.8"
  listen_addr:
    description:
      - Listen address used for inter-manager communication.
      - This can either be an address/port combination in the form
          C(192.168.1.1:4567), or an interface followed by a port number,
          like C(eth0:4567).
      - If the port number is omitted, the default swarm listening port
          is used.
      - Only used when swarm is initialised or joined. Because of this it's not
        considered for idempotency checking.
    type: str
    default: 0.0.0.0:2377
  force:
    description:
      - Use with state C(present) to force creating a new Swarm, even if already part of one.
      - Use with state C(absent) to Leave the swarm even if this node is a manager.
    type: bool
    default: no
  state:
    description:
      - Set to C(present), to create/update a new cluster.
      - Set to C(join), to join an existing cluster.
      - Set to C(absent), to leave an existing cluster.
      - Set to C(remove), to remove an absent node from the cluster.
        Note that removing requires Docker SDK for Python >= 2.4.0.
      - Set to C(inspect) to display swarm informations.
    type: str
    default: present
    choices:
      - present
      - join
      - absent
      - remove
      - inspect
  node_id:
    description:
      - Swarm id of the node to remove.
      - Used with I(state=remove).
    type: str
  join_token:
    description:
      - Swarm token used to join a swarm cluster.
      - Used with I(state=join).
    type: str
  remote_addrs:
    description:
      - Remote address of one or more manager nodes of an existing Swarm to connect to.
      - Used with I(state=join).
    type: list
    elements: str
  task_history_retention_limit:
    description:
      - Maximum number of tasks history stored.
      - Docker default value is C(5).
    type: int
  snapshot_interval:
    description:
      - Number of logs entries between snapshot.
      - Docker default value is C(10000).
    type: int
  keep_old_snapshots:
    description:
      - Number of snapshots to keep beyond the current snapshot.
      - Docker default value is C(0).
    type: int
  log_entries_for_slow_followers:
    description:
      - Number of log entries to keep around to sync up slow followers after a snapshot is created.
    type: int
  heartbeat_tick:
    description:
      - Amount of ticks (in seconds) between each heartbeat.
      - Docker default value is C(1s).
    type: int
  election_tick:
    description:
      - Amount of ticks (in seconds) needed without a leader to trigger a new election.
      - Docker default value is C(10s).
    type: int
  dispatcher_heartbeat_period:
    description:
      - The delay for an agent to send a heartbeat to the dispatcher.
      - Docker default value is C(5s).
    type: int
  node_cert_expiry:
    description:
      - Automatic expiry for nodes certificates.
      - Docker default value is C(3months).
    type: int
  name:
    description:
      - The name of the swarm.
    type: str
  labels:
    description:
      - User-defined key/value metadata.
      - Label operations in this module apply to the docker swarm cluster.
        Use M(docker_node) module to add/modify/remove swarm node labels.
      - Requires API version >= 1.32.
    type: dict
  signing_ca_cert:
    description:
      - The desired signing CA certificate for all swarm node TLS leaf certificates, in PEM format.
      - This must not be a path to a certificate, but the contents of the certificate.
      - Requires API version >= 1.30.
    type: str
  signing_ca_key:
    description:
      - The desired signing CA key for all swarm node TLS leaf certificates, in PEM format.
      - This must not be a path to a key, but the contents of the key.
      - Requires API version >= 1.30.
    type: str
  ca_force_rotate:
    description:
      - An integer whose purpose is to force swarm to generate a new signing CA certificate and key,
          if none have been specified.
      - Docker default value is C(0).
      - Requires API version >= 1.30.
    type: int
  autolock_managers:
    description:
      - If set, generate a key and use it to lock data stored on the managers.
      - Docker default value is C(no).
      - M(docker_swarm_info) can be used to retrieve the unlock key.
    type: bool
  rotate_worker_token:
    description: Rotate the worker join token.
    type: bool
    default: no
  rotate_manager_token:
    description: Rotate the manager join token.
    type: bool
    default: no
extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation
requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 1.10.0 (use L(docker-py,https://pypi.org/project/docker-py/) for Python 2.6)"
  - Docker API >= 1.25
author:
  - Thierry Bouvet (@tbouvet)
  - Piotr Wojciechowski (@WojciechowskiPiotr)
'''

EXAMPLES = '''

- name: Init a new swarm with default parameters
  docker_swarm:
    state: present

- name: Update swarm configuration
  docker_swarm:
    state: present
    election_tick: 5

- name: Add nodes
  docker_swarm:
    state: join
    advertise_addr: 192.168.1.2
    join_token: SWMTKN-1--xxxxx
    remote_addrs: [ '192.168.1.1:2377' ]

- name: Leave swarm for a node
  docker_swarm:
    state: absent

- name: Remove a swarm manager
  docker_swarm:
    state: absent
    force: true

- name: Remove node from swarm
  docker_swarm:
    state: remove
    node_id: mynode

- name: Inspect swarm
  docker_swarm:
    state: inspect
  register: swarm_info
'''

RETURN = '''
swarm_facts:
  description: Informations about swarm.
  returned: success
  type: dict
  contains:
      JoinTokens:
          description: Tokens to connect to the Swarm.
          returned: success
          type: dict
          contains:
              Worker:
                  description: Token to create a new *worker* node
                  returned: success
                  type: str
                  example: SWMTKN-1--xxxxx
              Manager:
                  description: Token to create a new *manager* node
                  returned: success
                  type: str
                  example: SWMTKN-1--xxxxx
      UnlockKey:
          description: The swarm unlock-key if I(autolock_managers) is C(true).
          returned: on success if I(autolock_managers) is C(true)
            and swarm is initialised, or if I(autolock_managers) has changed.
          type: str
          example: SWMKEY-1-xxx

actions:
  description: Provides the actions done on the swarm.
  returned: when action failed.
  type: list
  elements: str
  example: "['This cluster is already a swarm cluster']"

'''

import json
import traceback

try:
    from docker.errors import DockerException, APIError
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass

from ansible.module_utils.docker.common import (
    DockerBaseClass,
    DifferenceTracker,
    RequestException,
)

from ansible.module_utils.docker.swarm import AnsibleDockerSwarmClient

from ansible.module_utils._text import to_native


class TaskParameters(DockerBaseClass):
    def __init__(self):
        super(TaskParameters, self).__init__()

        self.advertise_addr = None
        self.listen_addr = None
        self.remote_addrs = None
        self.join_token = None

        # Spec
        self.snapshot_interval = None
        self.task_history_retention_limit = None
        self.keep_old_snapshots = None
        self.log_entries_for_slow_followers = None
        self.heartbeat_tick = None
        self.election_tick = None
        self.dispatcher_heartbeat_period = None
        self.node_cert_expiry = None
        self.name = None
        self.labels = None
        self.log_driver = None
        self.signing_ca_cert = None
        self.signing_ca_key = None
        self.ca_force_rotate = None
        self.autolock_managers = None
        self.rotate_worker_token = None
        self.rotate_manager_token = None
        self.default_addr_pool = None
        self.subnet_size = None

    @staticmethod
    def from_ansible_params(client):
        result = TaskParameters()
        for key, value in client.module.params.items():
            if key in result.__dict__:
                setattr(result, key, value)

        result.update_parameters(client)
        return result

    def update_from_swarm_info(self, swarm_info):
        spec = swarm_info['Spec']

        ca_config = spec.get('CAConfig') or dict()
        if self.node_cert_expiry is None:
            self.node_cert_expiry = ca_config.get('NodeCertExpiry')
        if self.ca_force_rotate is None:
            self.ca_force_rotate = ca_config.get('ForceRotate')

        dispatcher = spec.get('Dispatcher') or dict()
        if self.dispatcher_heartbeat_period is None:
            self.dispatcher_heartbeat_period = dispatcher.get('HeartbeatPeriod')

        raft = spec.get('Raft') or dict()
        if self.snapshot_interval is None:
            self.snapshot_interval = raft.get('SnapshotInterval')
        if self.keep_old_snapshots is None:
            self.keep_old_snapshots = raft.get('KeepOldSnapshots')
        if self.heartbeat_tick is None:
            self.heartbeat_tick = raft.get('HeartbeatTick')
        if self.log_entries_for_slow_followers is None:
            self.log_entries_for_slow_followers = raft.get('LogEntriesForSlowFollowers')
        if self.election_tick is None:
            self.election_tick = raft.get('ElectionTick')

        orchestration = spec.get('Orchestration') or dict()
        if self.task_history_retention_limit is None:
            self.task_history_retention_limit = orchestration.get('TaskHistoryRetentionLimit')

        encryption_config = spec.get('EncryptionConfig') or dict()
        if self.autolock_managers is None:
            self.autolock_managers = encryption_config.get('AutoLockManagers')

        if self.name is None:
            self.name = spec['Name']

        if self.labels is None:
            self.labels = spec.get('Labels') or {}

        if 'LogDriver' in spec['TaskDefaults']:
            self.log_driver = spec['TaskDefaults']['LogDriver']

    def update_parameters(self, client):
        assign = dict(
            snapshot_interval='snapshot_interval',
            task_history_retention_limit='task_history_retention_limit',
            keep_old_snapshots='keep_old_snapshots',
            log_entries_for_slow_followers='log_entries_for_slow_followers',
            heartbeat_tick='heartbeat_tick',
            election_tick='election_tick',
            dispatcher_heartbeat_period='dispatcher_heartbeat_period',
            node_cert_expiry='node_cert_expiry',
            name='name',
            labels='labels',
            signing_ca_cert='signing_ca_cert',
            signing_ca_key='signing_ca_key',
            ca_force_rotate='ca_force_rotate',
            autolock_managers='autolock_managers',
            log_driver='log_driver',
        )
        params = dict()
        for dest, source in assign.items():
            if not client.option_minimal_versions[source]['supported']:
                continue
            value = getattr(self, source)
            if value is not None:
                params[dest] = value
        self.spec = client.create_swarm_spec(**params)

    def compare_to_active(self, other, client, differences):
        for k in self.__dict__:
            if k in ('advertise_addr', 'listen_addr', 'remote_addrs', 'join_token',
                     'rotate_worker_token', 'rotate_manager_token', 'spec',
                     'default_addr_pool', 'subnet_size'):
                continue
            if not client.option_minimal_versions[k]['supported']:
                continue
            value = getattr(self, k)
            if value is None:
                continue
            other_value = getattr(other, k)
            if value != other_value:
                differences.add(k, parameter=value, active=other_value)
        if self.rotate_worker_token:
            differences.add('rotate_worker_token', parameter=True, active=False)
        if self.rotate_manager_token:
            differences.add('rotate_manager_token', parameter=True, active=False)
        return differences


class SwarmManager(DockerBaseClass):

    def __init__(self, client, results):

        super(SwarmManager, self).__init__()

        self.client = client
        self.results = results
        self.check_mode = self.client.check_mode
        self.swarm_info = {}

        self.state = client.module.params['state']
        self.force = client.module.params['force']
        self.node_id = client.module.params['node_id']

        self.differences = DifferenceTracker()
        self.parameters = TaskParameters.from_ansible_params(client)

        self.created = False

    def __call__(self):
        choice_map = {
            "present": self.init_swarm,
            "join": self.join,
            "absent": self.leave,
            "remove": self.remove,
            "inspect": self.inspect_swarm
        }

        if self.state == 'inspect':
            self.client.module.deprecate(
                "The 'inspect' state is deprecated, please use 'docker_swarm_info' to inspect swarm cluster",
                version='2.12', collection_name='ansible.builtin')

        choice_map.get(self.state)()

        if self.client.module._diff or self.parameters.debug:
            diff = dict()
            diff['before'], diff['after'] = self.differences.get_before_after()
            self.results['diff'] = diff

    def inspect_swarm(self):
        try:
            data = self.client.inspect_swarm()
            json_str = json.dumps(data, ensure_ascii=False)
            self.swarm_info = json.loads(json_str)

            self.results['changed'] = False
            self.results['swarm_facts'] = self.swarm_info

            unlock_key = self.get_unlock_key()
            self.swarm_info.update(unlock_key)
        except APIError:
            return

    def get_unlock_key(self):
        default = {'UnlockKey': None}
        if not self.has_swarm_lock_changed():
            return default
        try:
            return self.client.get_unlock_key() or default
        except APIError:
            return default

    def has_swarm_lock_changed(self):
        return self.parameters.autolock_managers and (
            self.created or self.differences.has_difference_for('autolock_managers')
        )

    def init_swarm(self):
        if not self.force and self.client.check_if_swarm_manager():
            self.__update_swarm()
            return

        if not self.check_mode:
            init_arguments = {
                'advertise_addr': self.parameters.advertise_addr,
                'listen_addr': self.parameters.listen_addr,
                'force_new_cluster': self.force,
                'swarm_spec': self.parameters.spec,
            }
            if self.parameters.default_addr_pool is not None:
                init_arguments['default_addr_pool'] = self.parameters.default_addr_pool
            if self.parameters.subnet_size is not None:
                init_arguments['subnet_size'] = self.parameters.subnet_size
            try:
                self.client.init_swarm(**init_arguments)
            except APIError as exc:
                self.client.fail("Can not create a new Swarm Cluster: %s" % to_native(exc))

        if not self.client.check_if_swarm_manager():
            if not self.check_mode:
                self.client.fail("Swarm not created or other error!")

        self.created = True
        self.inspect_swarm()
        self.results['actions'].append("New Swarm cluster created: %s" % (self.swarm_info.get('ID')))
        self.differences.add('state', parameter='present', active='absent')
        self.results['changed'] = True
        self.results['swarm_facts'] = {
            'JoinTokens': self.swarm_info.get('JoinTokens'),
            'UnlockKey': self.swarm_info.get('UnlockKey')
        }

    def __update_swarm(self):
        try:
            self.inspect_swarm()
            version = self.swarm_info['Version']['Index']
            self.parameters.update_from_swarm_info(self.swarm_info)
            old_parameters = TaskParameters()
            old_parameters.update_from_swarm_info(self.swarm_info)
            self.parameters.compare_to_active(old_parameters, self.client, self.differences)
            if self.differences.empty:
                self.results['actions'].append("No modification")
                self.results['changed'] = False
                return
            update_parameters = TaskParameters.from_ansible_params(self.client)
            update_parameters.update_parameters(self.client)
            if not self.check_mode:
                self.client.update_swarm(
                    version=version, swarm_spec=update_parameters.spec,
                    rotate_worker_token=self.parameters.rotate_worker_token,
                    rotate_manager_token=self.parameters.rotate_manager_token)
        except APIError as exc:
            self.client.fail("Can not update a Swarm Cluster: %s" % to_native(exc))
            return

        self.inspect_swarm()
        self.results['actions'].append("Swarm cluster updated")
        self.results['changed'] = True

    def join(self):
        if self.client.check_if_swarm_node():
            self.results['actions'].append("This node is already part of a swarm.")
            return
        if not self.check_mode:
            try:
                self.client.join_swarm(
                    remote_addrs=self.parameters.remote_addrs, join_token=self.parameters.join_token,
                    listen_addr=self.parameters.listen_addr, advertise_addr=self.parameters.advertise_addr)
            except APIError as exc:
                self.client.fail("Can not join the Swarm Cluster: %s" % to_native(exc))
        self.results['actions'].append("New node is added to swarm cluster")
        self.differences.add('joined', parameter=True, active=False)
        self.results['changed'] = True

    def leave(self):
        if not self.client.check_if_swarm_node():
            self.results['actions'].append("This node is not part of a swarm.")
            return
        if not self.check_mode:
            try:
                self.client.leave_swarm(force=self.force)
            except APIError as exc:
                self.client.fail("This node can not leave the Swarm Cluster: %s" % to_native(exc))
        self.results['actions'].append("Node has left the swarm cluster")
        self.differences.add('joined', parameter='absent', active='present')
        self.results['changed'] = True

    def remove(self):
        if not self.client.check_if_swarm_manager():
            self.client.fail("This node is not a manager.")

        try:
            status_down = self.client.check_if_swarm_node_is_down(node_id=self.node_id, repeat_check=5)
        except APIError:
            return

        if not status_down:
            self.client.fail("Can not remove the node. The status node is ready and not down.")

        if not self.check_mode:
            try:
                self.client.remove_node(node_id=self.node_id, force=self.force)
            except APIError as exc:
                self.client.fail("Can not remove the node from the Swarm Cluster: %s" % to_native(exc))
        self.results['actions'].append("Node is removed from swarm cluster.")
        self.differences.add('joined', parameter=False, active=True)
        self.results['changed'] = True


def _detect_remove_operation(client):
    return client.module.params['state'] == 'remove'


def main():
    argument_spec = dict(
        advertise_addr=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'join', 'absent', 'remove', 'inspect']),
        force=dict(type='bool', default=False),
        listen_addr=dict(type='str', default='0.0.0.0:2377'),
        remote_addrs=dict(type='list', elements='str'),
        join_token=dict(type='str'),
        snapshot_interval=dict(type='int'),
        task_history_retention_limit=dict(type='int'),
        keep_old_snapshots=dict(type='int'),
        log_entries_for_slow_followers=dict(type='int'),
        heartbeat_tick=dict(type='int'),
        election_tick=dict(type='int'),
        dispatcher_heartbeat_period=dict(type='int'),
        node_cert_expiry=dict(type='int'),
        name=dict(type='str'),
        labels=dict(type='dict'),
        signing_ca_cert=dict(type='str'),
        signing_ca_key=dict(type='str'),
        ca_force_rotate=dict(type='int'),
        autolock_managers=dict(type='bool'),
        node_id=dict(type='str'),
        rotate_worker_token=dict(type='bool', default=False),
        rotate_manager_token=dict(type='bool', default=False),
        default_addr_pool=dict(type='list', elements='str'),
        subnet_size=dict(type='int'),
    )

    required_if = [
        ('state', 'join', ['advertise_addr', 'remote_addrs', 'join_token']),
        ('state', 'remove', ['node_id'])
    ]

    option_minimal_versions = dict(
        labels=dict(docker_py_version='2.6.0', docker_api_version='1.32'),
        signing_ca_cert=dict(docker_py_version='2.6.0', docker_api_version='1.30'),
        signing_ca_key=dict(docker_py_version='2.6.0', docker_api_version='1.30'),
        ca_force_rotate=dict(docker_py_version='2.6.0', docker_api_version='1.30'),
        autolock_managers=dict(docker_py_version='2.6.0'),
        log_driver=dict(docker_py_version='2.6.0'),
        remove_operation=dict(
            docker_py_version='2.4.0',
            detect_usage=_detect_remove_operation,
            usage_msg='remove swarm nodes'
        ),
        default_addr_pool=dict(docker_py_version='4.0.0', docker_api_version='1.39'),
        subnet_size=dict(docker_py_version='4.0.0', docker_api_version='1.39'),
    )

    client = AnsibleDockerSwarmClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        min_docker_version='1.10.0',
        min_docker_api_version='1.25',
        option_minimal_versions=option_minimal_versions,
    )

    try:
        results = dict(
            changed=False,
            result='',
            actions=[]
        )

        SwarmManager(client, results)()
        client.module.exit_json(**results)
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
