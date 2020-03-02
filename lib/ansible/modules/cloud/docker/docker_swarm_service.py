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
author:
  - "Dario Zanzico (@dariko)"
  - "Jason Witkowski (@jwitko)"
  - "Hannes Ljungberg (@hannseman)"
short_description: docker swarm service
description:
  - Manages docker services via a swarm manager node.
version_added: "2.7"
options:
  args:
    description:
      - List arguments to be passed to the container.
      - Corresponds to the C(ARG) parameter of C(docker service create).
    type: list
    elements: str
  command:
    description:
      - Command to execute when the container starts.
      - A command may be either a string or a list or a list of strings.
      - Corresponds to the C(COMMAND) parameter of C(docker service create).
    type: raw
    version_added: 2.8
  configs:
    description:
      - List of dictionaries describing the service configs.
      - Corresponds to the C(--config) option of C(docker service create).
      - Requires API version >= 1.30.
    type: list
    elements: dict
    suboptions:
      config_id:
        description:
          - Config's ID.
        type: str
      config_name:
        description:
          - Config's name as defined at its creation.
        type: str
        required: yes
      filename:
        description:
          - Name of the file containing the config. Defaults to the I(config_name) if not specified.
        type: str
      uid:
        description:
          - UID of the config file's owner.
        type: str
      gid:
        description:
          - GID of the config file's group.
        type: str
      mode:
        description:
          - File access mode inside the container. Must be an octal number (like C(0644) or C(0444)).
        type: int
  constraints:
    description:
      - List of the service constraints.
      - Corresponds to the C(--constraint) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(placement.constraints) instead.
    type: list
    elements: str
  container_labels:
    description:
      - Dictionary of key value pairs.
      - Corresponds to the C(--container-label) option of C(docker service create).
    type: dict
  dns:
    description:
      - List of custom DNS servers.
      - Corresponds to the C(--dns) option of C(docker service create).
      - Requires API version >= 1.25.
    type: list
    elements: str
  dns_search:
    description:
      - List of custom DNS search domains.
      - Corresponds to the C(--dns-search) option of C(docker service create).
      - Requires API version >= 1.25.
    type: list
    elements: str
  dns_options:
    description:
      - List of custom DNS options.
      - Corresponds to the C(--dns-option) option of C(docker service create).
      - Requires API version >= 1.25.
    type: list
    elements: str
  endpoint_mode:
    description:
      - Service endpoint mode.
      - Corresponds to the C(--endpoint-mode) option of C(docker service create).
      - Requires API version >= 1.25.
    type: str
    choices:
      - vip
      - dnsrr
  env:
    description:
      - List or dictionary of the service environment variables.
      - If passed a list each items need to be in the format of C(KEY=VALUE).
      - If passed a dictionary values which might be parsed as numbers,
        booleans or other types by the YAML parser must be quoted (e.g. C("true"))
        in order to avoid data loss.
      - Corresponds to the C(--env) option of C(docker service create).
    type: raw
  env_files:
    description:
      - List of paths to files, present on the target, containing environment variables C(FOO=BAR).
      - The order of the list is significant in determining the value assigned to a
        variable that shows up more than once.
      - If variable also present in I(env), then I(env) value will override.
    type: list
    elements: path
    version_added: "2.8"
  force_update:
    description:
      - Force update even if no changes require it.
      - Corresponds to the C(--force) option of C(docker service update).
      - Requires API version >= 1.25.
    type: bool
    default: no
  groups:
    description:
      - List of additional group names and/or IDs that the container process will run as.
      - Corresponds to the C(--group) option of C(docker service update).
      - Requires API version >= 1.25.
    type: list
    elements: str
    version_added: "2.8"
  healthcheck:
    description:
      - Configure a check that is run to determine whether or not containers for this service are "healthy".
        See the docs for the L(HEALTHCHECK Dockerfile instruction,https://docs.docker.com/engine/reference/builder/#healthcheck)
        for details on how healthchecks work.
      - "I(interval), I(timeout) and I(start_period) are specified as durations. They accept duration as a string in a format
        that look like: C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
      - Requires API version >= 1.25.
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
        type: str
      timeout:
        description:
          - Maximum time to allow one check to run.
        type: str
      retries:
        description:
          - Consecutive failures needed to report unhealthy. It accept integer value.
        type: int
      start_period:
        description:
          - Start period for the container to initialize before starting health-retries countdown.
        type: str
    version_added: "2.8"
  hostname:
    description:
      - Container hostname.
      - Corresponds to the C(--hostname) option of C(docker service create).
      - Requires API version >= 1.25.
    type: str
  hosts:
    description:
      - Dict of host-to-IP mappings, where each host name is a key in the dictionary.
        Each host name will be added to the container's /etc/hosts file.
      - Corresponds to the C(--host) option of C(docker service create).
      - Requires API version >= 1.25.
    type: dict
    version_added: "2.8"
  image:
    description:
      - Service image path and tag.
      - Corresponds to the C(IMAGE) parameter of C(docker service create).
    type: str
  labels:
    description:
      - Dictionary of key value pairs.
      - Corresponds to the C(--label) option of C(docker service create).
    type: dict
  limits:
    description:
      - Configures service resource limits.
    suboptions:
      cpus:
        description:
          - Service CPU limit. C(0) equals no limit.
          - Corresponds to the C(--limit-cpu) option of C(docker service create).
        type: float
      memory:
        description:
          - "Service memory limit in format C(<number>[<unit>]). Number is a positive integer.
            Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
            C(T) (tebibyte), or C(P) (pebibyte)."
          - C(0) equals no limit.
          - Omitting the unit defaults to bytes.
          - Corresponds to the C(--limit-memory) option of C(docker service create).
        type: str
    type: dict
    version_added: "2.8"
  limit_cpu:
    description:
      - Service CPU limit. C(0) equals no limit.
      - Corresponds to the C(--limit-cpu) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(limits.cpus) instead.
    type: float
  limit_memory:
    description:
      - "Service memory limit in format C(<number>[<unit>]). Number is a positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte)."
      - C(0) equals no limit.
      - Omitting the unit defaults to bytes.
      - Corresponds to the C(--limit-memory) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(limits.memory) instead.
    type: str
  logging:
    description:
      - "Logging configuration for the service."
    suboptions:
      driver:
        description:
          - Configure the logging driver for a service.
          - Corresponds to the C(--log-driver) option of C(docker service create).
        type: str
      options:
        description:
          - Options for service logging driver.
          - Corresponds to the C(--log-opt) option of C(docker service create).
        type: dict
    type: dict
    version_added: "2.8"
  log_driver:
    description:
      - Configure the logging driver for a service.
      - Corresponds to the C(--log-driver) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(logging.driver) instead.
    type: str
  log_driver_options:
    description:
      - Options for service logging driver.
      - Corresponds to the C(--log-opt) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(logging.options) instead.
    type: dict
  mode:
    description:
      - Service replication mode.
      - Service will be removed and recreated when changed.
      - Corresponds to the C(--mode) option of C(docker service create).
    type: str
    default: replicated
    choices:
      - replicated
      - global
  mounts:
    description:
      - List of dictionaries describing the service mounts.
      - Corresponds to the C(--mount) option of C(docker service create).
    type: list
    elements: dict
    suboptions:
      source:
        description:
          - Mount source (e.g. a volume name or a host path).
          - Must be specified if I(type) is not C(tmpfs).
        type: str
      target:
        description:
          - Container path.
        type: str
        required: yes
      type:
        description:
          - The mount type.
          - Note that C(npipe) is only supported by Docker for Windows. Also note that C(npipe) was added in Ansible 2.9.
        type: str
        default: bind
        choices:
          - bind
          - volume
          - tmpfs
          - npipe
      readonly:
        description:
          - Whether the mount should be read-only.
        type: bool
      labels:
        description:
          - Volume labels to apply.
        type: dict
        version_added: "2.8"
      propagation:
        description:
          - The propagation mode to use.
          - Can only be used when I(mode) is C(bind).
        type: str
        choices:
          - shared
          - slave
          - private
          - rshared
          - rslave
          - rprivate
        version_added: "2.8"
      no_copy:
        description:
          - Disable copying of data from a container when a volume is created.
          - Can only be used when I(mode) is C(volume).
        type: bool
        version_added: "2.8"
      driver_config:
        description:
          - Volume driver configuration.
          - Can only be used when I(mode) is C(volume).
        suboptions:
          name:
            description:
              - Name of the volume-driver plugin to use for the volume.
            type: str
          options:
            description:
              - Options as key-value pairs to pass to the driver for this volume.
            type: dict
        type: dict
        version_added: "2.8"
      tmpfs_size:
        description:
          - "Size of the tmpfs mount in format C(<number>[<unit>]). Number is a positive integer.
            Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
            C(T) (tebibyte), or C(P) (pebibyte)."
          - Can only be used when I(mode) is C(tmpfs).
        type: str
        version_added: "2.8"
      tmpfs_mode:
        description:
          - File mode of the tmpfs in octal.
          - Can only be used when I(mode) is C(tmpfs).
        type: int
        version_added: "2.8"
  name:
    description:
      - Service name.
      - Corresponds to the C(--name) option of C(docker service create).
    type: str
    required: yes
  networks:
    description:
      - List of the service networks names or dictionaries.
      - When passed dictionaries valid sub-options are I(name), which is required, and
        I(aliases) and I(options).
      - Prior to API version 1.29, updating and removing networks is not supported.
        If changes are made the service will then be removed and recreated.
      - Corresponds to the C(--network) option of C(docker service create).
    type: list
    elements: raw
  placement:
    description:
      - Configures service placement preferences and constraints.
    suboptions:
      constraints:
        description:
          - List of the service constraints.
          - Corresponds to the C(--constraint) option of C(docker service create).
        type: list
        elements: str
      preferences:
        description:
          - List of the placement preferences as key value pairs.
          - Corresponds to the C(--placement-pref) option of C(docker service create).
          - Requires API version >= 1.27.
        type: list
        elements: dict
    type: dict
    version_added: "2.8"
  publish:
    description:
      - List of dictionaries describing the service published ports.
      - Corresponds to the C(--publish) option of C(docker service create).
      - Requires API version >= 1.25.
    type: list
    elements: dict
    suboptions:
      published_port:
        description:
          - The port to make externally available.
        type: int
        required: yes
      target_port:
        description:
          - The port inside the container to expose.
        type: int
        required: yes
      protocol:
        description:
          - What protocol to use.
        type: str
        default: tcp
        choices:
          - tcp
          - udp
      mode:
        description:
          - What publish mode to use.
          - Requires API version >= 1.32.
        type: str
        choices:
          - ingress
          - host
  read_only:
    description:
      - Mount the containers root filesystem as read only.
      - Corresponds to the C(--read-only) option of C(docker service create).
    type: bool
    version_added: "2.8"
  replicas:
    description:
      - Number of containers instantiated in the service. Valid only if I(mode) is C(replicated).
      - If set to C(-1), and service is not present, service replicas will be set to C(1).
      - If set to C(-1), and service is present, service replicas will be unchanged.
      - Corresponds to the C(--replicas) option of C(docker service create).
    type: int
    default: -1
  reservations:
    description:
      - Configures service resource reservations.
    suboptions:
      cpus:
        description:
          - Service CPU reservation. C(0) equals no reservation.
          - Corresponds to the C(--reserve-cpu) option of C(docker service create).
        type: float
      memory:
        description:
          - "Service memory reservation in format C(<number>[<unit>]). Number is a positive integer.
            Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
            C(T) (tebibyte), or C(P) (pebibyte)."
          - C(0) equals no reservation.
          - Omitting the unit defaults to bytes.
          - Corresponds to the C(--reserve-memory) option of C(docker service create).
        type: str
    type: dict
    version_added: "2.8"
  reserve_cpu:
    description:
      - Service CPU reservation. C(0) equals no reservation.
      - Corresponds to the C(--reserve-cpu) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(reservations.cpus) instead.
    type: float
  reserve_memory:
    description:
      - "Service memory reservation in format C(<number>[<unit>]). Number is a positive integer.
        Unit can be C(B) (byte), C(K) (kibibyte, 1024B), C(M) (mebibyte), C(G) (gibibyte),
        C(T) (tebibyte), or C(P) (pebibyte)."
      - C(0) equals no reservation.
      - Omitting the unit defaults to bytes.
      - Corresponds to the C(--reserve-memory) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(reservations.memory) instead.
    type: str
  resolve_image:
    description:
      - If the current image digest should be resolved from registry and updated if changed.
      - Requires API version >= 1.30.
    type: bool
    default: no
    version_added: 2.8
  restart_config:
    description:
      - Configures if and how to restart containers when they exit.
    suboptions:
      condition:
        description:
          - Restart condition of the service.
          - Corresponds to the C(--restart-condition) option of C(docker service create).
        type: str
        choices:
          - none
          - on-failure
          - any
      delay:
        description:
          - Delay between restarts.
          - "Accepts a a string in a format that look like:
            C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
          - Corresponds to the C(--restart-delay) option of C(docker service create).
        type: str
      max_attempts:
        description:
          - Maximum number of service restarts.
          - Corresponds to the C(--restart-condition) option of C(docker service create).
        type: int
      window:
        description:
          - Restart policy evaluation window.
          - "Accepts a string in a format that look like:
            C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
          - Corresponds to the C(--restart-window) option of C(docker service create).
        type: str
    type: dict
    version_added: "2.8"
  restart_policy:
    description:
      - Restart condition of the service.
      - Corresponds to the C(--restart-condition) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(restart_config.condition) instead.
    type: str
    choices:
      - none
      - on-failure
      - any
  restart_policy_attempts:
    description:
      - Maximum number of service restarts.
      - Corresponds to the C(--restart-condition) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(restart_config.max_attempts) instead.
    type: int
  restart_policy_delay:
    description:
      - Delay between restarts.
      - "Accepts a duration as an integer in nanoseconds or as a string in a format that look like:
        C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
      - Corresponds to the C(--restart-delay) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(restart_config.delay) instead.
    type: raw
  restart_policy_window:
    description:
      - Restart policy evaluation window.
      - "Accepts a duration as an integer in nanoseconds or as a string in a format that look like:
        C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
      - Corresponds to the C(--restart-window) option of C(docker service create).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(restart_config.window) instead.
    type: raw
  rollback_config:
    description:
      - Configures how the service should be rolled back in case of a failing update.
    suboptions:
      parallelism:
        description:
          - The number of containers to rollback at a time. If set to 0, all containers rollback simultaneously.
          - Corresponds to the C(--rollback-parallelism) option of C(docker service create).
          - Requires API version >= 1.28.
        type: int
      delay:
        description:
          - Delay between task rollbacks.
          - "Accepts a string in a format that look like:
            C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
          - Corresponds to the C(--rollback-delay) option of C(docker service create).
          - Requires API version >= 1.28.
        type: str
      failure_action:
        description:
          - Action to take in case of rollback failure.
          - Corresponds to the C(--rollback-failure-action) option of C(docker service create).
          - Requires API version >= 1.28.
        type: str
        choices:
          - continue
          - pause
      monitor:
        description:
          - Duration after each task rollback to monitor for failure.
          - "Accepts a string in a format that look like:
            C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
          - Corresponds to the C(--rollback-monitor) option of C(docker service create).
          - Requires API version >= 1.28.
        type: str
      max_failure_ratio:
        description:
          - Fraction of tasks that may fail during a rollback.
          - Corresponds to the C(--rollback-max-failure-ratio) option of C(docker service create).
          - Requires API version >= 1.28.
        type: float
      order:
        description:
          - Specifies the order of operations during rollbacks.
          - Corresponds to the C(--rollback-order) option of C(docker service create).
          - Requires API version >= 1.29.
        type: str
    type: dict
    version_added: "2.8"
  secrets:
    description:
      - List of dictionaries describing the service secrets.
      - Corresponds to the C(--secret) option of C(docker service create).
      - Requires API version >= 1.25.
    type: list
    elements: dict
    suboptions:
      secret_id:
        description:
          - Secret's ID.
        type: str
      secret_name:
        description:
          - Secret's name as defined at its creation.
        type: str
        required: yes
      filename:
        description:
          - Name of the file containing the secret. Defaults to the I(secret_name) if not specified.
          - Corresponds to the C(target) key of C(docker service create --secret).
        type: str
      uid:
        description:
          - UID of the secret file's owner.
        type: str
      gid:
        description:
          - GID of the secret file's group.
        type: str
      mode:
        description:
          - File access mode inside the container. Must be an octal number (like C(0644) or C(0444)).
        type: int
  state:
    description:
      - C(absent) - A service matching the specified name will be removed and have its tasks stopped.
      - C(present) - Asserts the existence of a service matching the name and provided configuration parameters.
        Unspecified configuration parameters will be set to docker defaults.
    type: str
    default: present
    choices:
      - present
      - absent
  stop_grace_period:
    description:
      - Time to wait before force killing a container.
      - "Accepts a duration as a string in a format that look like:
        C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
      - Corresponds to the C(--stop-grace-period) option of C(docker service create).
    type: str
    version_added: "2.8"
  stop_signal:
    description:
      - Override default signal used to stop the container.
      - Corresponds to the C(--stop-signal) option of C(docker service create).
    type: str
    version_added: "2.8"
  tty:
    description:
      - Allocate a pseudo-TTY.
      - Corresponds to the C(--tty) option of C(docker service create).
      - Requires API version >= 1.25.
    type: bool
  update_config:
    description:
      - Configures how the service should be updated. Useful for configuring rolling updates.
    suboptions:
      parallelism:
        description:
          - Rolling update parallelism.
          - Corresponds to the C(--update-parallelism) option of C(docker service create).
        type: int
      delay:
        description:
          - Rolling update delay.
          - "Accepts a string in a format that look like:
            C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
          - Corresponds to the C(--update-delay) option of C(docker service create).
        type: str
      failure_action:
        description:
          - Action to take in case of container failure.
          - Corresponds to the C(--update-failure-action) option of C(docker service create).
          - Usage of I(rollback) requires API version >= 1.29.
        type: str
        choices:
          - continue
          - pause
          - rollback
      monitor:
        description:
          - Time to monitor updated tasks for failures.
          - "Accepts a string in a format that look like:
            C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
          - Corresponds to the C(--update-monitor) option of C(docker service create).
          - Requires API version >= 1.25.
        type: str
      max_failure_ratio:
        description:
          - Fraction of tasks that may fail during an update before the failure action is invoked.
          - Corresponds to the C(--update-max-failure-ratio) option of C(docker service create).
          - Requires API version >= 1.25.
        type: float
      order:
        description:
          - Specifies the order of operations when rolling out an updated task.
          - Corresponds to the C(--update-order) option of C(docker service create).
          - Requires API version >= 1.29.
        type: str
    type: dict
    version_added: "2.8"
  update_delay:
    description:
      - Rolling update delay.
      - "Accepts a duration as an integer in nanoseconds or as a string in a format that look like:
        C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
      - Corresponds to the C(--update-delay) option of C(docker service create).
      - Before Ansible 2.8, the default value for this option was C(10).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(update_config.delay) instead.
    type: raw
  update_parallelism:
    description:
      - Rolling update parallelism.
      - Corresponds to the C(--update-parallelism) option of C(docker service create).
      - Before Ansible 2.8, the default value for this option was C(1).
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(update_config.parallelism) instead.
    type: int
  update_failure_action:
    description:
      - Action to take in case of container failure.
      - Corresponds to the C(--update-failure-action) option of C(docker service create).
      - Usage of I(rollback) requires API version >= 1.29.
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(update_config.failure_action) instead.
    type: str
    choices:
      - continue
      - pause
      - rollback
  update_monitor:
    description:
      - Time to monitor updated tasks for failures.
      - "Accepts a duration as an integer in nanoseconds or as a string in a format that look like:
        C(5h34m56s), C(1m30s) etc. The supported units are C(us), C(ms), C(s), C(m) and C(h)."
      - Corresponds to the C(--update-monitor) option of C(docker service create).
      - Requires API version >= 1.25.
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(update_config.monitor) instead.
    type: raw
  update_max_failure_ratio:
    description:
      - Fraction of tasks that may fail during an update before the failure action is invoked.
      - Corresponds to the C(--update-max-failure-ratio) option of C(docker service create).
      - Requires API version >= 1.25.
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(update_config.max_failure_ratio) instead.
    type: float
  update_order:
    description:
      - Specifies the order of operations when rolling out an updated task.
      - Corresponds to the C(--update-order) option of C(docker service create).
      - Requires API version >= 1.29.
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(update_config.order) instead.
    type: str
    choices:
      - stop-first
      - start-first
  user:
    description:
      - Sets the username or UID used for the specified command.
      - Before Ansible 2.8, the default value for this option was C(root).
      - The default has been removed so that the user defined in the image is used if no user is specified here.
      - Corresponds to the C(--user) option of C(docker service create).
    type: str
  working_dir:
    description:
      - Path to the working directory.
      - Corresponds to the C(--workdir) option of C(docker service create).
    type: str
    version_added: "2.8"
extends_documentation_fragment:
  - docker
  - docker.docker_py_2_documentation
requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 2.0.2"
  - "Docker API >= 1.24"
notes:
  - "Images will only resolve to the latest digest when using Docker API >= 1.30 and Docker SDK for Python >= 3.2.0.
     When using older versions use C(force_update: true) to trigger the swarm to resolve a new image."
'''

RETURN = '''
swarm_service:
  returned: always
  type: dict
  description:
    - Dictionary of variables representing the current state of the service.
      Matches the module parameters format.
    - Note that facts are not part of registered vars but accessible directly.
    - Note that before Ansible 2.7.9, the return variable was documented as C(ansible_swarm_service),
      while the module actually returned a variable called C(ansible_docker_service). The variable
      was renamed to C(swarm_service) in both code and documentation for Ansible 2.7.9 and Ansible 2.8.0.
      In Ansible 2.7.x, the old name C(ansible_docker_service) can still be used.
  sample: '{
    "args": [
      "3600"
    ],
    "command": [
      "sleep"
    ],
    "configs": null,
    "constraints": [
      "node.role == manager",
      "engine.labels.operatingsystem == ubuntu 14.04"
    ],
    "container_labels": null,
    "dns": null,
    "dns_options": null,
    "dns_search": null,
    "endpoint_mode": null,
    "env": [
       "ENVVAR1=envvar1",
       "ENVVAR2=envvar2"
    ],
    "force_update": null,
    "groups": null,
    "healthcheck": {
      "interval": 90000000000,
      "retries": 3,
      "start_period": 30000000000,
      "test": [
        "CMD",
        "curl",
        "--fail",
        "http://nginx.host.com"
      ],
      "timeout": 10000000000
    },
    "healthcheck_disabled": false,
    "hostname": null,
    "hosts": null,
    "image": "alpine:latest@sha256:b3dbf31b77fd99d9c08f780ce6f5282aba076d70a513a8be859d8d3a4d0c92b8",
    "labels": {
      "com.example.department": "Finance",
      "com.example.description": "Accounting webapp"
    },
    "limit_cpu": 0.5,
    "limit_memory": 52428800,
    "log_driver": "fluentd",
    "log_driver_options": {
      "fluentd-address": "127.0.0.1:24224",
      "fluentd-async-connect": "true",
      "tag": "myservice"
    },
    "mode": "replicated",
    "mounts": [
      {
        "readonly": false,
        "source": "/tmp/",
        "target": "/remote_tmp/",
        "type": "bind",
        "labels": null,
        "propagation": null,
        "no_copy": null,
        "driver_config": null,
        "tmpfs_size": null,
        "tmpfs_mode": null
      }
    ],
    "networks": null,
    "placement_preferences": [
      {
        "spread": "node.labels.mylabel"
      }
    ],
    "publish": null,
    "read_only": null,
    "replicas": 1,
    "reserve_cpu": 0.25,
    "reserve_memory": 20971520,
    "restart_policy": "on-failure",
    "restart_policy_attempts": 3,
    "restart_policy_delay": 5000000000,
    "restart_policy_window": 120000000000,
    "secrets": null,
    "stop_grace_period": null,
    "stop_signal": null,
    "tty": null,
    "update_delay": 10000000000,
    "update_failure_action": null,
    "update_max_failure_ratio": null,
    "update_monitor": null,
    "update_order": "stop-first",
    "update_parallelism": 2,
    "user": null,
    "working_dir": null
  }'
changes:
  returned: always
  description:
    - List of changed service attributes if a service has been altered, [] otherwise.
  type: list
  elements: str
  sample: ['container_labels', 'replicas']
rebuilt:
  returned: always
  description:
    - True if the service has been recreated (removed and created)
  type: bool
  sample: True
'''

EXAMPLES = '''
- name: Set command and arguments
  docker_swarm_service:
    name: myservice
    image: alpine
    command: sleep
    args:
      - "3600"

- name: Set a bind mount
  docker_swarm_service:
    name: myservice
    image: alpine
    mounts:
      - source: /tmp/
        target: /remote_tmp/
        type: bind

- name: Set service labels
  docker_swarm_service:
    name: myservice
    image: alpine
    labels:
      com.example.description: "Accounting webapp"
      com.example.department: "Finance"

- name: Set environment variables
  docker_swarm_service:
    name: myservice
    image: alpine
    env:
      ENVVAR1: envvar1
      ENVVAR2: envvar2
    env_files:
      - envs/common.env
      - envs/apps/web.env

- name: Set fluentd logging
  docker_swarm_service:
    name: myservice
    image: alpine
    logging:
      driver: fluentd
      options:
        fluentd-address: "127.0.0.1:24224"
        fluentd-async-connect: "true"
        tag: myservice

- name: Set restart policies
  docker_swarm_service:
    name: myservice
    image: alpine
    restart_config:
      condition: on-failure
      delay: 5s
      max_attempts: 3
      window: 120s

- name: Set update config
  docker_swarm_service:
    name: myservice
    image: alpine
    update_config:
      parallelism: 2
      delay: 10s
      order: stop-first

- name: Set rollback config
  docker_swarm_service:
    name: myservice
    image: alpine
    update_config:
      failure_action: rollback
    rollback_config:
      parallelism: 2
      delay: 10s
      order: stop-first

- name: Set placement preferences
  docker_swarm_service:
    name: myservice
    image: alpine:edge
    placement:
      preferences:
        - spread: node.labels.mylabel
      constraints:
        - node.role == manager
        - engine.labels.operatingsystem == ubuntu 14.04

- name: Set configs
  docker_swarm_service:
    name: myservice
    image: alpine:edge
    configs:
      - config_name: myconfig_name
        filename: "/tmp/config.txt"

- name: Set networks
  docker_swarm_service:
    name: myservice
    image: alpine:edge
    networks:
      - mynetwork

- name: Set networks as a dictionary
  docker_swarm_service:
    name: myservice
    image: alpine:edge
    networks:
      - name: "mynetwork"
        aliases:
          - "mynetwork_alias"
        options:
          foo: bar

- name: Set secrets
  docker_swarm_service:
    name: myservice
    image: alpine:edge
    secrets:
      - secret_name: mysecret_name
        filename: "/run/secrets/secret.txt"

- name: Start service with healthcheck
  docker_swarm_service:
    name: myservice
    image: nginx:1.13
    healthcheck:
      # Check if nginx server is healthy by curl'ing the server.
      # If this fails or timeouts, the healthcheck fails.
      test: ["CMD", "curl", "--fail", "http://nginx.host.com"]
      interval: 1m30s
      timeout: 10s
      retries: 3
      start_period: 30s

- name: Configure service resources
  docker_swarm_service:
    name: myservice
    image: alpine:edge
    reservations:
      cpus: 0.25
      memory: 20M
    limits:
      cpus: 0.50
      memory: 50M

- name: Remove service
  docker_swarm_service:
    name: myservice
    state: absent
'''

import shlex
import time
import operator
import traceback

from distutils.version import LooseVersion

from ansible.module_utils.docker.common import (
    AnsibleDockerClient,
    DifferenceTracker,
    DockerBaseClass,
    convert_duration_to_nanosecond,
    parse_healthcheck,
    clean_dict_booleans_for_docker_api,
    RequestException,
)

from ansible.module_utils.basic import human_to_bytes
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text

try:
    from docker import types
    from docker.utils import (
        parse_repository_tag,
        parse_env_file,
        format_environment,
    )
    from docker.errors import (
        APIError,
        DockerException,
        NotFound,
    )
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass


def get_docker_environment(env, env_files):
    """
    Will return a list of "KEY=VALUE" items. Supplied env variable can
    be either a list or a dictionary.

    If environment files are combined with explicit environment variables,
    the explicit environment variables take precedence.
    """
    env_dict = {}
    if env_files:
        for env_file in env_files:
            parsed_env_file = parse_env_file(env_file)
            for name, value in parsed_env_file.items():
                env_dict[name] = str(value)
    if env is not None and isinstance(env, string_types):
        env = env.split(',')
    if env is not None and isinstance(env, dict):
        for name, value in env.items():
            if not isinstance(value, string_types):
                raise ValueError(
                    'Non-string value found for env option. '
                    'Ambiguous env options must be wrapped in quotes to avoid YAML parsing. Key: %s' % name
                )
            env_dict[name] = str(value)
    elif env is not None and isinstance(env, list):
        for item in env:
            try:
                name, value = item.split('=', 1)
            except ValueError:
                raise ValueError('Invalid environment variable found in list, needs to be in format KEY=VALUE.')
            env_dict[name] = value
    elif env is not None:
        raise ValueError(
            'Invalid type for env %s (%s). Only list or dict allowed.' % (env, type(env))
        )
    env_list = format_environment(env_dict)
    if not env_list:
        if env is not None or env_files is not None:
            return []
        else:
            return None
    return sorted(env_list)


def get_docker_networks(networks, network_ids):
    """
    Validate a list of network names or a list of network dictionaries.
    Network names will be resolved to ids by using the network_ids mapping.
    """
    if networks is None:
        return None
    parsed_networks = []
    for network in networks:
        if isinstance(network, string_types):
            parsed_network = {'name': network}
        elif isinstance(network, dict):
            if 'name' not in network:
                raise TypeError(
                    '"name" is required when networks are passed as dictionaries.'
                )
            name = network.pop('name')
            parsed_network = {'name': name}
            aliases = network.pop('aliases', None)
            if aliases is not None:
                if not isinstance(aliases, list):
                    raise TypeError('"aliases" network option is only allowed as a list')
                if not all(
                    isinstance(alias, string_types) for alias in aliases
                ):
                    raise TypeError('Only strings are allowed as network aliases.')
                parsed_network['aliases'] = aliases
            options = network.pop('options', None)
            if options is not None:
                if not isinstance(options, dict):
                    raise TypeError('Only dict is allowed as network options.')
                parsed_network['options'] = clean_dict_booleans_for_docker_api(options)
            # Check if any invalid keys left
            if network:
                invalid_keys = ', '.join(network.keys())
                raise TypeError(
                    '%s are not valid keys for the networks option' % invalid_keys
                )

        else:
            raise TypeError(
                'Only a list of strings or dictionaries are allowed to be passed as networks.'
            )
        network_name = parsed_network.pop('name')
        try:
            parsed_network['id'] = network_ids[network_name]
        except KeyError as e:
            raise ValueError('Could not find a network named: %s.' % e)
        parsed_networks.append(parsed_network)
    return parsed_networks or []


def get_nanoseconds_from_raw_option(name, value):
    if value is None:
        return None
    elif isinstance(value, int):
        return value
    elif isinstance(value, string_types):
        try:
            return int(value)
        except ValueError:
            return convert_duration_to_nanosecond(value)
    else:
        raise ValueError(
            'Invalid type for %s %s (%s). Only string or int allowed.'
            % (name, value, type(value))
        )


def get_value(key, values, default=None):
    value = values.get(key)
    return value if value is not None else default


def has_dict_changed(new_dict, old_dict):
    """
    Check if new_dict has differences compared to old_dict while
    ignoring keys in old_dict which are None in new_dict.
    """
    if new_dict is None:
        return False
    if not new_dict and old_dict:
        return True
    if not old_dict and new_dict:
        return True
    defined_options = dict(
        (option, value) for option, value in new_dict.items()
        if value is not None
    )
    for option, value in defined_options.items():
        old_value = old_dict.get(option)
        if not value and not old_value:
            continue
        if value != old_value:
            return True
    return False


def has_list_changed(new_list, old_list, sort_lists=True, sort_key=None):
    """
    Check two lists have differences. Sort lists by default.
    """

    def sort_list(unsorted_list):
        """
        Sort a given list.
        The list may contain dictionaries, so use the sort key to handle them.
        """

        if unsorted_list and isinstance(unsorted_list[0], dict):
            if not sort_key:
                raise Exception(
                    'A sort key was not specified when sorting list'
                )
            else:
                return sorted(unsorted_list, key=lambda k: k[sort_key])

        # Either the list is empty or does not contain dictionaries
        try:
            return sorted(unsorted_list)
        except TypeError:
            return unsorted_list

    if new_list is None:
        return False
    old_list = old_list or []
    if len(new_list) != len(old_list):
        return True

    if sort_lists:
        zip_data = zip(sort_list(new_list), sort_list(old_list))
    else:
        zip_data = zip(new_list, old_list)
    for new_item, old_item in zip_data:
        is_same_type = type(new_item) == type(old_item)
        if not is_same_type:
            if isinstance(new_item, string_types) and isinstance(old_item, string_types):
                # Even though the types are different between these items,
                # they are both strings. Try matching on the same string type.
                try:
                    new_item_type = type(new_item)
                    old_item_casted = new_item_type(old_item)
                    if new_item != old_item_casted:
                        return True
                    else:
                        continue
                except UnicodeEncodeError:
                    # Fallback to assuming the strings are different
                    return True
            else:
                return True
        if isinstance(new_item, dict):
            if has_dict_changed(new_item, old_item):
                return True
        elif new_item != old_item:
            return True

    return False


def have_networks_changed(new_networks, old_networks):
    """Special case list checking for networks to sort aliases"""

    if new_networks is None:
        return False
    old_networks = old_networks or []
    if len(new_networks) != len(old_networks):
        return True

    zip_data = zip(
        sorted(new_networks, key=lambda k: k['id']),
        sorted(old_networks, key=lambda k: k['id'])
    )

    for new_item, old_item in zip_data:
        new_item = dict(new_item)
        old_item = dict(old_item)
        # Sort the aliases
        if 'aliases' in new_item:
            new_item['aliases'] = sorted(new_item['aliases'] or [])
        if 'aliases' in old_item:
            old_item['aliases'] = sorted(old_item['aliases'] or [])

        if has_dict_changed(new_item, old_item):
            return True

    return False


class DockerService(DockerBaseClass):
    def __init__(self, docker_api_version, docker_py_version):
        super(DockerService, self).__init__()
        self.image = ""
        self.command = None
        self.args = None
        self.endpoint_mode = None
        self.dns = None
        self.healthcheck = None
        self.healthcheck_disabled = None
        self.hostname = None
        self.hosts = None
        self.tty = None
        self.dns_search = None
        self.dns_options = None
        self.env = None
        self.force_update = None
        self.groups = None
        self.log_driver = None
        self.log_driver_options = None
        self.labels = None
        self.container_labels = None
        self.limit_cpu = None
        self.limit_memory = None
        self.reserve_cpu = None
        self.reserve_memory = None
        self.mode = "replicated"
        self.user = None
        self.mounts = None
        self.configs = None
        self.secrets = None
        self.constraints = None
        self.networks = None
        self.stop_grace_period = None
        self.stop_signal = None
        self.publish = None
        self.placement_preferences = None
        self.replicas = -1
        self.service_id = False
        self.service_version = False
        self.read_only = None
        self.restart_policy = None
        self.restart_policy_attempts = None
        self.restart_policy_delay = None
        self.restart_policy_window = None
        self.rollback_config = None
        self.update_delay = None
        self.update_parallelism = None
        self.update_failure_action = None
        self.update_monitor = None
        self.update_max_failure_ratio = None
        self.update_order = None
        self.working_dir = None

        self.docker_api_version = docker_api_version
        self.docker_py_version = docker_py_version

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
            'healthcheck': self.healthcheck,
            'healthcheck_disabled': self.healthcheck_disabled,
            'hostname': self.hostname,
            'hosts': self.hosts,
            'env': self.env,
            'force_update': self.force_update,
            'groups': self.groups,
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
            'secrets': self.secrets,
            'stop_grace_period': self.stop_grace_period,
            'stop_signal': self.stop_signal,
            'limit_cpu': self.limit_cpu,
            'limit_memory': self.limit_memory,
            'read_only': self.read_only,
            'reserve_cpu': self.reserve_cpu,
            'reserve_memory': self.reserve_memory,
            'restart_policy_delay': self.restart_policy_delay,
            'restart_policy_attempts': self.restart_policy_attempts,
            'restart_policy_window': self.restart_policy_window,
            'rollback_config': self.rollback_config,
            'update_delay': self.update_delay,
            'update_parallelism': self.update_parallelism,
            'update_failure_action': self.update_failure_action,
            'update_monitor': self.update_monitor,
            'update_max_failure_ratio': self.update_max_failure_ratio,
            'update_order': self.update_order,
            'user': self.user,
            'working_dir': self.working_dir,
        }

    @property
    def can_update_networks(self):
        # Before Docker API 1.29 adding/removing networks was not supported
        return (
            self.docker_api_version >= LooseVersion('1.29') and
            self.docker_py_version >= LooseVersion('2.7')
        )

    @property
    def can_use_task_template_networks(self):
        # In Docker API 1.25 attaching networks to TaskTemplate is preferred over Spec
        return (
            self.docker_api_version >= LooseVersion('1.25') and
            self.docker_py_version >= LooseVersion('2.7')
        )

    @staticmethod
    def get_restart_config_from_ansible_params(params):
        restart_config = params['restart_config'] or {}
        condition = get_value(
            'condition',
            restart_config,
            default=params['restart_policy']
        )
        delay = get_value(
            'delay',
            restart_config,
            default=params['restart_policy_delay']
        )
        delay = get_nanoseconds_from_raw_option(
            'restart_policy_delay',
            delay
        )
        max_attempts = get_value(
            'max_attempts',
            restart_config,
            default=params['restart_policy_attempts']
        )
        window = get_value(
            'window',
            restart_config,
            default=params['restart_policy_window']
        )
        window = get_nanoseconds_from_raw_option(
            'restart_policy_window',
            window
        )
        return {
            'restart_policy': condition,
            'restart_policy_delay': delay,
            'restart_policy_attempts': max_attempts,
            'restart_policy_window': window
        }

    @staticmethod
    def get_update_config_from_ansible_params(params):
        update_config = params['update_config'] or {}
        parallelism = get_value(
            'parallelism',
            update_config,
            default=params['update_parallelism']
        )
        delay = get_value(
            'delay',
            update_config,
            default=params['update_delay']
        )
        delay = get_nanoseconds_from_raw_option(
            'update_delay',
            delay
        )
        failure_action = get_value(
            'failure_action',
            update_config,
            default=params['update_failure_action']
        )
        monitor = get_value(
            'monitor',
            update_config,
            default=params['update_monitor']
        )
        monitor = get_nanoseconds_from_raw_option(
            'update_monitor',
            monitor
        )
        max_failure_ratio = get_value(
            'max_failure_ratio',
            update_config,
            default=params['update_max_failure_ratio']
        )
        order = get_value(
            'order',
            update_config,
            default=params['update_order']
        )
        return {
            'update_parallelism': parallelism,
            'update_delay': delay,
            'update_failure_action': failure_action,
            'update_monitor': monitor,
            'update_max_failure_ratio': max_failure_ratio,
            'update_order': order
        }

    @staticmethod
    def get_rollback_config_from_ansible_params(params):
        if params['rollback_config'] is None:
            return None
        rollback_config = params['rollback_config'] or {}
        delay = get_nanoseconds_from_raw_option(
            'rollback_config.delay',
            rollback_config.get('delay')
        )
        monitor = get_nanoseconds_from_raw_option(
            'rollback_config.monitor',
            rollback_config.get('monitor')
        )
        return {
            'parallelism': rollback_config.get('parallelism'),
            'delay': delay,
            'failure_action': rollback_config.get('failure_action'),
            'monitor': monitor,
            'max_failure_ratio': rollback_config.get('max_failure_ratio'),
            'order': rollback_config.get('order'),

        }

    @staticmethod
    def get_logging_from_ansible_params(params):
        logging_config = params['logging'] or {}
        driver = get_value(
            'driver',
            logging_config,
            default=params['log_driver']
        )
        options = get_value(
            'options',
            logging_config,
            default=params['log_driver_options']
        )
        return {
            'log_driver': driver,
            'log_driver_options': options,
        }

    @staticmethod
    def get_limits_from_ansible_params(params):
        limits = params['limits'] or {}
        cpus = get_value(
            'cpus',
            limits,
            default=params['limit_cpu']
        )
        memory = get_value(
            'memory',
            limits,
            default=params['limit_memory']
        )
        if memory is not None:
            try:
                memory = human_to_bytes(memory)
            except ValueError as exc:
                raise Exception('Failed to convert limit_memory to bytes: %s' % exc)
        return {
            'limit_cpu': cpus,
            'limit_memory': memory,
        }

    @staticmethod
    def get_reservations_from_ansible_params(params):
        reservations = params['reservations'] or {}
        cpus = get_value(
            'cpus',
            reservations,
            default=params['reserve_cpu']
        )
        memory = get_value(
            'memory',
            reservations,
            default=params['reserve_memory']
        )

        if memory is not None:
            try:
                memory = human_to_bytes(memory)
            except ValueError as exc:
                raise Exception('Failed to convert reserve_memory to bytes: %s' % exc)
        return {
            'reserve_cpu': cpus,
            'reserve_memory': memory,
        }

    @staticmethod
    def get_placement_from_ansible_params(params):
        placement = params['placement'] or {}
        constraints = get_value(
            'constraints',
            placement,
            default=params['constraints']
        )

        preferences = placement.get('preferences')
        return {
            'constraints': constraints,
            'placement_preferences': preferences,
        }

    @classmethod
    def from_ansible_params(
        cls,
        ap,
        old_service,
        image_digest,
        secret_ids,
        config_ids,
        network_ids,
        docker_api_version,
        docker_py_version,
    ):
        s = DockerService(docker_api_version, docker_py_version)
        s.image = image_digest
        s.args = ap['args']
        s.endpoint_mode = ap['endpoint_mode']
        s.dns = ap['dns']
        s.dns_search = ap['dns_search']
        s.dns_options = ap['dns_options']
        s.healthcheck, s.healthcheck_disabled = parse_healthcheck(ap['healthcheck'])
        s.hostname = ap['hostname']
        s.hosts = ap['hosts']
        s.tty = ap['tty']
        s.labels = ap['labels']
        s.container_labels = ap['container_labels']
        s.mode = ap['mode']
        s.stop_signal = ap['stop_signal']
        s.user = ap['user']
        s.working_dir = ap['working_dir']
        s.read_only = ap['read_only']

        s.networks = get_docker_networks(ap['networks'], network_ids)

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

        s.env = get_docker_environment(ap['env'], ap['env_files'])
        s.rollback_config = cls.get_rollback_config_from_ansible_params(ap)

        update_config = cls.get_update_config_from_ansible_params(ap)
        for key, value in update_config.items():
            setattr(s, key, value)

        restart_config = cls.get_restart_config_from_ansible_params(ap)
        for key, value in restart_config.items():
            setattr(s, key, value)

        logging_config = cls.get_logging_from_ansible_params(ap)
        for key, value in logging_config.items():
            setattr(s, key, value)

        limits = cls.get_limits_from_ansible_params(ap)
        for key, value in limits.items():
            setattr(s, key, value)

        reservations = cls.get_reservations_from_ansible_params(ap)
        for key, value in reservations.items():
            setattr(s, key, value)

        placement = cls.get_placement_from_ansible_params(ap)
        for key, value in placement.items():
            setattr(s, key, value)

        if ap['stop_grace_period'] is not None:
            s.stop_grace_period = convert_duration_to_nanosecond(ap['stop_grace_period'])

        if ap['force_update']:
            s.force_update = int(str(time.time()).replace('.', ''))

        if ap['groups'] is not None:
            # In case integers are passed as groups, we need to convert them to
            # strings as docker internally treats them as strings.
            s.groups = [str(g) for g in ap['groups']]

        if ap['replicas'] == -1:
            if old_service:
                s.replicas = old_service.replicas
            else:
                s.replicas = 1
        else:
            s.replicas = ap['replicas']

        if ap['publish'] is not None:
            s.publish = []
            for param_p in ap['publish']:
                service_p = {}
                service_p['protocol'] = param_p['protocol']
                service_p['mode'] = param_p['mode']
                service_p['published_port'] = param_p['published_port']
                service_p['target_port'] = param_p['target_port']
                s.publish.append(service_p)

        if ap['mounts'] is not None:
            s.mounts = []
            for param_m in ap['mounts']:
                service_m = {}
                service_m['readonly'] = param_m['readonly']
                service_m['type'] = param_m['type']
                if param_m['source'] is None and param_m['type'] != 'tmpfs':
                    raise ValueError('Source must be specified for mounts which are not of type tmpfs')
                service_m['source'] = param_m['source'] or ''
                service_m['target'] = param_m['target']
                service_m['labels'] = param_m['labels']
                service_m['no_copy'] = param_m['no_copy']
                service_m['propagation'] = param_m['propagation']
                service_m['driver_config'] = param_m['driver_config']
                service_m['tmpfs_mode'] = param_m['tmpfs_mode']
                tmpfs_size = param_m['tmpfs_size']
                if tmpfs_size is not None:
                    try:
                        tmpfs_size = human_to_bytes(tmpfs_size)
                    except ValueError as exc:
                        raise ValueError(
                            'Failed to convert tmpfs_size to bytes: %s' % exc
                        )

                service_m['tmpfs_size'] = tmpfs_size
                s.mounts.append(service_m)

        if ap['configs'] is not None:
            s.configs = []
            for param_m in ap['configs']:
                service_c = {}
                config_name = param_m['config_name']
                service_c['config_id'] = param_m['config_id'] or config_ids[config_name]
                service_c['config_name'] = config_name
                service_c['filename'] = param_m['filename'] or config_name
                service_c['uid'] = param_m['uid']
                service_c['gid'] = param_m['gid']
                service_c['mode'] = param_m['mode']
                s.configs.append(service_c)

        if ap['secrets'] is not None:
            s.secrets = []
            for param_m in ap['secrets']:
                service_s = {}
                secret_name = param_m['secret_name']
                service_s['secret_id'] = param_m['secret_id'] or secret_ids[secret_name]
                service_s['secret_name'] = secret_name
                service_s['filename'] = param_m['filename'] or secret_name
                service_s['uid'] = param_m['uid']
                service_s['gid'] = param_m['gid']
                service_s['mode'] = param_m['mode']
                s.secrets.append(service_s)

        return s

    def compare(self, os):
        differences = DifferenceTracker()
        needs_rebuild = False
        force_update = False
        if self.endpoint_mode is not None and self.endpoint_mode != os.endpoint_mode:
            differences.add('endpoint_mode', parameter=self.endpoint_mode, active=os.endpoint_mode)
        if has_list_changed(self.env, os.env):
            differences.add('env', parameter=self.env, active=os.env)
        if self.log_driver is not None and self.log_driver != os.log_driver:
            differences.add('log_driver', parameter=self.log_driver, active=os.log_driver)
        if self.log_driver_options is not None and self.log_driver_options != (os.log_driver_options or {}):
            differences.add('log_opt', parameter=self.log_driver_options, active=os.log_driver_options)
        if self.mode != os.mode:
            needs_rebuild = True
            differences.add('mode', parameter=self.mode, active=os.mode)
        if has_list_changed(self.mounts, os.mounts, sort_key='target'):
            differences.add('mounts', parameter=self.mounts, active=os.mounts)
        if has_list_changed(self.configs, os.configs, sort_key='config_name'):
            differences.add('configs', parameter=self.configs, active=os.configs)
        if has_list_changed(self.secrets, os.secrets, sort_key='secret_name'):
            differences.add('secrets', parameter=self.secrets, active=os.secrets)
        if have_networks_changed(self.networks, os.networks):
            differences.add('networks', parameter=self.networks, active=os.networks)
            needs_rebuild = not self.can_update_networks
        if self.replicas != os.replicas:
            differences.add('replicas', parameter=self.replicas, active=os.replicas)
        if has_list_changed(self.command, os.command, sort_lists=False):
            differences.add('command', parameter=self.command, active=os.command)
        if has_list_changed(self.args, os.args, sort_lists=False):
            differences.add('args', parameter=self.args, active=os.args)
        if has_list_changed(self.constraints, os.constraints):
            differences.add('constraints', parameter=self.constraints, active=os.constraints)
        if has_list_changed(self.placement_preferences, os.placement_preferences, sort_lists=False):
            differences.add('placement_preferences', parameter=self.placement_preferences, active=os.placement_preferences)
        if has_list_changed(self.groups, os.groups):
            differences.add('groups', parameter=self.groups, active=os.groups)
        if self.labels is not None and self.labels != (os.labels or {}):
            differences.add('labels', parameter=self.labels, active=os.labels)
        if self.limit_cpu is not None and self.limit_cpu != os.limit_cpu:
            differences.add('limit_cpu', parameter=self.limit_cpu, active=os.limit_cpu)
        if self.limit_memory is not None and self.limit_memory != os.limit_memory:
            differences.add('limit_memory', parameter=self.limit_memory, active=os.limit_memory)
        if self.reserve_cpu is not None and self.reserve_cpu != os.reserve_cpu:
            differences.add('reserve_cpu', parameter=self.reserve_cpu, active=os.reserve_cpu)
        if self.reserve_memory is not None and self.reserve_memory != os.reserve_memory:
            differences.add('reserve_memory', parameter=self.reserve_memory, active=os.reserve_memory)
        if self.container_labels is not None and self.container_labels != (os.container_labels or {}):
            differences.add('container_labels', parameter=self.container_labels, active=os.container_labels)
        if self.stop_signal is not None and self.stop_signal != os.stop_signal:
            differences.add('stop_signal', parameter=self.stop_signal, active=os.stop_signal)
        if self.stop_grace_period is not None and self.stop_grace_period != os.stop_grace_period:
            differences.add('stop_grace_period', parameter=self.stop_grace_period, active=os.stop_grace_period)
        if self.has_publish_changed(os.publish):
            differences.add('publish', parameter=self.publish, active=os.publish)
        if self.read_only is not None and self.read_only != os.read_only:
            differences.add('read_only', parameter=self.read_only, active=os.read_only)
        if self.restart_policy is not None and self.restart_policy != os.restart_policy:
            differences.add('restart_policy', parameter=self.restart_policy, active=os.restart_policy)
        if self.restart_policy_attempts is not None and self.restart_policy_attempts != os.restart_policy_attempts:
            differences.add('restart_policy_attempts', parameter=self.restart_policy_attempts, active=os.restart_policy_attempts)
        if self.restart_policy_delay is not None and self.restart_policy_delay != os.restart_policy_delay:
            differences.add('restart_policy_delay', parameter=self.restart_policy_delay, active=os.restart_policy_delay)
        if self.restart_policy_window is not None and self.restart_policy_window != os.restart_policy_window:
            differences.add('restart_policy_window', parameter=self.restart_policy_window, active=os.restart_policy_window)
        if has_dict_changed(self.rollback_config, os.rollback_config):
            differences.add('rollback_config', parameter=self.rollback_config, active=os.rollback_config)
        if self.update_delay is not None and self.update_delay != os.update_delay:
            differences.add('update_delay', parameter=self.update_delay, active=os.update_delay)
        if self.update_parallelism is not None and self.update_parallelism != os.update_parallelism:
            differences.add('update_parallelism', parameter=self.update_parallelism, active=os.update_parallelism)
        if self.update_failure_action is not None and self.update_failure_action != os.update_failure_action:
            differences.add('update_failure_action', parameter=self.update_failure_action, active=os.update_failure_action)
        if self.update_monitor is not None and self.update_monitor != os.update_monitor:
            differences.add('update_monitor', parameter=self.update_monitor, active=os.update_monitor)
        if self.update_max_failure_ratio is not None and self.update_max_failure_ratio != os.update_max_failure_ratio:
            differences.add('update_max_failure_ratio', parameter=self.update_max_failure_ratio, active=os.update_max_failure_ratio)
        if self.update_order is not None and self.update_order != os.update_order:
            differences.add('update_order', parameter=self.update_order, active=os.update_order)
        has_image_changed, change = self.has_image_changed(os.image)
        if has_image_changed:
            differences.add('image', parameter=self.image, active=change)
        if self.user and self.user != os.user:
            differences.add('user', parameter=self.user, active=os.user)
        if has_list_changed(self.dns, os.dns, sort_lists=False):
            differences.add('dns', parameter=self.dns, active=os.dns)
        if has_list_changed(self.dns_search, os.dns_search, sort_lists=False):
            differences.add('dns_search', parameter=self.dns_search, active=os.dns_search)
        if has_list_changed(self.dns_options, os.dns_options):
            differences.add('dns_options', parameter=self.dns_options, active=os.dns_options)
        if self.has_healthcheck_changed(os):
            differences.add('healthcheck', parameter=self.healthcheck, active=os.healthcheck)
        if self.hostname is not None and self.hostname != os.hostname:
            differences.add('hostname', parameter=self.hostname, active=os.hostname)
        if self.hosts is not None and self.hosts != (os.hosts or {}):
            differences.add('hosts', parameter=self.hosts, active=os.hosts)
        if self.tty is not None and self.tty != os.tty:
            differences.add('tty', parameter=self.tty, active=os.tty)
        if self.working_dir is not None and self.working_dir != os.working_dir:
            differences.add('working_dir', parameter=self.working_dir, active=os.working_dir)
        if self.force_update:
            force_update = True
        return not differences.empty or force_update, differences, needs_rebuild, force_update

    def has_healthcheck_changed(self, old_publish):
        if self.healthcheck_disabled is False and self.healthcheck is None:
            return False
        if self.healthcheck_disabled:
            if old_publish.healthcheck is None:
                return False
            if old_publish.healthcheck.get('test') == ['NONE']:
                return False
        return self.healthcheck != old_publish.healthcheck

    def has_publish_changed(self, old_publish):
        if self.publish is None:
            return False
        old_publish = old_publish or []
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

    def build_container_spec(self):
        mounts = None
        if self.mounts is not None:
            mounts = []
            for mount_config in self.mounts:
                mount_options = {
                    'target': 'target',
                    'source': 'source',
                    'type': 'type',
                    'readonly': 'read_only',
                    'propagation': 'propagation',
                    'labels': 'labels',
                    'no_copy': 'no_copy',
                    'driver_config': 'driver_config',
                    'tmpfs_size': 'tmpfs_size',
                    'tmpfs_mode': 'tmpfs_mode'
                }
                mount_args = {}
                for option, mount_arg in mount_options.items():
                    value = mount_config.get(option)
                    if value is not None:
                        mount_args[mount_arg] = value

                mounts.append(types.Mount(**mount_args))

        configs = None
        if self.configs is not None:
            configs = []
            for config_config in self.configs:
                config_args = {
                    'config_id': config_config['config_id'],
                    'config_name': config_config['config_name']
                }
                filename = config_config.get('filename')
                if filename:
                    config_args['filename'] = filename
                uid = config_config.get('uid')
                if uid:
                    config_args['uid'] = uid
                gid = config_config.get('gid')
                if gid:
                    config_args['gid'] = gid
                mode = config_config.get('mode')
                if mode:
                    config_args['mode'] = mode

                configs.append(types.ConfigReference(**config_args))

        secrets = None
        if self.secrets is not None:
            secrets = []
            for secret_config in self.secrets:
                secret_args = {
                    'secret_id': secret_config['secret_id'],
                    'secret_name': secret_config['secret_name']
                }
                filename = secret_config.get('filename')
                if filename:
                    secret_args['filename'] = filename
                uid = secret_config.get('uid')
                if uid:
                    secret_args['uid'] = uid
                gid = secret_config.get('gid')
                if gid:
                    secret_args['gid'] = gid
                mode = secret_config.get('mode')
                if mode:
                    secret_args['mode'] = mode

                secrets.append(types.SecretReference(**secret_args))

        dns_config_args = {}
        if self.dns is not None:
            dns_config_args['nameservers'] = self.dns
        if self.dns_search is not None:
            dns_config_args['search'] = self.dns_search
        if self.dns_options is not None:
            dns_config_args['options'] = self.dns_options
        dns_config = types.DNSConfig(**dns_config_args) if dns_config_args else None

        container_spec_args = {}
        if self.command is not None:
            container_spec_args['command'] = self.command
        if self.args is not None:
            container_spec_args['args'] = self.args
        if self.env is not None:
            container_spec_args['env'] = self.env
        if self.user is not None:
            container_spec_args['user'] = self.user
        if self.container_labels is not None:
            container_spec_args['labels'] = self.container_labels
        if self.healthcheck is not None:
            container_spec_args['healthcheck'] = types.Healthcheck(**self.healthcheck)
        elif self.healthcheck_disabled:
            container_spec_args['healthcheck'] = types.Healthcheck(test=['NONE'])
        if self.hostname is not None:
            container_spec_args['hostname'] = self.hostname
        if self.hosts is not None:
            container_spec_args['hosts'] = self.hosts
        if self.read_only is not None:
            container_spec_args['read_only'] = self.read_only
        if self.stop_grace_period is not None:
            container_spec_args['stop_grace_period'] = self.stop_grace_period
        if self.stop_signal is not None:
            container_spec_args['stop_signal'] = self.stop_signal
        if self.tty is not None:
            container_spec_args['tty'] = self.tty
        if self.groups is not None:
            container_spec_args['groups'] = self.groups
        if self.working_dir is not None:
            container_spec_args['workdir'] = self.working_dir
        if secrets is not None:
            container_spec_args['secrets'] = secrets
        if mounts is not None:
            container_spec_args['mounts'] = mounts
        if dns_config is not None:
            container_spec_args['dns_config'] = dns_config
        if configs is not None:
            container_spec_args['configs'] = configs

        return types.ContainerSpec(self.image, **container_spec_args)

    def build_placement(self):
        placement_args = {}
        if self.constraints is not None:
            placement_args['constraints'] = self.constraints
        if self.placement_preferences is not None:
            placement_args['preferences'] = [
                {key.title(): {'SpreadDescriptor': value}}
                for preference in self.placement_preferences
                for key, value in preference.items()
            ]
        return types.Placement(**placement_args) if placement_args else None

    def build_update_config(self):
        update_config_args = {}
        if self.update_parallelism is not None:
            update_config_args['parallelism'] = self.update_parallelism
        if self.update_delay is not None:
            update_config_args['delay'] = self.update_delay
        if self.update_failure_action is not None:
            update_config_args['failure_action'] = self.update_failure_action
        if self.update_monitor is not None:
            update_config_args['monitor'] = self.update_monitor
        if self.update_max_failure_ratio is not None:
            update_config_args['max_failure_ratio'] = self.update_max_failure_ratio
        if self.update_order is not None:
            update_config_args['order'] = self.update_order
        return types.UpdateConfig(**update_config_args) if update_config_args else None

    def build_log_driver(self):
        log_driver_args = {}
        if self.log_driver is not None:
            log_driver_args['name'] = self.log_driver
        if self.log_driver_options is not None:
            log_driver_args['options'] = self.log_driver_options
        return types.DriverConfig(**log_driver_args) if log_driver_args else None

    def build_restart_policy(self):
        restart_policy_args = {}
        if self.restart_policy is not None:
            restart_policy_args['condition'] = self.restart_policy
        if self.restart_policy_delay is not None:
            restart_policy_args['delay'] = self.restart_policy_delay
        if self.restart_policy_attempts is not None:
            restart_policy_args['max_attempts'] = self.restart_policy_attempts
        if self.restart_policy_window is not None:
            restart_policy_args['window'] = self.restart_policy_window
        return types.RestartPolicy(**restart_policy_args) if restart_policy_args else None

    def build_rollback_config(self):
        if self.rollback_config is None:
            return None
        rollback_config_options = [
            'parallelism',
            'delay',
            'failure_action',
            'monitor',
            'max_failure_ratio',
            'order',
        ]
        rollback_config_args = {}
        for option in rollback_config_options:
            value = self.rollback_config.get(option)
            if value is not None:
                rollback_config_args[option] = value
        return types.RollbackConfig(**rollback_config_args) if rollback_config_args else None

    def build_resources(self):
        resources_args = {}
        if self.limit_cpu is not None:
            resources_args['cpu_limit'] = int(self.limit_cpu * 1000000000.0)
        if self.limit_memory is not None:
            resources_args['mem_limit'] = self.limit_memory
        if self.reserve_cpu is not None:
            resources_args['cpu_reservation'] = int(self.reserve_cpu * 1000000000.0)
        if self.reserve_memory is not None:
            resources_args['mem_reservation'] = self.reserve_memory
        return types.Resources(**resources_args) if resources_args else None

    def build_task_template(self, container_spec, placement=None):
        log_driver = self.build_log_driver()
        restart_policy = self.build_restart_policy()
        resources = self.build_resources()

        task_template_args = {}
        if placement is not None:
            task_template_args['placement'] = placement
        if log_driver is not None:
            task_template_args['log_driver'] = log_driver
        if restart_policy is not None:
            task_template_args['restart_policy'] = restart_policy
        if resources is not None:
            task_template_args['resources'] = resources
        if self.force_update:
            task_template_args['force_update'] = self.force_update
        if self.can_use_task_template_networks:
            networks = self.build_networks()
            if networks:
                task_template_args['networks'] = networks
        return types.TaskTemplate(container_spec=container_spec, **task_template_args)

    def build_service_mode(self):
        if self.mode == 'global':
            self.replicas = None
        return types.ServiceMode(self.mode, replicas=self.replicas)

    def build_networks(self):
        networks = None
        if self.networks is not None:
            networks = []
            for network in self.networks:
                docker_network = {'Target': network['id']}
                if 'aliases' in network:
                    docker_network['Aliases'] = network['aliases']
                if 'options' in network:
                    docker_network['DriverOpts'] = network['options']
                networks.append(docker_network)
        return networks

    def build_endpoint_spec(self):
        endpoint_spec_args = {}
        if self.publish is not None:
            ports = []
            for port in self.publish:
                port_spec = {
                    'Protocol': port['protocol'],
                    'PublishedPort': port['published_port'],
                    'TargetPort': port['target_port']
                }
                if port.get('mode'):
                    port_spec['PublishMode'] = port['mode']
                ports.append(port_spec)
            endpoint_spec_args['ports'] = ports
        if self.endpoint_mode is not None:
            endpoint_spec_args['mode'] = self.endpoint_mode
        return types.EndpointSpec(**endpoint_spec_args) if endpoint_spec_args else None

    def build_docker_service(self):
        container_spec = self.build_container_spec()
        placement = self.build_placement()
        task_template = self.build_task_template(container_spec, placement)

        update_config = self.build_update_config()
        rollback_config = self.build_rollback_config()
        service_mode = self.build_service_mode()
        endpoint_spec = self.build_endpoint_spec()

        service = {'task_template': task_template, 'mode': service_mode}
        if update_config:
            service['update_config'] = update_config
        if rollback_config:
            service['rollback_config'] = rollback_config
        if endpoint_spec:
            service['endpoint_spec'] = endpoint_spec
        if self.labels:
            service['labels'] = self.labels
        if not self.can_use_task_template_networks:
            networks = self.build_networks()
            if networks:
                service['networks'] = networks
        return service


class DockerServiceManager(object):

    def __init__(self, client):
        self.client = client
        self.retries = 2
        self.diff_tracker = None

    def get_service(self, name):
        try:
            raw_data = self.client.inspect_service(name)
        except NotFound:
            return None
        ds = DockerService(self.client.docker_api_version, self.client.docker_py_version)

        task_template_data = raw_data['Spec']['TaskTemplate']
        ds.image = task_template_data['ContainerSpec']['Image']
        ds.user = task_template_data['ContainerSpec'].get('User')
        ds.env = task_template_data['ContainerSpec'].get('Env')
        ds.command = task_template_data['ContainerSpec'].get('Command')
        ds.args = task_template_data['ContainerSpec'].get('Args')
        ds.groups = task_template_data['ContainerSpec'].get('Groups')
        ds.stop_grace_period = task_template_data['ContainerSpec'].get('StopGracePeriod')
        ds.stop_signal = task_template_data['ContainerSpec'].get('StopSignal')
        ds.working_dir = task_template_data['ContainerSpec'].get('Dir')
        ds.read_only = task_template_data['ContainerSpec'].get('ReadOnly')

        healthcheck_data = task_template_data['ContainerSpec'].get('Healthcheck')
        if healthcheck_data:
            options = {
                'Test': 'test',
                'Interval': 'interval',
                'Timeout': 'timeout',
                'StartPeriod': 'start_period',
                'Retries': 'retries'
            }
            healthcheck = dict(
                (options[key], value) for key, value in healthcheck_data.items()
                if value is not None and key in options
            )
            ds.healthcheck = healthcheck

        update_config_data = raw_data['Spec'].get('UpdateConfig')
        if update_config_data:
            ds.update_delay = update_config_data.get('Delay')
            ds.update_parallelism = update_config_data.get('Parallelism')
            ds.update_failure_action = update_config_data.get('FailureAction')
            ds.update_monitor = update_config_data.get('Monitor')
            ds.update_max_failure_ratio = update_config_data.get('MaxFailureRatio')
            ds.update_order = update_config_data.get('Order')

        rollback_config_data = raw_data['Spec'].get('RollbackConfig')
        if rollback_config_data:
            ds.rollback_config = {
                'parallelism': rollback_config_data.get('Parallelism'),
                'delay': rollback_config_data.get('Delay'),
                'failure_action': rollback_config_data.get('FailureAction'),
                'monitor': rollback_config_data.get('Monitor'),
                'max_failure_ratio': rollback_config_data.get('MaxFailureRatio'),
                'order': rollback_config_data.get('Order'),
            }

        dns_config = task_template_data['ContainerSpec'].get('DNSConfig')
        if dns_config:
            ds.dns = dns_config.get('Nameservers')
            ds.dns_search = dns_config.get('Search')
            ds.dns_options = dns_config.get('Options')

        ds.hostname = task_template_data['ContainerSpec'].get('Hostname')

        hosts = task_template_data['ContainerSpec'].get('Hosts')
        if hosts:
            hosts = [
                list(reversed(host.split(":", 1)))
                if ":" in host
                else host.split(" ", 1)
                for host in hosts
            ]
            ds.hosts = dict((hostname, ip) for ip, hostname in hosts)
        ds.tty = task_template_data['ContainerSpec'].get('TTY')

        placement = task_template_data.get('Placement')
        if placement:
            ds.constraints = placement.get('Constraints')
            placement_preferences = []
            for preference in placement.get('Preferences', []):
                placement_preferences.append(
                    dict(
                        (key.lower(), value['SpreadDescriptor'])
                        for key, value in preference.items()
                    )
                )
            ds.placement_preferences = placement_preferences or None

        restart_policy_data = task_template_data.get('RestartPolicy')
        if restart_policy_data:
            ds.restart_policy = restart_policy_data.get('Condition')
            ds.restart_policy_delay = restart_policy_data.get('Delay')
            ds.restart_policy_attempts = restart_policy_data.get('MaxAttempts')
            ds.restart_policy_window = restart_policy_data.get('Window')

        raw_data_endpoint_spec = raw_data['Spec'].get('EndpointSpec')
        if raw_data_endpoint_spec:
            ds.endpoint_mode = raw_data_endpoint_spec.get('Mode')
            raw_data_ports = raw_data_endpoint_spec.get('Ports')
            if raw_data_ports:
                ds.publish = []
                for port in raw_data_ports:
                    ds.publish.append({
                        'protocol': port['Protocol'],
                        'mode': port.get('PublishMode', None),
                        'published_port': int(port['PublishedPort']),
                        'target_port': int(port['TargetPort'])
                    })

        raw_data_limits = task_template_data.get('Resources', {}).get('Limits')
        if raw_data_limits:
            raw_cpu_limits = raw_data_limits.get('NanoCPUs')
            if raw_cpu_limits:
                ds.limit_cpu = float(raw_cpu_limits) / 1000000000

            raw_memory_limits = raw_data_limits.get('MemoryBytes')
            if raw_memory_limits:
                ds.limit_memory = int(raw_memory_limits)

        raw_data_reservations = task_template_data.get('Resources', {}).get('Reservations')
        if raw_data_reservations:
            raw_cpu_reservations = raw_data_reservations.get('NanoCPUs')
            if raw_cpu_reservations:
                ds.reserve_cpu = float(raw_cpu_reservations) / 1000000000

            raw_memory_reservations = raw_data_reservations.get('MemoryBytes')
            if raw_memory_reservations:
                ds.reserve_memory = int(raw_memory_reservations)

        ds.labels = raw_data['Spec'].get('Labels')
        ds.log_driver = task_template_data.get('LogDriver', {}).get('Name')
        ds.log_driver_options = task_template_data.get('LogDriver', {}).get('Options')
        ds.container_labels = task_template_data['ContainerSpec'].get('Labels')

        mode = raw_data['Spec']['Mode']
        if 'Replicated' in mode.keys():
            ds.mode = to_text('replicated', encoding='utf-8')
            ds.replicas = mode['Replicated']['Replicas']
        elif 'Global' in mode.keys():
            ds.mode = 'global'
        else:
            raise Exception('Unknown service mode: %s' % mode)

        raw_data_mounts = task_template_data['ContainerSpec'].get('Mounts')
        if raw_data_mounts:
            ds.mounts = []
            for mount_data in raw_data_mounts:
                bind_options = mount_data.get('BindOptions', {})
                volume_options = mount_data.get('VolumeOptions', {})
                tmpfs_options = mount_data.get('TmpfsOptions', {})
                driver_config = volume_options.get('DriverConfig', {})
                driver_config = dict(
                    (key.lower(), value) for key, value in driver_config.items()
                ) or None
                ds.mounts.append({
                    'source': mount_data.get('Source', ''),
                    'type': mount_data['Type'],
                    'target': mount_data['Target'],
                    'readonly': mount_data.get('ReadOnly'),
                    'propagation': bind_options.get('Propagation'),
                    'no_copy': volume_options.get('NoCopy'),
                    'labels': volume_options.get('Labels'),
                    'driver_config': driver_config,
                    'tmpfs_mode': tmpfs_options.get('Mode'),
                    'tmpfs_size': tmpfs_options.get('SizeBytes'),
                })

        raw_data_configs = task_template_data['ContainerSpec'].get('Configs')
        if raw_data_configs:
            ds.configs = []
            for config_data in raw_data_configs:
                ds.configs.append({
                    'config_id': config_data['ConfigID'],
                    'config_name': config_data['ConfigName'],
                    'filename': config_data['File'].get('Name'),
                    'uid': config_data['File'].get('UID'),
                    'gid': config_data['File'].get('GID'),
                    'mode': config_data['File'].get('Mode')
                })

        raw_data_secrets = task_template_data['ContainerSpec'].get('Secrets')
        if raw_data_secrets:
            ds.secrets = []
            for secret_data in raw_data_secrets:
                ds.secrets.append({
                    'secret_id': secret_data['SecretID'],
                    'secret_name': secret_data['SecretName'],
                    'filename': secret_data['File'].get('Name'),
                    'uid': secret_data['File'].get('UID'),
                    'gid': secret_data['File'].get('GID'),
                    'mode': secret_data['File'].get('Mode')
                })

        raw_networks_data = task_template_data.get('Networks', raw_data['Spec'].get('Networks'))
        if raw_networks_data:
            ds.networks = []
            for network_data in raw_networks_data:
                network = {'id': network_data['Target']}
                if 'Aliases' in network_data:
                    network['aliases'] = network_data['Aliases']
                if 'DriverOpts' in network_data:
                    network['options'] = network_data['DriverOpts']
                ds.networks.append(network)
        ds.service_version = raw_data['Version']['Index']
        ds.service_id = raw_data['ID']
        return ds

    def update_service(self, name, old_service, new_service):
        service_data = new_service.build_docker_service()
        result = self.client.update_service(
            old_service.service_id,
            old_service.service_version,
            name=name,
            **service_data
        )
        # Prior to Docker SDK 4.0.0 no warnings were returned and will thus be ignored.
        # (see https://github.com/docker/docker-py/pull/2272)
        self.client.report_warnings(result, ['Warning'])

    def create_service(self, name, service):
        service_data = service.build_docker_service()
        result = self.client.create_service(name=name, **service_data)
        self.client.report_warnings(result, ['Warning'])

    def remove_service(self, name):
        self.client.remove_service(name)

    def get_image_digest(self, name, resolve=False):
        if (
            not name
            or not resolve
        ):
            return name
        repo, tag = parse_repository_tag(name)
        if not tag:
            tag = 'latest'
        name = repo + ':' + tag
        distribution_data = self.client.inspect_distribution(name)
        digest = distribution_data['Descriptor']['digest']
        return '%s@%s' % (name, digest)

    def get_networks_names_ids(self):
        return dict(
            (network['Name'], network['Id']) for network in self.client.networks()
        )

    def get_missing_secret_ids(self):
        """
        Resolve missing secret ids by looking them up by name
        """
        secret_names = [
            secret['secret_name']
            for secret in self.client.module.params.get('secrets') or []
            if secret['secret_id'] is None
        ]
        if not secret_names:
            return {}
        secrets = self.client.secrets(filters={'name': secret_names})
        secrets = dict(
            (secret['Spec']['Name'], secret['ID'])
            for secret in secrets
            if secret['Spec']['Name'] in secret_names
        )
        for secret_name in secret_names:
            if secret_name not in secrets:
                self.client.fail(
                    'Could not find a secret named "%s"' % secret_name
                )
        return secrets

    def get_missing_config_ids(self):
        """
        Resolve missing config ids by looking them up by name
        """
        config_names = [
            config['config_name']
            for config in self.client.module.params.get('configs') or []
            if config['config_id'] is None
        ]
        if not config_names:
            return {}
        configs = self.client.configs(filters={'name': config_names})
        configs = dict(
            (config['Spec']['Name'], config['ID'])
            for config in configs
            if config['Spec']['Name'] in config_names
        )
        for config_name in config_names:
            if config_name not in configs:
                self.client.fail(
                    'Could not find a config named "%s"' % config_name
                )
        return configs

    def run(self):
        self.diff_tracker = DifferenceTracker()
        module = self.client.module

        image = module.params['image']
        try:
            image_digest = self.get_image_digest(
                name=image,
                resolve=module.params['resolve_image']
            )
        except DockerException as e:
            self.client.fail(
                'Error looking for an image named %s: %s'
                % (image, e)
            )

        try:
            current_service = self.get_service(module.params['name'])
        except Exception as e:
            self.client.fail(
                'Error looking for service named %s: %s'
                % (module.params['name'], e)
            )
        try:
            secret_ids = self.get_missing_secret_ids()
            config_ids = self.get_missing_config_ids()
            network_ids = self.get_networks_names_ids()
            new_service = DockerService.from_ansible_params(
                module.params,
                current_service,
                image_digest,
                secret_ids,
                config_ids,
                network_ids,
                self.client.docker_api_version,
                self.client.docker_py_version
            )
        except Exception as e:
            return self.client.fail(
                'Error parsing module parameters: %s' % e
            )

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
                changed, differences, need_rebuild, force_update = new_service.compare(
                    current_service
                )
                if changed:
                    self.diff_tracker.merge(differences)
                    if need_rebuild:
                        if not module.check_mode:
                            self.remove_service(module.params['name'])
                            self.create_service(
                                module.params['name'],
                                new_service
                            )
                        msg = 'Service rebuilt'
                        rebuilt = True
                    else:
                        if not module.check_mode:
                            self.update_service(
                                module.params['name'],
                                current_service,
                                new_service
                            )
                        msg = 'Service updated'
                        rebuilt = False
                else:
                    if force_update:
                        if not module.check_mode:
                            self.update_service(
                                module.params['name'],
                                current_service,
                                new_service
                            )
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
                    self.create_service(module.params['name'], new_service)
                msg = 'Service created'
                changed = True
                facts = new_service.get_facts()

        return msg, changed, rebuilt, differences.get_legacy_docker_diffs(), facts

    def run_safe(self):
        while True:
            try:
                return self.run()
            except APIError as e:
                # Sometimes Version.Index will have changed between an inspect and
                # update. If this is encountered we'll retry the update.
                if self.retries > 0 and 'update out of sequence' in str(e.explanation):
                    self.retries -= 1
                    time.sleep(1)
                else:
                    raise


def _detect_publish_mode_usage(client):
    for publish_def in client.module.params['publish'] or []:
        if publish_def.get('mode'):
            return True
    return False


def _detect_healthcheck_start_period(client):
    if client.module.params['healthcheck']:
        return client.module.params['healthcheck']['start_period'] is not None
    return False


def _detect_mount_tmpfs_usage(client):
    for mount in client.module.params['mounts'] or []:
        if mount.get('type') == 'tmpfs':
            return True
        if mount.get('tmpfs_size') is not None:
            return True
        if mount.get('tmpfs_mode') is not None:
            return True
    return False


def _detect_update_config_failure_action_rollback(client):
    rollback_config_failure_action = (
        (client.module.params['update_config'] or {}).get('failure_action')
    )
    update_failure_action = client.module.params['update_failure_action']
    failure_action = rollback_config_failure_action or update_failure_action
    return failure_action == 'rollback'


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        image=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        mounts=dict(type='list', elements='dict', options=dict(
            source=dict(type='str'),
            target=dict(type='str', required=True),
            type=dict(
                type='str',
                default='bind',
                choices=['bind', 'volume', 'tmpfs', 'npipe'],
            ),
            readonly=dict(type='bool'),
            labels=dict(type='dict'),
            propagation=dict(
                type='str',
                choices=[
                    'shared',
                    'slave',
                    'private',
                    'rshared',
                    'rslave',
                    'rprivate'
                ]
            ),
            no_copy=dict(type='bool'),
            driver_config=dict(type='dict', options=dict(
                name=dict(type='str'),
                options=dict(type='dict')
            )),
            tmpfs_size=dict(type='str'),
            tmpfs_mode=dict(type='int')
        )),
        configs=dict(type='list', elements='dict', options=dict(
            config_id=dict(type='str'),
            config_name=dict(type='str', required=True),
            filename=dict(type='str'),
            uid=dict(type='str'),
            gid=dict(type='str'),
            mode=dict(type='int'),
        )),
        secrets=dict(type='list', elements='dict', options=dict(
            secret_id=dict(type='str'),
            secret_name=dict(type='str', required=True),
            filename=dict(type='str'),
            uid=dict(type='str'),
            gid=dict(type='str'),
            mode=dict(type='int'),
        )),
        networks=dict(type='list', elements='raw'),
        command=dict(type='raw'),
        args=dict(type='list', elements='str'),
        env=dict(type='raw'),
        env_files=dict(type='list', elements='path'),
        force_update=dict(type='bool', default=False),
        groups=dict(type='list', elements='str'),
        logging=dict(type='dict', options=dict(
            driver=dict(type='str'),
            options=dict(type='dict'),
        )),
        log_driver=dict(type='str', removed_in_version='2.12'),
        log_driver_options=dict(type='dict', removed_in_version='2.12'),
        publish=dict(type='list', elements='dict', options=dict(
            published_port=dict(type='int', required=True),
            target_port=dict(type='int', required=True),
            protocol=dict(type='str', default='tcp', choices=['tcp', 'udp']),
            mode=dict(type='str', choices=['ingress', 'host']),
        )),
        placement=dict(type='dict', options=dict(
            constraints=dict(type='list', elements='str'),
            preferences=dict(type='list', elements='dict'),
        )),
        constraints=dict(type='list', elements='str', removed_in_version='2.12'),
        tty=dict(type='bool'),
        dns=dict(type='list', elements='str'),
        dns_search=dict(type='list', elements='str'),
        dns_options=dict(type='list', elements='str'),
        healthcheck=dict(type='dict', options=dict(
            test=dict(type='raw'),
            interval=dict(type='str'),
            timeout=dict(type='str'),
            start_period=dict(type='str'),
            retries=dict(type='int'),
        )),
        hostname=dict(type='str'),
        hosts=dict(type='dict'),
        labels=dict(type='dict'),
        container_labels=dict(type='dict'),
        mode=dict(
            type='str',
            default='replicated',
            choices=['replicated', 'global']
        ),
        replicas=dict(type='int', default=-1),
        endpoint_mode=dict(type='str', choices=['vip', 'dnsrr']),
        stop_grace_period=dict(type='str'),
        stop_signal=dict(type='str'),
        limits=dict(type='dict', options=dict(
            cpus=dict(type='float'),
            memory=dict(type='str'),
        )),
        limit_cpu=dict(type='float', removed_in_version='2.12'),
        limit_memory=dict(type='str', removed_in_version='2.12'),
        read_only=dict(type='bool'),
        reservations=dict(type='dict', options=dict(
            cpus=dict(type='float'),
            memory=dict(type='str'),
        )),
        reserve_cpu=dict(type='float', removed_in_version='2.12'),
        reserve_memory=dict(type='str', removed_in_version='2.12'),
        resolve_image=dict(type='bool', default=False),
        restart_config=dict(type='dict', options=dict(
            condition=dict(type='str', choices=['none', 'on-failure', 'any']),
            delay=dict(type='str'),
            max_attempts=dict(type='int'),
            window=dict(type='str'),
        )),
        restart_policy=dict(
            type='str',
            choices=['none', 'on-failure', 'any'],
            removed_in_version='2.12'
        ),
        restart_policy_delay=dict(type='raw', removed_in_version='2.12'),
        restart_policy_attempts=dict(type='int', removed_in_version='2.12'),
        restart_policy_window=dict(type='raw', removed_in_version='2.12'),
        rollback_config=dict(type='dict', options=dict(
            parallelism=dict(type='int'),
            delay=dict(type='str'),
            failure_action=dict(
                type='str',
                choices=['continue', 'pause']
            ),
            monitor=dict(type='str'),
            max_failure_ratio=dict(type='float'),
            order=dict(type='str'),
        )),
        update_config=dict(type='dict', options=dict(
            parallelism=dict(type='int'),
            delay=dict(type='str'),
            failure_action=dict(
                type='str',
                choices=['continue', 'pause', 'rollback']
            ),
            monitor=dict(type='str'),
            max_failure_ratio=dict(type='float'),
            order=dict(type='str'),
        )),
        update_delay=dict(type='raw', removed_in_version='2.12'),
        update_parallelism=dict(type='int', removed_in_version='2.12'),
        update_failure_action=dict(
            type='str',
            choices=['continue', 'pause', 'rollback'],
            removed_in_version='2.12'
        ),
        update_monitor=dict(type='raw', removed_in_version='2.12'),
        update_max_failure_ratio=dict(type='float', removed_in_version='2.12'),
        update_order=dict(
            type='str',
            choices=['stop-first', 'start-first'],
            removed_in_version='2.12'
        ),
        user=dict(type='str'),
        working_dir=dict(type='str'),
    )

    option_minimal_versions = dict(
        constraints=dict(docker_py_version='2.4.0'),
        dns=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
        dns_options=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
        dns_search=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
        endpoint_mode=dict(docker_py_version='3.0.0', docker_api_version='1.25'),
        force_update=dict(docker_py_version='2.1.0', docker_api_version='1.25'),
        healthcheck=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
        hostname=dict(docker_py_version='2.2.0', docker_api_version='1.25'),
        hosts=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
        groups=dict(docker_py_version='2.6.0', docker_api_version='1.25'),
        tty=dict(docker_py_version='2.4.0', docker_api_version='1.25'),
        secrets=dict(docker_py_version='2.4.0', docker_api_version='1.25'),
        configs=dict(docker_py_version='2.6.0', docker_api_version='1.30'),
        update_max_failure_ratio=dict(docker_py_version='2.1.0', docker_api_version='1.25'),
        update_monitor=dict(docker_py_version='2.1.0', docker_api_version='1.25'),
        update_order=dict(docker_py_version='2.7.0', docker_api_version='1.29'),
        stop_signal=dict(docker_py_version='2.6.0', docker_api_version='1.28'),
        publish=dict(docker_py_version='3.0.0', docker_api_version='1.25'),
        read_only=dict(docker_py_version='2.6.0', docker_api_version='1.28'),
        resolve_image=dict(docker_api_version='1.30', docker_py_version='3.2.0'),
        rollback_config=dict(docker_py_version='3.5.0', docker_api_version='1.28'),
        # specials
        publish_mode=dict(
            docker_py_version='3.0.0',
            docker_api_version='1.25',
            detect_usage=_detect_publish_mode_usage,
            usage_msg='set publish.mode'
        ),
        healthcheck_start_period=dict(
            docker_py_version='2.6.0',
            docker_api_version='1.29',
            detect_usage=_detect_healthcheck_start_period,
            usage_msg='set healthcheck.start_period'
        ),
        update_config_max_failure_ratio=dict(
            docker_py_version='2.1.0',
            docker_api_version='1.25',
            detect_usage=lambda c: (c.module.params['update_config'] or {}).get(
                'max_failure_ratio'
            ) is not None,
            usage_msg='set update_config.max_failure_ratio'
        ),
        update_config_failure_action=dict(
            docker_py_version='3.5.0',
            docker_api_version='1.28',
            detect_usage=_detect_update_config_failure_action_rollback,
            usage_msg='set update_config.failure_action.rollback'
        ),
        update_config_monitor=dict(
            docker_py_version='2.1.0',
            docker_api_version='1.25',
            detect_usage=lambda c: (c.module.params['update_config'] or {}).get(
                'monitor'
            ) is not None,
            usage_msg='set update_config.monitor'
        ),
        update_config_order=dict(
            docker_py_version='2.7.0',
            docker_api_version='1.29',
            detect_usage=lambda c: (c.module.params['update_config'] or {}).get(
                'order'
            ) is not None,
            usage_msg='set update_config.order'
        ),
        placement_config_preferences=dict(
            docker_py_version='2.4.0',
            docker_api_version='1.27',
            detect_usage=lambda c: (c.module.params['placement'] or {}).get(
                'preferences'
            ) is not None,
            usage_msg='set placement.preferences'
        ),
        placement_config_constraints=dict(
            docker_py_version='2.4.0',
            detect_usage=lambda c: (c.module.params['placement'] or {}).get(
                'constraints'
            ) is not None,
            usage_msg='set placement.constraints'
        ),
        mounts_tmpfs=dict(
            docker_py_version='2.6.0',
            detect_usage=_detect_mount_tmpfs_usage,
            usage_msg='set mounts.tmpfs'
        ),
        rollback_config_order=dict(
            docker_api_version='1.29',
            detect_usage=lambda c: (c.module.params['rollback_config'] or {}).get(
                'order'
            ) is not None,
            usage_msg='set rollback_config.order'
        ),
    )
    required_if = [
        ('state', 'present', ['image'])
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
        min_docker_version='2.0.2',
        min_docker_api_version='1.24',
        option_minimal_versions=option_minimal_versions,
    )

    try:
        dsm = DockerServiceManager(client)
        msg, changed, rebuilt, changes, facts = dsm.run_safe()

        results = dict(
            msg=msg,
            changed=changed,
            rebuilt=rebuilt,
            changes=changes,
            swarm_service=facts,
        )
        if client.module._diff:
            before, after = dsm.diff_tracker.get_before_after()
            results['diff'] = dict(before=before, after=after)

        client.module.exit_json(**results)
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
