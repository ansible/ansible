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
  - Supports check mode. Run with C(--check) and C(--diff) to view config difference and list of actions to be taken.

version_added: "2.1"

notes:
  - For most config changes, the container needs to be recreated, i.e. the existing container has to be destroyed and
    a new one created. This can cause unexpected data loss and downtime. You can use the I(comparisons) option to
    prevent this.
  - If the module needs to recreate the container, it will only use the options provided to the module to create the
    new container (except I(image)). Therefore, always specify *all* options relevant to the container.
  - When I(restart) is set to C(true), the module will only restart the container if no config changes are detected.
    Please note that several options have default values; if the container to be restarted uses different values for
    these options, it will be recreated instead. The options with default values which can cause this are I(auto_remove),
    I(detach), I(init), I(interactive), I(memory), I(paused), I(privileged), I(read_only) and I(tty).

options:
  auto_remove:
    description:
      - Enable auto-removal of the container on daemon side when the container's process exits.
    type: bool
    default: no
    version_added: "2.4"
  blkio_weight:
    description:
      - Block IO (relative weight), between 10 and 1000.
    type: int
  capabilities:
    description:
      - List of capabilities to add to the container.
    type: list
    elements: str
  cap_drop:
    description:
      - List of capabilities to drop from the container.
    type: list
    elements: str
    version_added: "2.7"
  cleanup:
    description:
      - Use with I(detach=false) to remove the container after successful execution.
    type: bool
    default: no
    version_added: "2.2"
  command:
    description:
      - Command to execute when the container starts. A command may be either a string or a list.
      - Prior to version 2.4, strings were split on commas.
    type: raw
  comparisons:
    description:
      - Allows to specify how properties of existing containers are compared with
        module options to decide whether the container should be recreated / updated
        or not.
      - Only options which correspond to the state of a container as handled by the
        Docker daemon can be specified, as well as C(networks).
      - Must be a dictionary specifying for an option one of the keys C(strict), C(ignore)
        and C(allow_more_present).
      - If C(strict) is specified, values are tested for equality, and changes always
        result in updating or restarting. If C(ignore) is specified, changes are ignored.
      - C(allow_more_present) is allowed only for lists, sets and dicts. If it is
        specified for lists or sets, the container will only be updated or restarted if
        the module option contains a value which is not present in the container's
        options. If the option is specified for a dict, the container will only be updated
        or restarted if the module option contains a key which isn't present in the
        container's option, or if the value of a key present differs.
      - The wildcard option C(*) can be used to set one of the default values C(strict)
        or C(ignore) to *all* comparisons which are not explicitly set to other values.
      - See the examples for details.
    type: dict
    version_added: "2.8"
  cpu_period:
    description:
      - Limit CPU CFS (Completely Fair Scheduler) period.
    type: int
  cpu_quota:
    description:
      - Limit CPU CFS (Completely Fair Scheduler) quota.
    type: int
  cpuset_cpus:
    description:
      - CPUs in which to allow execution C(1,3) or C(1-3).
    type: str
  cpuset_mems:
    description:
      - Memory nodes (MEMs) in which to allow execution C(0-3) or C(0,1).
    type: str
  cpu_shares:
    description:
      - CPU shares (relative weight).
    type: int
  detach:
    description:
      - Enable detached mode to leave the container running in background.
      - If disabled, the task will reflect the status of the container run (failed if the command failed).
    type: bool
    default: yes
  devices:
    description:
      - List of host device bindings to add to the container.
      - "Each binding is a mapping expressed in the format C(<path_on_host>:<path_in_container>:<cgroup_permissions>)."
    type: list
    elements: str
  device_read_bps:
    description:
      - "List of device path and read rate (bytes per second) from device."
    type: list
    elements: dict
    suboptions:
      path:
        description:
        - Device path in the container.
        type: str
        required: yes
      rate:
        description:
        - "Device read limit in format C(<number>[<unit>])."
        - "Number is a positive integer. Unit can be one of C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
          C(T) (tebibyte), or C(P) (pebibyte)."
        - "Omitting the unit defaults to bytes."
        type: str
        required: yes
    version_added: "2.8"
  device_write_bps:
    description:
      - "List of device and write rate (bytes per second) to device."
    type: list
    elements: dict
    suboptions:
      path:
        description:
        - Device path in the container.
        type: str
        required: yes
      rate:
        description:
        - "Device read limit in format C(<number>[<unit>])."
        - "Number is a positive integer. Unit can be one of C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
          C(T) (tebibyte), or C(P) (pebibyte)."
        - "Omitting the unit defaults to bytes."
        type: str
        required: yes
    version_added: "2.8"
  device_read_iops:
    description:
      - "List of device and read rate (IO per second) from device."
    type: list
    elements: dict
    suboptions:
      path:
        description:
        - Device path in the container.
        type: str
        required: yes
      rate:
        description:
        - "Device read limit."
        - "Must be a positive integer."
        type: int
        required: yes
    version_added: "2.8"
  device_write_iops:
    description:
      - "List of device and write rate (IO per second) to device."
    type: list
    elements: dict
    suboptions:
      path:
        description:
        - Device path in the container.
        type: str
        required: yes
      rate:
        description:
        - "Device read limit."
        - "Must be a positive integer."
        type: int
        required: yes
    version_added: "2.8"
  dns_opts:
    description:
      - List of DNS options.
    type: list
    elements: str
  dns_servers:
    description:
      - List of custom DNS servers.
    type: list
    elements: str
  dns_search_domains:
    description:
      - List of custom DNS search domains.
    type: list
    elements: str
  domainname:
    description:
      - Container domainname.
    type: str
    version_added: "2.5"
  env:
    description:
      - Dictionary of key,value pairs.
      - Values which might be parsed as numbers, booleans or other types by the YAML parser must be quoted (e.g. C("true")) in order to avoid data loss.
    type: dict
  env_file:
    description:
      - Path to a file, present on the target, containing environment variables I(FOO=BAR).
      - If variable also present in I(env), then the I(env) value will override.
    type: path
    version_added: "2.2"
  entrypoint:
    description:
      - Command that overwrites the default C(ENTRYPOINT) of the image.
    type: list
    elements: str
  etc_hosts:
    description:
      - Dict of host-to-IP mappings, where each host name is a key in the dictionary.
        Each host name will be added to the container's C(/etc/hosts) file.
    type: dict
  exposed_ports:
    description:
      - List of additional container ports which informs Docker that the container
        listens on the specified network ports at runtime.
      - If the port is already exposed using C(EXPOSE) in a Dockerfile, it does not
        need to be exposed again.
    type: list
    elements: str
    aliases:
      - exposed
      - expose
  force_kill:
    description:
      - Use the kill command when stopping a running container.
    type: bool
    default: no
    aliases:
      - forcekill
  groups:
    description:
      - List of additional group names and/or IDs that the container process will run as.
    type: list
    elements: str
  healthcheck:
    description:
      - Configure a check that is run to determine whether or not containers for this service are "healthy".
      - "See the docs for the L(HEALTHCHECK Dockerfile instruction,https://docs.docker.com/engine/reference/builder/#healthcheck)
        for details on how healthchecks work."
      - "I(interval), I(timeout) and I(start_period) are specified as durations. They accept duration as a string in a format
        that look like: C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
    type: dict
    suboptions:
      test:
        description:
          - Command to run to check health.
          - Must be either a string or a list. If it is a list, the first item must be one of C(NONE), C(CMD) or C(CMD-SHELL).
        type: raw
      interval:
        description:
          - Time between running the check.
          - The default used by the Docker daemon is C(30s).
        type: str
      timeout:
        description:
          - Maximum time to allow one check to run.
          - The default used by the Docker daemon is C(30s).
        type: str
      retries:
        description:
          - Consecutive number of failures needed to report unhealthy.
          - The default used by the Docker daemon is C(3).
        type: int
      start_period:
        description:
          - Start period for the container to initialize before starting health-retries countdown.
          - The default used by the Docker daemon is C(0s).
        type: str
    version_added: "2.8"
  hostname:
    description:
      - The container's hostname.
    type: str
  ignore_image:
    description:
      - When I(state) is C(present) or C(started), the module compares the configuration of an existing
        container to requested configuration. The evaluation includes the image version. If the image
        version in the registry does not match the container, the container will be recreated. You can
        stop this behavior by setting I(ignore_image) to C(True).
      - "*Warning:* This option is ignored if C(image: ignore) or C(*: ignore) is specified in the
        I(comparisons) option."
    type: bool
    default: no
    version_added: "2.2"
  image:
    description:
      - Repository path and tag used to create the container. If an image is not found or pull is true, the image
        will be pulled from the registry. If no tag is included, C(latest) will be used.
      - Can also be an image ID. If this is the case, the image is assumed to be available locally.
        The I(pull) option is ignored for this case.
    type: str
  init:
    description:
      - Run an init inside the container that forwards signals and reaps processes.
      - This option requires Docker API >= 1.25.
    type: bool
    default: no
    version_added: "2.6"
  interactive:
    description:
      - Keep stdin open after a container is launched, even if not attached.
    type: bool
    default: no
  ipc_mode:
    description:
      - Set the IPC mode for the container.
      - Can be one of C(container:<name|id>) to reuse another container's IPC namespace or C(host) to use
        the host's IPC namespace within the container.
    type: str
  keep_volumes:
    description:
      - Retain anonymous volumes associated with a removed container.
    type: bool
    default: yes
  kill_signal:
    description:
      - Override default signal used to kill a running container.
    type: str
  kernel_memory:
    description:
      - "Kernel memory limit in format C(<number>[<unit>]). Number is a positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte). Minimum is C(4M)."
      - Omitting the unit defaults to bytes.
    type: str
  labels:
    description:
      - Dictionary of key value pairs.
    type: dict
  links:
    description:
      - List of name aliases for linked containers in the format C(container_name:alias).
      - Setting this will force container to be restarted.
    type: list
    elements: str
  log_driver:
    description:
      - Specify the logging driver. Docker uses C(json-file) by default.
      - See L(here,https://docs.docker.com/config/containers/logging/configure/) for possible choices.
    type: str
  log_options:
    description:
      - Dictionary of options specific to the chosen I(log_driver).
      - See U(https://docs.docker.com/engine/admin/logging/overview/) for details.
    type: dict
    aliases:
      - log_opt
  mac_address:
    description:
      - Container MAC address (e.g. 92:d0:c6:0a:29:33).
    type: str
  memory:
    description:
      - "Memory limit in format C(<number>[<unit>]). Number is a positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte)."
      - Omitting the unit defaults to bytes.
    type: str
    default: '0'
  memory_reservation:
    description:
      - "Memory soft limit in format C(<number>[<unit>]). Number is a positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte)."
      - Omitting the unit defaults to bytes.
    type: str
  memory_swap:
    description:
      - "Total memory limit (memory + swap) in format C(<number>[<unit>]).
        Number is a positive integer. Unit can be C(B) (byte), C(K) (kibibyte, 1024B),
        C(M) (mebibyte), C(G) (gibibyte), C(T) (tebibyte), or C(P) (pebibyte)."
      - Omitting the unit defaults to bytes.
    type: str
  memory_swappiness:
    description:
        - Tune a container's memory swappiness behavior. Accepts an integer between 0 and 100.
        - If not set, the value will be remain the same if container exists and will be inherited
          from the host machine if it is (re-)created.
    type: int
  mounts:
    version_added: "2.9"
    type: list
    elements: dict
    description:
      - Specification for mounts to be added to the container. More powerful alternative to I(volumes).
    suboptions:
      target:
        description:
          - Path inside the container.
        type: str
        required: true
      source:
        description:
          - Mount source (e.g. a volume name or a host path).
        type: str
      type:
        description:
          - The mount type.
          - Note that C(npipe) is only supported by Docker for Windows.
        type: str
        choices:
          - bind
          - npipe
          - tmpfs
          - volume
        default: volume
      read_only:
        description:
          - Whether the mount should be read-only.
        type: bool
      consistency:
        description:
          - The consistency requirement for the mount.
        type: str
        choices:
          - cached
          - consistent
          - default
          - delegated
      propagation:
        description:
          - Propagation mode. Only valid for the C(bind) type.
        type: str
        choices:
          - private
          - rprivate
          - shared
          - rshared
          - slave
          - rslave
      no_copy:
        description:
          - False if the volume should be populated with the data from the target. Only valid for the C(volume) type.
          - The default value is C(false).
        type: bool
      labels:
        description:
          - User-defined name and labels for the volume. Only valid for the C(volume) type.
        type: dict
      volume_driver:
        description:
          - Specify the volume driver. Only valid for the C(volume) type.
          - See L(here,https://docs.docker.com/storage/volumes/#use-a-volume-driver) for details.
        type: str
      volume_options:
        description:
          - Dictionary of options specific to the chosen volume_driver. See
            L(here,https://docs.docker.com/storage/volumes/#use-a-volume-driver) for details.
        type: dict
      tmpfs_size:
        description:
          - "The size for the tmpfs mount in bytes in format <number>[<unit>]."
          - "Number is a positive integer. Unit can be one of C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
             C(T) (tebibyte), or C(P) (pebibyte)."
          - "Omitting the unit defaults to bytes."
        type: str
      tmpfs_mode:
        description:
          - The permission mode for the tmpfs mount.
        type: str
  name:
    description:
      - Assign a name to a new container or match an existing container.
      - When identifying an existing container name may be a name or a long or short container ID.
    type: str
    required: yes
  network_mode:
    description:
      - Connect the container to a network. Choices are C(bridge), C(host), C(none) or C(container:<name|id>).
    type: str
  userns_mode:
    description:
      - Set the user namespace mode for the container. Currently, the only valid value are C(host) and the empty string.
    type: str
    version_added: "2.5"
  networks:
    description:
      - List of networks the container belongs to.
      - For examples of the data structure and usage see EXAMPLES below.
      - To remove a container from one or more networks, use the I(purge_networks) option.
      - Note that as opposed to C(docker run ...), M(docker_container) does not remove the default
        network if I(networks) is specified. You need to explicitly use I(purge_networks) to enforce
        the removal of the default network (and all other networks not explicitly mentioned in I(networks)).
        Alternatively, use the I(networks_cli_compatible) option, which will be enabled by default from Ansible 2.12 on.
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - The network's name.
        type: str
        required: yes
      ipv4_address:
        description:
          - The container's IPv4 address in this network.
        type: str
      ipv6_address:
        description:
          - The container's IPv6 address in this network.
        type: str
      links:
        description:
          - A list of containers to link to.
        type: list
        elements: str
      aliases:
        description:
          - List of aliases for this container in this network. These names
            can be used in the network to reach this container.
        type: list
        elements: str
    version_added: "2.2"
  networks_cli_compatible:
    description:
      - "When networks are provided to the module via the I(networks) option, the module
         behaves differently than C(docker run --network): C(docker run --network other)
         will create a container with network C(other) attached, but the default network
         not attached. This module with I(networks: {name: other}) will create a container
         with both C(default) and C(other) attached. If I(purge_networks) is set to C(yes),
         the C(default) network will be removed afterwards."
      - "If I(networks_cli_compatible) is set to C(yes), this module will behave as
         C(docker run --network) and will *not* add the default network if I(networks) is
         specified. If I(networks) is not specified, the default network will be attached."
      - "Note that docker CLI also sets I(network_mode) to the name of the first network
         added if C(--network) is specified. For more compatibility with docker CLI, you
         explicitly have to set I(network_mode) to the name of the first network you're
         adding."
      - Current value is C(no). A new default of C(yes) will be set in Ansible 2.12.
    type: bool
    version_added: "2.8"
  oom_killer:
    description:
      - Whether or not to disable OOM Killer for the container.
    type: bool
  oom_score_adj:
    description:
      - An integer value containing the score given to the container in order to tune
        OOM killer preferences.
    type: int
    version_added: "2.2"
  output_logs:
    description:
      - If set to true, output of the container command will be printed.
      - Only effective when I(log_driver) is set to C(json-file) or C(journald).
    type: bool
    default: no
    version_added: "2.7"
  paused:
    description:
      - Use with the started state to pause running processes inside the container.
    type: bool
    default: no
  pid_mode:
    description:
      - Set the PID namespace mode for the container.
      - Note that Docker SDK for Python < 2.0 only supports C(host). Newer versions of the
        Docker SDK for Python (docker) allow all values supported by the Docker daemon.
    type: str
  pids_limit:
    description:
      - Set PIDs limit for the container. It accepts an integer value.
      - Set C(-1) for unlimited PIDs.
    type: int
    version_added: "2.8"
  privileged:
    description:
      - Give extended privileges to the container.
    type: bool
    default: no
  published_ports:
    description:
      - List of ports to publish from the container to the host.
      - "Use docker CLI syntax: C(8000), C(9000:8000), or C(0.0.0.0:9000:8000), where 8000 is a
        container port, 9000 is a host port, and 0.0.0.0 is a host interface."
      - Port ranges can be used for source and destination ports. If two ranges with
        different lengths are specified, the shorter range will be used.
      - "Bind addresses must be either IPv4 or IPv6 addresses. Hostnames are *not* allowed. This
        is different from the C(docker) command line utility. Use the L(dig lookup,../lookup/dig.html)
        to resolve hostnames."
      - A value of C(all) will publish all exposed container ports to random host ports, ignoring
        any other mappings.
      - If I(networks) parameter is provided, will inspect each network to see if there exists
        a bridge network with optional parameter C(com.docker.network.bridge.host_binding_ipv4).
        If such a network is found, then published ports where no host IP address is specified
        will be bound to the host IP pointed to by C(com.docker.network.bridge.host_binding_ipv4).
        Note that the first bridge network with a C(com.docker.network.bridge.host_binding_ipv4)
        value encountered in the list of I(networks) is the one that will be used.
    type: list
    elements: str
    aliases:
      - ports
  pull:
    description:
       - If true, always pull the latest version of an image. Otherwise, will only pull an image
         when missing.
       - "*Note:* images are only pulled when specified by name. If the image is specified
         as a image ID (hash), it cannot be pulled."
    type: bool
    default: no
  purge_networks:
    description:
       - Remove the container from ALL networks not included in I(networks) parameter.
       - Any default networks such as C(bridge), if not found in I(networks), will be removed as well.
    type: bool
    default: no
    version_added: "2.2"
  read_only:
    description:
      - Mount the container's root file system as read-only.
    type: bool
    default: no
  recreate:
    description:
      - Use with present and started states to force the re-creation of an existing container.
    type: bool
    default: no
  restart:
    description:
      - Use with started state to force a matching container to be stopped and restarted.
    type: bool
    default: no
  restart_policy:
    description:
      - Container restart policy.
      - Place quotes around C(no) option.
    type: str
    choices:
      - 'no'
      - 'on-failure'
      - 'always'
      - 'unless-stopped'
  restart_retries:
    description:
      - Use with restart policy to control maximum number of restart attempts.
    type: int
  runtime:
    description:
      - Runtime to use for the container.
    type: str
    version_added: "2.8"
  shm_size:
    description:
      - "Size of C(/dev/shm) in format C(<number>[<unit>]). Number is positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte)."
      - Omitting the unit defaults to bytes. If you omit the size entirely, Docker daemon uses C(64M).
    type: str
  security_opts:
    description:
      - List of security options in the form of C("label:user:User").
    type: list
    elements: str
  state:
    description:
      - 'C(absent) - A container matching the specified name will be stopped and removed. Use I(force_kill) to kill the container
         rather than stopping it. Use I(keep_volumes) to retain anonymous volumes associated with the removed container.'
      - 'C(present) - Asserts the existence of a container matching the name and any provided configuration parameters. If no
        container matches the name, a container will be created. If a container matches the name but the provided configuration
        does not match, the container will be updated, if it can be. If it cannot be updated, it will be removed and re-created
        with the requested config.'
      - 'C(started) - Asserts that the container is first C(present), and then if the container is not running moves it to a running
        state. Use I(restart) to force a matching container to be stopped and restarted.'
      - 'C(stopped) - Asserts that the container is first C(present), and then if the container is running moves it to a stopped
        state.'
      - To control what will be taken into account when comparing configuration, see the I(comparisons) option. To avoid that the
        image version will be taken into account, you can also use the I(ignore_image) option.
      - Use the I(recreate) option to always force re-creation of a matching container, even if it is running.
      - If the container should be killed instead of stopped in case it needs to be stopped for recreation, or because I(state) is
        C(stopped), please use the I(force_kill) option. Use I(keep_volumes) to retain anonymous volumes associated with a removed container.
      - Use I(keep_volumes) to retain anonymous volumes associated with a removed container.
    type: str
    default: started
    choices:
      - absent
      - present
      - stopped
      - started
  stop_signal:
    description:
      - Override default signal used to stop the container.
    type: str
  stop_timeout:
    description:
      - Number of seconds to wait for the container to stop before sending C(SIGKILL).
        When the container is created by this module, its C(StopTimeout) configuration
        will be set to this value.
      - When the container is stopped, will be used as a timeout for stopping the
        container. In case the container has a custom C(StopTimeout) configuration,
        the behavior depends on the version of the docker daemon. New versions of
        the docker daemon will always use the container's configured C(StopTimeout)
        value if it has been configured.
    type: int
  trust_image_content:
    description:
      - If C(yes), skip image verification.
    type: bool
    default: no
  tmpfs:
    description:
      - Mount a tmpfs directory.
    type: list
    elements: str
    version_added: 2.4
  tty:
    description:
      - Allocate a pseudo-TTY.
    type: bool
    default: no
  ulimits:
    description:
      - "List of ulimit options. A ulimit is specified as C(nofile:262144:262144)."
    type: list
    elements: str
  sysctls:
    description:
      - Dictionary of key,value pairs.
    type: dict
    version_added: 2.4
  user:
    description:
      - Sets the username or UID used and optionally the groupname or GID for the specified command.
      - "Can be of the forms C(user), C(user:group), C(uid), C(uid:gid), C(user:gid) or C(uid:group)."
    type: str
  uts:
    description:
      - Set the UTS namespace mode for the container.
    type: str
  volumes:
    description:
      - List of volumes to mount within the container.
      - "Use docker CLI-style syntax: C(/host:/container[:mode])"
      - "Mount modes can be a comma-separated list of various modes such as C(ro), C(rw), C(consistent),
        C(delegated), C(cached), C(rprivate), C(private), C(rshared), C(shared), C(rslave), C(slave), and
        C(nocopy). Note that the docker daemon might not support all modes and combinations of such modes."
      - SELinux hosts can additionally use C(z) or C(Z) to use a shared or private label for the volume.
      - "Note that Ansible 2.7 and earlier only supported one mode, which had to be one of C(ro), C(rw),
        C(z), and C(Z)."
    type: list
    elements: str
  volume_driver:
    description:
      - The container volume driver.
    type: str
  volumes_from:
    description:
      - List of container names or IDs to get volumes from.
    type: list
    elements: str
  working_dir:
    description:
      - Path to the working directory.
    type: str
    version_added: "2.4"
extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation

author:
  - "Cove Schneider (@cove)"
  - "Joshua Conner (@joshuaconner)"
  - "Pavel Antonov (@softzilla)"
  - "Thomas Steinbach (@ThomasSteinbach)"
  - "Philippe Jandot (@zfil)"
  - "Daan Oosterveld (@dusdanig)"
  - "Chris Houseknecht (@chouseknecht)"
  - "Kassian Sun (@kassiansun)"
  - "Felix Fontein (@felixfontein)"

requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 1.8.0 (use L(docker-py,https://pypi.org/project/docker-py/) for Python 2.6)"
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
        SECRET_KEY: "ssssh"
        # Values which might be parsed as numbers, booleans or other types by the YAML parser need to be quoted
        BOOLEAN_KEY: "yes"

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

- name: Create a container with limited capabilities
  docker_container:
    name: sleepy
    image: ubuntu:16.04
    command: sleep infinity
    capabilities:
      - sys_time
    cap_drop:
      - all

- name: Finer container restart/update control
  docker_container:
    name: test
    image: ubuntu:18.04
    env:
      arg1: "true"
      arg2: "whatever"
    volumes:
      - /tmp:/tmp
    comparisons:
      image: ignore   # don't restart containers with older versions of the image
      env: strict   # we want precisely this environment
      volumes: allow_more_present   # if there are more volumes, that's ok, as long as `/tmp:/tmp` is there

- name: Finer container restart/update control II
  docker_container:
    name: test
    image: ubuntu:18.04
    env:
      arg1: "true"
      arg2: "whatever"
    comparisons:
      '*': ignore  # by default, ignore *all* options (including image)
      env: strict   # except for environment variables; there, we want to be strict

- name: Start container with healthstatus
  docker_container:
    name: nginx-proxy
    image: nginx:1.13
    state: started
    healthcheck:
      # Check if nginx server is healthy by curl'ing the server.
      # If this fails or timeouts, the healthcheck fails.
      test: ["CMD", "curl", "--fail", "http://nginx.host.com"]
      interval: 1m30s
      timeout: 10s
      retries: 3
      start_period: 30s

- name: Remove healthcheck from container
  docker_container:
    name: nginx-proxy
    image: nginx:1.13
    state: started
    healthcheck:
      # The "NONE" check needs to be specified
      test: ["NONE"]

- name: start container with block device read limit
  docker_container:
    name: test
    image: ubuntu:18.04
    state: started
    device_read_bps:
      # Limit read rate for /dev/sda to 20 mebibytes per second
      - path: /dev/sda
        rate: 20M
    device_read_iops:
      # Limit read rate for /dev/sdb to 300 IO per second
      - path: /dev/sdb
        rate: 300
'''

RETURN = '''
container:
    description:
      - Facts representing the current state of the container. Matches the docker inspection output.
      - Note that facts are part of the registered vars since Ansible 2.8. For compatibility reasons, the facts
        are also accessible directly as C(docker_container). Note that the returned fact will be removed in Ansible 2.12.
      - Before 2.3 this was C(ansible_docker_container) but was renamed in 2.3 to C(docker_container) due to
        conflicts with the connection plugin.
      - Empty if I(state) is C(absent)
      - If I(detached) is C(false), will include C(Output) attribute containing any output from container run.
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
import traceback
from distutils.version import LooseVersion
from time import sleep

from ansible.module_utils.common.text.formatters import human_to_bytes
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native, to_text

from ansible.module_utils.docker.common import (
    AnsibleDockerClient,
    DifferenceTracker,
    DockerBaseClass,
    compare_generic,
    is_image_name_id,
    sanitize_result,
    clean_dict_booleans_for_docker_api,
    omit_none_from_dict,
    parse_healthcheck,
    DOCKER_COMMON_ARGS,
    RequestException,
)

try:
    from docker import utils
    from ansible.module_utils.docker.common import docker_version
    if LooseVersion(docker_version) >= LooseVersion('1.10.0'):
        from docker.types import Ulimit, LogConfig
        from docker import types as docker_types
    else:
        from docker.utils.types import Ulimit, LogConfig
    from docker.errors import DockerException, APIError, NotFound
except Exception:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass


REQUIRES_CONVERSION_TO_BYTES = [
    'kernel_memory',
    'memory',
    'memory_reservation',
    'memory_swap',
    'shm_size'
]


def is_volume_permissions(mode):
    for part in mode.split(','):
        if part not in ('rw', 'ro', 'z', 'Z', 'consistent', 'delegated', 'cached', 'rprivate', 'private', 'rshared', 'shared', 'rslave', 'slave', 'nocopy'):
            return False
    return True


def parse_port_range(range_or_port, client):
    '''
    Parses a string containing either a single port or a range of ports.

    Returns a list of integers for each port in the list.
    '''
    if '-' in range_or_port:
        try:
            start, end = [int(port) for port in range_or_port.split('-')]
        except Exception:
            client.fail('Invalid port range: "{0}"'.format(range_or_port))
        if end < start:
            client.fail('Invalid port range: "{0}"'.format(range_or_port))
        return list(range(start, end + 1))
    else:
        try:
            return [int(range_or_port)]
        except Exception:
            client.fail('Invalid port: "{0}"'.format(range_or_port))


def split_colon_ipv6(text, client):
    '''
    Split string by ':', while keeping IPv6 addresses in square brackets in one component.
    '''
    if '[' not in text:
        return text.split(':')
    start = 0
    result = []
    while start < len(text):
        i = text.find('[', start)
        if i < 0:
            result.extend(text[start:].split(':'))
            break
        j = text.find(']', i)
        if j < 0:
            client.fail('Cannot find closing "]" in input "{0}" for opening "[" at index {1}!'.format(text, i + 1))
        result.extend(text[start:i].split(':'))
        k = text.find(':', j)
        if k < 0:
            result[-1] += text[i:]
            start = len(text)
        else:
            result[-1] += text[i:k]
            if k == len(text):
                result.append('')
                break
            start = k + 1
    return result


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
        self.cap_drop = None
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
        self.device_read_bps = None
        self.device_write_bps = None
        self.device_read_iops = None
        self.device_write_iops = None
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
        self.healthcheck = None
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
        self.output_logs = None
        self.log_options = None
        self.mac_address = None
        self.memory = None
        self.memory_reservation = None
        self.memory_swap = None
        self.memory_swappiness = None
        self.mounts = None
        self.name = None
        self.network_mode = None
        self.userns_mode = None
        self.networks = None
        self.networks_cli_compatible = None
        self.oom_killer = None
        self.oom_score_adj = None
        self.paused = None
        self.pid_mode = None
        self.pids_limit = None
        self.privileged = None
        self.purge_networks = None
        self.pull = None
        self.read_only = None
        self.recreate = None
        self.restart = None
        self.restart_retries = None
        self.restart_policy = None
        self.runtime = None
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

        # If state is 'absent', parameters do not have to be parsed or interpreted.
        # Only the container's name is needed.
        if self.state == 'absent':
            return

        if self.groups:
            # In case integers are passed as groups, we need to convert them to
            # strings as docker internally treats them as strings.
            self.groups = [to_text(g, errors='surrogate_or_strict') for g in self.groups]

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
        try:
            self.healthcheck, self.disable_healthcheck = parse_healthcheck(self.healthcheck)
        except ValueError as e:
            self.fail(to_native(e))

        self.exp_links = None
        self.volume_binds = self._get_volume_binds(self.volumes)
        self.pid_mode = self._replace_container_names(self.pid_mode)
        self.ipc_mode = self._replace_container_names(self.ipc_mode)
        self.network_mode = self._replace_container_names(self.network_mode)

        self.log("volumes:")
        self.log(self.volumes, pretty_print=True)
        self.log("volume binds:")
        self.log(self.volume_binds, pretty_print=True)

        if self.networks:
            for network in self.networks:
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
            self.entrypoint = ' '.join([to_text(x, errors='surrogate_or_strict') for x in self.entrypoint])

        if self.command:
            # convert from list to str
            if isinstance(self.command, list):
                self.command = ' '.join([to_text(x, errors='surrogate_or_strict') for x in self.command])

        self.mounts_opt, self.expected_mounts = self._process_mounts()

        self._check_mount_target_collisions()

        for param_name in ["device_read_bps", "device_write_bps"]:
            if client.module.params.get(param_name):
                self._process_rate_bps(option=param_name)

        for param_name in ["device_read_iops", "device_write_iops"]:
            if client.module.params.get(param_name):
                self._process_rate_iops(option=param_name)

    def fail(self, msg):
        self.client.fail(msg)

    @property
    def update_parameters(self):
        '''
        Returns parameters used to update a container
        '''

        update_parameters = dict(
            blkio_weight='blkio_weight',
            cpu_period='cpu_period',
            cpu_quota='cpu_quota',
            cpu_shares='cpu_shares',
            cpuset_cpus='cpuset_cpus',
            cpuset_mems='cpuset_mems',
            mem_limit='memory',
            mem_reservation='memory_reservation',
            memswap_limit='memory_swap',
            kernel_memory='kernel_memory',
            restart_policy='restart_policy',
        )

        result = dict()
        for key, value in update_parameters.items():
            if getattr(self, value, None) is not None:
                if key == 'restart_policy' and self.client.option_minimal_versions[value]['supported']:
                    restart_policy = dict(Name=self.restart_policy,
                                          MaximumRetryCount=self.restart_retries)
                    result[key] = restart_policy
                elif self.client.option_minimal_versions[value]['supported']:
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
            stop_timeout='stop_timeout',
            healthcheck='healthcheck',
        )

        if self.client.docker_py_version < LooseVersion('3.0'):
            # cpu_shares and volume_driver moved to create_host_config in > 3
            create_params['cpu_shares'] = 'cpu_shares'
            create_params['volume_driver'] = 'volume_driver'

        result = dict(
            host_config=self._host_config(),
            volumes=self._get_mounts(),
        )

        for key, value in create_params.items():
            if getattr(self, value, None) is not None:
                if self.client.option_minimal_versions[value]['supported']:
                    result[key] = getattr(self, value)

        if self.disable_healthcheck:
            # Make sure image's health check is overridden
            result['healthcheck'] = {'test': ['NONE']}

        if self.networks_cli_compatible and self.networks:
            network = self.networks[0]
            params = dict()
            for para in ('ipv4_address', 'ipv6_address', 'links', 'aliases'):
                if network.get(para):
                    params[para] = network[para]
            network_config = dict()
            network_config[network['name']] = self.client.create_endpoint_config(**params)
            result['networking_config'] = self.client.create_networking_config(network_config)
        return result

    def _expand_host_paths(self):
        new_vols = []
        for vol in self.volumes:
            if ':' in vol:
                if len(vol.split(':')) == 3:
                    host, container, mode = vol.split(':')
                    if not is_volume_permissions(mode):
                        self.fail('Found invalid volumes mode: {0}'.format(mode))
                    if re.match(r'[.~]', host):
                        host = os.path.abspath(os.path.expanduser(host))
                    new_vols.append("%s:%s:%s" % (host, container, mode))
                    continue
                elif len(vol.split(':')) == 2:
                    parts = vol.split(':')
                    if not is_volume_permissions(parts[1]) and re.match(r'[.~]', parts[0]):
                        host = os.path.abspath(os.path.expanduser(parts[0]))
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
                        dummy, container, dummy = vol.split(':')
                        result.append(container)
                        continue
                    if len(vol.split(':')) == 2:
                        parts = vol.split(':')
                        if not is_volume_permissions(parts[1]):
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
            cap_drop='cap_drop',
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
            init='init',
            uts_mode='uts',
            runtime='runtime',
            auto_remove='auto_remove',
            device_read_bps='device_read_bps',
            device_write_bps='device_write_bps',
            device_read_iops='device_read_iops',
            device_write_iops='device_write_iops',
            pids_limit='pids_limit',
            mounts='mounts',
        )

        if self.client.docker_py_version >= LooseVersion('1.9') and self.client.docker_api_version >= LooseVersion('1.22'):
            # blkio_weight can always be updated, but can only be set on creation
            # when Docker SDK for Python and Docker API are new enough
            host_config_params['blkio_weight'] = 'blkio_weight'

        if self.client.docker_py_version >= LooseVersion('3.0'):
            # cpu_shares and volume_driver moved to create_host_config in > 3
            host_config_params['cpu_shares'] = 'cpu_shares'
            host_config_params['volume_driver'] = 'volume_driver'

        params = dict()
        for key, value in host_config_params.items():
            if getattr(self, value, None) is not None:
                if self.client.option_minimal_versions[value]['supported']:
                    params[key] = getattr(self, value)

        if self.restart_policy:
            params['restart_policy'] = dict(Name=self.restart_policy,
                                            MaximumRetryCount=self.restart_retries)

        if 'mounts' in params:
            params['mounts'] = self.mounts_opt

        return self.client.create_host_config(**params)

    @property
    def default_host_ip(self):
        ip = '0.0.0.0'
        if not self.networks:
            return ip
        for net in self.networks:
            if net.get('name'):
                try:
                    network = self.client.inspect_network(net['name'])
                    if network.get('Driver') == 'bridge' and \
                       network.get('Options', {}).get('com.docker.network.bridge.host_binding_ipv4'):
                        ip = network['Options']['com.docker.network.bridge.host_binding_ipv4']
                        break
                except NotFound as nfe:
                    self.client.fail(
                        "Cannot inspect the network '{0}' to determine the default IP: {1}".format(net['name'], nfe),
                        exception=traceback.format_exc()
                    )
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
            parts = split_colon_ipv6(to_text(port, errors='surrogate_or_strict'), self.client)
            container_port = parts[-1]
            protocol = ''
            if '/' in container_port:
                container_port, protocol = parts[-1].split('/')
            container_ports = parse_port_range(container_port, self.client)

            p_len = len(parts)
            if p_len == 1:
                port_binds = len(container_ports) * [(default_ip,)]
            elif p_len == 2:
                port_binds = [(default_ip, port) for port in parse_port_range(parts[0], self.client)]
            elif p_len == 3:
                # We only allow IPv4 and IPv6 addresses for the bind address
                ipaddr = parts[0]
                if not re.match(r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$', parts[0]) and not re.match(r'^\[[0-9a-fA-F:]+\]$', ipaddr):
                    self.fail(('Bind addresses for published ports must be IPv4 or IPv6 addresses, not hostnames. '
                               'Use the dig lookup to resolve hostnames. (Found hostname: {0})').format(ipaddr))
                if re.match(r'^\[[0-9a-fA-F:]+\]$', ipaddr):
                    ipaddr = ipaddr[1:-1]
                if parts[1]:
                    port_binds = [(ipaddr, port) for port in parse_port_range(parts[1], self.client)]
                else:
                    port_binds = len(container_ports) * [(ipaddr,)]

            for bind, container_port in zip(port_binds, container_ports):
                idx = '{0}/{1}'.format(container_port, protocol) if protocol else container_port
                if idx in binds:
                    old_bind = binds[idx]
                    if isinstance(old_bind, list):
                        old_bind.append(bind)
                    else:
                        binds[idx] = [old_bind, bind]
                else:
                    binds[idx] = bind
        return binds

    def _get_volume_binds(self, volumes):
        '''
        Extract host bindings, if any, from list of volume mapping strings.

        :return: dictionary of bind mappings
        '''
        result = dict()
        if volumes:
            for vol in volumes:
                host = None
                if ':' in vol:
                    parts = vol.split(':')
                    if len(parts) == 3:
                        host, container, mode = parts
                        if not is_volume_permissions(mode):
                            self.fail('Found invalid volumes mode: {0}'.format(mode))
                    elif len(parts) == 2:
                        if not is_volume_permissions(parts[1]):
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
                port = to_text(port, errors='surrogate_or_strict').strip()
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
                    if exposed_port[1] != protocol:
                        continue
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
                if not isinstance(v, string_types):
                    self.client.module.warn(
                        "Non-string value found for log_options option '%s'. The value is automatically converted to '%s'. "
                        "If this is not correct, or you want to avoid such warnings, please quote the value." % (
                            k, to_text(v, errors='surrogate_or_strict'))
                    )
                v = to_text(v, errors='surrogate_or_strict')
                self.log_options[k] = v
                options['Config'][k] = v

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
                final_env[name] = to_text(value, errors='surrogate_or_strict')
        if self.env:
            for name, value in self.env.items():
                if not isinstance(value, string_types):
                    self.fail("Non-string value found for env option. Ambiguous env options must be "
                              "wrapped in quotes to avoid them being interpreted. Key: %s" % (name, ))
                final_env[name] = to_text(value, errors='surrogate_or_strict')
        return final_env

    def _get_network_id(self, network_name):
        network_id = None
        try:
            for network in self.client.networks(names=[network_name]):
                if network['Name'] == network_name:
                    network_id = network['Id']
                    break
        except Exception as exc:
            self.fail("Error getting network id for %s - %s" % (network_name, to_native(exc)))
        return network_id

    def _process_mounts(self):
        if self.mounts is None:
            return None, None
        mounts_list = []
        mounts_expected = []
        for mount in self.mounts:
            target = mount['target']
            datatype = mount['type']
            mount_dict = dict(mount)
            # Sanity checks (so we don't wait for docker-py to barf on input)
            if mount_dict.get('source') is None and datatype != 'tmpfs':
                self.client.fail('source must be specified for mount "{0}" of type "{1}"'.format(target, datatype))
            mount_option_types = dict(
                volume_driver='volume',
                volume_options='volume',
                propagation='bind',
                no_copy='volume',
                labels='volume',
                tmpfs_size='tmpfs',
                tmpfs_mode='tmpfs',
            )
            for option, req_datatype in mount_option_types.items():
                if mount_dict.get(option) is not None and datatype != req_datatype:
                    self.client.fail('{0} cannot be specified for mount "{1}" of type "{2}" (needs type "{3}")'.format(option, target, datatype, req_datatype))
            # Handle volume_driver and volume_options
            volume_driver = mount_dict.pop('volume_driver')
            volume_options = mount_dict.pop('volume_options')
            if volume_driver:
                if volume_options:
                    volume_options = clean_dict_booleans_for_docker_api(volume_options)
                mount_dict['driver_config'] = docker_types.DriverConfig(name=volume_driver, options=volume_options)
            if mount_dict['labels']:
                mount_dict['labels'] = clean_dict_booleans_for_docker_api(mount_dict['labels'])
            if mount_dict.get('tmpfs_size') is not None:
                try:
                    mount_dict['tmpfs_size'] = human_to_bytes(mount_dict['tmpfs_size'])
                except ValueError as exc:
                    self.fail('Failed to convert tmpfs_size of mount "{0}" to bytes: {1}'.format(target, exc))
            if mount_dict.get('tmpfs_mode') is not None:
                try:
                    mount_dict['tmpfs_mode'] = int(mount_dict['tmpfs_mode'], 8)
                except Exception as dummy:
                    self.client.fail('tmp_fs mode of mount "{0}" is not an octal string!'.format(target))
            # Fill expected mount dict
            mount_expected = dict(mount)
            mount_expected['tmpfs_size'] = mount_dict['tmpfs_size']
            mount_expected['tmpfs_mode'] = mount_dict['tmpfs_mode']
            # Add result to lists
            mounts_list.append(docker_types.Mount(**mount_dict))
            mounts_expected.append(omit_none_from_dict(mount_expected))
        return mounts_list, mounts_expected

    def _process_rate_bps(self, option):
        """
        Format device_read_bps and device_write_bps option
        """
        devices_list = []
        for v in getattr(self, option):
            device_dict = dict((x.title(), y) for x, y in v.items())
            device_dict['Rate'] = human_to_bytes(device_dict['Rate'])
            devices_list.append(device_dict)

        setattr(self, option, devices_list)

    def _process_rate_iops(self, option):
        """
        Format device_read_iops and device_write_iops option
        """
        devices_list = []
        for v in getattr(self, option):
            device_dict = dict((x.title(), y) for x, y in v.items())
            devices_list.append(device_dict)

        setattr(self, option, devices_list)

    def _replace_container_names(self, mode):
        """
        Parse IPC and PID modes. If they contain a container name, replace
        with the container's ID.
        """
        if mode is None or not mode.startswith('container:'):
            return mode
        container_name = mode[len('container:'):]
        # Try to inspect container to see whether this is an ID or a
        # name (and in the latter case, retrieve it's ID)
        container = self.client.get_container(container_name)
        if container is None:
            # If we can't find the container, issue a warning and continue with
            # what the user specified.
            self.client.module.warn('Cannot find a container with name or ID "{0}"'.format(container_name))
            return mode
        return 'container:{0}'.format(container['Id'])

    def _check_mount_target_collisions(self):
        last = dict()

        def f(t, name):
            if t in last:
                if name == last[t]:
                    self.client.fail('The mount point "{0}" appears twice in the {1} option'.format(t, name))
                else:
                    self.client.fail('The mount point "{0}" appears both in the {1} and {2} option'.format(t, name, last[t]))
            last[t] = name

        if self.expected_mounts:
            for t in [m['target'] for m in self.expected_mounts]:
                f(t, 'mounts')
        if self.volumes:
            for v in self.volumes:
                vs = v.split(':')
                f(vs[0 if len(vs) == 1 else 1], 'volumes')


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
        self.parameters_map['expected_healthcheck'] = 'healthcheck'
        self.parameters_map['expected_mounts'] = 'mounts'

    def fail(self, msg):
        self.parameters.client.fail(msg)

    @property
    def exists(self):
        return True if self.container else False

    @property
    def removing(self):
        if self.container and self.container.get('State'):
            return self.container['State'].get('Status') == 'removing'
        return False

    @property
    def running(self):
        if self.container and self.container.get('State'):
            if self.container['State'].get('Running') and not self.container['State'].get('Ghost', False):
                return True
        return False

    @property
    def paused(self):
        if self.container and self.container.get('State'):
            return self.container['State'].get('Paused', False)
        return False

    def _compare(self, a, b, compare):
        '''
        Compare values a and b as described in compare.
        '''
        return compare_generic(a, b, compare['comparison'], compare['type'])

    def _decode_mounts(self, mounts):
        if not mounts:
            return mounts
        result = []
        empty_dict = dict()
        for mount in mounts:
            res = dict()
            res['type'] = mount.get('Type')
            res['source'] = mount.get('Source')
            res['target'] = mount.get('Target')
            res['read_only'] = mount.get('ReadOnly', False)  # golang's omitempty for bool returns None for False
            res['consistency'] = mount.get('Consistency')
            res['propagation'] = mount.get('BindOptions', empty_dict).get('Propagation')
            res['no_copy'] = mount.get('VolumeOptions', empty_dict).get('NoCopy', False)
            res['labels'] = mount.get('VolumeOptions', empty_dict).get('Labels', empty_dict)
            res['volume_driver'] = mount.get('VolumeOptions', empty_dict).get('DriverConfig', empty_dict).get('Name')
            res['volume_options'] = mount.get('VolumeOptions', empty_dict).get('DriverConfig', empty_dict).get('Options', empty_dict)
            res['tmpfs_size'] = mount.get('TmpfsOptions', empty_dict).get('SizeBytes')
            res['tmpfs_mode'] = mount.get('TmpfsOptions', empty_dict).get('Mode')
            result.append(res)
        return result

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
        self.parameters.expected_healthcheck = self._get_expected_healthcheck()

        if not self.container.get('HostConfig'):
            self.fail("has_config_diff: Error parsing container properties. HostConfig missing.")
        if not self.container.get('Config'):
            self.fail("has_config_diff: Error parsing container properties. Config missing.")
        if not self.container.get('NetworkSettings'):
            self.fail("has_config_diff: Error parsing container properties. NetworkSettings missing.")

        host_config = self.container['HostConfig']
        log_config = host_config.get('LogConfig', dict())
        config = self.container['Config']
        network = self.container['NetworkSettings']

        # The previous version of the docker module ignored the detach state by
        # assuming if the container was running, it must have been detached.
        detach = not (config.get('AttachStderr') and config.get('AttachStdout'))

        # "ExposedPorts": null returns None type & causes AttributeError - PR #5517
        if config.get('ExposedPorts') is not None:
            expected_exposed = [self._normalize_port(p) for p in config.get('ExposedPorts', dict()).keys()]
        else:
            expected_exposed = []

        # Map parameters to container inspect results
        config_mapping = dict(
            expected_cmd=config.get('Cmd'),
            domainname=config.get('Domainname'),
            hostname=config.get('Hostname'),
            user=config.get('User'),
            detach=detach,
            init=host_config.get('Init'),
            interactive=config.get('OpenStdin'),
            capabilities=host_config.get('CapAdd'),
            cap_drop=host_config.get('CapDrop'),
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
            runtime=host_config.get('Runtime'),
            shm_size=host_config.get('ShmSize'),
            security_opts=host_config.get("SecurityOpt"),
            stop_signal=config.get("StopSignal"),
            tmpfs=host_config.get('Tmpfs'),
            tty=config.get('Tty'),
            expected_ulimits=host_config.get('Ulimits'),
            expected_sysctls=host_config.get('Sysctls'),
            uts=host_config.get('UTSMode'),
            expected_volumes=config.get('Volumes'),
            expected_binds=host_config.get('Binds'),
            volume_driver=host_config.get('VolumeDriver'),
            volumes_from=host_config.get('VolumesFrom'),
            working_dir=config.get('WorkingDir'),
            publish_all_ports=host_config.get('PublishAllPorts'),
            expected_healthcheck=config.get('Healthcheck'),
            disable_healthcheck=(not config.get('Healthcheck') or config.get('Healthcheck').get('Test') == ['NONE']),
            device_read_bps=host_config.get('BlkioDeviceReadBps'),
            device_write_bps=host_config.get('BlkioDeviceWriteBps'),
            device_read_iops=host_config.get('BlkioDeviceReadIOps'),
            device_write_iops=host_config.get('BlkioDeviceWriteIOps'),
            pids_limit=host_config.get('PidsLimit'),
            # According to https://github.com/moby/moby/, support for HostConfig.Mounts
            # has been included at least since v17.03.0-ce, which has API version 1.26.
            # The previous tag, v1.9.1, has API version 1.21 and does not have
            # HostConfig.Mounts. I have no idea what about API 1.25...
            expected_mounts=self._decode_mounts(host_config.get('Mounts')),
        )
        # Options which don't make sense without their accompanying option
        if self.parameters.log_driver:
            config_mapping['log_driver'] = log_config.get('Type')
            config_mapping['log_options'] = log_config.get('Config')

        if self.parameters.client.option_minimal_versions['auto_remove']['supported']:
            # auto_remove is only supported in Docker SDK for Python >= 2.0.0; unfortunately
            # it has a default value, that's why we have to jump through the hoops here
            config_mapping['auto_remove'] = host_config.get('AutoRemove')

        if self.parameters.client.option_minimal_versions['stop_timeout']['supported']:
            # stop_timeout is only supported in Docker SDK for Python >= 2.1. Note that
            # stop_timeout has a hybrid role, in that it used to be something only used
            # for stopping containers, and is now also used as a container property.
            # That's why it needs special handling here.
            config_mapping['stop_timeout'] = config.get('StopTimeout')

        if self.parameters.client.docker_api_version < LooseVersion('1.22'):
            # For docker API < 1.22, update_container() is not supported. Thus
            # we need to handle all limits which are usually handled by
            # update_container() as configuration changes which require a container
            # restart.
            restart_policy = host_config.get('RestartPolicy', dict())

            # Options which don't make sense without their accompanying option
            if self.parameters.restart_policy:
                config_mapping['restart_retries'] = restart_policy.get('MaximumRetryCount')

            config_mapping.update(dict(
                blkio_weight=host_config.get('BlkioWeight'),
                cpu_period=host_config.get('CpuPeriod'),
                cpu_quota=host_config.get('CpuQuota'),
                cpu_shares=host_config.get('CpuShares'),
                cpuset_cpus=host_config.get('CpusetCpus'),
                cpuset_mems=host_config.get('CpusetMems'),
                kernel_memory=host_config.get("KernelMemory"),
                memory=host_config.get('Memory'),
                memory_reservation=host_config.get('MemoryReservation'),
                memory_swap=host_config.get('MemorySwap'),
                restart_policy=restart_policy.get('Name')
            ))

        differences = DifferenceTracker()
        for key, value in config_mapping.items():
            minimal_version = self.parameters.client.option_minimal_versions.get(key, {})
            if not minimal_version.get('supported', True):
                continue
            compare = self.parameters.client.comparisons[self.parameters_map.get(key, key)]
            self.log('check differences %s %s vs %s (%s)' % (key, getattr(self.parameters, key), to_text(value, errors='surrogate_or_strict'), compare))
            if getattr(self.parameters, key, None) is not None:
                match = self._compare(getattr(self.parameters, key), value, compare)

                if not match:
                    if key == 'expected_healthcheck' and config_mapping['disable_healthcheck'] and self.parameters.disable_healthcheck:
                        # If the healthcheck is disabled (both in parameters and for the current container), and the user
                        # requested strict comparison for healthcheck, the comparison will fail. That's why we ignore the
                        # expected_healthcheck comparison in this case.
                        continue

                    # no match. record the differences
                    p = getattr(self.parameters, key)
                    c = value
                    if compare['type'] == 'set':
                        # Since the order does not matter, sort so that the diff output is better.
                        if p is not None:
                            p = sorted(p)
                        if c is not None:
                            c = sorted(c)
                    elif compare['type'] == 'set(dict)':
                        # Since the order does not matter, sort so that the diff output is better.
                        if key == 'expected_mounts':
                            # For selected values, use one entry as key
                            def sort_key_fn(x):
                                return x['target']
                        else:
                            # We sort the list of dictionaries by using the sorted items of a dict as its key.
                            def sort_key_fn(x):
                                return sorted((a, to_text(b, errors='surrogate_or_strict')) for a, b in x.items())
                        if p is not None:
                            p = sorted(p, key=sort_key_fn)
                        if c is not None:
                            c = sorted(c, key=sort_key_fn)
                    differences.add(key, parameter=p, active=c)

        has_differences = not differences.empty
        return has_differences, differences

    def has_different_resource_limits(self):
        '''
        Diff parameters and container resource limits
        '''
        if not self.container.get('HostConfig'):
            self.fail("limits_differ_from_container: Error parsing container properties. HostConfig missing.")
        if self.parameters.client.docker_api_version < LooseVersion('1.22'):
            # update_container() call not supported
            return False, []

        host_config = self.container['HostConfig']

        restart_policy = host_config.get('RestartPolicy') or dict()

        config_mapping = dict(
            blkio_weight=host_config.get('BlkioWeight'),
            cpu_period=host_config.get('CpuPeriod'),
            cpu_quota=host_config.get('CpuQuota'),
            cpu_shares=host_config.get('CpuShares'),
            cpuset_cpus=host_config.get('CpusetCpus'),
            cpuset_mems=host_config.get('CpusetMems'),
            kernel_memory=host_config.get("KernelMemory"),
            memory=host_config.get('Memory'),
            memory_reservation=host_config.get('MemoryReservation'),
            memory_swap=host_config.get('MemorySwap'),
            restart_policy=restart_policy.get('Name')
        )

        # Options which don't make sense without their accompanying option
        if self.parameters.restart_policy:
            config_mapping['restart_retries'] = restart_policy.get('MaximumRetryCount')

        differences = DifferenceTracker()
        for key, value in config_mapping.items():
            if getattr(self.parameters, key, None):
                compare = self.parameters.client.comparisons[self.parameters_map.get(key, key)]
                match = self._compare(getattr(self.parameters, key), value, compare)

                if not match:
                    # no match. record the differences
                    differences.add(key, parameter=getattr(self.parameters, key), active=value)
        different = not differences.empty
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
            network_info = connected_networks.get(network['name'])
            if network_info is None:
                different = True
                differences.append(dict(
                    parameter=network,
                    container=None
                ))
            else:
                diff = False
                network_info_ipam = network_info.get('IPAMConfig') or {}
                if network.get('ipv4_address') and network['ipv4_address'] != network_info_ipam.get('IPv4Address'):
                    diff = True
                if network.get('ipv6_address') and network['ipv6_address'] != network_info_ipam.get('IPv6Address'):
                    diff = True
                if network.get('aliases'):
                    if not compare_generic(network['aliases'], network_info.get('Aliases'), 'allow_more_present', 'set'):
                        diff = True
                if network.get('links'):
                    expected_links = []
                    for link, alias in network['links']:
                        expected_links.append("%s:%s" % (link, alias))
                    if not compare_generic(expected_links, network_info.get('Links'), 'allow_more_present', 'set'):
                        diff = True
                if diff:
                    different = True
                    differences.append(dict(
                        parameter=network,
                        container=dict(
                            name=network['name'],
                            ipv4_address=network_info_ipam.get('IPv4Address'),
                            ipv6_address=network_info_ipam.get('IPv6Address'),
                            aliases=network_info.get('Aliases'),
                            links=network_info.get('Links')
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
                    expected_bound_ports[container_port].append({'HostIp': host_ip, 'HostPort': to_text(host_port, errors='surrogate_or_strict')})
            else:
                expected_bound_ports[container_port] = [{'HostIp': config[0], 'HostPort': to_text(config[1], errors='surrogate_or_strict')}]
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
            image_vols = self._get_image_binds(image[self.parameters.client.image_inspect_source].get('Volumes'))
        param_vols = []
        if self.parameters.volumes:
            for vol in self.parameters.volumes:
                host = None
                if ':' in vol:
                    if len(vol.split(':')) == 3:
                        host, container, mode = vol.split(':')
                        if not is_volume_permissions(mode):
                            self.fail('Found invalid volumes mode: {0}'.format(mode))
                    if len(vol.split(':')) == 2:
                        parts = vol.split(':')
                        if not is_volume_permissions(parts[1]):
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
        if image and image[self.parameters.client.image_inspect_source].get('Volumes'):
            expected_vols.update(image[self.parameters.client.image_inspect_source].get('Volumes'))

        if self.parameters.volumes:
            for vol in self.parameters.volumes:
                container = None
                if ':' in vol:
                    if len(vol.split(':')) == 3:
                        dummy, container, mode = vol.split(':')
                        if not is_volume_permissions(mode):
                            self.fail('Found invalid volumes mode: {0}'.format(mode))
                    if len(vol.split(':')) == 2:
                        parts = vol.split(':')
                        if not is_volume_permissions(parts[1]):
                            dummy, container, mode = vol.split(':') + ['rw']
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
        if image and image[self.parameters.client.image_inspect_source].get('Env'):
            for env_var in image[self.parameters.client.image_inspect_source]['Env']:
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
            image_exposed_ports = image[self.parameters.client.image_inspect_source].get('ExposedPorts') or {}
            image_ports = [self._normalize_port(p) for p in image_exposed_ports.keys()]
        param_ports = []
        if self.parameters.ports:
            param_ports = [to_text(p[0], errors='surrogate_or_strict') + '/' + p[1] for p in self.parameters.ports]
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
            result[key] = to_text(value, errors='surrogate_or_strict')
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

    def _normalize_port(self, port):
        if '/' not in port:
            return port + '/tcp'
        return port

    def _get_expected_healthcheck(self):
        self.log('_get_expected_healthcheck')
        expected_healthcheck = dict()

        if self.parameters.healthcheck:
            expected_healthcheck.update([(k.title().replace("_", ""), v)
                                         for k, v in self.parameters.healthcheck.items()])

        return expected_healthcheck


class ContainerManager(DockerBaseClass):
    '''
    Perform container management tasks
    '''

    def __init__(self, client):

        super(ContainerManager, self).__init__()

        if client.module.params.get('log_options') and not client.module.params.get('log_driver'):
            client.module.warn('log_options is ignored when log_driver is not specified')
        if client.module.params.get('healthcheck') and not client.module.params.get('healthcheck').get('test'):
            client.module.warn('healthcheck is ignored when test is not specified')
        if client.module.params.get('restart_retries') is not None and not client.module.params.get('restart_policy'):
            client.module.warn('restart_retries is ignored when restart_policy is not specified')

        self.client = client
        self.parameters = TaskParameters(client)
        self.check_mode = self.client.check_mode
        self.results = {'changed': False, 'actions': []}
        self.diff = {}
        self.diff_tracker = DifferenceTracker()
        self.facts = {}

        state = self.parameters.state
        if state in ('stopped', 'started', 'present'):
            self.present(state)
        elif state == 'absent':
            self.absent()

        if not self.check_mode and not self.parameters.debug:
            self.results.pop('actions')

        if self.client.module._diff or self.parameters.debug:
            self.diff['before'], self.diff['after'] = self.diff_tracker.get_before_after()
            self.results['diff'] = self.diff

        if self.facts:
            self.results['ansible_facts'] = {'docker_container': self.facts}
            self.results['container'] = self.facts

    def wait_for_state(self, container_id, complete_states=None, wait_states=None, accept_removal=False):
        delay = 1.0
        while True:
            # Inspect container
            result = self.client.get_container_by_id(container_id)
            if result is None:
                if accept_removal:
                    return
                msg = 'Encontered vanished container while waiting for container {0}'
                self.fail(msg.format(container_id))
            # Check container state
            state = result.get('State', {}).get('Status')
            if complete_states is not None and state in complete_states:
                return
            if wait_states is not None and state not in wait_states:
                msg = 'Encontered unexpected state "{1}" while waiting for container {0}'
                self.fail(msg.format(container_id, state))
            # Wait
            sleep(delay)
            # Exponential backoff, but never wait longer than 10 seconds
            # (1.1**24 < 10, 1.1**25 > 10, so it will take 25 iterations
            #  until the maximal 10 seconds delay is reached. By then, the
            #  code will have slept for ~1.5 minutes.)
            delay = min(delay * 1.1, 10)

    def present(self, state):
        container = self._get_container(self.parameters.name)
        was_running = container.running
        was_paused = container.paused
        container_created = False

        # If the image parameter was passed then we need to deal with the image
        # version comparison. Otherwise we handle this depending on whether
        # the container already runs or not; in the former case, in case the
        # container needs to be restarted, we use the existing container's
        # image ID.
        image = self._get_image()
        self.log(image, pretty_print=True)
        if not container.exists or container.removing:
            # New container
            if container.removing:
                self.log('Found container in removal phase')
            else:
                self.log('No container found')
            if not self.parameters.image:
                self.fail('Cannot create container when image is not specified!')
            self.diff_tracker.add('exists', parameter=True, active=False)
            if container.removing and not self.check_mode:
                # Wait for container to be removed before trying to create it
                self.wait_for_state(container.Id, wait_states=['removing'], accept_removal=True)
            new_container = self.container_create(self.parameters.image, self.parameters.create_parameters)
            if new_container:
                container = new_container
            container_created = True
        else:
            # Existing container
            different, differences = container.has_different_configuration(image)
            image_different = False
            if self.parameters.comparisons['image']['comparison'] == 'strict':
                image_different = self._image_is_different(image, container)
            if image_different or different or self.parameters.recreate:
                self.diff_tracker.merge(differences)
                self.diff['differences'] = differences.get_legacy_docker_container_diffs()
                if image_different:
                    self.diff['image_different'] = True
                self.log("differences")
                self.log(differences.get_legacy_docker_container_diffs(), pretty_print=True)
                image_to_use = self.parameters.image
                if not image_to_use and container and container.Image:
                    image_to_use = container.Image
                if not image_to_use:
                    self.fail('Cannot recreate container when image is not specified or cannot be extracted from current container!')
                if container.running:
                    self.container_stop(container.Id)
                self.container_remove(container.Id)
                if not self.check_mode:
                    self.wait_for_state(container.Id, wait_states=['removing'], accept_removal=True)
                new_container = self.container_create(image_to_use, self.parameters.create_parameters)
                if new_container:
                    container = new_container
                container_created = True

        if container and container.exists:
            container = self.update_limits(container)
            container = self.update_networks(container, container_created)

            if state == 'started' and not container.running:
                self.diff_tracker.add('running', parameter=True, active=was_running)
                container = self.container_start(container.Id)
            elif state == 'started' and self.parameters.restart:
                self.diff_tracker.add('running', parameter=True, active=was_running)
                self.diff_tracker.add('restarted', parameter=True, active=False)
                container = self.container_restart(container.Id)
            elif state == 'stopped' and container.running:
                self.diff_tracker.add('running', parameter=False, active=was_running)
                self.container_stop(container.Id)
                container = self._get_container(container.Id)

            if state == 'started' and container.paused != self.parameters.paused:
                self.diff_tracker.add('paused', parameter=self.parameters.paused, active=was_paused)
                if not self.check_mode:
                    try:
                        if self.parameters.paused:
                            self.client.pause(container=container.Id)
                        else:
                            self.client.unpause(container=container.Id)
                    except Exception as exc:
                        self.fail("Error %s container %s: %s" % (
                            "pausing" if self.parameters.paused else "unpausing", container.Id, to_native(exc)
                        ))
                    container = self._get_container(container.Id)
                self.results['changed'] = True
                self.results['actions'].append(dict(set_paused=self.parameters.paused))

        self.facts = container.raw

    def absent(self):
        container = self._get_container(self.parameters.name)
        if container.exists:
            if container.running:
                self.diff_tracker.add('running', parameter=False, active=True)
                self.container_stop(container.Id)
            self.diff_tracker.add('exists', parameter=False, active=True)
            self.container_remove(container.Id)

    def fail(self, msg, **kwargs):
        self.client.fail(msg, **kwargs)

    def _output_logs(self, msg):
        self.client.module.log(msg=msg)

    def _get_container(self, container):
        '''
        Expects container ID or Name. Returns a container object
        '''
        return Container(self.client.get_container(container), self.parameters)

    def _get_image(self):
        if not self.parameters.image:
            self.log('No image specified')
            return None
        if is_image_name_id(self.parameters.image):
            image = self.client.find_image_by_id(self.parameters.image)
        else:
            repository, tag = utils.parse_repository_tag(self.parameters.image)
            if not tag:
                tag = "latest"
            image = self.client.find_image(repository, tag)
            if not image or self.parameters.pull:
                if not self.check_mode:
                    self.log("Pull the image.")
                    image, alreadyToLatest = self.client.pull_image(repository, tag)
                    if alreadyToLatest:
                        self.results['changed'] = False
                    else:
                        self.results['changed'] = True
                        self.results['actions'].append(dict(pulled_image="%s:%s" % (repository, tag)))
                elif not image:
                    # If the image isn't there, claim we'll pull.
                    # (Implicitly: if the image is there, claim it already was latest.)
                    self.results['changed'] = True
                    self.results['actions'].append(dict(pulled_image="%s:%s" % (repository, tag)))

        self.log("image")
        self.log(image, pretty_print=True)
        return image

    def _image_is_different(self, image, container):
        if image and image.get('Id'):
            if container and container.Image:
                if image.get('Id') != container.Image:
                    self.diff_tracker.add('image', parameter=image.get('Id'), active=container.Image)
                    return True
        return False

    def update_limits(self, container):
        limits_differ, different_limits = container.has_different_resource_limits()
        if limits_differ:
            self.log("limit differences:")
            self.log(different_limits.get_legacy_docker_container_diffs(), pretty_print=True)
            self.diff_tracker.merge(different_limits)
        if limits_differ and not self.check_mode:
            self.container_update(container.Id, self.parameters.update_parameters)
            return self._get_container(container.Id)
        return container

    def update_networks(self, container, container_created):
        updated_container = container
        if self.parameters.comparisons['networks']['comparison'] != 'ignore' or container_created:
            has_network_differences, network_differences = container.has_network_differences()
            if has_network_differences:
                if self.diff.get('differences'):
                    self.diff['differences'].append(dict(network_differences=network_differences))
                else:
                    self.diff['differences'] = [dict(network_differences=network_differences)]
                for netdiff in network_differences:
                    self.diff_tracker.add(
                        'network.{0}'.format(netdiff['parameter']['name']),
                        parameter=netdiff['parameter'],
                        active=netdiff['container']
                    )
                self.results['changed'] = True
                updated_container = self._add_networks(container, network_differences)

        if (self.parameters.comparisons['networks']['comparison'] == 'strict' and self.parameters.networks is not None) or self.parameters.purge_networks:
            has_extra_networks, extra_networks = container.has_extra_networks()
            if has_extra_networks:
                if self.diff.get('differences'):
                    self.diff['differences'].append(dict(purge_networks=extra_networks))
                else:
                    self.diff['differences'] = [dict(purge_networks=extra_networks)]
                for extra_network in extra_networks:
                    self.diff_tracker.add(
                        'network.{0}'.format(extra_network['name']),
                        active=extra_network
                    )
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
                                                                                          to_native(exc)))
            # connect to the network
            params = dict()
            for para in ('ipv4_address', 'ipv6_address', 'links', 'aliases'):
                if diff['parameter'].get(para):
                    params[para] = diff['parameter'][para]
            self.results['actions'].append(dict(added_to_network=diff['parameter']['name'], network_parameters=params))
            if not self.check_mode:
                try:
                    self.log("Connecting container to network %s" % diff['parameter']['id'])
                    self.log(params, pretty_print=True)
                    self.client.connect_container_to_network(container.Id, diff['parameter']['id'], **params)
                except Exception as exc:
                    self.fail("Error connecting container to network %s - %s" % (diff['parameter']['name'], to_native(exc)))
        return self._get_container(container.Id)

    def _purge_networks(self, container, networks):
        for network in networks:
            self.results['actions'].append(dict(removed_from_network=network['name']))
            if not self.check_mode:
                try:
                    self.client.disconnect_container_from_network(container.Id, network['name'])
                except Exception as exc:
                    self.fail("Error disconnecting container from network %s - %s" % (network['name'],
                                                                                      to_native(exc)))
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
                self.client.report_warnings(new_container)
            except Exception as exc:
                self.fail("Error creating container: %s" % to_native(exc))
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
                self.fail("Error starting container %s: %s" % (container_id, to_native(exc)))

            if not self.parameters.detach:
                if self.client.docker_py_version >= LooseVersion('3.0'):
                    status = self.client.wait(container_id)['StatusCode']
                else:
                    status = self.client.wait(container_id)
                if self.parameters.auto_remove:
                    output = "Cannot retrieve result as auto_remove is enabled"
                    if self.parameters.output_logs:
                        self.client.module.warn('Cannot output_logs if auto_remove is enabled!')
                else:
                    config = self.client.inspect_container(container_id)
                    logging_driver = config['HostConfig']['LogConfig']['Type']

                    if logging_driver in ('json-file', 'journald'):
                        output = self.client.logs(container_id, stdout=True, stderr=True, stream=False, timestamps=False)
                        if self.parameters.output_logs:
                            self._output_logs(msg=output)
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
            count = 0
            while True:
                try:
                    response = self.client.remove_container(container_id, v=volume_state, link=link, force=force)
                except NotFound as dummy:
                    pass
                except APIError as exc:
                    if 'Unpause the container before stopping or killing' in exc.explanation:
                        # New docker daemon versions do not allow containers to be removed
                        # if they are paused. Make sure we don't end up in an infinite loop.
                        if count == 3:
                            self.fail("Error removing container %s (tried to unpause three times): %s" % (container_id, to_native(exc)))
                        count += 1
                        # Unpause
                        try:
                            self.client.unpause(container=container_id)
                        except Exception as exc2:
                            self.fail("Error unpausing container %s for removal: %s" % (container_id, to_native(exc2)))
                        # Now try again
                        continue
                    if 'removal of container ' in exc.explanation and ' is already in progress' in exc.explanation:
                        pass
                    else:
                        self.fail("Error removing container %s: %s" % (container_id, to_native(exc)))
                except Exception as exc:
                    self.fail("Error removing container %s: %s" % (container_id, to_native(exc)))
                # We only loop when explicitly requested by 'continue'
                break
        return response

    def container_update(self, container_id, update_parameters):
        if update_parameters:
            self.log("update container %s" % (container_id))
            self.log(update_parameters, pretty_print=True)
            self.results['actions'].append(dict(updated=container_id, update_parameters=update_parameters))
            self.results['changed'] = True
            if not self.check_mode and callable(getattr(self.client, 'update_container')):
                try:
                    result = self.client.update_container(container_id, **update_parameters)
                    self.client.report_warnings(result)
                except Exception as exc:
                    self.fail("Error updating container %s: %s" % (container_id, to_native(exc)))
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

    def container_restart(self, container_id):
        self.results['actions'].append(dict(restarted=container_id, timeout=self.parameters.stop_timeout))
        self.results['changed'] = True
        if not self.check_mode:
            try:
                if self.parameters.stop_timeout:
                    dummy = self.client.restart(container_id, timeout=self.parameters.stop_timeout)
                else:
                    dummy = self.client.restart(container_id)
            except Exception as exc:
                self.fail("Error restarting container %s: %s" % (container_id, to_native(exc)))
        return self._get_container(container_id)

    def container_stop(self, container_id):
        if self.parameters.force_kill:
            self.container_kill(container_id)
            return
        self.results['actions'].append(dict(stopped=container_id, timeout=self.parameters.stop_timeout))
        self.results['changed'] = True
        response = None
        if not self.check_mode:
            count = 0
            while True:
                try:
                    if self.parameters.stop_timeout:
                        response = self.client.stop(container_id, timeout=self.parameters.stop_timeout)
                    else:
                        response = self.client.stop(container_id)
                except APIError as exc:
                    if 'Unpause the container before stopping or killing' in exc.explanation:
                        # New docker daemon versions do not allow containers to be removed
                        # if they are paused. Make sure we don't end up in an infinite loop.
                        if count == 3:
                            self.fail("Error removing container %s (tried to unpause three times): %s" % (container_id, to_native(exc)))
                        count += 1
                        # Unpause
                        try:
                            self.client.unpause(container=container_id)
                        except Exception as exc2:
                            self.fail("Error unpausing container %s for removal: %s" % (container_id, to_native(exc2)))
                        # Now try again
                        continue
                    self.fail("Error stopping container %s: %s" % (container_id, to_native(exc)))
                except Exception as exc:
                    self.fail("Error stopping container %s: %s" % (container_id, to_native(exc)))
                # We only loop when explicitly requested by 'continue'
                break
        return response


def detect_ipvX_address_usage(client):
    '''
    Helper function to detect whether any specified network uses ipv4_address or ipv6_address
    '''
    for network in client.module.params.get("networks") or []:
        if network.get('ipv4_address') is not None or network.get('ipv6_address') is not None:
            return True
    return False


class AnsibleDockerClientContainer(AnsibleDockerClient):
    # A list of module options which are not docker container properties
    __NON_CONTAINER_PROPERTY_OPTIONS = tuple([
        'env_file', 'force_kill', 'keep_volumes', 'ignore_image', 'name', 'pull', 'purge_networks',
        'recreate', 'restart', 'state', 'trust_image_content', 'networks', 'cleanup', 'kill_signal',
        'output_logs', 'paused'
    ] + list(DOCKER_COMMON_ARGS.keys()))

    def _parse_comparisons(self):
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
            mounts='set(dict)',
            networks='set(dict)',
            ulimits='set(dict)',
            device_read_bps='set(dict)',
            device_write_bps='set(dict)',
            device_read_iops='set(dict)',
            device_write_iops='set(dict)',
        )
        all_options = set()  # this is for improving user feedback when a wrong option was specified for comparison
        default_values = dict(
            stop_timeout='ignore',
        )
        for option, data in self.module.argument_spec.items():
            all_options.add(option)
            for alias in data.get('aliases', []):
                all_options.add(alias)
            # Ignore options which aren't used as container properties
            if option in self.__NON_CONTAINER_PROPERTY_OPTIONS and option != 'networks':
                continue
            # Determine option type
            if option in explicit_types:
                datatype = explicit_types[option]
            elif data['type'] == 'list':
                datatype = 'set'
            elif data['type'] == 'dict':
                datatype = 'dict'
            else:
                datatype = 'value'
            # Determine comparison type
            if option in default_values:
                comparison = default_values[option]
            elif datatype in ('list', 'value'):
                comparison = 'strict'
            else:
                comparison = 'allow_more_present'
            comparisons[option] = dict(type=datatype, comparison=comparison, name=option)
            # Keep track of aliases
            comp_aliases[option] = option
            for alias in data.get('aliases', []):
                comp_aliases[alias] = option
        # Process legacy ignore options
        if self.module.params['ignore_image']:
            comparisons['image']['comparison'] = 'ignore'
        if self.module.params['purge_networks']:
            comparisons['networks']['comparison'] = 'strict'
        # Process options
        if self.module.params.get('comparisons'):
            # If '*' appears in comparisons, process it first
            if '*' in self.module.params['comparisons']:
                value = self.module.params['comparisons']['*']
                if value not in ('strict', 'ignore'):
                    self.fail("The wildcard can only be used with comparison modes 'strict' and 'ignore'!")
                for option, v in comparisons.items():
                    if option == 'networks':
                        # `networks` is special: only update if
                        # some value is actually specified
                        if self.module.params['networks'] is None:
                            continue
                    v['comparison'] = value
            # Now process all other comparisons.
            comp_aliases_used = {}
            for key, value in self.module.params['comparisons'].items():
                if key == '*':
                    continue
                # Find main key
                key_main = comp_aliases.get(key)
                if key_main is None:
                    if key_main in all_options:
                        self.fail("The module option '%s' cannot be specified in the comparisons dict, "
                                  "since it does not correspond to container's state!" % key)
                    self.fail("Unknown module option '%s' in comparisons dict!" % key)
                if key_main in comp_aliases_used:
                    self.fail("Both '%s' and '%s' (aliases of %s) are specified in comparisons dict!" % (key, comp_aliases_used[key_main], key_main))
                comp_aliases_used[key_main] = key
                # Check value and update accordingly
                if value in ('strict', 'ignore'):
                    comparisons[key_main]['comparison'] = value
                elif value == 'allow_more_present':
                    if comparisons[key_main]['type'] == 'value':
                        self.fail("Option '%s' is a value and not a set/list/dict, so its comparison cannot be %s" % (key, value))
                    comparisons[key_main]['comparison'] = value
                else:
                    self.fail("Unknown comparison mode '%s'!" % value)
        # Add implicit options
        comparisons['publish_all_ports'] = dict(type='value', comparison='strict', name='published_ports')
        comparisons['expected_ports'] = dict(type='dict', comparison=comparisons['published_ports']['comparison'], name='expected_ports')
        comparisons['disable_healthcheck'] = dict(type='value',
                                                  comparison='ignore' if comparisons['healthcheck']['comparison'] == 'ignore' else 'strict',
                                                  name='disable_healthcheck')
        # Check legacy values
        if self.module.params['ignore_image'] and comparisons['image']['comparison'] != 'ignore':
            self.module.warn('The ignore_image option has been overridden by the comparisons option!')
        if self.module.params['purge_networks'] and comparisons['networks']['comparison'] != 'strict':
            self.module.warn('The purge_networks option has been overridden by the comparisons option!')
        self.comparisons = comparisons

    def _get_additional_minimal_versions(self):
        stop_timeout_supported = self.docker_api_version >= LooseVersion('1.25')
        stop_timeout_needed_for_update = self.module.params.get("stop_timeout") is not None and self.module.params.get('state') != 'absent'
        if stop_timeout_supported:
            stop_timeout_supported = self.docker_py_version >= LooseVersion('2.1')
            if stop_timeout_needed_for_update and not stop_timeout_supported:
                # We warn (instead of fail) since in older versions, stop_timeout was not used
                # to update the container's configuration, but only when stopping a container.
                self.module.warn("Docker SDK for Python's version is %s. Minimum version required is 2.1 to update "
                                 "the container's stop_timeout configuration. "
                                 "If you use the 'docker-py' module, you have to switch to the 'docker' Python package." % (docker_version,))
        else:
            if stop_timeout_needed_for_update and not stop_timeout_supported:
                # We warn (instead of fail) since in older versions, stop_timeout was not used
                # to update the container's configuration, but only when stopping a container.
                self.module.warn("Docker API version is %s. Minimum version required is 1.25 to set or "
                                 "update the container's stop_timeout configuration." % (self.docker_api_version_str,))
        self.option_minimal_versions['stop_timeout']['supported'] = stop_timeout_supported

    def __init__(self, **kwargs):
        option_minimal_versions = dict(
            # internal options
            log_config=dict(),
            publish_all_ports=dict(),
            ports=dict(),
            volume_binds=dict(),
            name=dict(),
            # normal options
            device_read_bps=dict(docker_py_version='1.9.0', docker_api_version='1.22'),
            device_read_iops=dict(docker_py_version='1.9.0', docker_api_version='1.22'),
            device_write_bps=dict(docker_py_version='1.9.0', docker_api_version='1.22'),
            device_write_iops=dict(docker_py_version='1.9.0', docker_api_version='1.22'),
            dns_opts=dict(docker_api_version='1.21', docker_py_version='1.10.0'),
            ipc_mode=dict(docker_api_version='1.25'),
            mac_address=dict(docker_api_version='1.25'),
            oom_score_adj=dict(docker_api_version='1.22'),
            shm_size=dict(docker_api_version='1.22'),
            stop_signal=dict(docker_api_version='1.21'),
            tmpfs=dict(docker_api_version='1.22'),
            volume_driver=dict(docker_api_version='1.21'),
            memory_reservation=dict(docker_api_version='1.21'),
            kernel_memory=dict(docker_api_version='1.21'),
            auto_remove=dict(docker_py_version='2.1.0', docker_api_version='1.25'),
            healthcheck=dict(docker_py_version='2.0.0', docker_api_version='1.24'),
            init=dict(docker_py_version='2.2.0', docker_api_version='1.25'),
            runtime=dict(docker_py_version='2.4.0', docker_api_version='1.25'),
            sysctls=dict(docker_py_version='1.10.0', docker_api_version='1.24'),
            userns_mode=dict(docker_py_version='1.10.0', docker_api_version='1.23'),
            uts=dict(docker_py_version='3.5.0', docker_api_version='1.25'),
            pids_limit=dict(docker_py_version='1.10.0', docker_api_version='1.23'),
            mounts=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
            # specials
            ipvX_address_supported=dict(docker_py_version='1.9.0', docker_api_version='1.22',
                                        detect_usage=detect_ipvX_address_usage,
                                        usage_msg='ipv4_address or ipv6_address in networks'),
            stop_timeout=dict(),  # see _get_additional_minimal_versions()
        )

        super(AnsibleDockerClientContainer, self).__init__(
            option_minimal_versions=option_minimal_versions,
            option_minimal_versions_ignore_params=self.__NON_CONTAINER_PROPERTY_OPTIONS,
            **kwargs
        )

        self.image_inspect_source = 'Config'
        if self.docker_api_version < LooseVersion('1.21'):
            self.image_inspect_source = 'ContainerConfig'

        self._get_additional_minimal_versions()
        self._parse_comparisons()


def main():
    argument_spec = dict(
        auto_remove=dict(type='bool', default=False),
        blkio_weight=dict(type='int'),
        capabilities=dict(type='list', elements='str'),
        cap_drop=dict(type='list', elements='str'),
        cleanup=dict(type='bool', default=False),
        command=dict(type='raw'),
        comparisons=dict(type='dict'),
        cpu_period=dict(type='int'),
        cpu_quota=dict(type='int'),
        cpuset_cpus=dict(type='str'),
        cpuset_mems=dict(type='str'),
        cpu_shares=dict(type='int'),
        detach=dict(type='bool', default=True),
        devices=dict(type='list', elements='str'),
        device_read_bps=dict(type='list', elements='dict', options=dict(
            path=dict(required=True, type='str'),
            rate=dict(required=True, type='str'),
        )),
        device_write_bps=dict(type='list', elements='dict', options=dict(
            path=dict(required=True, type='str'),
            rate=dict(required=True, type='str'),
        )),
        device_read_iops=dict(type='list', elements='dict', options=dict(
            path=dict(required=True, type='str'),
            rate=dict(required=True, type='int'),
        )),
        device_write_iops=dict(type='list', elements='dict', options=dict(
            path=dict(required=True, type='str'),
            rate=dict(required=True, type='int'),
        )),
        dns_servers=dict(type='list', elements='str'),
        dns_opts=dict(type='list', elements='str'),
        dns_search_domains=dict(type='list', elements='str'),
        domainname=dict(type='str'),
        entrypoint=dict(type='list', elements='str'),
        env=dict(type='dict'),
        env_file=dict(type='path'),
        etc_hosts=dict(type='dict'),
        exposed_ports=dict(type='list', elements='str', aliases=['exposed', 'expose']),
        force_kill=dict(type='bool', default=False, aliases=['forcekill']),
        groups=dict(type='list', elements='str'),
        healthcheck=dict(type='dict', options=dict(
            test=dict(type='raw'),
            interval=dict(type='str'),
            timeout=dict(type='str'),
            start_period=dict(type='str'),
            retries=dict(type='int'),
        )),
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
        links=dict(type='list', elements='str'),
        log_driver=dict(type='str'),
        log_options=dict(type='dict', aliases=['log_opt']),
        mac_address=dict(type='str'),
        memory=dict(type='str', default='0'),
        memory_reservation=dict(type='str'),
        memory_swap=dict(type='str'),
        memory_swappiness=dict(type='int'),
        mounts=dict(type='list', elements='dict', options=dict(
            target=dict(type='str', required=True),
            source=dict(type='str'),
            type=dict(type='str', choices=['bind', 'volume', 'tmpfs', 'npipe'], default='volume'),
            read_only=dict(type='bool'),
            consistency=dict(type='str', choices=['default', 'consistent', 'cached', 'delegated']),
            propagation=dict(type='str', choices=['private', 'rprivate', 'shared', 'rshared', 'slave', 'rslave']),
            no_copy=dict(type='bool'),
            labels=dict(type='dict'),
            volume_driver=dict(type='str'),
            volume_options=dict(type='dict'),
            tmpfs_size=dict(type='str'),
            tmpfs_mode=dict(type='str'),
        )),
        name=dict(type='str', required=True),
        network_mode=dict(type='str'),
        networks=dict(type='list', elements='dict', options=dict(
            name=dict(type='str', required=True),
            ipv4_address=dict(type='str'),
            ipv6_address=dict(type='str'),
            aliases=dict(type='list', elements='str'),
            links=dict(type='list', elements='str'),
        )),
        networks_cli_compatible=dict(type='bool'),
        oom_killer=dict(type='bool'),
        oom_score_adj=dict(type='int'),
        output_logs=dict(type='bool', default=False),
        paused=dict(type='bool', default=False),
        pid_mode=dict(type='str'),
        pids_limit=dict(type='int'),
        privileged=dict(type='bool', default=False),
        published_ports=dict(type='list', elements='str', aliases=['ports']),
        pull=dict(type='bool', default=False),
        purge_networks=dict(type='bool', default=False),
        read_only=dict(type='bool', default=False),
        recreate=dict(type='bool', default=False),
        restart=dict(type='bool', default=False),
        restart_policy=dict(type='str', choices=['no', 'on-failure', 'always', 'unless-stopped']),
        restart_retries=dict(type='int'),
        runtime=dict(type='str'),
        security_opts=dict(type='list', elements='str'),
        shm_size=dict(type='str'),
        state=dict(type='str', default='started', choices=['absent', 'present', 'started', 'stopped']),
        stop_signal=dict(type='str'),
        stop_timeout=dict(type='int'),
        sysctls=dict(type='dict'),
        tmpfs=dict(type='list', elements='str'),
        trust_image_content=dict(type='bool', default=False),
        tty=dict(type='bool', default=False),
        ulimits=dict(type='list', elements='str'),
        user=dict(type='str'),
        userns_mode=dict(type='str'),
        uts=dict(type='str'),
        volume_driver=dict(type='str'),
        volumes=dict(type='list', elements='str'),
        volumes_from=dict(type='list', elements='str'),
        working_dir=dict(type='str'),
    )

    required_if = [
        ('state', 'present', ['image'])
    ]

    client = AnsibleDockerClientContainer(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
        min_docker_api_version='1.20',
    )
    if client.module.params['networks_cli_compatible'] is None and client.module.params['networks']:
        client.module.deprecate(
            'Please note that docker_container handles networks slightly different than docker CLI. '
            'If you specify networks, the default network will still be attached as the first network. '
            '(You can specify purge_networks to remove all networks not explicitly listed.) '
            'This behavior will change in Ansible 2.12. You can change the behavior now by setting '
            'the new `networks_cli_compatible` option to `yes`, and remove this warning by setting '
            'it to `no`',
            version='2.12'
        )

    try:
        cm = ContainerManager(client)
        client.module.exit_json(**sanitize_result(cm.results))
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
