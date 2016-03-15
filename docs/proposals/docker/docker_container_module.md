# Docker_Container Module Proposal

## Purpose and Scope:

The purpose of docker_container is to manage the lifecycle of a container. The module will provide a mechanism for
moving the container between absent, present, stopped and started states. It will focus purely on managing container
state. The intention of the narrow focus is to make understanding and using the module clear and keep maintenance
and testing as easy as possible.

Docker_container will manage a container using docker-py to communicate with either a local or remote API. It will
support API versions >= 1.14. API connection details will be handled externally in a shared utility module similar to
how other cloud modules operate.

The container world is moving rapidly, so the goal is to create a suite of docker modules that keep pace, with docker_container
leading the way. If this project is successful, it will naturally deprecate the existing docker module.

## Parameters:

Docker_container will accept the parameters listed below. An attempt has been made to represent all the options available to
docker's create, kill, pause, run, rm, start, stop and update commands.

Parameters for connecting to the API are not listed here. They are included in the common utility module mentioned above.

```
blkio_weight:
  description:
    - Block IO (relative weight), between 10 and 1000.
  default: null

capabilities:
  description:
    - List of capabilities to add to the container.
  default: null

command:
  description:
    - Command or list of commands to execute in the container when it starts.
  default: null

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
  default: null

cpuset_mems:
  description:
    - Memory nodes (MEMs) in which to allow execution C(0-3) or C(0,1)
  default: null

cpu_shares:
  description:
    - CPU shares (relative weight).
  default: null 

detach:
  description:
    - Enable detached mode to leave the container running in background. 
      If disabled, fail unless the process exits cleanly.
  default: true

devices:
  description:
    - List of host device bindings to add to the container. Each binding is a mapping expressed
      in the format: <path_on_host>:<path_in_container>:<cgroup_permissions> 
  default: null

dns_servers:
  description:
    - List of custom DNS servers.
  default: null

dns_search_domains:
  description:
    - List of custom DNS search domains.
  default: null

env:
  description:
    - Dictionary of key,value pairs.
  default: null

entrypoint:
  description:
    - String or list of commands that overwrite the default ENTRYPOINT of the image.
  default: null

etc_hosts:
  description:
    - Dict of host-to-IP mappings, where each host name is key in the dictionary. Hostname will be added to the 
      container's /etc/hosts file.
  default: null

exposed_ports:
  description:
    - List of additional container ports to expose for port mappings or links.
      If the port is already exposed using EXPOSE in a Dockerfile, it does not
      need to be exposed again.
  default: null
  aliases:
    - exposed

force_kill:
  description:
    - Use with absent, present, started and stopped states to use the kill command rather
      than the stop command.
  default: false

groups:
  description:
    - List of additional group names and/or IDs that the container process will run as. 
  default: null

hostname:
  description:
    - Container hostname.
  default: null

image:
  description:
    - Container image used to create and match containers.
  required: true

interactive:
  description:
    - Keep stdin open after a container is launched, even if not attached.
  default: false

ipc_mode:
  description:
    - Set the IPC mode for the container. Can be one of 
      'container:<name|id>' to reuse another container's IPC namespace
      or 'host' to use the host's IPC namespace within the container.
  default: null

keep_volumes:
  description:
    - Retain volumes associated with a removed container.
  default: false

kill_signal:
  description:
    - Override default signal used to kill a running container.
  default null:

kernel_memory:
  description:
    - Kernel memory limit (format: <number>[<unit>]). Number is a positive integer.
      Unit can be one of b, k, m, or g. Minimum is 4M.
  default: 0

labels:
   description:
     - Dictionary of key value pairs.
   default: null

links:
  description:
    - List of name aliases for linked containers in the format C(container_name:alias)
  default: null

log_driver:
  description:
    - Specify the logging driver.
  choices:
    - json-file
    - syslog
    - journald
    - gelf
    - fluentd
    - awslogs
    - splunk
  defult: json-file

log_options:
  description:
    - Dictionary of options specific to the chosen log_driver. See https://docs.docker.com/engine/admin/logging/overview/ 
      for details.
  required: false
  default: null

mac_address:
  description:
    - Container MAC address (e.g. 92:d0:c6:0a:29:33)
default: null

memory:
  description:
    - Memory limit (format: <number>[<unit>]). Number is a positive integer.
      Unit can be one of b, k, m, or g
  default: 0

memory_reservation:
  description:
    - Memory soft limit (format: <number>[<unit>]). Number is a positive integer.
      Unit can be one of b, k, m, or g
  default: 0

memory_swap:
  description:
    - Total memory limit (memory + swap, format:<number>[<unit>]).
      Number is a positive integer. Unit can be one of b, k, m, or g.
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
    - Connect the container to a network.
  choices:
    - bridge
    - container:<name|id>
    - host
    - none
  default: null

networks:
  description:
    - Dictionary of networks to which the container will be connected. The dictionary must have a name key (the name of the network).
      Optional keys include: aliases (a list of container aliases), and links (a list of links in the format C(container_name:alias)).
  default: null

oom_killer:
  desription:
    - Whether or not to disable OOM Killer for the container.
  default: false

paused:
  description:
    - Use with the started state to pause running processes inside the container.
  default: false

pid_mode:
  description:
    - Set the PID namespace mode for the container. Currenly only supports 'host'.
  default: null

privileged:
  description:
    - Give extended privileges to the container.
  default: false

published_ports:
  description:
    - List of ports to publish from the container to the host.
    - Use docker CLI syntax: C(8000), C(9000:8000), or C(0.0.0.0:9000:8000), where 8000 is a
      container port, 9000 is a host port, and 0.0.0.0 is a host interface.
    - Container ports must be exposed either in the Dockerfile or via the C(expose) option.
    - A value of ALL will publish all exposed container ports to random host ports, ignoring
      any other mappings.
  aliases:
    - ports

read_only:
  description:
    - Mount the container's root file system as read-only.
  default: false

recreate:
  description:
    - Use with present and started states to force the re-creation of an existing container.
  default: false

restart:
  description:
    - Use with started state to force a matching container to be stopped and restarted.
  default: false

restart_policy:
  description:
    - Container restart policy.
  choices:
    - on-failure
    - always
  default: on-failure 

restart_retries:
   description:
     - Use with restart policy to control maximum number of restart attempts.
   default: 0 

shm_size:
  description:
    - Size of `/dev/shm`. The format is `<number><unit>`. `number` must be greater than `0`. 
      Unit is optional and can be `b` (bytes), `k` (kilobytes), `m` (megabytes), or `g` (gigabytes).
    - Ommitting the unit defaults to bytes. If you omit the size entirely, the system uses `64m`.
  default: null

security_opts:
  description:
    - List of security options in the form of C("label:user:User")
  default: null

state:
  description:
    - "absent" - A container matching the specified name will be stopped and removed. Use force_kill to kill the container
       rather than stopping it. Use keep_volumes to retain volumes associated with the removed container.

    - "present" - Asserts the existence of a container matching the name and any provided configuration parameters. If no
      container matches the name, a container will be created. If a container matches the name but the provided configuration
      does not match, the container will be updated, if it can be. If it cannot be updated, it will be removed and re-created
      with the requested config. Use recreate to force the re-creation of the matching container. Use force_kill to kill the
      container rather than stopping it. Use keep_volumes to retain volumes associated with a removed container.

    - "started" - Asserts there is a running container matching the name and any provided configuration. If no container
      matches the name, a container will be created and started. If a container matching the name is found but the
      configuration does not match, the container will be updated, if it can be. If it cannot be updated, it will be removed
      and a new container will be created with the requested configuration and started. Use recreate to always re-create a 
      matching container, even if it is running. Use restart to force a matching container to be stopped and restarted. Use
      force_kill to kill a container rather than stopping it. Use keep_volumes to retain volumes associated with a removed
      container.

    - "stopped" - a container matching the specified name will be stopped. Use force_kill to kill a container rather than
      stopping it.

  required: false
  default: started
  choices:
    - absent
    - present
    - stopped
    - started

stop_signal:
  description:
    - Override default signal used to stop the container.
  default: null 

stop_timeout:
  description:
    - Number of seconds to wait for the container to stop before sending SIGKILL.
  required: false

trust_image_content:
  description:
    - If true, skip image verification.
  default: false

tty:
  description:
    - Allocate a psuedo-TTY.
  default: false

ulimits:
  description:
    - List of ulimit options. A ulimit is specified as C(nofile:262144:262144)
  default: null

user:
  description
    - Sets the username or UID used and optionally the groupname or GID for the specified command.
    - Can be [ user | user:group | uid | uid:gid | user:gid | uid:group ]
  default: null

uts:
  description:
    - Set the UTS namespace mode for the container.
  default: null

volumes:
  description:
    - List of volumes to mount within the container.
    - 'Use docker CLI-style syntax: C(/host:/container[:mode])'
    - You can specify a read mode for the mount with either C(ro) or C(rw).
    - SELinux hosts can additionally use C(z) or C(Z) to use a shared or 
      private label for the volume.
default: null

volume_driver:
  description:
    - The container's volume driver.
  default: none

volumes_from:
  description:
    - List of container names or Ids to get volumes from. 
  default: null
```


## Examples:

```
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
    expose:
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
    recreate: yes
    forcekill: yes
    image: someplace/image
    command: echo "I'm here!"


- name: Start 4 load-balanced containers
  docker_container:
    name: "container{{ item }}"
    state: started
    recreate: yes
    image: someuser/anotherappimage
    command: sleep 1d
  with_sequence: count=4

-name: remove container
  docker_container:
    name: ohno
    state: absent

- name: Syslogging output 
  docker_container:
    name: myservice
    state: started 
    log_driver: syslog
    log_opt:
      syslog-address: tcp://my-syslog-server:514
      syslog-facility: daemon
      syslog-tag: myservice

```

## Returns:

The JSON object returned by the module will include a *results* object providing `docker inspect` output for the affected container.

```
{
    changed: True,
    failed: False,
    rc: 0
    results: {
        < the results of `docker inspect` >
    }
}
```
