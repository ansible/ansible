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
module: docker_swarm

short_description: Manage Swarm cluster.

version_added: "2.6"

description:
     - Init a new Swarm cluster
     - Add/Remove nodes or managers to an existing cluster
options:
    advertise_addr:
        description:
            - Externally reachable address advertised
                to other nodes. This can either be an address/port combination
                in the form ``192.168.1.1:4567``, or an interface followed by a
                port number, like ``eth0:4567``. If the port number is omitted,
                the port number from the listen address is used. If
                ``advertise_addr`` is not specified, it will be automatically
                detected when possible.
        required: false
    listen_addr:
        description:
            - Listen address used for inter-manager
                communication, as well as determining the networking interface
                used for the VXLAN Tunnel Endpoint (VTEP). This can either be
                an address/port combination in the form ``192.168.1.1:4567``,
                or an interface followed by a port number, like ``eth0:4567``.
                If the port number is omitted, the default swarm listening port
                is used.
        default: '0.0.0.0:2377'
        required: false
    force:
        description:
            - Use with state C(init) to force creating a new Swarm, even if already part of one.
            - Use with state C(leave) to Leave the swarm even if this node is a manager.
        type: bool
        default: false
    state:
        description:
            - Set to C(init), to create a new cluster.
            - Set to C(join), to join an existing cluster.
            - Set to C(leave), to leave an existing cluster.
            - Set to C(remove), to remove a node.
        required: true
        default: join
        choices:
          - init
          - join
          - leave
          - remove
    node_id:
        description:
            - Used with I(state=remove). Swarm id of the node to remove.
    join_token:
        description:
            - Used with I(state=join). Swarm token used to join a swarm cluster.
    remote_addrs:
        description:
            - Used with I(state=join). Remote address of a manager to connect to.
    task_history_retention_limit:
        description:
            - Maximum number of tasks history stored.
    snapshot_interval:
        description: Number of logs entries between snapshot.
    keep_old_snapshots:
        description: Number of snapshots to keep beyond the current snapshot.
    log_entries_for_slow_followers:
        description: Number of log entries to keep around to sync up slow followers after a snapshot is created.
    heartbeat_tick:
        description: Amount of ticks (in seconds) between each heartbeat.
    election_tick:
        description: Amount of ticks (in seconds) needed without a leader to trigger a new election.
    dispatcher_heartbeat_period:
        description: The delay for an agent to send a heartbeat to the dispatcher.
    node_cert_expiry:
        description: Automatic expiry for nodes certificates.
    name:
        description: Swarm's name
    labels:
        description: User-defined key/value metadata.
    signing_ca_cert:
        description: The desired signing CA certificate for all swarm node TLS leaf certificates, in PEM format.
    signing_ca_key:
        description: The desired signing CA key for all swarm node TLS leaf certificates, in PEM format.
    ca_force_rotate:
        description: An integer whose purpose is to force swarm
                to generate a new signing CA certificate and key, if none have
                been specified.
    autolock_managers:
        description: If set, generate a key and use it to lock data stored on the managers.
        type: bool


extends_documentation_fragment:
    - docker

requirements:
    - "python >= 2.7"
    - "Docker API >= 1.35"

author:
  - Thierry Bouvet (@tbouvet)
'''

EXAMPLES = '''

- name: Init a new swarm
  docker_swarm:
    state: "init"
    advertise_addr: "192.168.1.1"

- name: Add nodes
  docker_swarm:
    state: "join"
    advertise_addr: "192.168.1.2"
    join_token: "SWMTKN-1--xxxxx"
    remote_addrs: ["192.168.1.1:2377"]

- name: Leave swarm
  docker_swarm:
    state: "leave"

- name: Remove node from swarm
  docker_swarm:
    state: "remove"
    node_id: "mynode"

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
                  example: "SWMTKN-1--xxxxx"
              Manager:
                  description: Token to create a new I(manager) node
                  returned: success
                  type: str
                  example: "SWMTKN-1--xxxxx"
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
    # missing docker-py handled in ansible.module_utils.docker
    pass

from ansible.module_utils.docker_common import AnsibleDockerClient, DockerBaseClass


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
        self.signing_ca_cert = None
        self.signing_ca_key = None
        self.ca_force_rotate = None
        self.autolock_managers = None

        for key, value in client.module.params.items():
            setattr(self, key, value)

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
            autolock_managers=self.autolock_managers
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
            "init": self.init_swarm,
            "join": self.join,
            "leave": self.leave,
            "remove": self.remove
        }

        choice_map.get(self.parameters.state)()

    def fail(self, msg):
        self.client.module.fail_json(msg=msg)

    def __isSwarmManager(self):
        try:
            data = self.client.inspect_swarm()
            if data:
                json_str = json.dumps(data, ensure_ascii=False)
                self.swarm_info = json.loads(json_str)
                return True
        except APIError:
            return False

    def init_swarm(self):
        if self.__isSwarmManager():
            self.results['actions'].append("This cluster is already a swarm cluster: %s" % (self.swarm_info['ID']))
            self.results['swarm_facts'] = {u'JoinTokens': self.swarm_info['JoinTokens']}
            return

        try:
            self.client.init_swarm(
                advertise_addr=self.parameters.advertise_addr, listen_addr=self.parameters.listen_addr,
                force_new_cluster=self.parameters.force_new_cluster, swarm_spec=self.parameters.spec)
        except APIError as exc:
            self.fail("Can not create a new Swarm Cluster: %s" % exc)

        self.__isSwarmManager()
        self.results['actions'].append("New Swarm cluster created: %s" % (self.swarm_info['ID']))
        self.results['changed'] = True
        self.results['swarm_facts'] = {u'JoinTokens': self.swarm_info['JoinTokens']}

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
            self.fail("Can not join the Swarm Cluster: %s" % exc)
        self.results['actions'].append("New node is added to swarm cluster")
        self.results['changed'] = True

    def leave(self):
        if not(self.__isSwarmNode()):
            self.results['actions'].append("This node is not part of a swarm.")
            return
        try:
            self.client.leave_swarm(force=self.parameters.force)
        except APIError as exc:
            self.fail("This node can not leave the Swarm Cluster: %s" % exc)
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
            self.fail("This node is not a manager.")

        try:
            status_down = self.__check_node_is_down()
        except APIError:
            return

        if not(status_down):
            self.fail("Can not remove the node. The status node is ready and not down.")

        try:
            self.client.remove_node(node_id=self.parameters.node_id, force=self.parameters.force)
        except APIError as exc:
            self.fail("Can not remove the node from the Swarm Cluster: %s" % exc)
        self.results['actions'].append("Node is removed from swarm cluster.")
        self.results['changed'] = True


def main():
    argument_spec = dict(
        advertise_addr=dict(type='str'),
        state=dict(type='str', choices=['init', 'join', 'leave', 'remove'], default='join'),
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
        node_id=dict(type='str')
    )

    required_if = [
        ('state', 'init', ['advertise_addr']),
        ('state', 'join', ['advertise_addr', 'remote_addrs', 'join_token']),
        ('state', 'remove', ['node_id']),
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
