#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Cove Schneider
# Copyright: (c) 2014, Joshua Conner <joshua.conner@gmail.com>
# Copyright: (c) 2014, Pavel Antonov <antonov@adwz.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: docker
version_added: "1.4"
short_description: manage docker containers
deprecated:
  removed_in: "2.4"
  why: Replaced by dedicated modules.
  alternative: Use M(docker_container) and M(docker_image) instead.
description:
  - This is the original Ansible module for managing the Docker container life cycle.
  - NOTE - Additional and newer modules are available. For the latest on orchestrating containers with Ansible
    visit our Getting Started with Docker Guide at U(https://github.com/ansible/ansible/blob/devel/docs/docsite/rst/scenario_guides/guide_docker.rst).
options:
  count:
    description:
      - Number of matching containers that should be in the desired state.
    default: 1
  image:
    description:
      - Container image used to match and launch containers.
    required: true
  pull:
    description:
      - Control when container images are updated from the C(docker_url) registry.
      - If C(missing), images will be pulled only when missing from the host;
      - if C(always), the registry will be checked for a newer version of the image each time the task executes.
    choices: [ always, missing ]
    default: missing
    version_added: "1.9"
  entrypoint:
    description:
      - Corresponds to C(--entrypoint) option of C(docker run) command and
        C(ENTRYPOINT) directive of Dockerfile.
      - Used to match and launch containers.
    version_added: "2.1"
  command:
    description:
      - Command used to match and launch containers.
  name:
    description:
      - Name used to match and uniquely name launched containers. Explicit names
        are used to uniquely identify a single container or to link among
        containers. Mutually exclusive with a "count" other than "1".
    version_added: "1.5"
  ports:
    description:
      - "List containing private to public port mapping specification.
        Use docker 'CLI-style syntax: C(8000), C(9000:8000), or C(0.0.0.0:9000:8000)'
        where 8000 is a container port, 9000 is a host port, and 0.0.0.0 is - a host interface.
        The container ports need to be exposed either in the Dockerfile or via the C(expose) option."
    version_added: "1.5"
  expose:
    description:
      - List of additional container ports to expose for port mappings or links.
        If the port is already exposed using EXPOSE in a Dockerfile, you don't
        need to expose it again.
    version_added: "1.5"
  publish_all_ports:
    description:
      - Publish all exposed ports to the host interfaces.
    type: bool
    default: 'no'
    version_added: "1.5"
  volumes:
    description:
      - List of volumes to mount within the container.
      - 'Use docker CLI-style syntax: C(/host:/container[:mode])'
      - You can specify a read mode for the mount with either C(ro) or C(rw).
        Starting at version 2.1, SELinux hosts can additionally use C(z) or C(Z)
        mount options to use a shared or private label for the volume.
  volumes_from:
    description:
      - List of names of containers to mount volumes from.
  links:
    description:
      - List of other containers to link within this container with an optional.
      - 'alias. Use docker CLI-style syntax: C(redis:myredis).'
    version_added: "1.5"
  devices:
    description:
      - List of host devices to expose to container.
    version_added: "2.1"
  log_driver:
    description:
      - You can specify a different logging driver for the container than for the daemon.
      - C(awslogs) - (added in 2.1) Awslogs logging driver for Docker. Writes log messages to AWS Cloudwatch Logs.
      - C(fluentd) - Fluentd logging driver for Docker. Writes log messages to "fluentd" (forward input).
      - C(gelf) - Graylog Extended Log Format (GELF) logging driver for Docker. Writes log messages to a GELF endpoint likeGraylog or Logstash.
      - C(journald) - Journald logging driver for Docker. Writes log messages to "journald".
      - C(json-file) - Default logging driver for Docker. Writes JSON messages to file.
        docker logs command is available only for this logging driver.
      - C(none) - disables any logging for the container.
      - C(syslog) - Syslog logging driver for Docker. Writes log messages to syslog.
        docker logs command is not available for this logging driver.
      - Requires docker >= 1.6.0.
    default: json-file
    choices:
      - awslogs
      - fluentd
      - gelf
      - journald
      - json-file
      - none
      - syslog
    version_added: "2.0"
  log_opt:
    description:
      - Additional options to pass to the logging driver selected above. See Docker `log-driver
        <https://docs.docker.com/reference/logging/overview/>` documentation for more information.
        Requires docker >=1.7.0.
    version_added: "2.0"
  memory_limit:
    description:
      - RAM allocated to the container as a number of bytes or as a human-readable
        string like "512MB".
      - Leave as "0" to specify no limit.
    default: 0
  docker_url:
    description:
      - URL of the host running the docker daemon. This will default to the env
        var DOCKER_HOST if unspecified.
    default: ${DOCKER_HOST} or unix://var/run/docker.sock
  use_tls:
    description:
      - Whether to use tls to connect to the docker server.  "no" means not to
        use tls (and ignore any other tls related parameters). "encrypt" means
        to use tls to encrypt the connection to the server.  "verify" means to
        also verify that the server's certificate is valid for the server
        (this both verifies the certificate against the CA and that the
        certificate was issued for that host. If this is unspecified, tls will
        only be used if one of the other tls options require it.
    choices: [ encrypt, no, verify ]
    version_added: "1.9"
  tls_client_cert:
    description:
      - Path to the PEM-encoded certificate used to authenticate docker client.
        If specified tls_client_key must be valid
    default: ${DOCKER_CERT_PATH}/cert.pem
    version_added: "1.9"
  tls_client_key:
    description:
      - Path to the PEM-encoded key used to authenticate docker client. If
        specified tls_client_cert must be valid
    default: ${DOCKER_CERT_PATH}/key.pem
    version_added: "1.9"
  tls_ca_cert:
    description:
      - Path to a PEM-encoded certificate authority to secure the Docker connection.
        This has no effect if use_tls is encrypt.
    default: ${DOCKER_CERT_PATH}/ca.pem
    version_added: "1.9"
  tls_hostname:
    description:
      - A hostname to check matches what's supplied in the docker server's
        certificate.  If unspecified, the hostname is taken from the docker_url.
    default: Taken from docker_url
    version_added: "1.9"
  docker_api_version:
    description:
      - Remote API version to use. This defaults to the current default as
        specified by docker-py.
    default: docker-py default remote API version
    version_added: "1.8"
  docker_user:
    description:
      - Username or UID to use within the container
    version_added: "2.0"
  username:
    description:
      - Remote API username.
  password:
    description:
      - Remote API password.
  email:
    description:
      - Remote API email.
  hostname:
    description:
      - Container hostname.
  domainname:
    description:
      - Container domain name.
  env:
    description:
      - Pass a dict of environment variables to the container.
  env_file:
    description:
      - Pass in a path to a file with environment variable (FOO=BAR).
        If a key value is present in both explicitly presented (i.e. as 'env')
        and in the environment file, the explicit value will override.
        Requires docker-py >= 1.4.0.
    version_added: "2.1"
  dns:
    description:
      - List of custom DNS servers for the container.
  detach:
    description:
      - Enable detached mode to leave the container running in background. If
        disabled, fail unless the process exits cleanly.
    type: bool
    default: 'yes'
  signal:
    description:
      - With the state "killed", you can alter the signal sent to the
        container.
    default: KILL
    version_added: "2.0"
  state:
    description:
      - Assert the container's desired state. "present" only asserts that the
        matching containers exist. "started" asserts that the matching
        containers both exist and are running, but takes no action if any
        configuration has changed. "reloaded" (added in Ansible 1.9) asserts that all matching
        containers are running and restarts any that have any images or
        configuration out of date. "restarted" unconditionally restarts (or
        starts) the matching containers. "stopped" and '"killed" stop and kill
        all matching containers. "absent" stops and then' removes any matching
        containers.
    default: started
    choices:
      - absent
      - killed
      - present
      - reloaded
      - restarted
      - started
      - stopped
  privileged:
    description:
      - Whether the container should run in privileged mode or not.
    type: bool
    default: 'no'
  lxc_conf:
    description:
      - LXC configuration parameters, such as C(lxc.aa_profile:unconfined).
  stdin_open:
    description:
      - Keep stdin open after a container is launched.
    type: bool
    default: 'no'
    version_added: "1.6"
  tty:
    description:
      - Allocate a pseudo-tty within the container.
    type: bool
    default: 'no'
    version_added: "1.6"
  net:
    description:
      - 'Network mode for the launched container: bridge, none, container:<name|id>'
      - or host.
      - Requires docker >= 0.11.
    type: bool
    default: 'no'
    version_added: "1.8"
  pid:
    description:
      - Set the PID namespace mode for the container (currently only supports 'host').
      - Requires docker-py >= 1.0.0 and docker >= 1.5.0
    version_added: "1.9"
  registry:
    description:
      - Remote registry URL to pull images from.
    default: DockerHub
    version_added: "1.8"
  read_only:
    description:
      - Mount the container's root filesystem as read only.
    version_added: "2.0"
  restart_policy:
    description:
      - Container restart policy.
      - The 'unless-stopped' choice is only available starting in Ansible 2.1 and for Docker 1.9 and above.
    choices: [ always, no, on-failure, unless-stopped ]
    version_added: "1.9"
  restart_policy_retry:
    description:
      - Maximum number of times to restart a container.
      - Leave as "0" for unlimited retries.
    default: 0
    version_added: "1.9"
  extra_hosts:
    description:
    - Dict of custom host-to-IP mappings to be defined in the container
    version_added: "2.0"
  insecure_registry:
    description:
      - Use insecure private registry by HTTP instead of HTTPS.
      - Needed for docker-py >= 0.5.0.
    type: bool
    default: 'no'
    version_added: "1.9"
  cpu_set:
    description:
      - CPUs in which to allow execution.
      - Requires docker-py >= 0.6.0.
    version_added: "2.0"
  cap_add:
    description:
      - Add capabilities for the container.
      - Requires docker-py >= 0.5.0.
    type: bool
    default: 'no'
    version_added: "2.0"
  cap_drop:
    description:
      - Drop capabilities for the container.
      - Requires docker-py >= 0.5.0.
    type: bool
    default: 'no'
    version_added: "2.0"
  labels:
    description:
      - Set container labels.
      - Requires docker >= 1.6 and docker-py >= 1.2.0.
    version_added: "2.1"
  stop_timeout:
    description:
      - How many seconds to wait for the container to stop before killing it.
    default: 10
    version_added: "2.0"
  timeout:
    description:
      - Docker daemon response timeout in seconds.
    default: 60
    version_added: "2.1"
  cpu_shares:
    description:
      - CPU shares (relative weight).
      - Requires docker-py >= 0.6.0.
    default: 0
    version_added: "2.1"
  ulimits:
    description:
      - ulimits, list ulimits with name, soft and optionally
        hard limit separated by colons. e.g. C(nofile:1024:2048)
      - Requires docker-py >= 1.2.0 and docker >= 1.6.0
    version_added: "2.1"

author:
    - Cove Schneider (@cove)
    - Joshua Conner (@joshuaconner)
    - Pavel Antonov (@softzilla)
    - Thomas Steinbach (@ThomasSteinbach)
    - Philippe Jandot (@zfil)
    - Daan Oosterveld (@dusdanig)
requirements:
    - python >= 2.6
    - docker-py >= 0.3.0
    - The docker server >= 0.10.0
'''

EXAMPLES = '''
# Containers are matched either by name (if provided) or by an exact match of
# the image they were launched with and the command they're running. The module
# can accept either a name to target a container uniquely, or a count to operate
# on multiple containers at once when it makes sense to do so.

# Ensure that a data container with the name "mydata" exists. If no container
# by this name exists, it will be created, but not started.

- name: data container
  docker:
    name: mydata
    image: busybox
    state: present
    volumes:
    - /data

# Ensure that a Redis server is running, using the volume from the data
# container. Expose the default Redis port.

- name: redis container
  docker:
    name: myredis
    image: redis
    command: redis-server --appendonly yes
    state: started
    expose:
    - 6379
    volumes_from:
    - mydata

# Ensure that a container of your application server is running. This will:
# - pull the latest version of your application image from DockerHub.
# - ensure that a container is running with the specified name and exact image.
#   If any configuration options have changed, the existing container will be
#   stopped and removed, and a new one will be launched in its place.
# - link this container to the existing redis container launched above with
#   an alias.
# - grant the container read write permissions for the host's /dev/sda device
#   through a node named /dev/xvda
# - bind TCP port 9000 within the container to port 8080 on all interfaces
#   on the host.
# - bind UDP port 9001 within the container to port 8081 on the host, only
#   listening on localhost.
# - specify 2 ip resolutions.
# - set the environment variable SECRET_KEY to "ssssh".

- name: application container
  docker:
    name: myapplication
    image: someuser/appimage
    state: reloaded
    pull: always
    links:
    - "myredis:aliasedredis"
    devices:
    - "/dev/sda:/dev/xvda:rwm"
    ports:
    - "8080:9000"
    - "127.0.0.1:8081:9001/udp"
    extra_hosts:
      host1: "192.168.0.1"
      host2: "192.168.0.2"
    env:
      SECRET_KEY: ssssh

# Ensure that exactly five containers of another server are running with this
# exact image and command. If fewer than five are running, more will be launched;
# if more are running, the excess will be stopped.

- name: load-balanced containers
  docker:
    state: reloaded
    count: 5
    image: someuser/anotherappimage
    command: sleep 1d

# Unconditionally restart a service container. This may be useful within a
# handler, for example.

- name: application service
  docker:
    name: myservice
    image: someuser/serviceimage
    state: restarted

# Stop all containers running the specified image.

- name: obsolete container
  docker:
    image: someuser/oldandbusted
    state: stopped

# Stop and remove a container with the specified name.

- name: obsolete container
  docker:
    name: ohno
    image: someuser/oldandbusted
    state: absent

# Example Syslogging Output

- name: myservice container
  docker:
    name: myservice
    image: someservice/someimage
    state: reloaded
    log_driver: syslog
    log_opt:
      syslog-address: tcp://my-syslog-server:514
      syslog-facility: daemon
      syslog-tag: myservice
'''

from ansible.module_utils.common.removed import removed_module

if __name__ == '__main__':
    removed_module()
