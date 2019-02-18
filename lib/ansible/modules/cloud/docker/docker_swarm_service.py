#!/usr/bin/python
#
# (c) 2017, Dario Zanzico (git@dariozanzico.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}
DOCUMENTATION = '''
---
module: docker_swarm_service
author: "Dario Zanzico (@dariko), Jason Witkowski (@jwitko)"
short_description: docker swarm service
description: |
  Manage docker services. Allows live altering of already defined services
version_added: "2.7"
options:
  name:
    required: true
    description:
    - Service name
  image:
    type: str
    required: true
    description:
    - Service image path and tag.
      Maps docker service IMAGE parameter.
  resolve_image:
    type: bool
    required: false
    default: true
    description:
      - If the current image digest should be resolved from registry and updated if changed.
    version_added: 2.8
  state:
    required: true
    default: present
    description:
    - Service state.
    choices:
    - present
    - absent
  args:
    required: false
    default: []
    description:
    - List comprised of the command and the arguments to be run inside
    - the container
  command:
    required: false
    description:
    - Command to execute when the container starts.
      A command may be either a string or a list or a list of strings.
    version_added: 2.8
  constraints:
    required: false
    default: []
    description:
    - List of the service constraints.
    - Maps docker service --constraint option.
  placement_preferences:
    required: false
    type: list
    description:
    - List of the placement preferences as key value pairs.
    - Maps docker service C(--placement-pref) option.
    version_added: 2.8
  hostname:
    required: false
    default: ""
    description:
    - Container hostname
    - Maps docker service --hostname option.
    - Requires API version >= 1.25
  tty:
    required: false
    type: bool
    default: False
    description:
    - Allocate a pseudo-TTY
    - Maps docker service --tty option.
    - Requires API version >= 1.25
  dns:
    required: false
    default: []
    description:
    - List of custom DNS servers.
    - Maps docker service --dns option.
    - Requires API version >= 1.25
  dns_search:
    required: false
    default: []
    description:
    - List of custom DNS search domains.
    - Maps docker service --dns-search option.
    - Requires API version >= 1.25
  dns_options:
    required: false
    default: []
    description:
    - List of custom DNS options.
    - Maps docker service --dns-option option.
    - Requires API version >= 1.25
  force_update:
    required: false
    type: bool
    default: False
    description:
    - Force update even if no changes require it.
    - Maps to docker service update --force option.
    - Requires API version >= 1.25
  labels:
    required: false
    type: dict
    description:
    - Dictionary of key value pairs.
    - Maps docker service --label option.
  container_labels:
    required: false
    type: dict
    description:
    - Dictionary of key value pairs.
    - Maps docker service --container-label option.
  endpoint_mode:
    type: str
    description:
    - Service endpoint mode.
    - Maps docker service --endpoint-mode option.
    choices:
    - vip
    - dnsrr
  env:
    required: false
    default: []
    description:
    - List of the service environment variables.
    - Maps docker service --env option.
  log_driver:
    required: false
    default: json-file
    description:
    - Configure the logging driver for a service
  log_driver_options:
    required: false
    default: []
    description:
    - Options for service logging driver
  limit_cpu:
    required: false
    default: 0.000
    description:
    - Service CPU limit. 0 equals no limit.
    - Maps docker service --limit-cpu option.
  reserve_cpu:
    required: false
    default: 0.000
    description:
    - Service CPU reservation. 0 equals no reservation.
    - Maps docker service --reserve-cpu option.
  limit_memory:
    required: false
    default: 0
    description:
    - "Service memory limit (format: C(<number>[<unit>])). Number is a positive integer.
      Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
      C(T) (tebibyte), or C(P) (pebibyte)."
    - 0 equals no limit.
    - Omitting the unit defaults to bytes.
    - Maps docker service --limit-memory option.
  reserve_memory:
    required: false
    default: 0
    description:
    - "Service memory reservation (format: C(<number>[<unit>])). Number is a positive integer.
      Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
      C(T) (tebibyte), or C(P) (pebibyte)."
    - 0 equals no reservation.
    - Omitting the unit defaults to bytes.
    - Maps docker service --reserve-memory option.
  mode:
    required: false
    default: replicated
    description:
    - Service replication mode.
    - Maps docker service --mode option.
  mounts:
    required: false
    description:
    - List of dictionaries describing the service mounts.
    - Every item must be a dictionary exposing the keys source, target, type (defaults to 'bind'), readonly (defaults to false)
    - Maps docker service --mount option.
    default: []
  secrets:
    required: false
    description:
    - List of dictionaries describing the service secrets.
    - Every item must be a dictionary exposing the keys secret_id, secret_name, filename, uid (defaults to 0), gid (defaults to 0), mode (defaults to 0o444)
    - Maps docker service --secret option.
    - Requires API version >= 1.25
    default: []
  configs:
    required: false
    description:
    - List of dictionaries describing the service configs.
    - Every item must be a dictionary exposing the keys config_id, config_name, filename, uid (defaults to 0), gid (defaults to 0), mode (defaults to 0o444)
    - Maps docker service --config option.
    - Requires API version >= 1.30
    default: null
  networks:
    required: false
    default: []
    description:
    - List of the service networks names.
    - Maps docker service --network option.
  publish:
    type: list
    required: false
    default: []
    description:
    - List of dictionaries describing the service published ports.
    - Only used with api_version >= 1.25
    suboptions:
      published_port:
         type: int
         required: true
         description:
           - The port to make externally available.
      target_port:
         type: int
         required: true
         description:
           - The port inside the container to expose.
      protocol:
         type: str
         required: false
         default: tcp
         description:
           - What protocol to use.
         choices:
           - tcp
           - udp
      mode:
        type: str
        required: false
        description:
          - What publish mode to use.
          - Requires API version >= 1.32 and docker python library >= 3.0.0
        choices:
          - ingress
          - host
  replicas:
    required: false
    default: -1
    description:
    - Number of containers instantiated in the service. Valid only if ``mode=='replicated'``.
    - If set to -1, and service is not present, service replicas will be set to 1.
    - If set to -1, and service is present, service replicas will be unchanged.
    - Maps docker service --replicas option.
  restart_policy:
    required: false
    default: none
    description:
    - Restart condition of the service.
    - Maps docker service --restart-condition option.
    choices:
    - none
    - on-failure
    - any
  restart_policy_attempts:
    required: false
    default: 0
    description:
    - Maximum number of service restarts.
    - Maps docker service --restart-max-attempts option.
  restart_policy_delay:
    required: false
    default: 0
    description:
    - Delay between restarts.
    - Maps docker service --restart-delay option.
  restart_policy_window:
    required: false
    default: 0
    description:
    - Restart policy evaluation window.
    - Maps docker service --restart-window option.
  update_delay:
    required: false
    default: 10
    description:
    - Rolling update delay
    - Maps docker service --update-delay option
  update_parallelism:
    required: false
    default: 1
    description:
    - Rolling update parallelism
    - Maps docker service --update-parallelism option
  update_failure_action:
    required: false
    default: continue
    description:
    - Action to take in case of container failure
    - Maps to docker service --update-failure-action option
    choices:
    - continue
    - pause
  update_monitor:
    required: false
    default: 5000000000
    description:
    - Time to monitor updated tasks for failures, in nanoseconds.
    - Maps to docker service --update-monitor option
  update_max_failure_ratio:
    required: false
    default: 0.00
    description:
    - Fraction of tasks that may fail during an update before the failure action is invoked
    - Maps to docker service --update-max-failure-ratio
  update_order:
    required: false
    default: null
    description:
    - Specifies the order of operations when rolling out an updated task.
    - Maps to docker service --update-order
    - Requires API version >= 1.29
  user:
    type: str
    required: false
    description:
    - Sets the username or UID used for the specified command.
    - Before Ansible 2.8, the default value for this option was C(root).
      The default has been removed so that the user defined in the image is used if no user is specified here.
extends_documentation_fragment:
- docker
requirements:
- "docker-py >= 2.0"
- "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
   module has been superseded by L(docker,https://pypi.org/project/docker/)
   (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
   Version 2.1.0 or newer is only available with the C(docker) module."
- "Docker API >= 1.24"
notes:
  - "Images will only resolve to the latest digest when using Docker API >= 1.30 and docker-py >= 3.2.0.
     When using older versions use C(force_update: true) to trigger the swarm to resolve a new image."
'''

RETURN = '''
ansible_swarm_service:
  returned: always
  type: dict
  description:
  - Dictionary of variables representing the current state of the service.
    Matches the module parameters format.
  - Note that facts are not part of registered vars but accessible directly.
  sample: '{
    "args": [
      "sleep",
      "3600"
    ],
    "constraints": [],
    "container_labels": {},
    "endpoint_mode": "vip",
    "env": [
      "ENVVAR1=envvar1"
    ],
    "force_update": False,
    "image": "alpine",
    "labels": {},
    "limit_cpu": 0.0,
    "limit_memory": 0,
    "log_driver": "json-file",
    "log_driver_options": {},
    "mode": "replicated",
    "mounts": [
      {
        "source": "/tmp/",
        "target": "/remote_tmp/",
        "type": "bind"
      }
    ],
    "secrets": [],
    "configs": [],
    "networks": [],
    "publish": [],
    "replicas": 1,
    "reserve_cpu": 0.0,
    "reserve_memory": 0,
    "restart_policy": "any",
    "restart_policy_attempts": 5,
    "restart_policy_delay": 0,
    "restart_policy_window": 30,
    "update_delay": 10,
    "update_parallelism": 1,
    "update_failure_action": "continue",
    "update_monitor": 5000000000
    "update_max_failure_ratio": 0,
    "update_order": "stop-first"
  }'
changes:
  returned: always
  description:
  - List of changed service attributes if a service has been altered,
    [] otherwhise
  type: list
  sample: ['container_labels', 'replicas']
rebuilt:
  returned: always
  description:
  - True if the service has been recreated (removed and created)
  type: bool
  sample: True
'''

EXAMPLES = '''
-   name: define myservice
    docker_swarm_service:
        name: myservice
        image: "alpine"
        args:
        - "sleep"
        - "3600"
        mounts:
        -   source: /tmp/
            target: /remote_tmp/
            type: bind
        env:
        -   "ENVVAR1=envvar1"
        log_driver: fluentd
        log_driver_options:
          fluentd-address: "127.0.0.1:24224"
          fluentd-async-connect: true
          tag: "{{.Name}}/{{.ID}}"
        restart_policy: any
        restart_policy_attempts: 5
        restart_policy_window: 30
    register: dss_out1
-   name: change myservice.env
    docker_swarm_service:
        name: myservice
        image: "alpine"
        args:
        -   "sleep"
        -   "7200"
        mounts:
        -   source: /tmp/
            target: /remote_tmp/
            type: bind
        env:
        -   "ENVVAR1=envvar1"
        restart_policy: any
        restart_policy_attempts: 5
        restart_policy_window: 30
    register: dss_out2
-   name: test for changed myservice facts
    fail:
        msg: unchanged service
    when: "{{ dss_out1 == dss_out2 }}"
-   name: change myservice.image
    docker_swarm_service:
        name: myservice
        image: "alpine:edge"
        args:
        -   "sleep"
        -   "7200"
        mounts:
        -   source: /tmp/
            target: /remote_tmp/
            type: bind
        env:
        -   "ENVVAR1=envvar1"
        restart_policy: any
        restart_policy_attempts: 5
        restart_policy_window: 30
    register: dss_out3
-   name: test for changed myservice facts
    fail:
        msg: unchanged service
    when: "{{ dss_out2 == dss_out3 }}"
-   name: remove mount
    docker_swarm_service:
        name: myservice
        image: "alpine:edge"
        args:
        -   "sleep"
        -   "7200"
        env:
        -   "ENVVAR1=envvar1"
        restart_policy: any
        restart_policy_attempts: 5
        restart_policy_window: 30
    register: dss_out4
-   name: test for changed myservice facts
    fail:
        msg: unchanged service
    when: "{{ dss_out3 == dss_out4 }}"
-   name: keep service as it is
    docker_swarm_service:
        name: myservice
        image: "alpine:edge"
        args:
        -   "sleep"
        -   "7200"
        env:
        -   "ENVVAR1=envvar1"
        restart_policy: any
        restart_policy_attempts: 5
        restart_policy_window: 30
    register: dss_out5
-   name: test for changed service facts
    fail:
        msg: changed service
    when: "{{ dss_out5 != dss_out5 }}"
-   name: remove myservice
    docker_swarm_service:
        name: myservice
        state: absent
-   name: set placement preferences
    docker_swarm_service:
        name: myservice
        image: alpine:edge
        placement_preferences:
          - spread: "node.labels.mylabel"
'''

import time
import shlex
import operator
from ansible.module_utils.docker_common import (
    AnsibleDockerClient,
    DifferenceTracker,
    DockerBaseClass,
)
from ansible.module_utils.basic import human_to_bytes
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text

try:
    from distutils.version import LooseVersion
    from docker import types
    from docker.utils import parse_repository_tag
    from docker.errors import DockerException
except Exception:
    # missing docker-py handled in ansible.module_utils.docker
    pass


class DockerService(DockerBaseClass):
    def __init__(self):
        super(DockerService, self).__init__()
        self.image = ""
        self.command = None
        self.args = []
        self.endpoint_mode = None
        self.dns = []
        self.hostname = ""
        self.tty = False
        self.dns_search = []
        self.dns_options = []
        self.env = []
        self.force_update = None
        self.log_driver = "json-file"
        self.log_driver_options = {}
        self.labels = {}
        self.container_labels = {}
        self.limit_cpu = 0.000
        self.limit_memory = 0
        self.reserve_cpu = 0.000
        self.reserve_memory = 0
        self.mode = "replicated"
        self.user = None
        self.mounts = []
        self.configs = []
        self.secrets = []
        self.constraints = []
        self.networks = []
        self.publish = []
        self.constraints = []
        self.placement_preferences = None
        self.replicas = -1
        self.service_id = False
        self.service_version = False
        self.restart_policy = None
        self.restart_policy_attempts = None
        self.restart_policy_delay = None
        self.restart_policy_window = None
        self.update_delay = None
        self.update_parallelism = 1
        self.update_failure_action = "continue"
        self.update_monitor = 5000000000
        self.update_max_failure_ratio = 0.00
        self.update_order = None

    def get_facts(self):
        return {
            'image': self.image,
            'mounts': self.mounts,
            'configs': self.configs,
            'networks': self.networks,
            'command': self.command,
            'args': self.args,
            'tty': self.tty,
            'dns': self.dns,
            'dns_search': self.dns_search,
            'dns_options': self.dns_options,
            'hostname': self.hostname,
            'env': self.env,
            'force_update': self.force_update,
            'log_driver': self.log_driver,
            'log_driver_options': self.log_driver_options,
            'publish': self.publish,
            'constraints': self.constraints,
            'placement_preferences': self.placement_preferences,
            'labels': self.labels,
            'container_labels': self.container_labels,
            'mode': self.mode,
            'replicas': self.replicas,
            'endpoint_mode': self.endpoint_mode,
            'restart_policy': self.restart_policy,
            'limit_cpu': self.limit_cpu,
            'limit_memory': self.limit_memory,
            'reserve_cpu': self.reserve_cpu,
            'reserve_memory': self.reserve_memory,
            'restart_policy_delay': self.restart_policy_delay,
            'restart_policy_attempts': self.restart_policy_attempts,
            'restart_policy_window': self.restart_policy_window,
            'update_delay': self.update_delay,
            'update_parallelism': self.update_parallelism,
            'update_failure_action': self.update_failure_action,
            'update_monitor': self.update_monitor,
            'update_max_failure_ratio': self.update_max_failure_ratio,
            'update_order': self.update_order}

    @staticmethod
    def from_ansible_params(ap, old_service, image_digest):
        s = DockerService()
        s.image = image_digest
        s.constraints = ap['constraints']
        s.placement_preferences = ap['placement_preferences']
        s.args = ap['args']
        s.endpoint_mode = ap['endpoint_mode']
        s.dns = ap['dns']
        s.dns_search = ap['dns_search']
        s.dns_options = ap['dns_options']
        s.hostname = ap['hostname']
        s.tty = ap['tty']
        s.env = ap['env']
        s.log_driver = ap['log_driver']
        s.log_driver_options = ap['log_driver_options']
        s.labels = ap['labels']
        s.container_labels = ap['container_labels']
        s.limit_cpu = ap['limit_cpu']
        s.reserve_cpu = ap['reserve_cpu']
        s.mode = ap['mode']
        s.networks = ap['networks']
        s.restart_policy = ap['restart_policy']
        s.restart_policy_attempts = ap['restart_policy_attempts']
        s.restart_policy_delay = ap['restart_policy_delay']
        s.restart_policy_window = ap['restart_policy_window']
        s.update_delay = ap['update_delay']
        s.update_parallelism = ap['update_parallelism']
        s.update_failure_action = ap['update_failure_action']
        s.update_monitor = ap['update_monitor']
        s.update_max_failure_ratio = ap['update_max_failure_ratio']
        s.update_order = ap['update_order']
        s.user = ap['user']

        s.command = ap['command']
        if isinstance(s.command, string_types):
            s.command = shlex.split(s.command)
        elif isinstance(s.command, list):
            invalid_items = [
                (index, item)
                for index, item in enumerate(s.command)
                if not isinstance(item, string_types)
            ]
            if invalid_items:
                errors = ', '.join(
                    [
                        '%s (%s) at index %s' % (item, type(item), index)
                        for index, item in invalid_items
                    ]
                )
                raise Exception(
                    'All items in a command list need to be strings. '
                    'Check quoting. Invalid items: %s.'
                    % errors
                )
            s.command = ap['command']
        elif s.command is not None:
            raise ValueError(
                'Invalid type for command %s (%s). '
                'Only string or list allowed. Check quoting.'
                % (s.command, type(s.command))
            )

        if ap['force_update']:
            s.force_update = int(str(time.time()).replace('.', ''))

        if ap['replicas'] == -1:
            if old_service:
                s.replicas = old_service.replicas
            else:
                s.replicas = 1
        else:
            s.replicas = ap['replicas']

        for param_name in ['reserve_memory', 'limit_memory']:
            if ap.get(param_name):
                try:
                    setattr(s, param_name, human_to_bytes(ap[param_name]))
                except ValueError as exc:
                    raise Exception("Failed to convert %s to bytes: %s" % (param_name, exc))

        s.publish = []
        for param_p in ap['publish']:
            service_p = {}
            service_p['protocol'] = param_p['protocol']
            service_p['mode'] = param_p['mode']
            service_p['published_port'] = int(param_p['published_port'])
            service_p['target_port'] = int(param_p['target_port'])
            if service_p['protocol'] not in ['tcp', 'udp']:
                raise ValueError("got publish.protocol '%s', valid values:'tcp', 'udp'" %
                                 service_p['protocol'])
            if service_p['mode'] not in [None, 'ingress', 'host']:
                raise ValueError("got publish.mode '%s', valid values:'ingress', 'host'" %
                                 service_p['mode'])
            s.publish.append(service_p)
        s.mounts = []
        for param_m in ap['mounts']:
            service_m = {}
            service_m['readonly'] = bool(param_m.get('readonly', False))
            service_m['type'] = param_m.get('type', 'bind')
            service_m['source'] = param_m['source']
            service_m['target'] = param_m['target']
            s.mounts.append(service_m)

        s.configs = None
        if ap['configs'] is not None:
            s.configs = []
            for param_m in ap['configs']:
                service_c = {}
                service_c['config_id'] = param_m['config_id']
                service_c['config_name'] = str(param_m['config_name'])
                service_c['filename'] = param_m.get('filename', service_c['config_name'])
                service_c['uid'] = int(param_m.get('uid', "0"))
                service_c['gid'] = int(param_m.get('gid', "0"))
                service_c['mode'] = param_m.get('mode', 0o444)
                s.configs.append(service_c)

        s.secrets = []
        for param_m in ap['secrets']:
            service_s = {}
            service_s['secret_id'] = param_m['secret_id']
            service_s['secret_name'] = str(param_m['secret_name'])
            service_s['filename'] = param_m.get('filename', service_s['secret_name'])
            service_s['uid'] = int(param_m.get('uid', "0"))
            service_s['gid'] = int(param_m.get('gid', "0"))
            service_s['mode'] = param_m.get('mode', 0o444)
            s.secrets.append(service_s)
        return s

    def compare(self, os):
        differences = DifferenceTracker()
        needs_rebuild = False
        force_update = False
        if self.endpoint_mode is not None and self.endpoint_mode != os.endpoint_mode:
            differences.add('endpoint_mode', parameter=self.endpoint_mode, active=os.endpoint_mode)
        if self.env != os.env:
            differences.add('env', parameter=self.env, active=os.env)
        if self.log_driver != os.log_driver:
            differences.add('log_driver', parameter=self.log_driver, active=os.log_driver)
        if self.log_driver_options != os.log_driver_options:
            differences.add('log_opt', parameter=self.log_driver_options, active=os.log_driver_options)
        if self.mode != os.mode:
            needs_rebuild = True
            differences.add('mode', parameter=self.mode, active=os.mode)
        if self.mounts != os.mounts:
            differences.add('mounts', parameter=self.mounts, active=os.mounts)
        if self.configs is not None and self.configs != os.configs:
            differences.add('configs', parameter=self.configs, active=os.configs)
        if self.secrets != os.secrets:
            differences.add('secrets', parameter=self.secrets, active=os.secrets)
        if self.networks != os.networks:
            differences.add('networks', parameter=self.networks, active=os.networks)
            needs_rebuild = True
        if self.replicas != os.replicas:
            differences.add('replicas', parameter=self.replicas, active=os.replicas)
        if self.command is not None and self.command != os.command:
            differences.add('command', parameter=self.command, active=os.command)
        if self.args != os.args:
            differences.add('args', parameter=self.args, active=os.args)
        if self.constraints != os.constraints:
            differences.add('constraints', parameter=self.constraints, active=os.constraints)
        if self.placement_preferences is not None and self.placement_preferences != os.placement_preferences:
            differences.add('placement_preferences', parameter=self.placement_preferences, active=os.placement_preferences)
        if self.labels != os.labels:
            differences.add('labels', parameter=self.labels, active=os.labels)
        if self.limit_cpu != os.limit_cpu:
            differences.add('limit_cpu', parameter=self.limit_cpu, active=os.limit_cpu)
        if self.limit_memory != os.limit_memory:
            differences.add('limit_memory', parameter=self.limit_memory, active=os.limit_memory)
        if self.reserve_cpu != os.reserve_cpu:
            differences.add('reserve_cpu', parameter=self.reserve_cpu, active=os.reserve_cpu)
        if self.reserve_memory != os.reserve_memory:
            differences.add('reserve_memory', parameter=self.reserve_memory, active=os.reserve_memory)
        if self.container_labels != os.container_labels:
            differences.add('container_labels', parameter=self.container_labels, active=os.container_labels)
        if self.has_publish_changed(os.publish):
            differences.add('publish', parameter=self.publish, active=os.publish)
        if self.restart_policy != os.restart_policy:
            differences.add('restart_policy', parameter=self.restart_policy, active=os.restart_policy)
        if self.restart_policy_attempts != os.restart_policy_attempts:
            differences.add('restart_policy_attempts', parameter=self.restart_policy_attempts, active=os.restart_policy_attempts)
        if self.restart_policy_delay != os.restart_policy_delay:
            differences.add('restart_policy_delay', parameter=self.restart_policy_delay, active=os.restart_policy_delay)
        if self.restart_policy_window != os.restart_policy_window:
            differences.add('restart_policy_window', parameter=self.restart_policy_window, active=os.restart_policy_window)
        if self.update_delay != os.update_delay:
            differences.add('update_delay', parameter=self.update_delay, active=os.update_delay)
        if self.update_parallelism != os.update_parallelism:
            differences.add('update_parallelism', parameter=self.update_parallelism, active=os.update_parallelism)
        if self.update_failure_action != os.update_failure_action:
            differences.add('update_failure_action', parameter=self.update_failure_action, active=os.update_failure_action)
        if self.update_monitor != os.update_monitor:
            differences.add('update_monitor', parameter=self.update_monitor, active=os.update_monitor)
        if self.update_max_failure_ratio != os.update_max_failure_ratio:
            differences.add('update_max_failure_ratio', parameter=self.update_max_failure_ratio, active=os.update_max_failure_ratio)
        if self.update_order is not None and self.update_order != os.update_order:
            differences.add('update_order', parameter=self.update_order, active=os.update_order)
        has_image_changed, change = self.has_image_changed(os.image)
        if has_image_changed:
            differences.add('image', parameter=self.image, active=change)
        if self.user and self.user != os.user:
            differences.add('user', parameter=self.user, active=os.user)
        if self.dns != os.dns:
            differences.add('dns', parameter=self.dns, active=os.dns)
        if self.dns_search != os.dns_search:
            differences.add('dns_search', parameter=self.dns_search, active=os.dns_search)
        if self.dns_options != os.dns_options:
            differences.add('dns_options', parameter=self.dns_options, active=os.dns_options)
        if self.hostname != os.hostname:
            differences.add('hostname', parameter=self.hostname, active=os.hostname)
        if self.tty != os.tty:
            differences.add('tty', parameter=self.tty, active=os.tty)
        if self.force_update:
            force_update = True
        return not differences.empty or force_update, differences, needs_rebuild, force_update

    def has_publish_changed(self, old_publish):
        if len(self.publish) != len(old_publish):
            return True
        publish_sorter = operator.itemgetter('published_port', 'target_port', 'protocol')
        publish = sorted(self.publish, key=publish_sorter)
        old_publish = sorted(old_publish, key=publish_sorter)
        for publish_item, old_publish_item in zip(publish, old_publish):
            ignored_keys = set()
            if not publish_item.get('mode'):
                ignored_keys.add('mode')
            # Create copies of publish_item dicts where keys specified in ignored_keys are left out
            filtered_old_publish_item = dict(
                (k, v) for k, v in old_publish_item.items() if k not in ignored_keys
            )
            filtered_publish_item = dict(
                (k, v) for k, v in publish_item.items() if k not in ignored_keys
            )
            if filtered_publish_item != filtered_old_publish_item:
                return True
        return False

    def has_image_changed(self, old_image):
        if '@' not in self.image:
            old_image = old_image.split('@')[0]
        return self.image != old_image, old_image

    def __str__(self):
        return str({
            'mode': self.mode,
            'env': self.env,
            'endpoint_mode': self.endpoint_mode,
            'mounts': self.mounts,
            'configs': self.configs,
            'secrets': self.secrets,
            'networks': self.networks,
            'replicas': self.replicas})

    def generate_docker_py_service_description(self, name, docker_networks):
        mounts = []
        for mount_config in self.mounts:
            mounts.append(
                types.Mount(target=mount_config['target'],
                            source=mount_config['source'],
                            type=mount_config['type'],
                            read_only=mount_config['readonly'])
            )

        configs = None
        if self.configs:
            configs = []
            for config_config in self.configs:
                configs.append(
                    types.ConfigReference(
                        config_id=config_config['config_id'],
                        config_name=config_config['config_name'],
                        filename=config_config.get('filename'),
                        uid=config_config.get('uid'),
                        gid=config_config.get('gid'),
                        mode=config_config.get('mode')
                    )
                )

        secrets = []
        for secret_config in self.secrets:
            secrets.append(
                types.SecretReference(
                    secret_id=secret_config['secret_id'],
                    secret_name=secret_config['secret_name'],
                    filename=secret_config.get('filename'),
                    uid=secret_config.get('uid'),
                    gid=secret_config.get('gid'),
                    mode=secret_config.get('mode')
                )
            )

        dns_config = types.DNSConfig(
            nameservers=self.dns,
            search=self.dns_search,
            options=self.dns_options
        )

        cspec = types.ContainerSpec(
            image=self.image,
            command=self.command,
            args=self.args,
            hostname=self.hostname,
            env=self.env,
            user=self.user,
            labels=self.container_labels,
            mounts=mounts,
            secrets=secrets,
            tty=self.tty,
            dns_config=dns_config,
            configs=configs
        )

        log_driver = types.DriverConfig(name=self.log_driver, options=self.log_driver_options)

        placement = types.Placement(
            constraints=self.constraints,
            preferences=[
                {key.title(): {"SpreadDescriptor": value}}
                for preference in self.placement_preferences
                for key, value in preference.items()
            ] if self.placement_preferences else None,
        )

        restart_policy = types.RestartPolicy(
            condition=self.restart_policy,
            delay=self.restart_policy_delay,
            max_attempts=self.restart_policy_attempts,
            window=self.restart_policy_window)

        resources = types.Resources(
            cpu_limit=int(self.limit_cpu * 1000000000.0),
            mem_limit=self.limit_memory,
            cpu_reservation=int(self.reserve_cpu * 1000000000.0),
            mem_reservation=self.reserve_memory
        )

        update_policy = types.UpdateConfig(
            parallelism=self.update_parallelism,
            delay=self.update_delay,
            failure_action=self.update_failure_action,
            monitor=self.update_monitor,
            max_failure_ratio=self.update_max_failure_ratio,
            order=self.update_order
        )

        task_template = types.TaskTemplate(
            container_spec=cspec,
            log_driver=log_driver,
            restart_policy=restart_policy,
            placement=placement,
            resources=resources,
            force_update=self.force_update)

        if self.mode == 'global':
            self.replicas = None

        mode = types.ServiceMode(self.mode, replicas=self.replicas)

        networks = []
        for network_name in self.networks:
            network_id = None
            try:
                network_id = list(filter(lambda n: n['name'] == network_name, docker_networks))[0]['id']
            except Exception:
                pass
            if network_id:
                networks.append({'Target': network_id})
            else:
                raise Exception("no docker networks named: %s" % network_name)

        ports = {}
        for port in self.publish:
            if port.get('mode'):
                ports[int(port['published_port'])] = (int(port['target_port']), port['protocol'], port['mode'])
            else:
                ports[int(port['published_port'])] = (int(port['target_port']), port['protocol'])
        endpoint_spec = types.EndpointSpec(mode=self.endpoint_mode, ports=ports)
        return update_policy, task_template, networks, endpoint_spec, mode, self.labels

    # def fail(self, msg):
    #     self.parameters.client.module.fail_json(msg=msg)
    #
    # @property
    # def exists(self):
    #     return True if self.service else False


class DockerServiceManager():
    def get_networks_names_ids(self):
        return [{'name': n['Name'], 'id': n['Id']} for n in self.client.networks()]

    def get_service(self, name):
        # The Docker API allows filtering services by name but the filter looks
        # for a substring match, not an exact match. (Filtering for "foo" would
        # return information for services "foobar" and "foobuzz" even if the
        # service "foo" doesn't exist.) Avoid incorrectly determining that a
        # service is present by filtering the list of services returned from the
        # Docker API so that the name must be an exact match.
        raw_data = [
            service for service in self.client.services(filters={'name': name})
            if service['Spec']['Name'] == name
        ]
        if len(raw_data) == 0:
            return None

        raw_data = raw_data[0]
        networks_names_ids = self.get_networks_names_ids()
        ds = DockerService()

        task_template_data = raw_data['Spec']['TaskTemplate']
        update_config_data = raw_data['Spec']['UpdateConfig']

        ds.image = task_template_data['ContainerSpec']['Image']
        ds.user = task_template_data['ContainerSpec'].get('User', None)
        ds.env = task_template_data['ContainerSpec'].get('Env', [])
        ds.command = task_template_data['ContainerSpec'].get('Command')
        ds.args = task_template_data['ContainerSpec'].get('Args', [])
        ds.update_delay = update_config_data['Delay']
        ds.update_parallelism = update_config_data['Parallelism']
        ds.update_failure_action = update_config_data['FailureAction']
        ds.update_monitor = update_config_data['Monitor']
        ds.update_max_failure_ratio = update_config_data['MaxFailureRatio']

        if 'Order' in update_config_data:
            ds.update_order = update_config_data['Order']

        dns_config = task_template_data['ContainerSpec'].get('DNSConfig', None)
        if dns_config:
            if 'Nameservers' in dns_config.keys():
                ds.dns = dns_config['Nameservers']
            if 'Search' in dns_config.keys():
                ds.dns_search = dns_config['Search']
            if 'Options' in dns_config.keys():
                ds.dns_options = dns_config['Options']
        ds.hostname = task_template_data['ContainerSpec'].get('Hostname', '')
        ds.tty = task_template_data['ContainerSpec'].get('TTY', False)
        if 'Placement' in task_template_data.keys():
            placement = task_template_data['Placement']
            ds.constraints = placement.get('Constraints', [])
            placement_preferences = []
            for preference in placement.get('Preferences', []):
                placement_preferences.append(
                    dict(
                        (key.lower(), value["SpreadDescriptor"])
                        for key, value in preference.items()
                    )
                )
            ds.placement_preferences = placement_preferences or None

        restart_policy_data = task_template_data.get('RestartPolicy', None)
        if restart_policy_data:
            ds.restart_policy = restart_policy_data.get('Condition')
            ds.restart_policy_delay = restart_policy_data.get('Delay')
            ds.restart_policy_attempts = restart_policy_data.get('MaxAttempts')
            ds.restart_policy_window = restart_policy_data.get('Window')

        raw_data_endpoint_spec = raw_data['Spec'].get('EndpointSpec')
        if raw_data_endpoint_spec:
            ds.endpoint_mode = raw_data_endpoint_spec.get('Mode')
            for port in raw_data_endpoint_spec.get('Ports', []):
                ds.publish.append({
                    'protocol': port['Protocol'],
                    'mode': port.get('PublishMode', None),
                    'published_port': int(port['PublishedPort']),
                    'target_port': int(port['TargetPort'])})

        if 'Resources' in task_template_data.keys():
            if 'Limits' in task_template_data['Resources'].keys():
                if 'NanoCPUs' in task_template_data['Resources']['Limits'].keys():
                    ds.limit_cpu = float(task_template_data['Resources']['Limits']['NanoCPUs']) / 1000000000
                if 'MemoryBytes' in task_template_data['Resources']['Limits'].keys():
                    ds.limit_memory = int(task_template_data['Resources']['Limits']['MemoryBytes'])
            if 'Reservations' in task_template_data['Resources'].keys():
                if 'NanoCPUs' in task_template_data['Resources']['Reservations'].keys():
                    ds.reserve_cpu = float(task_template_data['Resources']['Reservations']['NanoCPUs']) / 1000000000
                if 'MemoryBytes' in task_template_data['Resources']['Reservations'].keys():
                    ds.reserve_memory = int(
                        task_template_data['Resources']['Reservations']['MemoryBytes'])

        ds.labels = raw_data['Spec'].get('Labels', {})
        if 'LogDriver' in task_template_data.keys():
            ds.log_driver = task_template_data['LogDriver'].get('Name', 'json-file')
            ds.log_driver_options = task_template_data['LogDriver'].get('Options', {})
        ds.container_labels = task_template_data['ContainerSpec'].get('Labels', {})
        mode = raw_data['Spec']['Mode']
        if 'Replicated' in mode.keys():
            ds.mode = to_text('replicated', encoding='utf-8')
            ds.replicas = mode['Replicated']['Replicas']
        elif 'Global' in mode.keys():
            ds.mode = 'global'
        else:
            raise Exception("Unknown service mode: %s" % mode)
        for mount_data in raw_data['Spec']['TaskTemplate']['ContainerSpec'].get('Mounts', []):
            ds.mounts.append({
                'source': mount_data['Source'],
                'type': mount_data['Type'],
                'target': mount_data['Target'],
                'readonly': mount_data.get('ReadOnly', False)})
        for config_data in raw_data['Spec']['TaskTemplate']['ContainerSpec'].get('Configs', []):
            ds.configs.append({
                'config_id': config_data['ConfigID'],
                'config_name': config_data['ConfigName'],
                'filename': config_data['File'].get('Name'),
                'uid': int(config_data['File'].get('UID')),
                'gid': int(config_data['File'].get('GID')),
                'mode': config_data['File'].get('Mode')
            })
        for secret_data in raw_data['Spec']['TaskTemplate']['ContainerSpec'].get('Secrets', []):
            ds.secrets.append({
                'secret_id': secret_data['SecretID'],
                'secret_name': secret_data['SecretName'],
                'filename': secret_data['File'].get('Name'),
                'uid': int(secret_data['File'].get('UID')),
                'gid': int(secret_data['File'].get('GID')),
                'mode': secret_data['File'].get('Mode')
            })
        networks_names_ids = self.get_networks_names_ids()
        for raw_network_data in raw_data['Spec']['TaskTemplate'].get('Networks', raw_data['Spec'].get('Networks', [])):
            network_name = [network_name_id['name'] for network_name_id in networks_names_ids if
                            network_name_id['id'] == raw_network_data['Target']]
            if len(network_name) == 0:
                ds.networks.append(raw_network_data['Target'])
            else:
                ds.networks.append(network_name[0])
        ds.service_version = raw_data['Version']['Index']
        ds.service_id = raw_data['ID']
        return ds

    def update_service(self, name, old_service, new_service):
        update_policy, task_template, networks, endpoint_spec, mode, labels = new_service.generate_docker_py_service_description(
            name, self.get_networks_names_ids())
        self.client.update_service(
            old_service.service_id,
            old_service.service_version,
            name=name,
            endpoint_spec=endpoint_spec,
            networks=networks,
            mode=mode,
            update_config=update_policy,
            task_template=task_template,
            labels=labels)

    def create_service(self, name, service):
        update_policy, task_template, networks, endpoint_spec, mode, labels = service.generate_docker_py_service_description(
            name, self.get_networks_names_ids())
        self.client.create_service(
            name=name,
            endpoint_spec=endpoint_spec,
            mode=mode,
            networks=networks,
            update_config=update_policy,
            task_template=task_template,
            labels=labels)

    def remove_service(self, name):
        self.client.remove_service(name)

    def get_image_digest(self, name, resolve=True):
        if (
            not name
            or not resolve
            or self.client.docker_py_version < LooseVersion('3.2')
            or self.client.docker_api_version < LooseVersion('1.30')
        ):
            return name
        repo, tag = parse_repository_tag(name)
        if not tag:
            tag = 'latest'
        name = repo + ':' + tag
        distribution_data = self.client.inspect_distribution(name)
        digest = distribution_data['Descriptor']['digest']
        return '%s@%s' % (name, digest)

    def __init__(self, client):
        self.client = client
        self.diff_tracker = DifferenceTracker()

    def run(self):
        module = self.client.module

        image = module.params['image']
        try:
            image_digest = self.get_image_digest(
                name=image,
                resolve=module.params['resolve_image']
            )
        except DockerException as e:
            return module.fail_json(
                msg="Error looking for an image named %s: %s" % (image, e))
        try:
            current_service = self.get_service(module.params['name'])
        except Exception as e:
            return module.fail_json(
                msg="Error looking for service named %s: %s" %
                    (module.params['name'], e))
        try:
            new_service = DockerService.from_ansible_params(
                module.params,
                current_service,
                image_digest
            )
        except Exception as e:
            return module.fail_json(
                msg="Error parsing module parameters: %s" % e)

        changed = False
        msg = 'noop'
        rebuilt = False
        differences = DifferenceTracker()
        facts = {}

        if current_service:
            if module.params['state'] == 'absent':
                if not module.check_mode:
                    self.remove_service(module.params['name'])
                msg = 'Service removed'
                changed = True
            else:
                changed, differences, need_rebuild, force_update = new_service.compare(current_service)
                if changed:
                    self.diff_tracker.merge(differences)
                    if need_rebuild:
                        if not module.check_mode:
                            self.remove_service(module.params['name'])
                            self.create_service(module.params['name'],
                                                new_service)
                        msg = 'Service rebuilt'
                        rebuilt = True
                    else:
                        if not module.check_mode:
                            self.update_service(module.params['name'],
                                                current_service,
                                                new_service)
                        msg = 'Service updated'
                        rebuilt = False
                else:
                    if force_update:
                        if not module.check_mode:
                            self.update_service(module.params['name'],
                                                current_service,
                                                new_service)
                        msg = 'Service forcefully updated'
                        rebuilt = False
                        changed = True
                    else:
                        msg = 'Service unchanged'
                facts = new_service.get_facts()
        else:
            if module.params['state'] == 'absent':
                msg = 'Service absent'
            else:
                if not module.check_mode:
                    service_id = self.create_service(module.params['name'],
                                                     new_service)
                msg = 'Service created'
                changed = True
                facts = new_service.get_facts()

        return msg, changed, rebuilt, differences.get_legacy_docker_diffs(), facts


def _detect_publish_mode_usage(client):
    for publish_def in client.module.params['publish']:
        if publish_def.get('mode'):
            return True
    return False


def main():
    argument_spec = dict(
        name=dict(required=True),
        image=dict(type='str'),
        state=dict(default="present", choices=['present', 'absent']),
        mounts=dict(default=[], type='list'),
        configs=dict(default=None, type='list'),
        secrets=dict(default=[], type='list'),
        networks=dict(default=[], type='list'),
        command=dict(default=None, type='raw'),
        args=dict(default=[], type='list'),
        env=dict(default=[], type='list'),
        force_update=dict(default=False, type='bool'),
        log_driver=dict(default="json-file", type='str'),
        log_driver_options=dict(default={}, type='dict'),
        publish=dict(default=[], type='list', elements='dict', options=dict(
            published_port=dict(type='int', required=True),
            target_port=dict(type='int', required=True),
            protocol=dict(default='tcp', type='str', required=False, choices=('tcp', 'udp')),
            mode=dict(type='str', required=False, choices=('ingress', 'host')),
        )),
        constraints=dict(default=[], type='list'),
        placement_preferences=dict(default=None, type='list'),
        tty=dict(default=False, type='bool'),
        dns=dict(default=[], type='list'),
        dns_search=dict(default=[], type='list'),
        dns_options=dict(default=[], type='list'),
        hostname=dict(default="", type='str'),
        labels=dict(default={}, type='dict'),
        container_labels=dict(default={}, type='dict'),
        mode=dict(default="replicated"),
        replicas=dict(default=-1, type='int'),
        endpoint_mode=dict(default=None, choices=['vip', 'dnsrr']),
        restart_policy=dict(default='none', choices=['none', 'on-failure', 'any']),
        limit_cpu=dict(default=0, type='float'),
        limit_memory=dict(default=0, type='str'),
        reserve_cpu=dict(default=0, type='float'),
        reserve_memory=dict(default=0, type='str'),
        resolve_image=dict(default=True, type='bool'),
        restart_policy_delay=dict(default=0, type='int'),
        restart_policy_attempts=dict(default=0, type='int'),
        restart_policy_window=dict(default=0, type='int'),
        update_delay=dict(default=10, type='int'),
        update_parallelism=dict(default=1, type='int'),
        update_failure_action=dict(default='continue', choices=['continue', 'pause']),
        update_monitor=dict(default=5000000000, type='int'),
        update_max_failure_ratio=dict(default=0, type='float'),
        update_order=dict(default=None, type='str'),
        user=dict(type='str'))

    option_minimal_versions = dict(
        dns=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
        dns_options=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
        dns_search=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
        force_update=dict(docker_py_version='2.1.0', docker_api_version='1.25'),
        hostname=dict(docker_py_version='2.2.0', docker_api_version='1.25'),
        tty=dict(docker_py_version='2.4.0', docker_api_version='1.25'),
        secrets=dict(docker_py_version='2.1.0', docker_api_version='1.25'),
        configs=dict(docker_py_version='2.6.0', docker_api_version='1.30'),
        update_order=dict(docker_py_version='2.7.0', docker_api_version='1.29'),
        # specials
        publish_mode=dict(
            docker_py_version='3.0.0',
            docker_api_version='1.25',
            detect_usage=_detect_publish_mode_usage,
            usage_msg='set publish.mode'
        )
    )

    required_if = [
        ('state', 'present', ['image'])
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
        min_docker_version='2.0.0',
        min_docker_api_version='1.24',
        option_minimal_versions=option_minimal_versions,
    )

    dsm = DockerServiceManager(client)
    msg, changed, rebuilt, changes, facts = dsm.run()

    results = dict(
        msg=msg,
        changed=changed,
        rebuilt=rebuilt,
        changes=changes,
        ansible_docker_service=facts,
    )
    if client.module._diff:
        before, after = dsm.diff_tracker.get_before_after()
        results['diff'] = dict(before=before, after=after)

    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
