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
            - If C(advertise_addr) is not specified, it will be automatically
                detected when possible.
    listen_addr:
        description:
            - Listen address used for inter-manager communication.
            - This can either be an address/port combination in the form
                C(192.168.1.1:4567), or an interface followed by a port number,
                like C(eth0:4567).
            - If the port number is omitted, the default swarm listening port
                is used.
        default: 0.0.0.0:2377
    force:
        description:
            - Use with state C(present) to force creating a new Swarm, even if already part of one.
            - Use with state C(absent) to Leave the swarm even if this node is a manager.
        type: bool
        default: 'no'
    state:
        description:
            - Set to C(present), to create/update a new cluster.
            - Set to C(join), to join an existing cluster.
            - Set to C(absent), to leave an existing cluster.
            - Set to C(remove), to remove an absent node from the cluster.
            - Set to C(inspect) to display swarm informations.
        required: true
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
    join_token:
        description:
            - Swarm token used to join a swarm cluster.
            - Used with I(state=join).
    remote_addrs:
        description:
            - Remote address of a manager to connect to.
            - Used with I(state=join).
    task_history_retention_limit:
        description:
            - Maximum number of tasks history stored.
            - Docker default value is C(5).
    snapshot_interval:
        description:
            - Number of logs entries between snapshot.
            - Docker default value is C(10000).
    keep_old_snapshots:
        description:
            - Number of snapshots to keep beyond the current snapshot.
            - Docker default value is C(0).
    log_entries_for_slow_followers:
        description:
            - Number of log entries to keep around to sync up slow followers after a snapshot is created.
    heartbeat_tick:
        description:
            - Amount of ticks (in seconds) between each heartbeat.
            - Docker default value is C(1s).
    election_tick:
        description:
            - Amount of ticks (in seconds) needed without a leader to trigger a new election.
            - Docker default value is C(10s).
    dispatcher_heartbeat_period:
        description:
            - The delay for an agent to send a heartbeat to the dispatcher.
            - Docker default value is C(5s).
    node_cert_expiry:
        description:
            - Automatic expiry for nodes certificates.
            - Docker default value is C(3months).
    name:
        description:
            - The name of the swarm.
    labels:
        description:
            - User-defined key/value metadata.
    signing_ca_cert:
        description:
            - The desired signing CA certificate for all swarm node TLS leaf certificates, in PEM format.
    signing_ca_key:
        description:
            - The desired signing CA key for all swarm node TLS leaf certificates, in PEM format.
    ca_force_rotate:
        description:
            - An integer whose purpose is to force swarm to generate a new signing CA certificate and key,
                if none have been specified.
            - Docker default value is C(0).
    autolock_managers:
        description:
            - If set, generate a key and use it to lock data stored on the managers.
            - Docker default value is C(no).
        type: bool
    rotate_worker_token:
        description: Rotate the worker join token.
        type: bool
        default: 'no'
    rotate_manager_token:
        description: Rotate the manager join token.
        type: bool
        default: 'no'
extends_documentation_fragment:
    - docker
requirements:
    - python >= 2.7
    - "docker-py >= 2.6.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       Version 2.1.0 or newer is only available with the C(docker) module."
    - Docker API >= 1.35
author:
  - Thierry Bouvet (@tbouvet)
'''

EXAMPLES = '''

- name: Init a new swarm with default parameters
  docker_swarm:
    state: present
    advertise_addr: 192.168.1.1

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
  type: complex
  contains:
      JoinTokens:
          description: Tokens to connect to the Swarm.
          returned: success
          type: complex
          contains:
              Worker:
                  description: Token to create a new I(worker) node
                  returned: success
                  type: str
                  example: SWMTKN-1--xxxxx
              Manager:
                  description: Token to create a new I(manager) node
                  returned: success
                  type: str
                  example: SWMTKN-1--xxxxx
actions:
  description: Provides the actions done on the swarm.
  returned: when action failed.
  type: list
  example: "['This cluster is already a swarm cluster']"

'''

import json
from time import sleep
try:
    from docker.errors import APIError
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils.docker_common import AnsibleDockerClient, DockerBaseClass
from ansible.module_utils._text import to_native


class TaskParameters(DockerBaseClass):
    def __init__(self, client):
        super(TaskParameters, self).__init__()

        self.state = None
        self.advertise_addr = None
        self.listen_addr = None
        self.force_new_cluster = None
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
        self.external_cas = None
        self.name = None
        self.labels = None
        self.log_driver = None
        self.signing_ca_cert = None
        self.signing_ca_key = None
        self.ca_force_rotate = None
        self.autolock_managers = None
        self.rotate_worker_token = None
        self.rotate_manager_token = None

        for key, value in client.module.params.items():
            setattr(self, key, value)

        self.update_parameters(client)

    def update_parameters(self, client):
        self.spec = client.create_swarm_spec(
            snapshot_interval=self.snapshot_interval,
            task_history_retention_limit=self.task_history_retention_limit,
            keep_old_snapshots=self.keep_old_snapshots,
            log_entries_for_slow_followers=self.log_entries_for_slow_followers,
            heartbeat_tick=self.heartbeat_tick,
            election_tick=self.election_tick,
            dispatcher_heartbeat_period=self.dispatcher_heartbeat_period,
            node_cert_expiry=self.node_cert_expiry,
            name=self.name,
            labels=self.labels,
            signing_ca_cert=self.signing_ca_cert,
            signing_ca_key=self.signing_ca_key,
            ca_force_rotate=self.ca_force_rotate,
            autolock_managers=self.autolock_managers,
            log_driver=self.log_driver
        )


class SwarmManager(DockerBaseClass):

    def __init__(self, client, results):

        super(SwarmManager, self).__init__()

        self.client = client
        self.results = results
        self.check_mode = self.client.check_mode

        self.parameters = TaskParameters(client)

    def __call__(self):
        choice_map = {
            "present": self.init_swarm,
            "join": self.join,
            "absent": self.leave,
            "remove": self.remove,
            "inspect": self.inspect_swarm
        }

        choice_map.get(self.parameters.state)()

    def __isSwarmManager(self):
        try:
            data = self.client.inspect_swarm()
            json_str = json.dumps(data, ensure_ascii=False)
            self.swarm_info = json.loads(json_str)
            return True
        except APIError:
            return False

    def inspect_swarm(self):
        try:
            data = self.client.inspect_swarm()
            json_str = json.dumps(data, ensure_ascii=False)
            self.swarm_info = json.loads(json_str)
            self.results['changed'] = False
            self.results['swarm_facts'] = self.swarm_info
        except APIError:
            return

    def init_swarm(self):
        if self.__isSwarmManager():
            self.__update_swarm()
            return

        try:
            if self.parameters.advertise_addr is None:
                self.client.fail(msg="advertise_addr is required to initialize a swarm cluster.")

            self.client.init_swarm(
                advertise_addr=self.parameters.advertise_addr, listen_addr=self.parameters.listen_addr,
                force_new_cluster=self.parameters.force_new_cluster, swarm_spec=self.parameters.spec)
        except APIError as exc:
            self.client.fail(msg="Can not create a new Swarm Cluster: %s" % to_native(exc))

        self.__isSwarmManager()
        self.results['actions'].append("New Swarm cluster created: %s" % (self.swarm_info['ID']))
        self.results['changed'] = True
        self.results['swarm_facts'] = {u'JoinTokens': self.swarm_info['JoinTokens']}

    def __update_spec(self, spec):
        if (self.parameters.node_cert_expiry is None):
            self.parameters.node_cert_expiry = spec['CAConfig']['NodeCertExpiry']

        if (self.parameters.dispatcher_heartbeat_period is None):
            self.parameters.dispatcher_heartbeat_period = spec['Dispatcher']['HeartbeatPeriod']

        if (self.parameters.snapshot_interval is None):
            self.parameters.snapshot_interval = spec['Raft']['SnapshotInterval']
        if (self.parameters.keep_old_snapshots is None):
            self.parameters.keep_old_snapshots = spec['Raft']['KeepOldSnapshots']
        if (self.parameters.heartbeat_tick is None):
            self.parameters.heartbeat_tick = spec['Raft']['HeartbeatTick']
        if (self.parameters.log_entries_for_slow_followers is None):
            self.parameters.log_entries_for_slow_followers = spec['Raft']['LogEntriesForSlowFollowers']
        if (self.parameters.election_tick is None):
            self.parameters.election_tick = spec['Raft']['ElectionTick']

        if (self.parameters.task_history_retention_limit is None):
            self.parameters.task_history_retention_limit = spec['Orchestration']['TaskHistoryRetentionLimit']

        if (self.parameters.autolock_managers is None):
            self.parameters.autolock_managers = spec['EncryptionConfig']['AutoLockManagers']

        if (self.parameters.name is None):
            self.parameters.name = spec['Name']

        if (self.parameters.labels is None):
            self.parameters.labels = spec['Labels']

        if 'LogDriver' in spec['TaskDefaults']:
            self.parameters.log_driver = spec['TaskDefaults']['LogDriver']

        self.parameters.update_parameters(self.client)

        return self.parameters.spec

    def __update_swarm(self):
        try:
            self.inspect_swarm()
            version = self.swarm_info['Version']['Index']
            spec = self.swarm_info['Spec']
            new_spec = self.__update_spec(spec)
            del spec['TaskDefaults']
            if spec == new_spec:
                self.results['actions'].append("No modification")
                self.results['changed'] = False
                return
            self.client.update_swarm(
                version=version, swarm_spec=new_spec, rotate_worker_token=self.parameters.rotate_worker_token,
                rotate_manager_token=self.parameters.rotate_manager_token)
        except APIError as exc:
            self.client.fail(msg="Can not update a Swarm Cluster: %s" % to_native(exc))
            return

        self.inspect_swarm()
        self.results['actions'].append("Swarm cluster updated")
        self.results['changed'] = True

    def __isSwarmNode(self):
        info = self.client.info()
        if info:
            json_str = json.dumps(info, ensure_ascii=False)
            self.swarm_info = json.loads(json_str)
            if self.swarm_info['Swarm']['NodeID']:
                return True
        return False

    def join(self):
        if self.__isSwarmNode():
            self.results['actions'].append("This node is already part of a swarm.")
            return
        try:
            self.client.join_swarm(
                remote_addrs=self.parameters.remote_addrs, join_token=self.parameters.join_token, listen_addr=self.parameters.listen_addr,
                advertise_addr=self.parameters.advertise_addr)
        except APIError as exc:
            self.client.fail(msg="Can not join the Swarm Cluster: %s" % to_native(exc))
        self.results['actions'].append("New node is added to swarm cluster")
        self.results['changed'] = True

    def leave(self):
        if not(self.__isSwarmNode()):
            self.results['actions'].append("This node is not part of a swarm.")
            return
        try:
            self.client.leave_swarm(force=self.parameters.force)
        except APIError as exc:
            self.client.fail(msg="This node can not leave the Swarm Cluster: %s" % to_native(exc))
        self.results['actions'].append("Node has leaved the swarm cluster")
        self.results['changed'] = True

    def __get_node_info(self):
        try:
            node_info = self.client.inspect_node(node_id=self.parameters.node_id)
        except APIError as exc:
            raise exc
        json_str = json.dumps(node_info, ensure_ascii=False)
        node_info = json.loads(json_str)
        return node_info

    def __check_node_is_down(self):
        for _x in range(0, 5):
            node_info = self.__get_node_info()
            if node_info['Status']['State'] == 'down':
                return True
            sleep(5)
        return False

    def remove(self):
        if not(self.__isSwarmManager()):
            self.client.fail(msg="This node is not a manager.")

        try:
            status_down = self.__check_node_is_down()
        except APIError:
            return

        if not(status_down):
            self.client.fail(msg="Can not remove the node. The status node is ready and not down.")

        try:
            self.client.remove_node(node_id=self.parameters.node_id, force=self.parameters.force)
        except APIError as exc:
            self.client.fail(msg="Can not remove the node from the Swarm Cluster: %s" % to_native(exc))
        self.results['actions'].append("Node is removed from swarm cluster.")
        self.results['changed'] = True


def main():
    argument_spec = dict(
        advertise_addr=dict(type='str'),
        state=dict(type='str', choices=['present', 'join', 'absent', 'remove', 'inspect'], default='present'),
        force=dict(type='bool', default=False),
        listen_addr=dict(type='str', default='0.0.0.0:2377'),
        remote_addrs=dict(type='list'),
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
        rotate_manager_token=dict(type='bool', default=False)
    )

    required_if = [
        ('state', 'join', ['advertise_addr', 'remote_addrs', 'join_token']),
        ('state', 'remove', ['node_id'])
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if
    )

    results = dict(
        changed=False,
        result='',
        actions=[]
    )

    SwarmManager(client, results)()
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
