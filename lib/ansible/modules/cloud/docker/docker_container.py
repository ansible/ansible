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
module: docker_container

short_description: manage docker containers

description:
  - Manage the life cycle of docker containers.
  - Supports check mode. Run with --check and --diff to view config difference and list of actions to be taken.

version_added: "2.1"

options:
  auto_remove:
    description:
      - enable auto-removal of the container on daemon side when the container's process exits
    type: bool
    default: 'no'
    version_added: "2.4"
  blkio_weight:
    description:
      - Block IO (relative weight), between 10 and 1000.
  capabilities:
    description:
      - List of capabilities to add to the container.
  cleanup:
    description:
      - Use with I(detach=false) to remove the container after successful execution.
    type: bool
    default: 'no'
    version_added: "2.2"
  command:
    description:
      - Command to execute when the container starts.
        A command may be either a string or a list.
        Prior to version 2.4, strings were split on commas.
  cpu_period:
    description:
      - Limit CPU CFS (Completely Fair Scheduler) period
    default: 0
  cpu_quota:
    description:
      - Limit CPU CFS (Completely Fair Scheduler) quota
    default: 0
  cpuset_cpus:
    description:
      - CPUs in which to allow execution C(1,3) or C(1-3).
  cpuset_mems:
    description:
      - Memory nodes (MEMs) in which to allow execution C(0-3) or C(0,1)
  cpu_shares:
    description:
      - CPU shares (relative weight).
  detach:
    description:
      - Enable detached mode to leave the container running in background.
        If disabled, the task will reflect the status of the container run (failed if the command failed).
    type: bool
    default: true
  devices:
    description:
      - "List of host device bindings to add to the container. Each binding is a mapping expressed
        in the format: <path_on_host>:<path_in_container>:<cgroup_permissions>"
  dns_opts:
    description:
      - list of DNS options
  dns_servers:
    description:
      - List of custom DNS servers.
  dns_search_domains:
    description:
      - List of custom DNS search domains.
  domainname:
    description:
      - Container domainname.
    version_added: "2.5"
  env:
    description:
      - Dictionary of key,value pairs.
  env_file:
    version_added: "2.2"
    description:
      - Path to a file, present on the target, containing environment variables I(FOO=BAR).
      - If variable also present in C(env), then C(env) value will override.
  entrypoint:
    description:
      - Command that overwrites the default ENTRYPOINT of the image.
  etc_hosts:
    description:
      - Dict of host-to-IP mappings, where each host name is a key in the dictionary.
        Each host name will be added to the container's /etc/hosts file.
  exposed_ports:
    description:
      - List of additional container ports which informs Docker that the container
        listens on the specified network ports at runtime.
        If the port is already exposed using EXPOSE in a Dockerfile, it does not
        need to be exposed again.
    aliases:
      - exposed
      - expose
  force_kill:
    description:
      - Use the kill command when stopping a running container.
    type: bool
    default: 'no'
    aliases:
      - forcekill
  groups:
    description:
      - List of additional group names and/or IDs that the container process will run as.
  hostname:
    description:
      - Container hostname.
  ignore_image:
    description:
      - When C(state) is I(present) or I(started) the module compares the configuration of an existing
        container to requested configuration. The evaluation includes the image version. If
        the image version in the registry does not match the container, the container will be
        recreated. Stop this behavior by setting C(ignore_image) to I(True).
    type: bool
    default: 'no'
    version_added: "2.2"
  image:
    description:
      - Repository path and tag used to create the container. If an image is not found or pull is true, the image
        will be pulled from the registry. If no tag is included, 'latest' will be used.
  init:
    description:
      - Run an init inside the container that forwards signals and reaps processes.
        This option requires Docker API 1.25+.
    type: bool
    default: 'no'
    version_added: "2.6"
  interactive:
    description:
      - Keep stdin open after a container is launched, even if not attached.
    type: bool
    default: 'no'
  ipc_mode:
    description:
      - Set the IPC mode for the container. Can be one of 'container:<name|id>' to reuse another
        container's IPC namespace or 'host' to use the host's IPC namespace within the container.
  keep_volumes:
    description:
      - Retain volumes associated with a removed container.
    type: bool
    default: 'yes'
  kill_signal:
    description:
      - Override default signal used to kill a running container.
  kernel_memory:
    description:
      - "Kernel memory limit (format: C(<number>[<unit>])). Number is a positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte). Minimum is C(4M)."
      - Omitting the unit defaults to bytes.
    default: 0
  labels:
     description:
       - Dictionary of key value pairs.
  links:
    description:
      - List of name aliases for linked containers in the format C(container_name:alias)
  log_driver:
    description:
      - Specify the logging driver. Docker uses I(json-file) by default.
      - See L(here,https://docs.docker.com/config/containers/logging/configure/) for possible choices.
    required: false
  log_options:
    description:
      - Dictionary of options specific to the chosen log_driver. See https://docs.docker.com/engine/admin/logging/overview/
        for details.
    aliases:
      - log_opt
  mac_address:
    description:
      - Container MAC address (e.g. 92:d0:c6:0a:29:33)
  memory:
    description:
      - "Memory limit (format: C(<number>[<unit>])). Number is a positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte)."
      - Omitting the unit defaults to bytes.
    default: '0'
  memory_reservation:
    description:
      - "Memory soft limit (format: C(<number>[<unit>])). Number is a positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte)."
      - Omitting the unit defaults to bytes.
    default: 0
  memory_swap:
    description:
      - "Total memory limit (memory + swap, format: C(<number>[<unit>])).
        Number is a positive integer. Unit can be C(B) (byte), C(K) (kibibyte, 1024B),
        C(M) (mebibyte), C(G) (gibibyte), C(T) (tebibyte), or C(P) (pebibyte)."
      - Omitting the unit defaults to bytes.
    default: 0
  memory_swappiness:
    description:
        - Tune a container's memory swappiness behavior. Accepts an integer between 0 and 100.
    default: 0
  name:
    description:
      - Assign a name to a new container or match an existing container.
      - When identifying an existing container name may be a name or a long or short container ID.
    required: true
  network_mode:
    description:
      - Connect the container to a network. Choices are "bridge", "host", "none" or "container:<name|id>"
  userns_mode:
     description:
       - User namespace to use
     version_added: "2.5"
  networks:
     description:
       - List of networks the container belongs to.
       - Each network is a dict with keys C(name), C(ipv4_address), C(ipv6_address), C(links), C(aliases).
       - For each network C(name) is required, all other keys are optional.
       - If included, C(links) or C(aliases) are lists.
       - For examples of the data structure and usage see EXAMPLES below.
       - To remove a container from one or more networks, use the C(purge_networks) option.
       - Note that as opposed to C(docker run ...), M(docker_container) does not remove the default
         network if C(networks) is specified. You need to explicity use C(purge_networks) to enforce
         the removal of the default network (and all other networks not explicitly mentioned in C(networks)).
     version_added: "2.2"
  oom_killer:
    description:
      - Whether or not to disable OOM Killer for the container.
    type: bool
    default: 'no'
  oom_score_adj:
    description:
      - An integer value containing the score given to the container in order to tune OOM killer preferences.
    default: 0
    version_added: "2.2"
  paused:
    description:
      - Use with the started state to pause running processes inside the container.
    type: bool
    default: 'no'
  pid_mode:
    description:
      - Set the PID namespace mode for the container. Currently only supports 'host'.
  privileged:
    description:
      - Give extended privileges to the container.
    type: bool
    default: 'no'
  published_ports:
    description:
      - List of ports to publish from the container to the host.
      - "Use docker CLI syntax: C(8000), C(9000:8000), or C(0.0.0.0:9000:8000), where 8000 is a
        container port, 9000 is a host port, and 0.0.0.0 is a host interface."
      - Container ports must be exposed either in the Dockerfile or via the C(expose) option.
      - A value of C(all) will publish all exposed container ports to random host ports, ignoring
        any other mappings.
      - If C(networks) parameter is provided, will inspect each network to see if there exists
        a bridge network with optional parameter com.docker.network.bridge.host_binding_ipv4.
        If such a network is found, then published ports where no host IP address is specified
        will be bound to the host IP pointed to by com.docker.network.bridge.host_binding_ipv4.
        Note that the first bridge network with a com.docker.network.bridge.host_binding_ipv4
        value encountered in the list of C(networks) is the one that will be used.
    aliases:
      - ports
  pull:
    description:
       - If true, always pull the latest version of an image. Otherwise, will only pull an image when missing.
    type: bool
    default: 'no'
  purge_networks:
    description:
       - Remove the container from ALL networks not included in C(networks) parameter.
       - Any default networks such as I(bridge), if not found in C(networks), will be removed as well.
    type: bool
    default: 'no'
    version_added: "2.2"
  read_only:
    description:
      - Mount the container's root file system as read-only.
    type: bool
    default: 'no'
  recreate:
    description:
      - Use with present and started states to force the re-creation of an existing container.
    type: bool
    default: 'no'
  restart:
    description:
      - Use with started state to force a matching container to be stopped and restarted.
    type: bool
    default: 'no'
  restart_policy:
    description:
      - Container restart policy. Place quotes around I(no) option.
    choices:
      - 'no'
      - 'on-failure'
      - 'always'
      - 'unless-stopped'
  restart_retries:
    description:
       - Use with restart policy to control maximum number of restart attempts.
    default: 0
  shm_size:
    description:
      - "Size of C(/dev/shm) (format: C(<number>[<unit>])). Number is positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte)."
      - Omitting the unit defaults to bytes. If you omit the size entirely, the system uses C(64M).
  security_opts:
    description:
      - List of security options in the form of C("label:user:User")
  state:
    description:
      - 'I(absent) - A container matching the specified name will be stopped and removed. Use force_kill to kill the container
         rather than stopping it. Use keep_volumes to retain volumes associated with the removed container.'
      - 'I(present) - Asserts the existence of a container matching the name and any provided configuration parameters. If no
        container matches the name, a container will be created. If a container matches the name but the provided configuration
        does not match, the container will be updated, if it can be. If it cannot be updated, it will be removed and re-created
        with the requested config. Image version will be taken into account when comparing configuration. To ignore image
        version use the ignore_image option. Use the recreate option to force the re-creation of the matching container. Use
        force_kill to kill the container rather than stopping it. Use keep_volumes to retain volumes associated with a removed
        container.'
      - 'I(started) - Asserts there is a running container matching the name and any provided configuration. If no container
        matches the name, a container will be created and started. If a container matching the name is found but the
        configuration does not match, the container will be updated, if it can be. If it cannot be updated, it will be removed
        and a new container will be created with the requested configuration and started. Image version will be taken into
        account when comparing configuration. To ignore image version use the ignore_image option. Use recreate to always
        re-create a matching container, even if it is running. Use restart to force a matching container to be stopped and
        restarted. Use force_kill to kill a container rather than stopping it. Use keep_volumes to retain volumes associated
        with a removed container.'
      - 'I(stopped) - Asserts that the container is first I(present), and then if the container is running moves it to a stopped
        state. Use force_kill to kill a container rather than stopping it.'
    default: started
    choices:
      - absent
      - present
      - stopped
      - started
  stop_signal:
    description:
      - Override default signal used to stop the container.
  stop_timeout:
    description:
      - Number of seconds to wait for the container to stop before sending SIGKILL.
  trust_image_content:
    description:
      - If C(yes), skip image verification.
    type: bool
    default: 'no'
  tmpfs:
    description:
      - Mount a tmpfs directory
    version_added: 2.4
  tty:
    description:
      - Allocate a pseudo-TTY.
    type: bool
    default: 'no'
  ulimits:
    description:
      - "List of ulimit options. A ulimit is specified as C(nofile:262144:262144)"
  sysctls:
    description:
      - Dictionary of key,value pairs.
    version_added: 2.4
  user:
    description:
      - Sets the username or UID used and optionally the groupname or GID for the specified command.
      - "Can be [ user | user:group | uid | uid:gid | user:gid | uid:group ]"
  uts:
    description:
      - Set the UTS namespace mode for the container.
  volumes:
    description:
      - List of volumes to mount within the container.
      - "Use docker CLI-style syntax: C(/host:/container[:mode])"
      - You can specify a read mode for the mount with either C(ro) or C(rw).
      - SELinux hosts can additionally use C(z) or C(Z) to use a shared or
        private label for the volume.
  volume_driver:
    description:
      - The container volume driver.
  volumes_from:
    description:
      - List of container names or Ids to get volumes from.
  working_dir:
    description:
      - Path to the working directory.
    version_added: "2.4"
extends_documentation_fragment:
    - docker

author:
    - "Cove Schneider (@cove)"
    - "Joshua Conner (@joshuaconner)"
    - "Pavel Antonov (@softzilla)"
    - "Thomas Steinbach (@ThomasSteinbach)"
    - "Philippe Jandot (@zfil)"
    - "Daan Oosterveld (@dusdanig)"
    - "Chris Houseknecht (@chouseknecht)"
    - "Kassian Sun (@kassiansun)"

requirements:
    - "python >= 2.6"
    - "docker-py >= 1.7.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
       install the C(docker) Python module. Note that both modules should I(not)
       be installed at the same time. Also note that when both modules are installed
       and one of them is uninstalled, the other might no longer function and a
       reinstall of it is required."
    - "Docker API >= 1.20"
'''

EXAMPLES = '''
- name: Create a data container
  docker_container:
    name: mydata
    image: busybox
    volumes:
      - /data

- name: Re-create a redis container
  docker_container:
    name: myredis
    image: redis
    command: redis-server --appendonly yes
    state: present
    recreate: yes
    exposed_ports:
      - 6379
    volumes_from:
      - mydata

- name: Restart a container
  docker_container:
    name: myapplication
    image: someuser/appimage
    state: started
    restart: yes
    links:
     - "myredis:aliasedredis"
    devices:
     - "/dev/sda:/dev/xvda:rwm"
    ports:
     - "8080:9000"
     - "127.0.0.1:8081:9001/udp"
    env:
        SECRET_KEY: ssssh

- name: Container present
  docker_container:
    name: mycontainer
    state: present
    image: ubuntu:14.04
    command: sleep infinity

- name: Stop a container
  docker_container:
    name: mycontainer
    state: stopped

- name: Start 4 load-balanced containers
  docker_container:
    name: "container{{ item }}"
    recreate: yes
    image: someuser/anotherappimage
    command: sleep 1d
  with_sequence: count=4

- name: remove container
  docker_container:
    name: ohno
    state: absent

- name: Syslogging output
  docker_container:
    name: myservice
    image: busybox
    log_driver: syslog
    log_options:
      syslog-address: tcp://my-syslog-server:514
      syslog-facility: daemon
      # NOTE: in Docker 1.13+ the "syslog-tag" option was renamed to "tag" for
      # older docker installs, use "syslog-tag" instead
      tag: myservice

- name: Create db container and connect to network
  docker_container:
    name: db_test
    image: "postgres:latest"
    networks:
      - name: "{{ docker_network_name }}"

- name: Start container, connect to network and link
  docker_container:
    name: sleeper
    image: ubuntu:14.04
    networks:
      - name: TestingNet
        ipv4_address: "172.1.1.100"
        aliases:
          - sleepyzz
        links:
          - db_test:db
      - name: TestingNet2

- name: Start a container with a command
  docker_container:
    name: sleepy
    image: ubuntu:14.04
    command: ["sleep", "infinity"]

- name: Add container to networks
  docker_container:
    name: sleepy
    networks:
      - name: TestingNet
        ipv4_address: 172.1.1.18
        links:
          - sleeper
      - name: TestingNet2
        ipv4_address: 172.1.10.20

- name: Update network with aliases
  docker_container:
    name: sleepy
    networks:
      - name: TestingNet
        aliases:
          - sleepyz
          - zzzz

- name: Remove container from one network
  docker_container:
    name: sleepy
    networks:
      - name: TestingNet2
    purge_networks: yes

- name: Remove container from all networks
  docker_container:
    name: sleepy
    purge_networks: yes

- name: Start a container and use an env file
  docker_container:
    name: agent
    image: jenkinsci/ssh-slave
    env_file: /var/tmp/jenkins/agent.env
'''

RETURN = '''
docker_container:
    description:
      - Before 2.3 this was 'ansible_docker_container' but was renamed due to conflicts with the connection plugin.
      - Facts representing the current state of the container. Matches the docker inspection output.
      - Note that facts are not part of registered vars but accessible directly.
      - Empty if C(state) is I(absent)
      - If detached is I(False), will include Output attribute containing any output from container run.
    returned: always
    type: dict
    sample: '{
        "AppArmorProfile": "",
        "Args": [],
        "Config": {
            "AttachStderr": false,
            "AttachStdin": false,
            "AttachStdout": false,
            "Cmd": [
                "/usr/bin/supervisord"
            ],
            "Domainname": "",
            "Entrypoint": null,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ],
            "ExposedPorts": {
                "443/tcp": {},
                "80/tcp": {}
            },
            "Hostname": "8e47bf643eb9",
            "Image": "lnmp_nginx:v1",
            "Labels": {},
            "OnBuild": null,
            "OpenStdin": false,
            "StdinOnce": false,
            "Tty": false,
            "User": "",
            "Volumes": {
                "/tmp/lnmp/nginx-sites/logs/": {}
            },
            ...
    }'
'''

import os
import re
import shlex
from distutils.version import LooseVersion

from ansible.module_utils.basic import human_to_bytes
from ansible.module_utils.docker_common import HAS_DOCKER_PY_2, HAS_DOCKER_PY_3, AnsibleDockerClient, DockerBaseClass, sanitize_result
from ansible.module_utils.six import string_types

try:
    from docker import utils
    if HAS_DOCKER_PY_2 or HAS_DOCKER_PY_3:
        from docker.types import Ulimit, LogConfig
    else:
        from docker.utils.types import Ulimit, LogConfig
    from ansible.module_utils.docker_common import docker_version
except:
    # missing docker-py handled in ansible.module_utils.docker
    pass


REQUIRES_CONVERSION_TO_BYTES = [
    'kernel_memory',
    'memory',
    'memory_reservation',
    'memory_swap',
    'shm_size'
]

VOLUME_PERMISSIONS = ('rw', 'ro', 'z', 'Z')


class TaskParameters(DockerBaseClass):
    '''
    Access and parse module parameters
    '''

    def __init__(self, client):
        super(TaskParameters, self).__init__()
        self.client = client

        self.auto_remove = None
        self.blkio_weight = None
        self.capabilities = None
        self.cleanup = None
        self.command = None
        self.cpu_period = None
        self.cpu_quota = None
        self.cpuset_cpus = None
        self.cpuset_mems = None
        self.cpu_shares = None
        self.detach = None
        self.debug = None
        self.devices = None
        self.dns_servers = None
        self.dns_opts = None
        self.dns_search_domains = None
        self.domainname = None
        self.env = None
        self.env_file = None
        self.entrypoint = None
        self.etc_hosts = None
        self.exposed_ports = None
        self.force_kill = None
        self.groups = None
        self.hostname = None
        self.ignore_image = None
        self.image = None
        self.init = None
        self.interactive = None
        self.ipc_mode = None
        self.keep_volumes = None
        self.kernel_memory = None
        self.kill_signal = None
        self.labels = None
        self.links = None
        self.log_driver = None
        self.log_options = None
        self.mac_address = None
        self.memory = None
        self.memory_reservation = None
        self.memory_swap = None
        self.memory_swappiness = None
        self.name = None
        self.network_mode = None
        self.userns_mode = None
        self.networks = None
        self.oom_killer = None
        self.oom_score_adj = None
        self.paused = None
        self.pid_mode = None
        self.privileged = None
        self.purge_networks = None
        self.pull = None
        self.read_only = None
        self.recreate = None
        self.restart = None
        self.restart_retries = None
        self.restart_policy = None
        self.shm_size = None
        self.security_opts = None
        self.state = None
        self.stop_signal = None
        self.stop_timeout = None
        self.tmpfs = None
        self.trust_image_content = None
        self.tty = None
        self.user = None
        self.uts = None
        self.volumes = None
        self.volume_binds = dict()
        self.volumes_from = None
        self.volume_driver = None
        self.working_dir = None

        for key, value in client.module.params.items():
            setattr(self, key, value)
        self.comparisons = client.comparisons

        if self.groups:
            # In case integers are passed as groups, we need to convert them to
            # strings as docker internally treats them as strings.
            self.groups = [str(g) for g in self.groups]

        # If state is 'absent', parameters do not have to be parsed or interpreted.
        # Only the container's name is needed.
        if self.state == 'absent':
            return

        for param_name in REQUIRES_CONVERSION_TO_BYTES:
            if client.module.params.get(param_name):
                try:
                    setattr(self, param_name, human_to_bytes(client.module.params.get(param_name)))
                except ValueError as exc:
                    self.fail("Failed to convert %s to bytes: %s" % (param_name, exc))

        self.publish_all_ports = False
        self.published_ports = self._parse_publish_ports()
        if self.published_ports in ('all', 'ALL'):
            self.publish_all_ports = True
            self.published_ports = None

        self.ports = self._parse_exposed_ports(self.published_ports)
        self.log("expose ports:")
        self.log(self.ports, pretty_print=True)

        self.links = self._parse_links(self.links)

        if self.volumes:
            self.volumes = self._expand_host_paths()

        self.tmpfs = self._parse_tmpfs()
        self.env = self._get_environment()
        self.ulimits = self._parse_ulimits()
        self.sysctls = self._parse_sysctls()
        self.log_config = self._parse_log_config()
        self.exp_links = None
        self.volume_binds = self._get_volume_binds(self.volumes)

        self.log("volumes:")
        self.log(self.volumes, pretty_print=True)
        self.log("volume binds:")
        self.log(self.volume_binds, pretty_print=True)

        if self.networks:
            for network in self.networks:
                if not network.get('name'):
                    self.fail("Parameter error: network must have a name attribute.")
                network['id'] = self._get_network_id(network['name'])
                if not network['id']:
                    self.fail("Parameter error: network named %s could not be found. Does it exist?" % network['name'])
                if network.get('links'):
                    network['links'] = self._parse_links(network['links'])

        if self.mac_address:
            # Ensure the MAC address uses colons instead of hyphens for later comparison
            self.mac_address = self.mac_address.replace('-', ':')

        if self.entrypoint:
            # convert from list to str.
            self.entrypoint = ' '.join([str(x) for x in self.entrypoint])

        if self.command:
            # convert from list to str
            if isinstance(self.command, list):
                self.command = ' '.join([str(x) for x in self.command])

    def fail(self, msg):
        self.client.module.fail_json(msg=msg)

    @property
    def update_parameters(self):
        '''
        Returns parameters used to update a container
        '''

        update_parameters = dict(
            cpu_period='cpu_period',
            cpu_quota='cpu_quota',
            cpu_shares='cpu_shares',
            cpuset_cpus='cpuset_cpus',
            mem_limit='memory',
            mem_reservation='memory_reservation',
            memswap_limit='memory_swap',
            kernel_memory='kernel_memory',
        )

        if self.client.HAS_BLKIO_WEIGHT_OPT:
            # blkio_weight is only supported in docker>=1.9
            update_parameters['blkio_weight'] = 'blkio_weight'

        if self.client.HAS_CPUSET_MEMS_OPT:
            # cpuset_mems is only supported in docker>=2.3
            update_parameters['cpuset_mems'] = 'cpuset_mems'

        result = dict()
        for key, value in update_parameters.items():
            if getattr(self, value, None) is not None:
                result[key] = getattr(self, value)
        return result

    @property
    def create_parameters(self):
        '''
        Returns parameters used to create a container
        '''
        create_params = dict(
            command='command',
            domainname='domainname',
            hostname='hostname',
            user='user',
            detach='detach',
            stdin_open='interactive',
            tty='tty',
            ports='ports',
            environment='env',
            name='name',
            entrypoint='entrypoint',
            mac_address='mac_address',
            labels='labels',
            stop_signal='stop_signal',
            working_dir='working_dir',
        )

        if not HAS_DOCKER_PY_3:
            create_params['cpu_shares'] = 'cpu_shares'
            create_params['volume_driver'] = 'volume_driver'

        result = dict(
            host_config=self._host_config(),
            volumes=self._get_mounts(),
        )

        for key, value in create_params.items():
            if getattr(self, value, None) is not None:
                result[key] = getattr(self, value)
        return result

    def _expand_host_paths(self):
        new_vols = []
        for vol in self.volumes:
            if ':' in vol:
                if len(vol.split(':')) == 3:
                    host, container, mode = vol.split(':')
                    if re.match(r'[\.~]', host):
                        host = os.path.abspath(host)
                    new_vols.append("%s:%s:%s" % (host, container, mode))
                    continue
                elif len(vol.split(':')) == 2:
                    parts = vol.split(':')
                    if parts[1] not in VOLUME_PERMISSIONS and re.match(r'[\.~]', parts[0]):
                        host = os.path.abspath(parts[0])
                        new_vols.append("%s:%s:rw" % (host, parts[1]))
                        continue
            new_vols.append(vol)
        return new_vols

    def _get_mounts(self):
        '''
        Return a list of container mounts.
        :return:
        '''
        result = []
        if self.volumes:
            for vol in self.volumes:
                if ':' in vol:
                    if len(vol.split(':')) == 3:
                        host, container, _ = vol.split(':')
                        result.append(container)
                        continue
                    if len(vol.split(':')) == 2:
                        parts = vol.split(':')
                        if parts[1] not in VOLUME_PERMISSIONS:
                            result.append(parts[1])
                            continue
                result.append(vol)
        self.log("mounts:")
        self.log(result, pretty_print=True)
        return result

    def _host_config(self):
        '''
        Returns parameters used to create a HostConfig object
        '''

        host_config_params = dict(
            port_bindings='published_ports',
            publish_all_ports='publish_all_ports',
            links='links',
            privileged='privileged',
            dns='dns_servers',
            dns_opt='dns_opts',
            dns_search='dns_search_domains',
            binds='volume_binds',
            volumes_from='volumes_from',
            network_mode='network_mode',
            userns_mode='userns_mode',
            cap_add='capabilities',
            extra_hosts='etc_hosts',
            read_only='read_only',
            ipc_mode='ipc_mode',
            security_opt='security_opts',
            ulimits='ulimits',
            sysctls='sysctls',
            log_config='log_config',
            mem_limit='memory',
            memswap_limit='memory_swap',
            mem_swappiness='memory_swappiness',
            oom_score_adj='oom_score_adj',
            oom_kill_disable='oom_killer',
            shm_size='shm_size',
            group_add='groups',
            devices='devices',
            pid_mode='pid_mode',
            tmpfs='tmpfs',
        )

        if self.client.HAS_AUTO_REMOVE_OPT:
            # auto_remove is only supported in docker>=2
            host_config_params['auto_remove'] = 'auto_remove'

        if self.client.HAS_BLKIO_WEIGHT_OPT:
            # blkio_weight is only supported in docker>=1.9
            host_config_params['blkio_weight'] = 'blkio_weight'

        if HAS_DOCKER_PY_3:
            # cpu_shares and volume_driver moved to create_host_config in > 3
            host_config_params['cpu_shares'] = 'cpu_shares'
            host_config_params['volume_driver'] = 'volume_driver'

        if self.client.HAS_INIT_OPT:
            host_config_params['init'] = 'init'

        if self.client.HAS_UTS_MODE_OPT:
            host_config_params['uts_mode'] = 'uts'

        params = dict()
        for key, value in host_config_params.items():
            if getattr(self, value, None) is not None:
                params[key] = getattr(self, value)

        if self.restart_policy:
            params['restart_policy'] = dict(Name=self.restart_policy,
                                            MaximumRetryCount=self.restart_retries)

        return self.client.create_host_config(**params)

    @property
    def default_host_ip(self):
        ip = '0.0.0.0'
        if not self.networks:
            return ip
        for net in self.networks:
            if net.get('name'):
                network = self.client.inspect_network(net['name'])
                if network.get('Driver') == 'bridge' and \
                   network.get('Options', {}).get('com.docker.network.bridge.host_binding_ipv4'):
                    ip = network['Options']['com.docker.network.bridge.host_binding_ipv4']
                    break
        return ip

    def _parse_publish_ports(self):
        '''
        Parse ports from docker CLI syntax
        '''
        if self.published_ports is None:
            return None

        if 'all' in self.published_ports:
            return 'all'

        default_ip = self.default_host_ip

        binds = {}
        for port in self.published_ports:
            parts = str(port).split(':')
            container_port = parts[-1]
            if '/' not in container_port:
                container_port = int(parts[-1])

            p_len = len(parts)
            if p_len == 1:
                bind = (default_ip,)
            elif p_len == 2:
                bind = (default_ip, int(parts[0]))
            elif p_len == 3:
                bind = (parts[0], int(parts[1])) if parts[1] else (parts[0],)

            if container_port in binds:
                old_bind = binds[container_port]
                if isinstance(old_bind, list):
                    old_bind.append(bind)
                else:
                    binds[container_port] = [binds[container_port], bind]
            else:
                binds[container_port] = bind
        return binds

    @staticmethod
    def _get_volume_binds(volumes):
        '''
        Extract host bindings, if any, from list of volume mapping strings.

        :return: dictionary of bind mappings
        '''
        result = dict()
        if volumes:
            for vol in volumes:
                host = None
                if ':' in vol:
                    if len(vol.split(':')) == 3:
                        host, container, mode = vol.split(':')
                    if len(vol.split(':')) == 2:
                        parts = vol.split(':')
                        if parts[1] not in VOLUME_PERMISSIONS:
                            host, container, mode = (vol.split(':') + ['rw'])
                if host is not None:
                    result[host] = dict(
                        bind=container,
                        mode=mode
                    )
        return result

    def _parse_exposed_ports(self, published_ports):
        '''
        Parse exposed ports from docker CLI-style ports syntax.
        '''
        exposed = []
        if self.exposed_ports:
            for port in self.exposed_ports:
                port = str(port).strip()
                protocol = 'tcp'
                match = re.search(r'(/.+$)', port)
                if match:
                    protocol = match.group(1).replace('/', '')
                    port = re.sub(r'/.+$', '', port)
                exposed.append((port, protocol))
        if published_ports:
            # Any published port should also be exposed
            for publish_port in published_ports:
                match = False
                if isinstance(publish_port, string_types) and '/' in publish_port:
                    port, protocol = publish_port.split('/')
                    port = int(port)
                else:
                    protocol = 'tcp'
                    port = int(publish_port)
                for exposed_port in exposed:
                    if isinstance(exposed_port[0], string_types) and '-' in exposed_port[0]:
                        start_port, end_port = exposed_port[0].split('-')
                        if int(start_port) <= port <= int(end_port):
                            match = True
                    elif exposed_port[0] == port:
                        match = True
                if not match:
                    exposed.append((port, protocol))
        return exposed

    @staticmethod
    def _parse_links(links):
        '''
        Turn links into a dictionary
        '''
        if links is None:
            return None

        result = []
        for link in links:
            parsed_link = link.split(':', 1)
            if len(parsed_link) == 2:
                result.append((parsed_link[0], parsed_link[1]))
            else:
                result.append((parsed_link[0], parsed_link[0]))
        return result

    def _parse_ulimits(self):
        '''
        Turn ulimits into an array of Ulimit objects
        '''
        if self.ulimits is None:
            return None

        results = []
        for limit in self.ulimits:
            limits = dict()
            pieces = limit.split(':')
            if len(pieces) >= 2:
                limits['name'] = pieces[0]
                limits['soft'] = int(pieces[1])
                limits['hard'] = int(pieces[1])
            if len(pieces) == 3:
                limits['hard'] = int(pieces[2])
            try:
                results.append(Ulimit(**limits))
            except ValueError as exc:
                self.fail("Error parsing ulimits value %s - %s" % (limit, exc))
        return results

    def _parse_sysctls(self):
        '''
        Turn sysctls into an hash of Sysctl objects
        '''
        return self.sysctls

    def _parse_log_config(self):
        '''
        Create a LogConfig object
        '''
        if self.log_driver is None:
            return None

        options = dict(
            Type=self.log_driver,
            Config=dict()
        )

        if self.log_options is not None:
            options['Config'] = dict()
            for k, v in self.log_options.items():
                options['Config'][k] = str(v)

        try:
            return LogConfig(**options)
        except ValueError as exc:
            self.fail('Error parsing logging options - %s' % (exc))

    def _parse_tmpfs(self):
        '''
        Turn tmpfs into a hash of Tmpfs objects
        '''
        result = dict()
        if self.tmpfs is None:
            return result

        for tmpfs_spec in self.tmpfs:
            split_spec = tmpfs_spec.split(":", 1)
            if len(split_spec) > 1:
                result[split_spec[0]] = split_spec[1]
            else:
                result[split_spec[0]] = ""
        return result

    def _get_environment(self):
        """
        If environment file is combined with explicit environment variables, the explicit environment variables
        take precedence.
        """
        final_env = {}
        if self.env_file:
            parsed_env_file = utils.parse_env_file(self.env_file)
            for name, value in parsed_env_file.items():
                final_env[name] = str(value)
        if self.env:
            for name, value in self.env.items():
                final_env[name] = str(value)
        return final_env

    def _get_network_id(self, network_name):
        network_id = None
        try:
            for network in self.client.networks(names=[network_name]):
                if network['Name'] == network_name:
                    network_id = network['Id']
                    break
        except Exception as exc:
            self.fail("Error getting network id for %s - %s" % (network_name, str(exc)))
        return network_id


class Container(DockerBaseClass):

    def __init__(self, container, parameters):
        super(Container, self).__init__()
        self.raw = container
        self.Id = None
        self.container = container
        if container:
            self.Id = container['Id']
            self.Image = container['Image']
        self.log(self.container, pretty_print=True)
        self.parameters = parameters
        self.parameters.expected_links = None
        self.parameters.expected_ports = None
        self.parameters.expected_exposed = None
        self.parameters.expected_volumes = None
        self.parameters.expected_ulimits = None
        self.parameters.expected_sysctls = None
        self.parameters.expected_etc_hosts = None
        self.parameters.expected_env = None
        self.parameters_map = dict()
        self.parameters_map['expected_links'] = 'links'
        self.parameters_map['expected_ports'] = 'expected_ports'
        self.parameters_map['expected_exposed'] = 'exposed_ports'
        self.parameters_map['expected_volumes'] = 'volumes'
        self.parameters_map['expected_ulimits'] = 'ulimits'
        self.parameters_map['expected_sysctls'] = 'sysctls'
        self.parameters_map['expected_etc_hosts'] = 'etc_hosts'
        self.parameters_map['expected_env'] = 'env'
        self.parameters_map['expected_entrypoint'] = 'entrypoint'
        self.parameters_map['expected_binds'] = 'volumes'
        self.parameters_map['expected_cmd'] = 'command'
        self.parameters_map['expected_devices'] = 'devices'

    def fail(self, msg):
        self.parameters.client.module.fail_json(msg=msg)

    @property
    def exists(self):
        return True if self.container else False

    @property
    def running(self):
        if self.container and self.container.get('State'):
            if self.container['State'].get('Running') and not self.container['State'].get('Ghost', False):
                return True
        return False

    def _compare_dict_allow_more_present(self, av, bv):
        '''
        Compare two dictionaries for whether every entry of the first is in the second.
        '''
        for key, value in av.items():
            if key not in bv:
                return False
            if bv[key] != value:
                return False
        return True

    def _compare(self, a, b, compare):
        '''
        Compare values a and b as described in compare.
        '''
        method = compare['comparison']
        if method == 'ignore':
            return True
        # If a or b is None:
        if a is None or b is None:
            # If both are None: equality
            if a == b:
                return True
            # Otherwise, not equal for values, and equal
            # if the other is empty for set/list/dict
            if compare['type'] == 'value':
                return False
            return len(b if a is None else a) == 0
        # Do proper comparison (both objects not None)
        if compare['type'] == 'value':
            return a == b
        elif compare['type'] == 'list':
            if method == 'strict':
                return a == b
            else:
                set_a = set(a)
                set_b = set(b)
                return set_b >= set_a
        elif compare['type'] == 'dict':
            if method == 'strict':
                return a == b
            else:
                return self._compare_dict_allow_more_present(a, b)
        elif compare['type'] == 'set':
            set_a = set(a)
            set_b = set(b)
            if method == 'strict':
                return set_a == set_b
            else:
                return set_b >= set_a
        elif compare['type'] == 'set(dict)':
            for av in a:
                found = False
                for bv in b:
                    if self._compare_dict_allow_more_present(av, bv):
                        found = True
                        break
                if not found:
                    return False
            if method == 'strict':
                # If we would know that both a and b do not contain duplicates,
                # we could simply compare len(a) to len(b) to finish this test.
                # We can assume that b has no duplicates (as it is returned by
                # docker), but we don't know for a.
                for bv in b:
                    found = False
                    for av in a:
                        if self._compare_dict_allow_more_present(av, bv):
                            found = True
                            break
                    if not found:
                        return False
            return True

    def has_different_configuration(self, image):
        '''
        Diff parameters vs existing container config. Returns tuple: (True | False, List of differences)
        '''
        self.log('Starting has_different_configuration')
        self.parameters.expected_entrypoint = self._get_expected_entrypoint()
        self.parameters.expected_links = self._get_expected_links()
        self.parameters.expected_ports = self._get_expected_ports()
        self.parameters.expected_exposed = self._get_expected_exposed(image)
        self.parameters.expected_volumes = self._get_expected_volumes(image)
        self.parameters.expected_binds = self._get_expected_binds(image)
        self.parameters.expected_ulimits = self._get_expected_ulimits(self.parameters.ulimits)
        self.parameters.expected_sysctls = self._get_expected_sysctls(self.parameters.sysctls)
        self.parameters.expected_etc_hosts = self._convert_simple_dict_to_list('etc_hosts')
        self.parameters.expected_env = self._get_expected_env(image)
        self.parameters.expected_cmd = self._get_expected_cmd()
        self.parameters.expected_devices = self._get_expected_devices()

        if not self.container.get('HostConfig'):
            self.fail("has_config_diff: Error parsing container properties. HostConfig missing.")
        if not self.container.get('Config'):
            self.fail("has_config_diff: Error parsing container properties. Config missing.")
        if not self.container.get('NetworkSettings'):
            self.fail("has_config_diff: Error parsing container properties. NetworkSettings missing.")

        host_config = self.container['HostConfig']
        log_config = host_config.get('LogConfig', dict())
        restart_policy = host_config.get('RestartPolicy', dict())
        config = self.container['Config']
        network = self.container['NetworkSettings']

        # The previous version of the docker module ignored the detach state by
        # assuming if the container was running, it must have been detached.
        detach = not (config.get('AttachStderr') and config.get('AttachStdout'))

        # "ExposedPorts": null returns None type & causes AttributeError - PR #5517
        if config.get('ExposedPorts') is not None:
            expected_exposed = [re.sub(r'/.+$', '', p) for p in config.get('ExposedPorts', dict()).keys()]
        else:
            expected_exposed = []

        # Map parameters to container inspect results
        config_mapping = dict(
            expected_cmd=config.get('Cmd'),
            domainname=config.get('Domainname'),
            hostname=config.get('Hostname'),
            user=config.get('User'),
            detach=detach,
            interactive=config.get('OpenStdin'),
            capabilities=host_config.get('CapAdd'),
            expected_devices=host_config.get('Devices'),
            dns_servers=host_config.get('Dns'),
            dns_opts=host_config.get('DnsOptions'),
            dns_search_domains=host_config.get('DnsSearch'),
            expected_env=(config.get('Env') or []),
            expected_entrypoint=config.get('Entrypoint'),
            expected_etc_hosts=host_config['ExtraHosts'],
            expected_exposed=expected_exposed,
            groups=host_config.get('GroupAdd'),
            ipc_mode=host_config.get("IpcMode"),
            labels=config.get('Labels'),
            expected_links=host_config.get('Links'),
            mac_address=network.get('MacAddress'),
            memory_swappiness=host_config.get('MemorySwappiness'),
            network_mode=host_config.get('NetworkMode'),
            userns_mode=host_config.get('UsernsMode'),
            oom_killer=host_config.get('OomKillDisable'),
            oom_score_adj=host_config.get('OomScoreAdj'),
            pid_mode=host_config.get('PidMode'),
            privileged=host_config.get('Privileged'),
            expected_ports=host_config.get('PortBindings'),
            read_only=host_config.get('ReadonlyRootfs'),
            restart_policy=restart_policy.get('Name'),
            # Cannot test shm_size, as shm_size is not included in container inspection results.
            # shm_size=host_config.get('ShmSize'),
            security_opts=host_config.get("SecurityOpt"),
            stop_signal=config.get("StopSignal"),
            tmpfs=host_config.get('Tmpfs'),
            tty=config.get('Tty'),
            expected_ulimits=host_config.get('Ulimits'),
            expected_sysctls=host_config.get('Sysctls'),
            uts=host_config.get('UTSMode'),
            expected_volumes=config.get('Volumes'),
            expected_binds=host_config.get('Binds'),
            volumes_from=host_config.get('VolumesFrom'),
            working_dir=config.get('WorkingDir'),
            publish_all_ports=host_config.get('PublishAllPorts'),
        )
        if self.parameters.restart_policy:
            config_mapping['restart_retries'] = restart_policy.get('MaximumRetryCount')
        if self.parameters.log_driver:
            config_mapping['log_driver'] = log_config.get('Type')
            config_mapping['log_options'] = log_config.get('Config')

        if self.parameters.client.HAS_AUTO_REMOVE_OPT:
            # auto_remove is only supported in docker>=2
            config_mapping['auto_remove'] = host_config.get('AutoRemove')

        if HAS_DOCKER_PY_3:
            # volume_driver moved to create_host_config in > 3
            config_mapping['volume_driver'] = host_config.get('VolumeDriver')

        differences = []
        for key, value in config_mapping.items():
            compare = self.parameters.client.comparisons[self.parameters_map.get(key, key)]
            self.log('check differences %s %s vs %s (%s)' % (key, getattr(self.parameters, key), str(value), compare))
            if getattr(self.parameters, key, None) is not None:
                match = self._compare(getattr(self.parameters, key), value, compare)

                if not match:
                    # no match. record the differences
                    item = dict()
                    item[key] = dict(
                        parameter=getattr(self.parameters, key),
                        container=value
                    )
                    differences.append(item)

        has_differences = True if len(differences) > 0 else False
        return has_differences, differences

    def has_different_resource_limits(self):
        '''
        Diff parameters and container resource limits
        '''
        if not self.container.get('HostConfig'):
            self.fail("limits_differ_from_container: Error parsing container properties. HostConfig missing.")

        host_config = self.container['HostConfig']

        config_mapping = dict(
            cpu_period=host_config.get('CpuPeriod'),
            cpu_quota=host_config.get('CpuQuota'),
            cpuset_cpus=host_config.get('CpusetCpus'),
            kernel_memory=host_config.get("KernelMemory"),
            memory=host_config.get('Memory'),
            memory_reservation=host_config.get('MemoryReservation'),
            memory_swap=host_config.get('MemorySwap'),
            oom_score_adj=host_config.get('OomScoreAdj'),
            oom_killer=host_config.get('OomKillDisable'),
        )

        if self.parameters.client.HAS_BLKIO_WEIGHT_OPT:
            # blkio_weight is only supported in docker>=1.9
            config_mapping['blkio_weight'] = host_config.get('BlkioWeight')

        if self.parameters.client.HAS_CPUSET_MEMS_OPT:
            # cpuset_mems is only supported in docker>=2.3
            config_mapping['cpuset_mems'] = host_config.get('CpusetMems')

        if HAS_DOCKER_PY_3:
            # cpu_shares moved to create_host_config in > 3
            config_mapping['cpu_shares'] = host_config.get('CpuShares')

        differences = []
        for key, value in config_mapping.items():
            if getattr(self.parameters, key, None):
                compare = self.parameters.client.comparisons[self.parameters_map.get(key, key)]
                match = self._compare(getattr(self.parameters, key), value, compare)

                if not match:
                    # no match. record the differences
                    item = dict()
                    item[key] = dict(
                        parameter=getattr(self.parameters, key),
                        container=value
                    )
                    differences.append(item)
        different = (len(differences) > 0)
        return different, differences

    def has_network_differences(self):
        '''
        Check if the container is connected to requested networks with expected options: links, aliases, ipv4, ipv6
        '''
        different = False
        differences = []

        if not self.parameters.networks:
            return different, differences

        if not self.container.get('NetworkSettings'):
            self.fail("has_missing_networks: Error parsing container properties. NetworkSettings missing.")

        connected_networks = self.container['NetworkSettings']['Networks']
        for network in self.parameters.networks:
            if connected_networks.get(network['name'], None) is None:
                different = True
                differences.append(dict(
                    parameter=network,
                    container=None
                ))
            else:
                diff = False
                if network.get('ipv4_address') and network['ipv4_address'] != connected_networks[network['name']].get('IPAddress'):
                    diff = True
                if network.get('ipv6_address') and network['ipv6_address'] != connected_networks[network['name']].get('GlobalIPv6Address'):
                    diff = True
                if network.get('aliases') and not connected_networks[network['name']].get('Aliases'):
                    diff = True
                if network.get('aliases') and connected_networks[network['name']].get('Aliases'):
                    for alias in network.get('aliases'):
                        if alias not in connected_networks[network['name']].get('Aliases', []):
                            diff = True
                if network.get('links') and not connected_networks[network['name']].get('Links'):
                    diff = True
                if network.get('links') and connected_networks[network['name']].get('Links'):
                    expected_links = []
                    for link, alias in network['links']:
                        expected_links.append("%s:%s" % (link, alias))
                    for link in expected_links:
                        if link not in connected_networks[network['name']].get('Links', []):
                            diff = True
                if diff:
                    different = True
                    differences.append(dict(
                        parameter=network,
                        container=dict(
                            name=network['name'],
                            ipv4_address=connected_networks[network['name']].get('IPAddress'),
                            ipv6_address=connected_networks[network['name']].get('GlobalIPv6Address'),
                            aliases=connected_networks[network['name']].get('Aliases'),
                            links=connected_networks[network['name']].get('Links')
                        )
                    ))
        return different, differences

    def has_extra_networks(self):
        '''
        Check if the container is connected to non-requested networks
        '''
        extra_networks = []
        extra = False

        if not self.container.get('NetworkSettings'):
            self.fail("has_extra_networks: Error parsing container properties. NetworkSettings missing.")

        connected_networks = self.container['NetworkSettings'].get('Networks')
        if connected_networks:
            for network, network_config in connected_networks.items():
                keep = False
                if self.parameters.networks:
                    for expected_network in self.parameters.networks:
                        if expected_network['name'] == network:
                            keep = True
                if not keep:
                    extra = True
                    extra_networks.append(dict(name=network, id=network_config['NetworkID']))
        return extra, extra_networks

    def _get_expected_devices(self):
        if not self.parameters.devices:
            return None
        expected_devices = []
        for device in self.parameters.devices:
            parts = device.split(':')
            if len(parts) == 1:
                expected_devices.append(
                    dict(
                        CgroupPermissions='rwm',
                        PathInContainer=parts[0],
                        PathOnHost=parts[0]
                    ))
            elif len(parts) == 2:
                parts = device.split(':')
                expected_devices.append(
                    dict(
                        CgroupPermissions='rwm',
                        PathInContainer=parts[1],
                        PathOnHost=parts[0]
                    )
                )
            else:
                expected_devices.append(
                    dict(
                        CgroupPermissions=parts[2],
                        PathInContainer=parts[1],
                        PathOnHost=parts[0]
                    ))
        return expected_devices

    def _get_expected_entrypoint(self):
        if not self.parameters.entrypoint:
            return None
        return shlex.split(self.parameters.entrypoint)

    def _get_expected_ports(self):
        if not self.parameters.published_ports:
            return None
        expected_bound_ports = {}
        for container_port, config in self.parameters.published_ports.items():
            if isinstance(container_port, int):
                container_port = "%s/tcp" % container_port
            if len(config) == 1:
                if isinstance(config[0], int):
                    expected_bound_ports[container_port] = [{'HostIp': "0.0.0.0", 'HostPort': config[0]}]
                else:
                    expected_bound_ports[container_port] = [{'HostIp': config[0], 'HostPort': ""}]
            elif isinstance(config[0], tuple):
                expected_bound_ports[container_port] = []
                for host_ip, host_port in config:
                    expected_bound_ports[container_port].append({'HostIp': host_ip, 'HostPort': str(host_port)})
            else:
                expected_bound_ports[container_port] = [{'HostIp': config[0], 'HostPort': str(config[1])}]
        return expected_bound_ports

    def _get_expected_links(self):
        if self.parameters.links is None:
            return None
        self.log('parameter links:')
        self.log(self.parameters.links, pretty_print=True)
        exp_links = []
        for link, alias in self.parameters.links:
            exp_links.append("/%s:%s/%s" % (link, ('/' + self.parameters.name), alias))
        return exp_links

    def _get_expected_binds(self, image):
        self.log('_get_expected_binds')
        image_vols = []
        if image:
            image_vols = self._get_image_binds(image['ContainerConfig'].get('Volumes'))
        param_vols = []
        if self.parameters.volumes:
            for vol in self.parameters.volumes:
                host = None
                if ':' in vol:
                    if len(vol.split(':')) == 3:
                        host, container, mode = vol.split(':')
                    if len(vol.split(':')) == 2:
                        parts = vol.split(':')
                        if parts[1] not in VOLUME_PERMISSIONS:
                            host, container, mode = vol.split(':') + ['rw']
                if host:
                    param_vols.append("%s:%s:%s" % (host, container, mode))
        result = list(set(image_vols + param_vols))
        self.log("expected_binds:")
        self.log(result, pretty_print=True)
        return result

    def _get_image_binds(self, volumes):
        '''
        Convert array of binds to array of strings with format host_path:container_path:mode

        :param volumes: array of bind dicts
        :return: array of strings
        '''
        results = []
        if isinstance(volumes, dict):
            results += self._get_bind_from_dict(volumes)
        elif isinstance(volumes, list):
            for vol in volumes:
                results += self._get_bind_from_dict(vol)
        return results

    @staticmethod
    def _get_bind_from_dict(volume_dict):
        results = []
        if volume_dict:
            for host_path, config in volume_dict.items():
                if isinstance(config, dict) and config.get('bind'):
                    container_path = config.get('bind')
                    mode = config.get('mode', 'rw')
                    results.append("%s:%s:%s" % (host_path, container_path, mode))
        return results

    def _get_expected_volumes(self, image):
        self.log('_get_expected_volumes')
        expected_vols = dict()
        if image and image['ContainerConfig'].get('Volumes'):
            expected_vols.update(image['ContainerConfig'].get('Volumes'))

        if self.parameters.volumes:
            for vol in self.parameters.volumes:
                container = None
                if ':' in vol:
                    if len(vol.split(':')) == 3:
                        host, container, mode = vol.split(':')
                    if len(vol.split(':')) == 2:
                        parts = vol.split(':')
                        if parts[1] not in VOLUME_PERMISSIONS:
                            host, container, mode = vol.split(':') + ['rw']
                new_vol = dict()
                if container:
                    new_vol[container] = dict()
                else:
                    new_vol[vol] = dict()
                expected_vols.update(new_vol)

        if not expected_vols:
            expected_vols = None
        self.log("expected_volumes:")
        self.log(expected_vols, pretty_print=True)
        return expected_vols

    def _get_expected_env(self, image):
        self.log('_get_expected_env')
        expected_env = dict()
        if image and image['ContainerConfig'].get('Env'):
            for env_var in image['ContainerConfig']['Env']:
                parts = env_var.split('=', 1)
                expected_env[parts[0]] = parts[1]
        if self.parameters.env:
            expected_env.update(self.parameters.env)
        param_env = []
        for key, value in expected_env.items():
            param_env.append("%s=%s" % (key, value))
        return param_env

    def _get_expected_exposed(self, image):
        self.log('_get_expected_exposed')
        image_ports = []
        if image:
            image_ports = [re.sub(r'/.+$', '', p) for p in (image['ContainerConfig'].get('ExposedPorts') or {}).keys()]
        param_ports = []
        if self.parameters.ports:
            param_ports = [str(p[0]) for p in self.parameters.ports]
        result = list(set(image_ports + param_ports))
        self.log(result, pretty_print=True)
        return result

    def _get_expected_ulimits(self, config_ulimits):
        self.log('_get_expected_ulimits')
        if config_ulimits is None:
            return None
        results = []
        for limit in config_ulimits:
            results.append(dict(
                Name=limit.name,
                Soft=limit.soft,
                Hard=limit.hard
            ))
        return results

    def _get_expected_sysctls(self, config_sysctls):
        self.log('_get_expected_sysctls')
        if config_sysctls is None:
            return None
        result = dict()
        for key, value in config_sysctls.items():
            result[key] = str(value)
        return result

    def _get_expected_cmd(self):
        self.log('_get_expected_cmd')
        if not self.parameters.command:
            return None
        return shlex.split(self.parameters.command)

    def _convert_simple_dict_to_list(self, param_name, join_with=':'):
        if getattr(self.parameters, param_name, None) is None:
            return None
        results = []
        for key, value in getattr(self.parameters, param_name).items():
            results.append("%s%s%s" % (key, join_with, value))
        return results


class ContainerManager(DockerBaseClass):
    '''
    Perform container management tasks
    '''

    def __init__(self, client):

        super(ContainerManager, self).__init__()

        if client.module.params.get('log_options') and not client.module.params.get('log_driver'):
            client.module.warn('log_options is ignored when log_driver is not specified')
        if client.module.params.get('restart_retries') and not client.module.params.get('restart_policy'):
            client.module.warn('restart_retries is ignored when restart_policy is not specified')

        self.client = client
        self.parameters = TaskParameters(client)
        self.check_mode = self.client.check_mode
        self.results = {'changed': False, 'actions': []}
        self.diff = {}
        self.facts = {}

        state = self.parameters.state
        if state in ('stopped', 'started', 'present'):
            self.present(state)
        elif state == 'absent':
            self.absent()

        if not self.check_mode and not self.parameters.debug:
            self.results.pop('actions')

        if self.client.module._diff or self.parameters.debug:
            self.results['diff'] = self.diff

        if self.facts:
            self.results['ansible_facts'] = {'docker_container': self.facts}

    def present(self, state):
        container = self._get_container(self.parameters.name)

        # If the image parameter was passed then we need to deal with the image
        # version comparison. Otherwise we handle this depending on whether
        # the container already runs or not; in the former case, in case the
        # container needs to be restarted, we use the existing container's
        # image ID.
        image = self._get_image()
        self.log(image, pretty_print=True)
        if not container.exists:
            # New container
            self.log('No container found')
            if not self.parameters.image:
                self.fail('Cannot create container when image is not specified!')
            new_container = self.container_create(self.parameters.image, self.parameters.create_parameters)
            if new_container:
                container = new_container
        else:
            # Existing container
            different, differences = container.has_different_configuration(image)
            image_different = False
            if self.parameters.comparisons['image']['comparison'] == 'strict':
                image_different = self._image_is_different(image, container)
            if image_different or different or self.parameters.recreate:
                self.diff['differences'] = differences
                if image_different:
                    self.diff['image_different'] = True
                self.log("differences")
                self.log(differences, pretty_print=True)
                image_to_use = self.parameters.image
                if not image_to_use and container and container.Image:
                    image_to_use = container.Image
                if not image_to_use:
                    self.fail('Cannot recreate container when image is not specified or cannot be extracted from current container!')
                if container.running:
                    self.container_stop(container.Id)
                self.container_remove(container.Id)
                new_container = self.container_create(image_to_use, self.parameters.create_parameters)
                if new_container:
                    container = new_container

        if container and container.exists:
            container = self.update_limits(container)
            container = self.update_networks(container)

            if state == 'started' and not container.running:
                container = self.container_start(container.Id)
            elif state == 'started' and self.parameters.restart:
                self.container_stop(container.Id)
                container = self.container_start(container.Id)
            elif state == 'stopped' and container.running:
                self.container_stop(container.Id)
                container = self._get_container(container.Id)

        self.facts = container.raw

    def absent(self):
        container = self._get_container(self.parameters.name)
        if container.exists:
            if container.running:
                self.container_stop(container.Id)
            self.container_remove(container.Id)

    def fail(self, msg, **kwargs):
        self.client.module.fail_json(msg=msg, **sanitize_result(kwargs))

    def _get_container(self, container):
        '''
        Expects container ID or Name. Returns a container object
        '''
        return Container(self.client.get_container(container), self.parameters)

    def _get_image(self):
        if not self.parameters.image:
            self.log('No image specified')
            return None
        repository, tag = utils.parse_repository_tag(self.parameters.image)
        if not tag:
            tag = "latest"
        image = self.client.find_image(repository, tag)
        if not self.check_mode:
            if not image or self.parameters.pull:
                self.log("Pull the image.")
                image, alreadyToLatest = self.client.pull_image(repository, tag)
                if alreadyToLatest:
                    self.results['changed'] = False
                else:
                    self.results['changed'] = True
                    self.results['actions'].append(dict(pulled_image="%s:%s" % (repository, tag)))
        self.log("image")
        self.log(image, pretty_print=True)
        return image

    def _image_is_different(self, image, container):
        if image and image.get('Id'):
            if container and container.Image:
                if image.get('Id') != container.Image:
                    return True
        return False

    def update_limits(self, container):
        limits_differ, different_limits = container.has_different_resource_limits()
        if limits_differ:
            self.log("limit differences:")
            self.log(different_limits, pretty_print=True)
        if limits_differ and not self.check_mode:
            self.container_update(container.Id, self.parameters.update_parameters)
            return self._get_container(container.Id)
        return container

    def update_networks(self, container):
        has_network_differences, network_differences = container.has_network_differences()
        updated_container = container
        if has_network_differences:
            if self.diff.get('differences'):
                self.diff['differences'].append(dict(network_differences=network_differences))
            else:
                self.diff['differences'] = [dict(network_differences=network_differences)]
            self.results['changed'] = True
            updated_container = self._add_networks(container, network_differences)

        if self.parameters.purge_networks:
            has_extra_networks, extra_networks = container.has_extra_networks()
            if has_extra_networks:
                if self.diff.get('differences'):
                    self.diff['differences'].append(dict(purge_networks=extra_networks))
                else:
                    self.diff['differences'] = [dict(purge_networks=extra_networks)]
                self.results['changed'] = True
                updated_container = self._purge_networks(container, extra_networks)
        return updated_container

    def _add_networks(self, container, differences):
        for diff in differences:
            # remove the container from the network, if connected
            if diff.get('container'):
                self.results['actions'].append(dict(removed_from_network=diff['parameter']['name']))
                if not self.check_mode:
                    try:
                        self.client.disconnect_container_from_network(container.Id, diff['parameter']['id'])
                    except Exception as exc:
                        self.fail("Error disconnecting container from network %s - %s" % (diff['parameter']['name'],
                                                                                          str(exc)))
            # connect to the network
            params = dict(
                ipv4_address=diff['parameter'].get('ipv4_address', None),
                ipv6_address=diff['parameter'].get('ipv6_address', None),
                links=diff['parameter'].get('links', None),
                aliases=diff['parameter'].get('aliases', None)
            )
            self.results['actions'].append(dict(added_to_network=diff['parameter']['name'], network_parameters=params))
            if not self.check_mode:
                try:
                    self.log("Connecting container to network %s" % diff['parameter']['id'])
                    self.log(params, pretty_print=True)
                    self.client.connect_container_to_network(container.Id, diff['parameter']['id'], **params)
                except Exception as exc:
                    self.fail("Error connecting container to network %s - %s" % (diff['parameter']['name'], str(exc)))
        return self._get_container(container.Id)

    def _purge_networks(self, container, networks):
        for network in networks:
            self.results['actions'].append(dict(removed_from_network=network['name']))
            if not self.check_mode:
                try:
                    self.client.disconnect_container_from_network(container.Id, network['name'])
                except Exception as exc:
                    self.fail("Error disconnecting container from network %s - %s" % (network['name'],
                                                                                      str(exc)))
        return self._get_container(container.Id)

    def container_create(self, image, create_parameters):
        self.log("create container")
        self.log("image: %s parameters:" % image)
        self.log(create_parameters, pretty_print=True)
        self.results['actions'].append(dict(created="Created container", create_parameters=create_parameters))
        self.results['changed'] = True
        new_container = None
        if not self.check_mode:
            try:
                new_container = self.client.create_container(image, **create_parameters)
            except Exception as exc:
                self.fail("Error creating container: %s" % str(exc))
            return self._get_container(new_container['Id'])
        return new_container

    def container_start(self, container_id):
        self.log("start container %s" % (container_id))
        self.results['actions'].append(dict(started=container_id))
        self.results['changed'] = True
        if not self.check_mode:
            try:
                self.client.start(container=container_id)
            except Exception as exc:
                self.fail("Error starting container %s: %s" % (container_id, str(exc)))

            if not self.parameters.detach:
                if HAS_DOCKER_PY_3:
                    status = self.client.wait(container_id)['StatusCode']
                else:
                    status = self.client.wait(container_id)
                config = self.client.inspect_container(container_id)
                logging_driver = config['HostConfig']['LogConfig']['Type']

                if logging_driver == 'json-file' or logging_driver == 'journald':
                    output = self.client.logs(container_id, stdout=True, stderr=True, stream=False, timestamps=False)
                else:
                    output = "Result logged using `%s` driver" % logging_driver

                if status != 0:
                    self.fail(output, status=status)
                if self.parameters.cleanup:
                    self.container_remove(container_id, force=True)
                insp = self._get_container(container_id)
                if insp.raw:
                    insp.raw['Output'] = output
                else:
                    insp.raw = dict(Output=output)
                return insp
        return self._get_container(container_id)

    def container_remove(self, container_id, link=False, force=False):
        volume_state = (not self.parameters.keep_volumes)
        self.log("remove container container:%s v:%s link:%s force%s" % (container_id, volume_state, link, force))
        self.results['actions'].append(dict(removed=container_id, volume_state=volume_state, link=link, force=force))
        self.results['changed'] = True
        response = None
        if not self.check_mode:
            try:
                response = self.client.remove_container(container_id, v=volume_state, link=link, force=force)
            except Exception as exc:
                self.fail("Error removing container %s: %s" % (container_id, str(exc)))
        return response

    def container_update(self, container_id, update_parameters):
        if update_parameters:
            self.log("update container %s" % (container_id))
            self.log(update_parameters, pretty_print=True)
            self.results['actions'].append(dict(updated=container_id, update_parameters=update_parameters))
            self.results['changed'] = True
            if not self.check_mode and callable(getattr(self.client, 'update_container')):
                try:
                    self.client.update_container(container_id, **update_parameters)
                except Exception as exc:
                    self.fail("Error updating container %s: %s" % (container_id, str(exc)))
        return self._get_container(container_id)

    def container_kill(self, container_id):
        self.results['actions'].append(dict(killed=container_id, signal=self.parameters.kill_signal))
        self.results['changed'] = True
        response = None
        if not self.check_mode:
            try:
                if self.parameters.kill_signal:
                    response = self.client.kill(container_id, signal=self.parameters.kill_signal)
                else:
                    response = self.client.kill(container_id)
            except Exception as exc:
                self.fail("Error killing container %s: %s" % (container_id, exc))
        return response

    def container_stop(self, container_id):
        if self.parameters.force_kill:
            self.container_kill(container_id)
            return
        self.results['actions'].append(dict(stopped=container_id, timeout=self.parameters.stop_timeout))
        self.results['changed'] = True
        response = None
        if not self.check_mode:
            try:
                if self.parameters.stop_timeout:
                    response = self.client.stop(container_id, timeout=self.parameters.stop_timeout)
                else:
                    response = self.client.stop(container_id)
            except Exception as exc:
                self.fail("Error stopping container %s: %s" % (container_id, str(exc)))
        return response


class AnsibleDockerClientContainer(AnsibleDockerClient):

    def _setup_comparisons(self):
        comparisons = {}
        comp_aliases = {}
        # Put in defaults
        explicit_types = dict(
            command='list',
            devices='set(dict)',
            dns_search_domains='list',
            dns_servers='list',
            env='set',
            entrypoint='list',
            etc_hosts='set',
            ulimits='set(dict)',
        )
        for option, data in self.module.argument_spec.items():
            # Ignore options which aren't used as container properties
            if option in ('docker_host', 'tls_hostname', 'api_version', 'timeout', 'cacert_path', 'cert_path',
                          'key_path', 'ssl_version', 'tls', 'tls_verify', 'debug', 'env_file', 'force_kill',
                          'keep_volumes', 'ignore_image', 'name', 'pull', 'purge_networks', 'recreate',
                          'restart', 'state', 'stop_timeout', 'trust_image_content', 'networks'):
                continue
            # Determine option type
            if option in explicit_types:
                type = explicit_types[option]
            elif data['type'] == 'list':
                type = 'set'
            elif data['type'] == 'dict':
                type = 'dict'
            else:
                type = 'value'
            # Determine comparison type
            if type in ('list', 'value'):
                comparison = 'strict'
            else:
                comparison = 'allow_more_present'
            comparisons[option] = dict(type=type, comparison=comparison, name=option)
            # Keep track of aliases
            comp_aliases[option] = option
            for alias in data.get('aliases', []):
                comp_aliases[alias] = option
        # Process legacy ignore options
        if self.module.params['ignore_image']:
            comparisons['image']['comparison'] = 'ignore'
        # Add implicit options
        comparisons['publish_all_ports'] = dict(type='value', comparison='strict', name='published_ports')
        comparisons['expected_ports'] = dict(type='dict', comparison=comparisons['published_ports']['comparison'], name='expected_ports')
        self.comparisons = comparisons

    def __init__(self, **kwargs):
        super(AnsibleDockerClientContainer, self).__init__(**kwargs)

        docker_api_version = self.version()['ApiVersion']
        init_supported = LooseVersion(docker_api_version) >= LooseVersion('1.25')
        if self.module.params.get("init") and not init_supported:
            self.fail('docker API version is %s. Minimum version required is 1.25 to set init option.' % (docker_api_version,))

        init_supported = init_supported and LooseVersion(docker_version) >= LooseVersion('2.2')
        if self.module.params.get("init") and not init_supported:
            self.fail("docker or docker-py version is %s. Minimum version required is 2.2 to set init option. "
                      "If you use the 'docker-py' module, you have to switch to the docker 'Python' package." % (docker_version,))

        uts_mode_supported = LooseVersion(docker_version) >= LooseVersion('3.5')
        if self.module.params.get("uts") is not None and not uts_mode_supported:
            self.fail("docker or docker-py version is %s. Minimum version required is 3.5 to set uts option. "
                      "If you use the 'docker-py' module, you have to switch to the docker 'Python' package." % (docker_version,))

        blkio_weight_supported = LooseVersion(docker_version) >= LooseVersion('1.9')
        if self.module.params.get("blkio_weight") is not None and not blkio_weight_supported:
            self.fail("docker or docker-py version is %s. Minimum version required is 1.9 to set blkio_weight option.")

        cpuset_mems_supported = LooseVersion(docker_version) >= LooseVersion('2.3')
        if self.module.params.get("cpuset_mems") is not None and not cpuset_mems_supported:
            self.fail("docker or docker-py version is %s. Minimum version required is 2.3 to set cpuset_mems option. "
                      "If you use the 'docker-py' module, you have to switch to the docker 'Python' package." % (docker_version,))

        self.HAS_INIT_OPT = init_supported
        self.HAS_UTS_MODE_OPT = uts_mode_supported
        self.HAS_BLKIO_WEIGHT_OPT = blkio_weight_supported
        self.HAS_CPUSET_MEMS_OPT = cpuset_mems_supported
        self.HAS_AUTO_REMOVE_OPT = HAS_DOCKER_PY_2 or HAS_DOCKER_PY_3
        if self.module.params.get('auto_remove') and not self.HAS_AUTO_REMOVE_OPT:
            self.fail("'auto_remove' is not compatible with the 'docker-py' Python package. It requires the newer 'docker' Python package.")

        self._setup_comparisons()


def main():
    argument_spec = dict(
        auto_remove=dict(type='bool', default=False),
        blkio_weight=dict(type='int'),
        capabilities=dict(type='list'),
        cleanup=dict(type='bool', default=False),
        command=dict(type='raw'),
        cpu_period=dict(type='int'),
        cpu_quota=dict(type='int'),
        cpuset_cpus=dict(type='str'),
        cpuset_mems=dict(type='str'),
        cpu_shares=dict(type='int'),
        detach=dict(type='bool', default=True),
        devices=dict(type='list'),
        dns_servers=dict(type='list'),
        dns_opts=dict(type='list'),
        dns_search_domains=dict(type='list'),
        domainname=dict(type='str'),
        entrypoint=dict(type='list'),
        env=dict(type='dict'),
        env_file=dict(type='path'),
        etc_hosts=dict(type='dict'),
        exposed_ports=dict(type='list', aliases=['exposed', 'expose']),
        force_kill=dict(type='bool', default=False, aliases=['forcekill']),
        groups=dict(type='list'),
        hostname=dict(type='str'),
        ignore_image=dict(type='bool', default=False),
        image=dict(type='str'),
        init=dict(type='bool', default=False),
        interactive=dict(type='bool', default=False),
        ipc_mode=dict(type='str'),
        keep_volumes=dict(type='bool', default=True),
        kernel_memory=dict(type='str'),
        kill_signal=dict(type='str'),
        labels=dict(type='dict'),
        links=dict(type='list'),
        log_driver=dict(type='str'),
        log_options=dict(type='dict', aliases=['log_opt']),
        mac_address=dict(type='str'),
        memory=dict(type='str', default='0'),
        memory_reservation=dict(type='str'),
        memory_swap=dict(type='str'),
        memory_swappiness=dict(type='int'),
        name=dict(type='str', required=True),
        network_mode=dict(type='str'),
        networks=dict(type='list'),
        oom_killer=dict(type='bool'),
        oom_score_adj=dict(type='int'),
        paused=dict(type='bool', default=False),
        pid_mode=dict(type='str'),
        privileged=dict(type='bool', default=False),
        published_ports=dict(type='list', aliases=['ports']),
        pull=dict(type='bool', default=False),
        purge_networks=dict(type='bool', default=False),
        read_only=dict(type='bool', default=False),
        recreate=dict(type='bool', default=False),
        restart=dict(type='bool', default=False),
        restart_policy=dict(type='str', choices=['no', 'on-failure', 'always', 'unless-stopped']),
        restart_retries=dict(type='int', default=None),
        security_opts=dict(type='list'),
        shm_size=dict(type='str'),
        state=dict(type='str', choices=['absent', 'present', 'started', 'stopped'], default='started'),
        stop_signal=dict(type='str'),
        stop_timeout=dict(type='int'),
        sysctls=dict(type='dict'),
        tmpfs=dict(type='list'),
        trust_image_content=dict(type='bool', default=False),
        tty=dict(type='bool', default=False),
        ulimits=dict(type='list'),
        user=dict(type='str'),
        userns_mode=dict(type='str'),
        uts=dict(type='str'),
        volume_driver=dict(type='str'),
        volumes=dict(type='list'),
        volumes_from=dict(type='list'),
        working_dir=dict(type='str'),
    )

    required_if = [
        ('state', 'present', ['image'])
    ]

    client = AnsibleDockerClientContainer(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True
    )

    cm = ContainerManager(client)
    client.module.exit_json(**sanitize_result(cm.results))


if __name__ == '__main__':
    main()
