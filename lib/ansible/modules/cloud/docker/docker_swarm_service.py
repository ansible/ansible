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
    required: true
    description:
    - Service image path and tag.
      Maps docker service IMAGE parameter.
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
  constraints:
    required: false
    default: []
    description:
    - List of the service constraints.
    - Maps docker service --constraint option.
  hostname:
    required: false
    default: ""
    description:
    - Container hostname
    - Maps docker service --hostname option.
    - Requires api_version >= 1.25
  tty:
    required: false
    type: bool
    default: False
    description:
    - Allocate a pseudo-TTY
    - Maps docker service --tty option.
    - Requires api_version >= 1.25
  dns:
    required: false
    default: []
    description:
    - List of custom DNS servers.
    - Maps docker service --dns option.
    - Requires api_version >= 1.25
  dns_search:
    required: false
    default: []
    description:
    - List of custom DNS search domains.
    - Maps docker service --dns-search option.
    - Requires api_version >= 1.25
  dns_options:
    required: false
    default: []
    description:
    - List of custom DNS options.
    - Maps docker service --dns-option option.
    - Requires api_version >= 1.25
  force_update:
    required: false
    type: bool
    default: False
    description:
    - Force update even if no changes require it.
    - Maps to docker service update --force option.
    - Requires api_version >= 1.25
  labels:
    required: false
    description:
    - List of the service labels.
    - Maps docker service --label option.
  container_labels:
    required: false
    description:
    - List of the service containers labels.
    - Maps docker service --container-label option.
    default: []
  endpoint_mode:
    required: false
    description:
    - Service endpoint mode.
    - Maps docker service --endpoint-mode option.
    default: vip
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
    - Service memory limit in MB. 0 equals no limit.
    - Maps docker service --limit-memory option.
  reserve_memory:
    required: false
    default: 0
    description:
    - Service memory reservation in MB. 0 equals no reservation.
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
    default: []
  configs:
    required: false
    description:
    - List of dictionaries describing the service configs.
    - Every item must be a dictionary exposing the keys config_id, config_name, filename, uid (defaults to 0), gid (defaults to 0), mode (defaults to 0o444)
    - Maps docker service --config option.
    default: []
  networks:
    required: false
    default: []
    description:
    - List of the service networks names.
    - Maps docker service --network option.
  publish:
    default: []
    required: false
    description:
    - List of dictionaries describing the service published ports.
    - Every item must be a dictionary exposing the keys published_port, target_port, protocol (defaults to 'tcp'), mode <ingress|host>, default to ingress.
    - Only used with api_version >= 1.25
    - If api_version >= 1.32 and docker python library >= 3.0.0 attribute 'mode' can be set to 'ingress' or 'host' (default 'ingress').
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
    default: stop-first
    description:
    - Specifies the order of operations when rolling out an updated task.
    - Maps to docker service --update-order
    choices:
    - stop-first
    - start-first
  user:
    required: false
    default: root
    description: username or UID
extends_documentation_fragment:
- docker
requirements:
- "docker-py >= 2.0"
- "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
   module has been superseded by L(docker,https://pypi.org/project/docker/)
   (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
   Version 2.1.0 or newer is only available with the C(docker) module."
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
'''

import time
from ansible.module_utils.docker_common import DockerBaseClass
from ansible.module_utils.docker_common import AnsibleDockerClient
from ansible.module_utils.docker_common import docker_version
from ansible.module_utils.basic import human_to_bytes
from ansible.module_utils._text import to_text


try:
    from distutils.version import LooseVersion
    from docker import utils
    from docker import types
except Exception as dummy:
    # missing docker-py handled in ansible.module_utils.docker
    pass


class DockerService(DockerBaseClass):
    def __init__(self):
        super(DockerService, self).__init__()
        self.constraints = []
        self.image = ""
        self.args = []
        self.endpoint_mode = "vip"
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
        self.user = "root"
        self.mounts = []
        self.configs = []
        self.secrets = []
        self.constraints = []
        self.networks = []
        self.publish = []
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
        self.update_order = "stop-first"

    def get_facts(self):
        return {
            'image': self.image,
            'mounts': self.mounts,
            'configs': self.configs,
            'networks': self.networks,
            'args': self.args,
            'tty': self.tty,
            'dns': self.dns,
            'dns_search': self.dns_search,
            'dns_options': self.dns_options,
            'hostname': self.hostname,
            'env': self.env,
            'force_update': self.force_update,
            'log_driver': self.log_driver,
            'log_driver_options ': self.log_driver_options,
            'publish': self.publish,
            'constraints': self.constraints,
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
    def from_ansible_params(ap, old_service):
        s = DockerService()
        s.constraints = ap['constraints']
        s.image = ap['image']
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
            service_p['protocol'] = param_p.get('protocol', 'tcp')
            service_p['mode'] = param_p.get('mode', 'ingress')
            service_p['published_port'] = int(param_p['published_port'])
            service_p['target_port'] = int(param_p['target_port'])
            if service_p['protocol'] not in ['tcp', 'udp']:
                raise ValueError("got publish.protocol '%s', valid values:'tcp', 'udp'" %
                                 service_p['protocol'])
            if service_p['mode'] not in ['ingress', 'host']:
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
        differences = []
        needs_rebuild = False
        force_update = False
        if self.endpoint_mode != os.endpoint_mode:
            differences.append('endpoint_mode')
        if self.env != os.env:
            differences.append('env')
        if self.log_driver != os.log_driver:
            differences.append('log_driver')
        if self.log_driver_options != os.log_driver_options:
            differences.append('log_opt')
        if self.mode != os.mode:
            needs_rebuild = True
            differences.append('mode')
        if self.mounts != os.mounts:
            differences.append('mounts')
        if self.configs != os.configs:
            differences.append('configs')
        if self.secrets != os.secrets:
            differences.append('secrets')
        if self.networks != os.networks:
            differences.append('networks')
            needs_rebuild = True
        if self.replicas != os.replicas:
            differences.append('replicas')
        if self.args != os.args:
            differences.append('args')
        if self.constraints != os.constraints:
            differences.append('constraints')
        if self.labels != os.labels:
            differences.append('labels')
        if self.limit_cpu != os.limit_cpu:
            differences.append('limit_cpu')
        if self.limit_memory != os.limit_memory:
            differences.append('limit_memory')
        if self.reserve_cpu != os.reserve_cpu:
            differences.append('reserve_cpu')
        if self.reserve_memory != os.reserve_memory:
            differences.append('reserve_memory')
        if self.container_labels != os.container_labels:
            differences.append('container_labels')
        if self.publish != os.publish:
            differences.append('publish')
        if self.restart_policy != os.restart_policy:
            differences.append('restart_policy')
        if self.restart_policy_attempts != os.restart_policy_attempts:
            differences.append('restart_policy_attempts')
        if self.restart_policy_delay != os.restart_policy_delay:
            differences.append('restart_policy_delay')
        if self.restart_policy_window != os.restart_policy_window:
            differences.append('restart_policy_window')
        if self.update_delay != os.update_delay:
            differences.append('update_delay')
        if self.update_parallelism != os.update_parallelism:
            differences.append('update_parallelism')
        if self.update_failure_action != os.update_failure_action:
            differences.append('update_failure_action')
        if self.update_monitor != os.update_monitor:
            differences.append('update_monitor')
        if self.update_max_failure_ratio != os.update_max_failure_ratio:
            differences.append('update_max_failure_ratio')
        if self.update_order != os.update_order:
            differences.append('update_order')
        if self.image != os.image.split('@')[0]:
            differences.append('image')
        if self.user != os.user:
            differences.append('user')
        if self.dns != os.dns:
            differences.append('dns')
        if self.dns_search != os.dns_search:
            differences.append('dns_search')
        if self.dns_options != os.dns_options:
            differences.append('dns_options')
        if self.hostname != os.hostname:
            differences.append('hostname')
        if self.tty != os.tty:
            differences.append('tty')
        if self.force_update:
            differences.append('force_update')
            force_update = True
        return len(differences) > 0, differences, needs_rebuild, force_update

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

        cspec = types.ContainerSpec(
            image=self.image,
            user=self.user,
            dns_config=types.DNSConfig(nameservers=self.dns, search=self.dns_search, options=self.dns_options),
            args=self.args,
            env=self.env,
            tty=self.tty,
            hostname=self.hostname,
            labels=self.container_labels,
            mounts=mounts,
            secrets=secrets,
            configs=configs
        )

        log_driver = types.DriverConfig(name=self.log_driver, options=self.log_driver_options)

        placement = types.Placement(constraints=self.constraints)

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
                network_id = filter(lambda n: n['name'] == network_name, docker_networks)[0]['id']
            except Exception as dummy:
                pass
            if network_id:
                networks.append({'Target': network_id})
            else:
                raise Exception("no docker networks named: %s" % network_name)

        ports = {}
        for port in self.publish:
            ports[int(port['published_port'])] = (int(port['target_port']), port['protocol'], port['mode'])
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
        raw_data = self.client.services(filters={'name': name})
        if len(raw_data) == 0:
            return None

        raw_data = raw_data[0]
        networks_names_ids = self.get_networks_names_ids()
        ds = DockerService()

        task_template_data = raw_data['Spec']['TaskTemplate']
        update_config_data = raw_data['Spec']['UpdateConfig']

        ds.image = task_template_data['ContainerSpec']['Image']
        ds.user = task_template_data['ContainerSpec'].get('User', 'root')
        ds.env = task_template_data['ContainerSpec'].get('Env', [])
        ds.args = task_template_data['ContainerSpec'].get('Args', [])
        ds.update_delay = update_config_data['Delay']
        ds.update_parallelism = update_config_data['Parallelism']
        ds.update_failure_action = update_config_data['FailureAction']
        ds.update_monitor = update_config_data['Monitor']
        ds.update_max_failure_ratio = update_config_data['MaxFailureRatio']
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
            ds.constraints = task_template_data['Placement'].get('Constraints', [])

        restart_policy_data = task_template_data.get('RestartPolicy', None)
        if restart_policy_data:
            ds.restart_policy = restart_policy_data.get('Condition')
            ds.restart_policy_delay = restart_policy_data.get('Delay')
            ds.restart_policy_attempts = restart_policy_data.get('MaxAttempts')
            ds.restart_policy_window = restart_policy_data.get('Window')

        raw_data_endpoint = raw_data.get('Endpoint', None)
        if raw_data_endpoint:
            raw_data_endpoint_spec = raw_data_endpoint.get('Spec', None)
            if raw_data_endpoint_spec:
                ds.endpoint_mode = raw_data_endpoint_spec.get('Mode', 'vip')
                for port in raw_data_endpoint_spec.get('Ports', []):
                    ds.publish.append({
                        'protocol': port['Protocol'],
                        'mode': port.get('PublishMode', 'ingress'),
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

    def __init__(self, client):
        self.client = client

    def test_parameter_versions(self):
        parameters_versions = [
            {'param': 'dns', 'attribute': 'dns', 'min_version': '1.25'},
            {'param': 'dns_options', 'attribute': 'dns_options', 'min_version': '1.25'},
            {'param': 'dns_search', 'attribute': 'dns_search', 'min_version': '1.25'},
            {'param': 'hostname', 'attribute': 'hostname', 'min_version': '1.25'},
            {'param': 'tty', 'attribute': 'tty', 'min_version': '1.25'},
            {'param': 'secrets', 'attribute': 'secrets', 'min_version': '1.25'},
            {'param': 'configs', 'attribute': 'configs', 'min_version': '1.30'}]
        params = self.client.module.params
        empty_service = DockerService()
        for pv in parameters_versions:
            if (params[pv['param']] != getattr(empty_service, pv['attribute']) and
                    (LooseVersion(self.client.version()['ApiVersion']) <
                     LooseVersion(pv['min_version']))):
                self.client.module.fail_json(
                    msg=('%s parameter supported only with api_version>=%s'
                         % (pv['param'], pv['min_version'])))

        for publish_def in self.client.module.params.get('publish', []):
            if 'mode' in publish_def.keys():
                if LooseVersion(self.client.version()['ApiVersion']) < LooseVersion('1.25'):
                    self.client.module.fail_json(msg='publish.mode parameter supported only with api_version>=1.25')
                if LooseVersion(docker_version) < LooseVersion('3.0.0'):
                    self.client.module.fail_json(msg='publish.mode parameter requires docker python library>=3.0.0')

    def run(self):
        self.test_parameter_versions()

        module = self.client.module
        try:
            current_service = self.get_service(module.params['name'])
        except Exception as e:
            return module.fail_json(
                msg="Error looking for service named %s: %s" %
                    (module.params['name'], e))
        try:
            new_service = DockerService.from_ansible_params(module.params, current_service)
        except Exception as e:
            return module.fail_json(
                msg="Error parsing module parameters: %s" % e)

        changed = False
        msg = 'noop'
        rebuilt = False
        changes = []
        facts = {}

        if current_service:
            if module.params['state'] == 'absent':
                if not module.check_mode:
                    self.remove_service(module.params['name'])
                msg = 'Service removed'
                changed = True
            else:
                changed, changes, need_rebuild, force_update = new_service.compare(current_service)
                if changed:
                    changed = True
                    if need_rebuild:
                        if not module.check_mode:
                            self.remove_service(module.params['name'])
                            self.create_service(module.params['name'],
                                                new_service)
                        msg = 'Service rebuilt'
                        rebuilt = True
                        changes = changes
                    else:
                        if not module.check_mode:
                            self.update_service(module.params['name'],
                                                current_service,
                                                new_service)
                        msg = 'Service updated'
                        rebuilt = False
                        changes = changes
                else:
                    if force_update and not module.check_mode:
                        self.update_service(module.params['name'],
                                            current_service,
                                            new_service)
                        msg = 'Service forcefully updated'
                        rebuilt = False
                        changed = True
                        changes = changes
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

        return msg, changed, rebuilt, changes, facts


def main():
    argument_spec = dict(
        name=dict(required=True),
        image=dict(type='str'),
        state=dict(default="present", choices=['present', 'absent']),
        mounts=dict(default=[], type='list'),
        configs=dict(default=[], type='list'),
        secrets=dict(default=[], type='list'),
        networks=dict(default=[], type='list'),
        args=dict(default=[], type='list'),
        env=dict(default=[], type='list'),
        force_update=dict(default=False, type='bool'),
        log_driver=dict(default="json-file", type='str'),
        log_driver_options=dict(default={}, type='dict'),
        publish=dict(default=[], type='list'),
        constraints=dict(default=[], type='list'),
        tty=dict(default=False, type='bool'),
        dns=dict(default=[], type='list'),
        dns_search=dict(default=[], type='list'),
        dns_options=dict(default=[], type='list'),
        hostname=dict(default="", type='str'),
        labels=dict(default={}, type='dict'),
        container_labels=dict(default={}, type='dict'),
        mode=dict(default="replicated"),
        replicas=dict(default=-1, type='int'),
        endpoint_mode=dict(default='vip', choices=['vip', 'dnsrr']),
        restart_policy=dict(default='none', choices=['none', 'on-failure', 'any']),
        limit_cpu=dict(default=0, type='float'),
        limit_memory=dict(default=0, type='str'),
        reserve_cpu=dict(default=0, type='float'),
        reserve_memory=dict(default=0, type='str'),
        restart_policy_delay=dict(default=0, type='int'),
        restart_policy_attempts=dict(default=0, type='int'),
        restart_policy_window=dict(default=0, type='int'),
        update_delay=dict(default=10, type='int'),
        update_parallelism=dict(default=1, type='int'),
        update_failure_action=dict(default='continue', choices=['continue', 'pause']),
        update_monitor=dict(default=5000000000, type='int'),
        update_max_failure_ratio=dict(default=0, type='float'),
        update_order=dict(default='stop-first', choices=['stop-first', 'start-first']),
        user=dict(default='root'))
    required_if = [
        ('state', 'present', ['image'])
    ]
    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
        min_docker_version='2.0.0',
    )

    dsm = DockerServiceManager(client)
    msg, changed, rebuilt, changes, facts = dsm.run()

    client.module.exit_json(msg=msg, changed=changed, rebuilt=rebuilt, changes=changes, ansible_docker_service=facts)


if __name__ == '__main__':
    main()
