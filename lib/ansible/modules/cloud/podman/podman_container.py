#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
module: podman_container
author:
  - "Sagi Shnaidman (@sshnaidm)"
version_added: '2.9'
short_description: Manage podman containers
notes: []
description:
  - Start, stop, restart and manage Podman containers
requirements:
  - "Podman installed on host"
options:
  name:
    description:
      - Name of the container
    required: True
    type: str
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the machine running C(podman)
    default: 'podman'
    type: str
  state:
    description:
      - I(absent) - A container matching the specified name will be stopped and removed.
      - I(present) - Asserts the existence of a container matching the name and any provided configuration parameters. If no
          container matches the name, a container will be created. If a container matches the name but the provided configuration
          does not match, the container will be updated, if it can be. If it cannot be updated, it will be removed and re-created
          with the requested config. Image version will be taken into account when comparing configuration. Use the recreate option
          to force the re-creation of the matching container.
      - I(started) - Asserts there is a running container matching the name and any provided configuration. If no container
          matches the name, a container will be created and started. Use recreate to always re-create a matching container, even
          if it is running. Use force_restart to force a matching container to be stopped and restarted.
      - I(stopped) - Asserts that the container is first I(present), and then if the container is running moves it to a stopped
          state.
    type: str
    default: 'started'
    choices:
      - absent
      - present
      - stopped
      - started
  image:
    description:
      - Repository path (or image name) and tag used to create the container. If an image is not found, the image
        will be pulled from the registry. If no tag is included, C(latest) will be used.
      - Can also be an image ID. If this is the case, the image is assumed to be available locally.
    type: str
  annotation:
    description:
      - Add an annotation to the container. The format is key value, multiple times.
    type: dict
  authfile:
    description:
      - Path of the authentication file. Default is ``${XDG_RUNTIME_DIR}/containers/auth.json``
        (Not available for remote commands) You can also override the default path of the authentication file
        by setting the ``REGISTRY_AUTH_FILE`` environment variable. ``export REGISTRY_AUTH_FILE=path``
    type: str
  blkio_weight:
    description:
      - Block IO weight (relative weight) accepts a weight value between 10 and 1000
    type: int
  blkio_weight_device:
    description:
      - Block IO weight (relative device weight, format DEVICE_NAME[:]WEIGHT).
    type: str
  cap_add:
    description:
      - List of capabilities to add to the container.
    type: list
  cap_drop:
    description:
      - List of capabilities to drop from the container.
    type: list
  cgroup_parent:
    description:
      - Path to cgroups under which the cgroup for the container will be created.
        If the path is not absolute, the path is considered to be relative to
        the cgroups path of the init process. Cgroups will be created if they do not already exist.
    type: str
  cidfile:
    description:
      - Write the container ID to the file
    type: str
  cmd_args:
    description:
      - Any additionl command options you want to pass to podman command, cmd_args - ['--other-param', 'value']
    type: list
  conmon_pidfile:
    description:
      - Write the pid of the conmon process to a file.
        conmon runs in a separate process than Podman,
        so this is necessary when using systemd to restart Podman containers.
    type: str
  command:
    description:
      - Override command of container
    type: raw
  cpu_period:
    description:
      - Limit the CPU real-time period in microseconds
    type: int
  cpu_rt_runtime:
    description:
      - Limit the CPU real-time runtime in microseconds
    type: int
  cpu_shares:
    description:
      - CPU shares (relative weight)
    type: int
  cpus:
    description:
      - Number of CPUs. The default is 0.0 which means no limit.
    type: str
  cpuset_cpusr:
    description:
      - CPUs in which to allow execution (0-3, 0,1)
    type: str
  cpuset_mems:
    description:
      - Memory nodes (MEMs) in which to allow execution (0-3, 0,1). Only effective on NUMA systems.
    type: str
  detach:
    description:
      - Run container in detach mode
    type: bool
    default: True
  detach_keys:
    description:
      - Override the key sequence for detaching a container. Format is a single character or ctrl-value
    type: str
  device:
    description:
      - Add a host device to the container.
        The format is <device-on-host>[:<device-on-container>][:<permissions>]
        (e.g. device /dev/sdc:/dev/xvdc:rwm)
    type: str
  device_read_bps:
    description:
      - Limit read rate (bytes per second) from a device (e.g. device-read-bps /dev/sda:1mb)
    type: str
  device_read_iops:
    description:
      - Limit read rate (IO per second) from a device (e.g. device-read-iops /dev/sda:1000)
    type: str
  device_write_bps:
    description:
      - Limit write rate (bytes per second) to a device (e.g. device-write-bps /dev/sda:1mb)
    type: str
  device_write_iops:
    description:
      - Limit write rate (IO per second) to a device (e.g. device-write-iops /dev/sda:1000)
    type: str
  dns:
    description:
      - Set custom DNS servers
    type: list
  dns_option:
    description:
      - Set custom DNS options
    type: str
  dns_search:
    description:
      - Set custom DNS search domains (Use dns_search with '' if you don't wish to set the search domain)
    type: str
  entrypoint:
    description:
      - Overwrite the default ENTRYPOINT of the image
    type: str
  env:
    description:
      - Set environment variables.
        This option allows you to specify arbitrary environment variables that
        are available for the process that will be launched inside of the container.
    type: dict
  env_file:
    description:
      - Read in a line delimited file of environment variables
    type: str
  etc_hosts:
    description:
      - Dict of host-to-IP mappings, where each host name is a key in the dictionary.
          Each host name will be added to the container's ``/etc/hosts`` file.
    type: dict
    aliases:
      - add_hosts
  expose:
    description:
      - Expose a port, or a range of ports (e.g. expose "3300-3310") to set up
        port redirection on the host system.
    type: list
    aliases:
      - exposed
      - exposed_ports
  force_restart:
    description:
      - Force restart of container.
    type: bool
    aliases:
      - restart
  gidmap:
    description:
      - Run the container in a new user namespace using the supplied mapping.
    type: str
  group_add:
    description:
      - Add additional groups to run as
    type: str
  healthcheck:
    description:
      - Set or alter a healthcheck command for a container.
    type: str
  healthcheck_interval:
    description:
      - Set an interval for the healthchecks
        (a value of disable results in no automatic timer setup) (default "30s")
    type: str
  healthcheck_retries:
    description:
      - The number of retries allowed before a healthcheck is considered to be unhealthy.
        The default value is 3.
    type: int
  healthcheck_start_period:
    description:
      - The initialization time needed for a container to bootstrap.
        The value can be expressed in time format like 2m3s. The default value is 0s
    type: str
  healthcheck_timeout:
    description:
      - The maximum time allowed to complete the healthcheck before an interval
        is considered failed. Like start-period, the value can be expressed in
        a time format such as 1m22s. The default value is 30s
    type: str
  hostname:
    description:
      - Container host name. Sets the container host name that is available inside the container.
    type: str
  http_proxy:
    description:
      - By default proxy environment variables are passed into the container if
        set for the podman process. This can be disabled by setting the http_proxy
        option to false. The environment variables passed in include http_proxy,
        https_proxy, ftp_proxy, no_proxy, and also the upper case versions of those.
        Defaults to true
    type: bool
  image_volume:
    description:
      - Tells podman how to handle the builtin image volumes.
        The options are bind, tmpfs, or ignore (default bind)
    type: str
    choices:
      - 'bind'
      - 'tmpfs'
      - 'ignore'
  init:
    description:
      - Run an init inside the container that forwards signals and reaps processes.
    type: str
  init_path:
    description:
      - Path to the container-init binary.
    type: str
  interactive:
    description:
      - Keep STDIN open even if not attached. The default is false.
        When set to true, keep stdin open even if not attached.
        The default is false.
    type: bool
  ip:
    description:
      - Specify a static IP address for the container, for example '10.88.64.128'.
        Can only be used if no additional CNI networks to join were specified via
        'network:', and if the container is not joining another container's network
        namespace via 'network container:<name|id>'.
        The address must be within the default CNI network's pool (default 10.88.0.0/16).
    type: str
  ipc:
    description:
      - Default is to create a private IPC namespace (POSIX SysV IPC) for the container
    type: str
  kernel_memory:
    description:
      - Kernel memory limit (format <number>[<unit>], where unit = b, k, m or g)
    type: str
  label:
    description:
      - Add metadata to a container, pass dictionary of label names and values
    type: dict
  label_file:
    description:
      - Read in a line delimited file of labels
    type: str
  log_opt:
    description:
      - Logging driver specific options. Used to set the path to the container log file.
        For example log_opt "path=/var/log/container/mycontainer.json"
    type: str
    aliases:
      - log_options
  memory:
    description:
      - Memory limit (format 10k, where unit = b, k, m or g)
    type: str
  memory_reservation:
    description:
      - Memory soft limit (format 100m, where unit = b, k, m or g)
    type: str
  memory_swap:
    description:
      - A limit value equal to memory plus swap. Must be used with the -m (--memory) flag.
        The swap LIMIT should always be larger than -m (--memory) value.
        By default, the swap LIMIT will be set to double the value of --memory
    type: str
  memory_swappiness:
    description:
      - Tune a container's memory swappiness behavior. Accepts an integer between 0 and 100.
    type: int
  mount:
    description:
      - Attach a filesystem mount to the container. bind or tmpfs
        For example mount "type=bind,source=/path/on/host,destination=/path/in/container"
    type: str
  network:
    description:
      - Set the Network mode for the container
        * bridge create a network stack on the default bridge
        * none no networking
        * container:<name|id> reuse another container's network stack
        * host use the podman host network stack.
        * <network-name>|<network-id> connect to a user-defined network
        * ns:<path> path to a network namespace to join
        * slirp4netns use slirp4netns to create a user network stack.
          This is the default for rootless containers
    type: str
    aliases:
      - net
  no_hosts:
    description:
      - Do not create /etc/hosts for the container
    type: bool
  oom_kill_disable:
    description:
      - Whether to disable OOM Killer for the container or not.
    type: bool
  oom_score_adj:
    description:
      - Tune the host's OOM preferences for containers (accepts -1000 to 1000)
    type: int
  pid:
    description:
      - Set the PID mode for the container
    type: str
  pids_limit:
    description:
      - Tune the container's pids limit. Set -1 to have unlimited pids for the container.
    type: str
  pod:
    description:
      - Run container in an existing pod.
        If you want podman to make the pod for you, preference the pod name with "new:"
    type: str
  privileged:
    description:
      - Give extended privileges to this container. The default is false.
    type: bool
  publish:
    description:
      - Publish a container's port, or range of ports, to the host.
        Format - ip:hostPort:containerPort | ip::containerPort | hostPort:containerPort | containerPort
    type: list
    aliases:
      - ports
      - published
      - published_ports
  publish_all:
    description:
      - Publish all exposed ports to random ports on the host interfaces. The default is false.
    type: bool
  read_only:
    description:
      - Mount the container's root filesystem as read only.
    type: bool
  read_only_tmpfs:
    description:
      - If container is running in --read-only mode, then mount a read-write tmpfs on /run, /tmp, and /var/tmp. The default is true
    type: bool
  recreate:
    description:
      - Use with present and started states to force the re-creation of an existing container.
    type: bool
  restart_policy:
    description:
      - Restart policy to follow when containers exit.
        Restart policy will not take effect if a container is stopped via the
        podman kill or podman stop commands. Valid values are
        * no - Do not restart containers on exit
        * on-failure[:max_retries] - Restart containers when they exit with a non-0 exit code, retrying indefinitely
          or until the optional max_retries count is hit
        * always - Restart containers when they exit, regardless of status, retrying indefinitely
    type: str
  rm:
    description:
      - Automatically remove the container when it exits. The default is false.
    type: bool
    aliases:
      - remove
  rootfs:
    description:
      - If true, the first argument refers to an exploded container on the file system.
    type: bool
  security_opt:
    description:
      - Security Options. For example security_opt "seccomp=unconfined"
    type: str
  shm_size:
    description:
      - Size of /dev/shm. The format is <number><unit>. number must be greater than 0.
        Unit is optional and can be b (bytes), k (kilobytes), m(megabytes), or g (gigabytes).
        If you omit the unit, the system uses bytes. If you omit the size entirely, the system uses 64m
    type: str
  sig_proxy:
    description:
      - Proxy signals sent to the podman run command to the container process.
        SIGCHLD, SIGSTOP, and SIGKILL are not proxied. The default is true.
    type: bool
  stop_signal:
    description:
      - Signal to stop a container. Default is SIGTERM.
    type: str
  stop_timeout:
    description:
      - Timeout (in seconds) to stop a container. Default is 10.
    type: int
  subgidname:
    description:
      - Run the container in a new user namespace using the map with 'name' in the /etc/subgid file.
    type: str
  subuidname:
    description:
      - Run the container in a new user namespace using the map with 'name' in the /etc/subuid file.
    type: str
  sysctl:
    description:
      - Configure namespaced kernel parameters at runtime
    type: str
  systemd:
    description:
      - Run container in systemd mode. The default is true.
    type: bool
  tmpfs:
    description:
      - Create a tmpfs mount. For example tmpfs "/tmp:rw,size=787448k,mode=1777"
    type: str
  tty:
    description:
      - Allocate a pseudo-TTY. The default is false.
    type: bool
  uidmap:
    description:
      - Run the container in a new user namespace using the supplied mapping.
    type: str
  ulimit:
    description:
      - Ulimit options
    type: str
  user:
    description:
      - Sets the username or UID used and optionally the groupname or GID for the specified command.
    type: str
  userns:
    description:
      - Set the user namespace mode for the container.
        It defaults to the PODMAN_USERNS environment variable.
        An empty value means user namespaces are disabled.
    type: str
  uts:
    description:
      - Set the UTS mode for the container
    type: str
  volume:
    description:
      - Create a bind mount. If you specify, volume /HOST-DIR:/CONTAINER-DIR,
        podman bind mounts /HOST-DIR in the host to /CONTAINER-DIR in the podman container.
    type: list
    aliases:
      - volumes
  volumes_from:
    description:
      - Mount volumes from the specified container(s).
    type: list
  workdir:
    description:
      - Working directory inside the container.
        The default working directory for running binaries within a container is the root directory (/).
    type: str
"""

EXAMPLES = """
- name: Run container
  podman_container:
    name: container
    image: quay.io/bitnami/wildfly
    state: started

- name: Create a data container
  podman_container:
    name: mydata
    image: busybox
    volume:
      - /tmp/data

- name: Re-create a redis container
  podman_container:
    name: myredis
    image: redis
    command: redis-server --appendonly yes
    state: present
    recreate: yes
    expose:
      - 6379
    volumes_from:
      - mydata

- name: Restart a container
  podman_container:
    name: myapplication
    image: redis
    state: started
    restart: yes
    etc_hosts:
        other: "127.0.0.1"
    restart_policy: "no"
    device: "/dev/sda:/dev/xvda:rwm"
    ports:
        - "8080:9000"
        - "127.0.0.1:8081:9001/udp"
    env:
        SECRET_KEY: "ssssh"
        BOOLEAN_KEY: "yes"

- name: Container present
  podman_container:
    name: mycontainer
    state: present
    image: ubuntu:14.04
    command: "sleep 1d"

- name: Stop a container
  podman_container:
    name: mycontainer
    state: stopped

- name: Start 4 load-balanced containers
  podman_container:
    name: "container{{ item }}"
    recreate: yes
    image: someuser/anotherappimage
    command: sleep 1d
  with_sequence: count=4

- name: remove container
  podman_container:
    name: ohno
    state: absent

- name: Writing output
  podman_container:
    name: myservice
    image: busybox
    log_options: path=/var/log/container/mycontainer.json
"""

RETURN = """
container:
    description:
      - Facts representing the current state of the container. Matches the podman inspection output.
      - Note that facts are part of the registered vars since Ansible 2.8. For compatibility reasons, the facts
        are also accessible directly as C(podman_container). Note that the returned fact will be removed in Ansible 2.12.
      - Empty if C(state) is I(absent).
      - If detached is I(False), will include Output attribute containing any output from container run.
    returned: always
    type: dict
    sample: '{
        "AppArmorProfile": "",
        "Args": [
            "sh"
        ],
        "BoundingCaps": [
            "CAP_CHOWN",
            ...
        ],
        "Config": {
            "Annotations": {
                "io.kubernetes.cri-o.ContainerType": "sandbox",
                "io.kubernetes.cri-o.TTY": "false"
            },
            "AttachStderr": false,
            "AttachStdin": false,
            "AttachStdout": false,
            "Cmd": [
                "sh"
            ],
            "Domainname": "",
            "Entrypoint": "",
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "TERM=xterm",
                "HOSTNAME=",
                "container=podman"
            ],
            "Hostname": "",
            "Image": "docker.io/library/busybox:latest",
            "Labels": null,
            "OpenStdin": false,
            "StdinOnce": false,
            "StopSignal": 15,
            "Tty": false,
            "User": {
                "gid": 0,
                "uid": 0
            },
            "Volumes": null,
            "WorkingDir": "/"
        },
        "ConmonPidFile": "...",
        "Created": "2019-06-17T19:13:09.873858307+03:00",
        "Dependencies": [],
        "Driver": "overlay",
        "EffectiveCaps": [
            "CAP_CHOWN",
            ...
        ],
        "ExecIDs": [],
        "ExitCommand": [
            "/usr/bin/podman",
            "--root",
            ...
        ],
        "GraphDriver": {
            ...
        },
        "HostConfig": {
            ...
        },
        "HostnamePath": "...",
        "HostsPath": "...",
        "ID": "...",
        "Image": "...",
        "ImageName": "docker.io/library/busybox:latest",
        "IsInfra": false,
        "LogPath": "/tmp/container/mycontainer.json",
        "MountLabel": "system_u:object_r:container_file_t:s0:c282,c782",
        "Mounts": [
            ...
        ],
        "Name": "myservice",
        "Namespace": "",
        "NetworkSettings": {
            "Bridge": "",
            ...
        },
        "Path": "sh",
        "ProcessLabel": "system_u:system_r:container_t:s0:c282,c782",
        "ResolvConfPath": "...",
        "RestartCount": 0,
        "Rootfs": "",
        "State": {
            "Dead": false,
            "Error": "",
            "ExitCode": 0,
            "FinishedAt": "2019-06-17T19:13:10.157518963+03:00",
            "Healthcheck": {
                "FailingStreak": 0,
                "Log": null,
                "Status": ""
            },
            "OOMKilled": false,
            "OciVersion": "1.0.1-dev",
            "Paused": false,
            "Pid": 4083,
            "Restarting": false,
            "Running": false,
            "StartedAt": "2019-06-17T19:13:10.152479729+03:00",
            "Status": "exited"
        },
        "StaticDir": "..."
            ...
    }'
"""

import json

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.podman.common import run_podman_command
from ansible.module_utils._text import to_bytes, to_native


def construct_command_from_params(action, params):
    """Creates list of arguments for podman CLI command

    Arguments:
        action {str} -- action type from 'run', 'stop', 'create', 'delete', 'start'
        params {dict} -- dictionary of module parameters

    Returns:
        list -- list of byte strings for Popen command
    """
    if action == 'start':
        cmd = ['start', params['name']]
        return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]

    if action == 'stop':
        cmd = ['stop', params['name']]
        return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]

    if action == 'delete':
        cmd = ['rm', '-f', params['name']]
        return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]

    if action in ['create', 'run']:
        cmd = [action, '--name', params['name']]

        if params['detach']:
            cmd += ['--detach']

        for host_ip in params['etc_hosts'].items():
            cmd += ['--add-host', ':'.join(host_ip)]

        for annotate in params['annotation'].items():
            cmd += ['--annotation', '='.join(annotate)]
        # Another thousand parameters

        if params['blkio_weight'] is not None:
            cmd += ['--blkio-weight', params['blkio_weight']]

        if params['blkio_weight_device']:
            cmd += ['--blkio-weight-device', params['blkio_weight_device']]

        for cap_add in params['cap_add']:
            cmd += ['--cap-add', cap_add]

        for cap_drop in params['cap_drop']:
            cmd += ['--cap-drop', cap_drop]

        if params['cgroup_parent']:
            cmd += ['--cgroup-parent', params['cgroup_parent']]

        if params['cidfile']:
            cmd += ['--cidfile', params['cidfile']]

        if params['conmon_pidfile']:
            cmd += ['--conmon-pidfile', params['conmon_pidfile']]

        if params['cpu_period']:
            cmd += ['--cpu-period', params['cpu_period']]

        if params['cpu_rt_runtime'] is not None:
            cmd += ['--cpu-rt-runtime', params['cpu_rt_runtime']]

        if params['cpu_shares'] is not None:
            cmd += ['--cpu-shares', params['cpu_shares']]

        if params['cpus']:
            cmd += ['--cpus', params['cpus']]

        if params['cpuset_cpusr']:
            cmd += ['--cpuset-cpusr', params['cpuset_cpusr']]

        if params['cpuset_mems']:
            cmd += ['--cpuset-mems', params['cpuset_mems']]

        if params['detach_keys']:
            cmd += ['--detach-keys', params['detach_keys']]

        if params['device']:
            cmd += ['--device', params['device']]

        if params['device_read_bps']:
            cmd += ['--device-read-bps', params['device_read_bps']]

        if params['device_read_iops']:
            cmd += ['--device-read-iops', params['device_read_iops']]

        if params['device_write_bps']:
            cmd += ['--device-write-bps', params['device_write_bps']]

        if params['device_write_iops']:
            cmd += ['--device-write-iops', params['device_write_iops']]

        if params['dns']:
            cmd += ['--dns', ','.join(params['dns'])]

        if params['dns_option']:
            cmd += ['--dns-option', params['dns_option']]

        if params['dns_search'] is not None:
            cmd += ['--dns-search', params['dns_search']]

        if params['entrypoint']:
            cmd += ['--entrypoint', params['entrypoint']]

        for env_value in params['env'].items():
            cmd += ['--env', b"=".join([to_bytes(k, errors='surrogate_or_strict') for k in env_value])]

        if params['env_file']:
            cmd += ['--env-file', params['env_file']]

        for exp in params['expose']:
            cmd += ['--expose', exp]

        if params['gidmap']:
            cmd += ['--gidmap', params['gidmap']]

        if params['group_add']:
            cmd += ['--group-add', params['group_add']]

        if params['healthcheck']:
            cmd += ['--healthcheck', params['healthcheck']]

        if params['healthcheck_interval']:
            cmd += ['--healthcheck-interval', params['healthcheck_interval']]

        if params['healthcheck_retries']:
            cmd += ['--healthcheck-retries', params['healthcheck_retries']]

        if params['healthcheck_start_period']:
            cmd += ['--healthcheck-start-period', params['healthcheck_start_period']]

        if params['healthcheck_timeout']:
            cmd += ['--healthcheck-timeout', params['healthcheck_timeout']]

        if params['hostname']:
            cmd += ['--hostname', params['hostname']]

        if params['http_proxy'] is not None:
            cmd += ['--http-proxy', params['http_proxy']]

        if params['image_volume']:
            cmd += ['--image-volume', params['image_volume']]

        if params['init']:
            cmd += ['--init', params['init']]

        if params['init_path']:
            cmd += ['--init-path', params['init_path']]

        if params['interactive'] is not None:
            cmd += ['--interactive', params['interactive']]

        if params['ip']:
            cmd += ['--ip', params['ip']]

        if params['ipc']:
            cmd += ['--ipc', params['ipc']]

        if params['kernel_memory']:
            cmd += ['--kernel-memory', params['kernel_memory']]

        for label in params['label'].items():
            cmd += ['--label', '='.join(label)]

        if params['label_file']:
            cmd += ['--label-file', params['label_file']]

        if params['log_opt']:
            cmd += ['--log-opt', params['log_opt']]

        if params['memory']:
            cmd += ['--memory', params['memory']]

        if params['memory_reservation']:
            cmd += ['--memory-reservation', params['memory_reservation']]

        if params['memory_swap']:
            cmd += ['--memory-swap', params['memory_swap']]

        if params['memory_swappiness']:
            cmd += ['--memory-swappiness', params['memory_swappiness']]

        if params['mount']:
            cmd += ['--mount', params['mount']]

        if params['network']:
            cmd += ['--network', params['network']]

        if params['no_hosts'] is not None:
            cmd += ['--no-hosts', params['no_hosts']]

        if params['oom_kill_disable'] is not None:
            cmd += ['--oom-kill-disable', params['oom_kill_disable']]

        if params['oom_score_adj']:
            cmd += ['--oom-score-adj', params['oom_score_adj']]

        if params['pid']:
            cmd += ['--pid', params['pid']]

        if params['pids_limit']:
            cmd += ['--pids-limit', params['pids_limit']]

        if params['pod']:
            cmd += ['--pod', params['pod']]

        if params['privileged'] is not None:
            cmd += ['--privileged', params['privileged']]

        for pub in params['publish']:
            cmd += ['--publish', pub]

        if params['publish_all'] is not None:
            cmd += ['--publish-all', params['publish_all']]

        if params['read_only'] is not None:
            cmd += ['--read-only', params['read_only']]

        if params['read_only_tmpfs'] is not None:
            cmd += ['--read-only-tmpfs', params['read_only_tmpfs']]

        if params['restart_policy']:
            cmd += ['--restart=%s' % params['restart_policy']]

        if params['rm'] is not None:
            cmd += ['--rm', params['rm']]

        if params['rootfs'] is not None and params['rootfs']:
            cmd += ['--rootfs']

        if params['security_opt']:
            cmd += ['--security-opt', params['security_opt']]

        if params['shm_size']:
            cmd += ['--shm-size', params['shm_size']]

        if params['sig_proxy'] is not None:
            cmd += ['--sig-proxy', params['sig_proxy']]

        if params['stop_signal']:
            cmd += ['--stop-signal', params['stop_signal']]

        if params['stop_timeout']:
            cmd += ['--stop-timeout', params['stop_timeout']]

        if params['subgidname']:
            cmd += ['--subgidname', params['subgidname']]

        if params['subuidname']:
            cmd += ['--subuidname', params['subuidname']]

        if params['sysctl']:
            cmd += ['--sysctl', params['sysctl']]

        if params['systemd'] is not None:
            cmd += ['--systemd', params['systemd']]

        if params['tmpfs']:
            cmd += ['--tmpfs', params['tmpfs']]

        if params['tty'] is not None:
            cmd += ['--tty', params['tty']]

        if params['uidmap']:
            cmd += ['--uidmap', params['uidmap']]

        if params['ulimit']:
            cmd += ['--ulimit', params['ulimit']]

        if params['user']:
            cmd += ['--user', params['user']]

        if params['userns']:
            cmd += ['--userns', params['userns']]

        if params['uts']:
            cmd += ['--uts', params['uts']]

        for vol in params['volume']:
            cmd += ['--volume', vol]

        for vol in params['volumes_from']:
            cmd += ['--volumes-from', vol]

        if params['workdir']:
            cmd += ['--workdir', params['workdir']]

        # Add your own args for podman command
        if params['cmd_args']:
            cmd += params['cmd_args']

        cmd.append(params['image'])

        if params['command']:
            cmd += params['command'].split()

        return [to_bytes(i, errors='surrogate_or_strict') for i in cmd]


def ensure_image_exists(module, image):
    """If image is passed, ensure it exists, if not - pull it or fail

    Arguments:
        module {obj} -- ansible module object
        image {str} -- name of image

    Returns:
        list -- list of image actions - if it pulled or nothing was done
    """
    image_actions = []
    if not image:
        return image_actions
    rc, out, err = run_podman_command(module, args=['image', 'exists', image], ignore_errors=True)
    if rc == 0:
        return image_actions
    rc, out, err = run_podman_command(module, args=['image', 'pull', image], ignore_errors=True)
    if rc != 0:
        module.fail_json(msg="Can't pull image %s" % image, stdout=out, stderr=err)
    image_actions.append("pulled image %s" % image)
    return image_actions


class PodmanContainer:
    """Perform container tasks

    Manages podman container, inspects it and checks its current state
    """
    def __init__(self, module, name):
        """Initialize PodmanContainer class

        Arguments:
            module {obj} -- ansible module object
            name {str} -- name of container
        """

        super(PodmanContainer, self).__init__()
        self.module = module
        self.name = name
        self.info = self.get_info()

    @property
    def exists(self):
        """Check if container exists """
        return bool(self.info != {})

    @property
    def different(self):
        """Check if container is different"""
        # TODO(sshnaidm): implement difference calculation between input vars
        # and current container to understand if we need to recreate it
        return True

    @property
    def running(self):
        """Return True if container is running now"""
        return self.exists and self.info['State']['Running']

    @property
    def stopped(self):
        """Return True if container exists and is not running now"""
        return self.exists and not self.info['State']['Running']

    def get_info(self):
        """Inspect container and gather info about it"""
        rc, out, err = run_podman_command(
            module=self.module,
            args=['container', 'inspect', self.name], ignore_errors=True)
        return json.loads(out)[0] if rc == 0 else {}

    def _perform_action(self, action):
        """Perform action with container

        Arguments:
            action {str} -- action to perform - start, create, stop, run, delete
        """
        b_command = construct_command_from_params(action, self.module.params)
        self.module.log("PODMAN-DEBUG: %s" % " ".join([to_native(i) for i in b_command]))
        rc, out, err = run_podman_command(
            module=self.module,
            args=[b'container'] + b_command,
            ignore_errors=True)
        if rc != 0:
            self.module.fail_json(
                msg="Can't %s container %s" % (action, self.name),
                stdout=out, stderr=err)

    def run(self):
        """Run the container"""
        self._perform_action('run')

    def delete(self):
        """Delete the container"""
        self._perform_action('delete')

    def stop(self):
        """Stop the container"""
        self._perform_action('stop')

    def start(self):
        """Start the container"""
        self._perform_action('start')

    def create(self):
        """Create the container"""
        self._perform_action('create')

    def recreate(self):
        """Recreate the container"""
        self.delete()
        self.run()

    def restart(self):
        """Restart the container"""
        self.stop()
        self.run()


class PodmanManager:
    """Module manager class

    Defines according to parameters what actions should be applied to container
    """

    def __init__(self, module):
        """Initialize PodmanManager class

        Arguments:
            module {obj} -- ansible module object
        """

        super(PodmanManager, self).__init__()

        self.module = module
        self.results = {
            'changed': False,
            'actions': [],
            'container': {},
        }
        self.name = self.module.params['name']
        self.executable = self.module.get_bin_path(self.module.params['executable'], required=True)
        self.image = self.module.params['image']
        image_actions = ensure_image_exists(self.module, self.image)
        self.results['actions'] += image_actions
        self.state = self.module.params['state']
        self.restart = self.module.params['force_restart']
        self.recreate = self.module.params['recreate']
        self.container = PodmanContainer(self.module, self.name)

    def update_container_result(self, changed=True):
        """Inspect the current container, update results with last info and exit

        Keyword Arguments:
            changed {bool} -- whether any action was performed (default: {True})
        """
        facts = self.container.get_info()
        self.results.update({'changed': changed, 'container': facts,
                             'ansible_facts': {'podman_container': facts}})
        self.module.exit_json(**self.results)

    def make_started(self):
        """Run actions if desired state is 'started'"""
        if self.container.running and (self.container.different or self.recreate):
            self.container.recreate()
            self.results['actions'].append('recreated %s' % self.container.name)
            self.update_container_result()
        elif self.container.running and not self.container.different:
            if self.restart:
                self.container.restart()
                self.results['actions'].append('restarted %s' % self.container.name)
                self.update_container_result()
            self.module.exit_json(**self.results)
        elif not self.container.exists:
            self.container.run()
            self.results['actions'].append('started %s' % self.container.name)
            self.update_container_result()
        elif self.container.stopped and self.container.different:
            self.container.recreate()
            self.results['actions'].append('recreated %s' % self.container.name)
            self.update_container_result()
        elif self.container.stopped and not self.container.different:
            self.container.start()
            self.results['actions'].append('started %s' % self.container.name)
            self.update_container_result()

    def make_stopped(self):
        """Run actions if desired state is 'stopped'"""
        if not self.container.exists and not self.image:
            self.module.fail_json(msg='Cannot create container when image is not specified!')
        if not self.container.exists:
            self.container.create()
            self.results['actions'].append('created %s' % self.container.name)
            self.update_container_result()
        if self.container.stopped:
            self.update_container_result(changed=False)
        elif self.container.running:
            self.container.stop()
            self.results['actions'].append('stopped %s' % self.container.name)
            self.update_container_result()

    def make_absent(self):
        """Run actions if desired state is 'absent'"""
        if not self.container.exists:
            self.results.update({'changed': False})
        elif self.container.exists:
            self.container.delete()
            self.results['actions'].append('deleted %s' % self.container.name)
            self.results.update({'changed': True})
        self.results.update({'container': {},
                             'ansible_facts': {'podman_container': {}}})
        self.module.exit_json(**self.results)

    def execute(self):
        """Execute the desired action according to map of actions and states"""
        states_map = {
            'present': self.make_started,
            'started': self.make_started,
            'absent': self.make_absent,
            'stopped': self.make_stopped
        }
        process_action = states_map[self.state]
        process_action()
        self.module.fail_json(msg="Unexpected logic error happened, please contact maintainers ASAP!")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cmd_args=dict(type='list', default=[], elements='str'),
            command=dict(type='raw'),
            detach=dict(type='bool', default=True),
            executable=dict(type='str', default='podman'),
            image=dict(type='str'),
            name=dict(type='str', required=True),
            force_restart=dict(type='bool', default=False, aliases=['restart']),
            recreate=dict(type='bool', default=False),
            state=dict(type='str', default='started',
                       choices=['started', 'present', 'stopped', 'absent'],),
            etc_hosts=dict(type='dict', default={}, aliases=['add_hosts']),
            annotation=dict(type='dict', default={}),
            authfile=dict(type='str', fallback=(env_fallback, ['REGISTRY_AUTH_FILE'])),
            blkio_weight=dict(type='int'),
            blkio_weight_device=dict(type='str'),
            cap_add=dict(type='list', elements='str', default=[]),
            cap_drop=dict(type='list', elements='str', default=[]),
            cgroup_parent=dict(type='str'),
            cidfile=dict(type='str'),
            conmon_pidfile=dict(type='str'),
            cpu_period=dict(type='int'),
            cpu_rt_runtime=dict(type='int'),
            cpu_shares=dict(type='int'),
            cpus=dict(type='str'),
            cpuset_cpusr=dict(type='str'),
            cpuset_mems=dict(type='str'),
            detach_keys=dict(type='str'),
            device=dict(type='str'),
            device_read_bps=dict(type='str'),
            device_read_iops=dict(type='str'),
            device_write_bps=dict(type='str'),
            device_write_iops=dict(type='str'),
            dns=dict(type='list', elements='str', default=[]),
            dns_option=dict(type='str'),
            dns_search=dict(type='str'),
            entrypoint=dict(type='str'),
            env=dict(type='dict', default={}),
            env_file=dict(type='str'),
            expose=dict(type='list', elements='str', aliases=['exposed', 'exposed_ports'], default=[]),
            gidmap=dict(type='str'),
            group_add=dict(type='str'),
            healthcheck=dict(type='str'),
            healthcheck_interval=dict(type='str'),
            healthcheck_retries=dict(type='int'),
            healthcheck_start_period=dict(type='str'),
            healthcheck_timeout=dict(type='str'),
            hostname=dict(type='str'),
            http_proxy=dict(type='bool'),
            image_volume=dict(type='str', choices=['bind', 'tmpfs', 'ignore']),
            init=dict(type='str'),
            init_path=dict(type='str'),
            interactive=dict(type='bool'),
            ip=dict(type='str'),
            ipc=dict(type='str'),
            kernel_memory=dict(type='str'),
            label=dict(type='dict', default={}),
            label_file=dict(type='str'),
            log_opt=dict(type='str', aliases=['log_options']),
            memory=dict(type='str'),
            memory_reservation=dict(type='str'),
            memory_swap=dict(type='str'),
            memory_swappiness=dict(type='int'),
            mount=dict(type='str'),
            network=dict(type='str', aliases=['net']),
            no_hosts=dict(type='bool'),
            oom_kill_disable=dict(type='bool'),
            oom_score_adj=dict(type='int'),
            pid=dict(type='str'),
            pids_limit=dict(type='str'),
            pod=dict(type='str'),
            privileged=dict(type='bool'),
            publish=dict(type='list', elements='str', aliases=['ports', 'published', 'published_ports'], default=[]),
            publish_all=dict(type='bool'),
            read_only=dict(type='bool'),
            read_only_tmpfs=dict(type='bool'),
            restart_policy=dict(type='str'),
            rm=dict(type='bool', aliases=['remove']),
            rootfs=dict(type='bool'),
            security_opt=dict(type='str'),
            shm_size=dict(type='str'),
            sig_proxy=dict(type='bool'),
            stop_signal=dict(type='str'),
            stop_timeout=dict(type='int'),
            subuidname=dict(type='str'),
            subgidname=dict(type='str'),
            sysctl=dict(type='str'),
            systemd=dict(type='bool'),
            tmpfs=dict(type='str'),
            tty=dict(type='bool'),
            uidmap=dict(type='str'),
            ulimit=dict(type='str'),
            user=dict(type='str'),
            userns=dict(type='str'),
            uts=dict(type='str'),
            volume=dict(type='list', elements='str', aliases=['volumes'], default=[]),
            volumes_from=dict(type='list', elements='str', default=[]),
            workdir=dict(type='str'),
        ),
        mutually_exclusive=(
            ['no_hosts', 'etc_hosts'],

        ),
    )
    # work on input vars
    if module.params['state'] in ['started', 'present'] and not module.params['image']:
        module.fail_json(msg="State '%s' required image to be configured!" % module.params['state'])

    PodmanManager(module).execute()


if __name__ == '__main__':
    main()
