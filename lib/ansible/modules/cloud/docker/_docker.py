#!/usr/bin/python

# (c) 2013, Cove Schneider
# (c) 2014, Joshua Conner <joshua.conner@gmail.com>
# (c) 2014, Pavel Antonov <antonov@adwz.ru>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: docker
version_added: "1.4"
short_description: manage docker containers
deprecated: In 2.2 use M(docker_container) and M(docker_image) instead.
description:
  - This is the original Ansible module for managing the Docker container life cycle.
  - "NOTE: Additional and newer modules are available. For the latest on orchestrating containers with Ansible
    visit our Getting Started with Docker Guide at U(https://github.com/ansible/ansible/blob/devel/docs/docsite/rst/guide_docker.rst)."
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
        If "missing," images will be pulled only when missing from the host;
        if '"always," the registry will be checked for a newer version of the
        image' each time the task executes.
    default: missing
    choices: [ "missing", "always" ]
    version_added: "1.9"
  entrypoint:
    description:
      - Corresponds to ``--entrypoint`` option of ``docker run`` command and
        ``ENTRYPOINT`` directive of Dockerfile.
        Used to match and launch containers.
    default: null
    required: false
    version_added: "2.1"
  command:
    description:
      - Command used to match and launch containers.
    default: null
  name:
    description:
      - Name used to match and uniquely name launched containers. Explicit names
        are used to uniquely identify a single container or to link among
        containers. Mutually exclusive with a "count" other than "1".
    default: null
    version_added: "1.5"
  ports:
    description:
      - "List containing private to public port mapping specification.
        Use docker 'CLI-style syntax: C(8000), C(9000:8000), or C(0.0.0.0:9000:8000)'
        where 8000 is a container port, 9000 is a host port, and 0.0.0.0 is - a host interface.
        The container ports need to be exposed either in the Dockerfile or via the C(expose) option."
    default: null
    version_added: "1.5"
  expose:
    description:
      - List of additional container ports to expose for port mappings or links.
        If the port is already exposed using EXPOSE in a Dockerfile, you don't
        need to expose it again.
    default: null
    version_added: "1.5"
  publish_all_ports:
    description:
      - Publish all exposed ports to the host interfaces.
    default: false
    version_added: "1.5"
  volumes:
    description:
      - List of volumes to mount within the container
      - 'Use docker CLI-style syntax: C(/host:/container[:mode])'
      - You can specify a read mode for the mount with either C(ro) or C(rw).
        Starting at version 2.1, SELinux hosts can additionally use C(z) or C(Z)
        mount options to use a shared or private label for the volume.
    default: null
  volumes_from:
    description:
      - List of names of containers to mount volumes from.
    default: null
  links:
    description:
      - List of other containers to link within this container with an optional
      - 'alias. Use docker CLI-style syntax: C(redis:myredis).'
    default: null
    version_added: "1.5"
  devices:
    description:
      - List of host devices to expose to container
    default: null
    required: false
    version_added: "2.1"
  log_driver:
    description:
      - You can specify a different logging driver for the container than for the daemon.
        "json-file" Default logging driver for Docker. Writes JSON messages to file.
        docker logs command is available only for this logging driver.
        "none" disables any logging for the container.
        "syslog" Syslog logging driver for Docker. Writes log messages to syslog.
        docker logs command is not available for this logging driver.
        "journald" Journald logging driver for Docker. Writes log messages to "journald".
        "gelf" Graylog Extended Log Format (GELF) logging driver for Docker. Writes log messages to a GELF endpoint likeGraylog or Logstash.
        "fluentd" Fluentd logging driver for Docker. Writes log messages to "fluentd" (forward input).
        "awslogs" (added in 2.1) Awslogs logging driver for Docker. Writes log messages to AWS Cloudwatch Logs.
        If not defined explicitly, the Docker daemon's default ("json-file") will apply.
        Requires docker >= 1.6.0.
    required: false
    default: json-file
    choices:
      - json-file
      - none
      - syslog
      - journald
      - gelf
      - fluentd
      - awslogs
    version_added: "2.0"
  log_opt:
    description:
      - Additional options to pass to the logging driver selected above. See Docker `log-driver
        <https://docs.docker.com/reference/logging/overview/>` documentation for more information.
        Requires docker >=1.7.0.
    required: false
    default: null
    version_added: "2.0"
  memory_limit:
    description:
      - RAM allocated to the container as a number of bytes or as a human-readable
        string like "512MB". Leave as "0" to specify no limit.
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
    choices: [ "no", "encrypt", "verify" ]
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
    required: false
    default: null
    version_added: "2.0"
  username:
    description:
      - Remote API username.
    default: null
  password:
    description:
      - Remote API password.
    default: null
  email:
    description:
      - Remote API email.
    default: null
  hostname:
    description:
      - Container hostname.
    default: null
  domainname:
    description:
      - Container domain name.
    default: null
  env:
    description:
      - Pass a dict of environment variables to the container.
    default: null
  env_file:
    version_added: "2.1"
    description:
      - Pass in a path to a file with environment variable (FOO=BAR).
        If a key value is present in both explicitly presented (i.e. as 'env')
        and in the environment file, the explicit value will override.
        Requires docker-py >= 1.4.0.
    default: null
    required: false
  dns:
    description:
      - List of custom DNS servers for the container.
    required: false
    default: null
  detach:
    description:
      - Enable detached mode to leave the container running in background. If
        disabled, fail unless the process exits cleanly.
    default: true
  signal:
    version_added: "2.0"
    description:
      - With the state "killed", you can alter the signal sent to the
        container.
    required: false
    default: KILL
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
    required: false
    default: started
    choices:
      - present
      - started
      - reloaded
      - restarted
      - stopped
      - killed
      - absent
  privileged:
    description:
      - Whether the container should run in privileged mode or not.
    default: false
  lxc_conf:
    description:
      - LXC configuration parameters, such as C(lxc.aa_profile:unconfined).
    default: null
  stdin_open:
    description:
      - Keep stdin open after a container is launched.
    default: false
    version_added: "1.6"
  tty:
    description:
      - Allocate a pseudo-tty within the container.
    default: false
    version_added: "1.6"
  net:
    description:
      - 'Network mode for the launched container: bridge, none, container:<name|id>'
      - or host. Requires docker >= 0.11.
    default: false
    version_added: "1.8"
  pid:
    description:
      - Set the PID namespace mode for the container (currently only supports 'host'). Requires docker-py >= 1.0.0 and docker >= 1.5.0
    required: false
    default: None
    aliases: []
    version_added: "1.9"
  registry:
    description:
      - Remote registry URL to pull images from.
    default: DockerHub
    aliases: []
    version_added: "1.8"
  read_only:
    description:
      - Mount the container's root filesystem as read only
    default: null
    aliases: []
    version_added: "2.0"
  restart_policy:
    description:
      - Container restart policy.
      - The 'unless-stopped' choice is only available starting in Ansible 2.1 and for Docker 1.9 and above.
    choices: ["no", "on-failure", "always", "unless-stopped"]
    default: null
    version_added: "1.9"
  restart_policy_retry:
    description:
      - Maximum number of times to restart a container. Leave as "0" for unlimited
        retries.
    default: 0
    version_added: "1.9"
  extra_hosts:
    version_added: "2.0"
    description:
    - Dict of custom host-to-IP mappings to be defined in the container
  insecure_registry:
    description:
      - Use insecure private registry by HTTP instead of HTTPS. Needed for
        docker-py >= 0.5.0.
    default: false
    version_added: "1.9"
  cpu_set:
    description:
      - CPUs in which to allow execution. Requires docker-py >= 0.6.0.
    required: false
    default: null
    version_added: "2.0"
  cap_add:
    description:
      - Add capabilities for the container. Requires docker-py >= 0.5.0.
    required: false
    default: false
    version_added: "2.0"
  cap_drop:
    description:
      - Drop capabilities for the container. Requires docker-py >= 0.5.0.
    required: false
    default: false
    aliases: []
    version_added: "2.0"
  labels:
    description:
      - Set container labels. Requires docker >= 1.6 and docker-py >= 1.2.0.
    required: false
    default: null
    version_added: "2.1"
  stop_timeout:
    description:
      - How many seconds to wait for the container to stop before killing it.
    required: false
    default: 10
    version_added: "2.0"
  timeout:
    description:
      - Docker daemon response timeout in seconds.
    required: false
    default: 60
    version_added: "2.1"
  cpu_shares:
    description:
      - CPU shares (relative weight). Requires docker-py >= 0.6.0.
    required: false
    default: 0
    version_added: "2.1"
  ulimits:
    description:
      - ulimits, list ulimits with name, soft and optionally
        hard limit separated by colons. e.g. nofile:1024:2048
        Requires docker-py >= 1.2.0 and docker >= 1.6.0
    required: false
    default: null
    version_added: "2.1"

author:
    - "Cove Schneider (@cove)"
    - "Joshua Conner (@joshuaconner)"
    - "Pavel Antonov (@softzilla)"
    - "Thomas Steinbach (@ThomasSteinbach)"
    - "Philippe Jandot (@zfil)"
    - "Daan Oosterveld (@dusdanig)"
requirements:
    - "python >= 2.6"
    - "docker-py >= 0.3.0"
    - "The docker server >= 0.10.0"
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

import json
import os
import shlex
try:
    from urlparse import urlparse
except ImportError:
    # python3
    from urllib.parse import urlparse

try:
    import docker.client
    import docker.utils
    import docker.errors
    from requests.exceptions import RequestException
    HAS_DOCKER_PY = True
except ImportError:
    HAS_DOCKER_PY = False

DEFAULT_DOCKER_API_VERSION = None
DEFAULT_TIMEOUT_SECONDS = 60
if HAS_DOCKER_PY:
    try:
        from docker.errors import APIError as DockerAPIError
    except ImportError:
        from docker.client import APIError as DockerAPIError
    try:
        # docker-py 1.2+
        import docker.constants
        DEFAULT_DOCKER_API_VERSION = docker.constants.DEFAULT_DOCKER_API_VERSION
        DEFAULT_TIMEOUT_SECONDS = docker.constants.DEFAULT_TIMEOUT_SECONDS
    except (ImportError, AttributeError):
        # docker-py less than 1.2
        DEFAULT_DOCKER_API_VERSION = docker.client.DEFAULT_DOCKER_API_VERSION
        DEFAULT_TIMEOUT_SECONDS = docker.client.DEFAULT_TIMEOUT_SECONDS

from ansible.module_utils.basic import AnsibleModule


def _human_to_bytes(number):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    if isinstance(number, int):
        return number
    if number.isdigit():
        return int(number)
    if number[-1] == suffixes[0] and number[-2].isdigit():
        return number[:-1]

    i = 1
    for each in suffixes[1:]:
        if number[-len(each):] == suffixes[i]:
            return int(number[:-len(each)]) * (1024 ** i)
        i = i + 1

    raise ValueError('Could not convert %s to integer' % (number,))


def _ansible_facts(container_list):
    return {"docker_containers": container_list}


def _docker_id_quirk(inspect):
    # XXX: some quirk in docker
    if 'ID' in inspect:
        inspect['Id'] = inspect['ID']
        del inspect['ID']
    return inspect


def get_split_image_tag(image):
    # If image contains a host or org name, omit that from our check
    if '/' in image:
        registry, resource = image.rsplit('/', 1)
    else:
        registry, resource = None, image

    # now we can determine if image has a tag or a digest
    for s in ['@',':']:
        if s in resource:
            resource, tag = resource.split(s, 1)
            if registry:
                resource = '/'.join((registry, resource))
            break
    else:
        tag = "latest"
        resource = image

    return resource, tag

def normalize_image(image):
    """
    Normalize a Docker image name to include the implied :latest tag.
    """

    return ":".join(get_split_image_tag(image))


def is_running(container):
    '''Return True if an inspected container is in a state we consider "running."'''

    return container['State']['Running'] is True and not container['State'].get('Ghost', False)


def get_docker_py_versioninfo():
    if hasattr(docker, '__version__'):
        # a '__version__' attribute was added to the module but not until
        # after 0.3.0 was pushed to pypi. If it's there, use it.
        version = []
        for part in docker.__version__.split('.'):
            try:
                version.append(int(part))
            except ValueError:
                for idx, char in enumerate(part):
                    if not char.isdigit():
                        nondigit = part[idx:]
                        digit = part[:idx]
                        break
                if digit:
                    version.append(int(digit))
                if nondigit:
                    version.append(nondigit)
    elif hasattr(docker.Client, '_get_raw_response_socket'):
        # HACK: if '__version__' isn't there, we check for the existence of
        # `_get_raw_response_socket` in the docker.Client class, which was
        # added in 0.3.0
        version = (0, 3, 0)
    else:
        # This is untrue but this module does not function with a version less
        # than 0.3.0 so it's okay to lie here.
        version = (0,)

    return tuple(version)


def check_dependencies(module):
    """
    Ensure `docker-py` >= 0.3.0 is installed, and call module.fail_json with a
    helpful error message if it isn't.
    """
    if not HAS_DOCKER_PY:
        module.fail_json(msg="`docker-py` doesn't seem to be installed, but is required for the Ansible Docker module.")
    else:
        versioninfo = get_docker_py_versioninfo()
        if versioninfo < (0, 3, 0):
            module.fail_json(msg="The Ansible Docker module requires `docker-py` >= 0.3.0.")


class DockerManager(object):

    counters = dict(
        created=0, started=0, stopped=0, killed=0, removed=0, restarted=0, pulled=0
    )
    reload_reasons = []
    _capabilities = set()

    # Map optional parameters to minimum (docker-py version, server APIVersion)
    # docker-py version is a tuple of ints because we have to compare them
    # server APIVersion is passed to a docker-py function that takes strings
    _cap_ver_req = {
        'devices': ((0, 7, 0), '1.2'),
        'dns': ((0, 3, 0), '1.10'),
        'volumes_from': ((0, 3, 0), '1.10'),
        'restart_policy': ((0, 5, 0), '1.14'),
        'extra_hosts': ((0, 7, 0), '1.3.1'),
        'pid': ((1, 0, 0), '1.17'),
        'log_driver': ((1, 2, 0), '1.18'),
        'log_opt': ((1, 2, 0), '1.18'),
        'host_config': ((0, 7, 0), '1.15'),
        'cpu_set': ((0, 6, 0), '1.14'),
        'cap_add': ((0, 5, 0), '1.14'),
        'cap_drop': ((0, 5, 0), '1.14'),
        'read_only': ((1, 0, 0), '1.17'),
        'labels': ((1, 2, 0), '1.18'),
        'stop_timeout': ((0, 5, 0), '1.0'),
        'ulimits': ((1, 2, 0), '1.18'),
        # Clientside only
        'insecure_registry': ((0, 5, 0), '0.0'),
        'env_file': ((1, 4, 0), '0.0')
        }

    def __init__(self, module):
        self.module = module

        self.binds = None
        self.volumes = None
        if self.module.params.get('volumes'):
            self.binds = []
            self.volumes = []
            vols = self.module.params.get('volumes')
            for vol in vols:
                parts = vol.split(":")
                # regular volume
                if len(parts) == 1:
                    self.volumes.append(parts[0])
                # host mount (e.g. /mnt:/tmp, bind mounts host's /tmp to /mnt in the container)
                elif 2 <= len(parts) <= 3:
                    # default to read-write
                    mode = 'rw'
                    # with supplied bind mode
                    if len(parts) == 3:
                        if parts[2] not in ["rw", "rw,Z", "rw,z", "z,rw", "Z,rw", "Z", "z", "ro", "ro,Z", "ro,z", "z,ro", "Z,ro"]:
                            self.module.fail_json(msg='invalid bind mode ' + parts[2])
                        else:
                            mode = parts[2]
                    self.binds.append("%s:%s:%s" % (parts[0], parts[1], mode))
                else:
                    self.module.fail_json(msg='volumes support 1 to 3 arguments')

        self.lxc_conf = None
        if self.module.params.get('lxc_conf'):
            self.lxc_conf = []
            options = self.module.params.get('lxc_conf')
            for option in options:
                parts = option.split(':', 1)
                self.lxc_conf.append({"Key": parts[0], "Value": parts[1]})

        self.exposed_ports = None
        if self.module.params.get('expose'):
            self.exposed_ports = self.get_exposed_ports(self.module.params.get('expose'))

        self.port_bindings = None
        if self.module.params.get('ports'):
            self.port_bindings = self.get_port_bindings(self.module.params.get('ports'))

        self.links = None
        if self.module.params.get('links'):
            self.links = self.get_links(self.module.params.get('links'))

        self.ulimits = None
        if self.module.params.get('ulimits'):
            self.ulimits = []
            ulimits = self.module.params.get('ulimits')
            for ulimit in ulimits:
                parts = ulimit.split(":")
                if len(parts) == 2:
                    self.ulimits.append({'name': parts[0], 'soft': int(parts[1]), 'hard': int(parts[1])})
                elif len(parts) == 3:
                    self.ulimits.append({'name': parts[0], 'soft': int(parts[1]), 'hard': int(parts[2])})
                else:
                    self.module.fail_json(msg='ulimits support 2 to 3 arguments')

        # Connect to the docker server using any configured host and TLS settings.

        env_host = os.getenv('DOCKER_HOST')
        env_docker_verify = os.getenv('DOCKER_TLS_VERIFY')
        env_cert_path = os.getenv('DOCKER_CERT_PATH')
        env_docker_hostname = os.getenv('DOCKER_TLS_HOSTNAME')

        docker_url = module.params.get('docker_url')
        if not docker_url:
            if env_host:
                docker_url = env_host
            else:
                docker_url = 'unix://var/run/docker.sock'

        docker_api_version = module.params.get('docker_api_version')
        timeout = module.params.get('timeout')

        tls_client_cert = module.params.get('tls_client_cert', None)
        if not tls_client_cert and env_cert_path:
            tls_client_cert = os.path.join(env_cert_path, 'cert.pem')

        tls_client_key = module.params.get('tls_client_key', None)
        if not tls_client_key and env_cert_path:
            tls_client_key = os.path.join(env_cert_path, 'key.pem')

        tls_ca_cert = module.params.get('tls_ca_cert')
        if not tls_ca_cert and env_cert_path:
            tls_ca_cert = os.path.join(env_cert_path, 'ca.pem')

        tls_hostname = module.params.get('tls_hostname')
        if tls_hostname is None:
            if env_docker_hostname:
                tls_hostname = env_docker_hostname
            else:
                parsed_url = urlparse(docker_url)
                if ':' in parsed_url.netloc:
                    tls_hostname = parsed_url.netloc[:parsed_url.netloc.rindex(':')]
                else:
                    tls_hostname = parsed_url
        if not tls_hostname:
            tls_hostname = True

        # use_tls can be one of four values:
        # no: Do not use tls
        # encrypt: Use tls.  We may do client auth.  We will not verify the server
        # verify: Use tls.  We may do client auth.  We will verify the server
        # None: Only use tls if the parameters for client auth were specified
        #   or tls_ca_cert (which requests verifying the server with
        #   a specific ca certificate)
        use_tls = module.params.get('use_tls')
        if use_tls is None and env_docker_verify is not None:
            use_tls = 'verify'

        tls_config = None
        if use_tls != 'no':
            params = {}

            # Setup client auth
            if tls_client_cert and tls_client_key:
                params['client_cert'] = (tls_client_cert, tls_client_key)

            # We're allowed to verify the connection to the server
            if use_tls == 'verify' or (use_tls is None and tls_ca_cert):
                if tls_ca_cert:
                    params['ca_cert'] = tls_ca_cert
                    params['verify'] = True
                    params['assert_hostname'] = tls_hostname
                else:
                    params['verify'] = True
                    params['assert_hostname'] = tls_hostname
            elif use_tls == 'encrypt':
                params['verify'] = False

            if params:
                # See https://github.com/docker/docker-py/blob/d39da11/docker/utils/utils.py#L279-L296
                docker_url = docker_url.replace('tcp://', 'https://')
                tls_config = docker.tls.TLSConfig(**params)

        self.client = docker.Client(base_url=docker_url,
                                    version=docker_api_version,
                                    tls=tls_config,
                                    timeout=timeout)

        self.docker_py_versioninfo = get_docker_py_versioninfo()

        env = self.module.params.get('env', None)
        env_file = self.module.params.get('env_file', None)
        self.environment = self.get_environment(env, env_file)

    def _check_capabilities(self):
        """
        Create a list of available capabilities
        """
        api_version = self.client.version()['ApiVersion']
        for cap, req_vers in self._cap_ver_req.items():
            if (self.docker_py_versioninfo >= req_vers[0] and
                    docker.utils.compare_version(req_vers[1], api_version) >= 0):
                self._capabilities.add(cap)

    def ensure_capability(self, capability, fail=True):
        """
        Some of the functionality this ansible module implements are only
        available in newer versions of docker.  Ensure that the capability
        is available here.

        If fail is set to False then return True or False depending on whether
        we have the capability.  Otherwise, simply fail and exit the module if
        we lack the capability.
        """
        if not self._capabilities:
            self._check_capabilities()

        if capability in self._capabilities:
            return True

        if not fail:
            return False

        api_version = self.client.version()['ApiVersion']
        self.module.fail_json(msg='Specifying the `%s` parameter requires'
                ' docker-py: %s, docker server apiversion %s; found'
                ' docker-py: %s, server: %s' % (
                    capability,
                    '.'.join(map(str, self._cap_ver_req[capability][0])),
                    self._cap_ver_req[capability][1],
                    '.'.join(map(str, self.docker_py_versioninfo)),
                    api_version))

    def get_environment(self, env, env_file):
        """
        If environment files are combined with explicit environment variables, the explicit environment variables will override the key from the env file.
        """
        final_env = {}

        if env_file:
            self.ensure_capability('env_file')
            parsed_env_file = docker.utils.parse_env_file(env_file)

            for name, value in parsed_env_file.items():
                final_env[name] = str(value)

        if env:
            for name, value in env.items():
                final_env[name] = str(value)

        return final_env

    def get_links(self, links):
        """
        Parse the links passed, if a link is specified without an alias then just create the alias of the same name as the link
        """
        processed_links = {}

        for link in links:
            parsed_link = link.split(':', 1)
            if(len(parsed_link) == 2):
                processed_links[parsed_link[0]] = parsed_link[1]
            else:
                processed_links[parsed_link[0]] = parsed_link[0]

        return processed_links

    def get_exposed_ports(self, expose_list):
        """
        Parse the ports and protocols (TCP/UDP) to expose in the docker-py `create_container` call from the docker CLI-style syntax.
        """
        if expose_list:
            exposed = []
            for port in expose_list:
                port = str(port).strip()
                if port.endswith('/tcp') or port.endswith('/udp'):
                    port_with_proto = tuple(port.split('/'))
                else:
                    # assume tcp protocol if not specified
                    port_with_proto = (port, 'tcp')
                exposed.append(port_with_proto)
            return exposed
        else:
            return None

    def get_start_params(self):
        """
        Create start params
        """
        params = {
            'lxc_conf': self.lxc_conf,
            'binds': self.binds,
            'port_bindings': self.port_bindings,
            'publish_all_ports': self.module.params.get('publish_all_ports'),
            'privileged': self.module.params.get('privileged'),
            'links': self.links,
            'network_mode': self.module.params.get('net'),
        }

        optionals = {}
        for optional_param in ('devices', 'dns', 'volumes_from',
                'restart_policy', 'restart_policy_retry', 'pid', 'extra_hosts',
                'log_driver', 'cap_add', 'cap_drop', 'read_only', 'log_opt'):
            optionals[optional_param] = self.module.params.get(optional_param)

        if optionals['devices'] is not None:
            self.ensure_capability('devices')
            params['devices'] = optionals['devices']

        if optionals['dns'] is not None:
            self.ensure_capability('dns')
            params['dns'] = optionals['dns']

        if optionals['volumes_from'] is not None:
            self.ensure_capability('volumes_from')
            params['volumes_from'] = optionals['volumes_from']

        if optionals['restart_policy'] is not None:
            self.ensure_capability('restart_policy')
            params['restart_policy'] = { 'Name': optionals['restart_policy'] }
            if params['restart_policy']['Name'] == 'on-failure':
                params['restart_policy']['MaximumRetryCount'] = optionals['restart_policy_retry']

        # docker_py only accepts 'host' or None
        if 'pid' in optionals and not optionals['pid']:
            optionals['pid'] = None

        if optionals['pid'] is not None:
            self.ensure_capability('pid')
            params['pid_mode'] = optionals['pid']

        if optionals['extra_hosts'] is not None:
            self.ensure_capability('extra_hosts')
            params['extra_hosts'] = optionals['extra_hosts']

        if optionals['log_driver'] is not None:
            self.ensure_capability('log_driver')
            log_config = docker.utils.LogConfig(type=docker.utils.LogConfig.types.JSON)
            if optionals['log_opt'] is not None:
                for k, v in optionals['log_opt'].items():
                    log_config.set_config_value(k, v)
            log_config.type = optionals['log_driver']
            params['log_config'] = log_config

        if optionals['cap_add'] is not None:
            self.ensure_capability('cap_add')
            params['cap_add'] = optionals['cap_add']

        if optionals['cap_drop'] is not None:
            self.ensure_capability('cap_drop')
            params['cap_drop'] = optionals['cap_drop']

        if optionals['read_only'] is not None:
            self.ensure_capability('read_only')
            params['read_only'] = optionals['read_only']

        return params

    def create_host_config(self):
        """
        Create HostConfig object
        """
        params = self.get_start_params()
        return docker.utils.create_host_config(**params)

    def get_port_bindings(self, ports):
        """
        Parse the `ports` string into a port bindings dict for the `start_container` call.
        """
        binds = {}
        for port in ports:
            # ports could potentially be an array like [80, 443], so we make sure they're strings
            # before splitting
            parts = str(port).split(':')
            container_port = parts[-1]
            if '/' not in container_port:
                container_port = int(parts[-1])

            p_len = len(parts)
            if p_len == 1:
                # Bind `container_port` of the container to a dynamically
                # allocated TCP port on all available interfaces of the host
                # machine.
                bind = ('0.0.0.0',)
            elif p_len == 2:
                # Bind `container_port` of the container to port `parts[0]` on
                # all available interfaces of the host machine.
                bind = ('0.0.0.0', int(parts[0]))
            elif p_len == 3:
                # Bind `container_port` of the container to port `parts[1]` on
                # IP `parts[0]` of the host machine. If `parts[1]` empty bind
                # to a dynamically allocated port of IP `parts[0]`.
                bind = (parts[0], int(parts[1])) if parts[1] else (parts[0],)

            if container_port in binds:
                old_bind = binds[container_port]
                if isinstance(old_bind, list):
                    # append to list if it already exists
                    old_bind.append(bind)
                else:
                    # otherwise create list that contains the old and new binds
                    binds[container_port] = [binds[container_port], bind]
            else:
                binds[container_port] = bind

        return binds

    def get_summary_message(self):
        '''
        Generate a message that briefly describes the actions taken by this
        task, in English.
        '''

        parts = []
        for k, v in self.counters.items():
            if v == 0:
                continue

            if v == 1:
                plural = ""
            else:
                plural = "s"
            parts.append("%s %d container%s" % (k, v, plural))

        if parts:
            return ", ".join(parts) + "."
        else:
            return "No action taken."

    def get_reload_reason_message(self):
        '''
        Generate a message describing why any reloaded containers were reloaded.
        '''

        if self.reload_reasons:
            return ", ".join(self.reload_reasons)
        else:
            return None

    def get_summary_counters_msg(self):
        msg = ""
        for k, v in self.counters.items():
            msg = msg + "%s %d " % (k, v)

        return msg

    def increment_counter(self, name):
        self.counters[name] = self.counters[name] + 1

    def has_changed(self):
        for k, v in self.counters.items():
            if v > 0:
                return True

        return False

    def get_inspect_image(self):
        try:
            return self.client.inspect_image(self.module.params.get('image'))
        except DockerAPIError as e:
            if e.response.status_code == 404:
                return None
            else:
                raise e

    def get_image_repo_tags(self):
        image, tag = get_split_image_tag(self.module.params.get('image'))
        if tag is None:
            tag = 'latest'
        resource = '%s:%s' % (image, tag)

        for image in self.client.images(name=image):
            if resource in image.get('RepoTags', []):
                return image['RepoTags']
        return []

    def get_inspect_containers(self, containers):
        inspect = []
        for i in containers:
            details = self.client.inspect_container(i['Id'])
            details = _docker_id_quirk(details)
            inspect.append(details)

        return inspect

    def get_differing_containers(self):
        """
        Inspect all matching, running containers, and return those that were
        started with parameters that differ from the ones that are provided
        during this module run. A list containing the differing
        containers will be returned, and a short string describing the specific
        difference encountered in each container will be appended to
        reload_reasons.

        This generates the set of containers that need to be stopped and
        started with new parameters with state=reloaded.
        """

        running = self.get_running_containers()
        current = self.get_inspect_containers(running)
        defaults = self.client.info()

        #Get API version
        api_version = self.client.version()['ApiVersion']

        image = self.get_inspect_image()
        if image is None:
            # The image isn't present. Assume that we're about to pull a new
            # tag and *everything* will be restarted.
            #
            # This will give false positives if you untag an image on the host
            # and there's nothing more to pull.
            return current

        differing = []

        for container in current:

            # IMAGE
            # Compare the image by ID rather than name, so that containers
            # will be restarted when new versions of an existing image are
            # pulled.
            if container['Image'] != image['Id']:
                self.reload_reasons.append('image ({0} => {1})'.format(container['Image'], image['Id']))
                differing.append(container)
                continue

            # ENTRYPOINT

            expected_entrypoint = self.module.params.get('entrypoint')
            if expected_entrypoint:
                expected_entrypoint = shlex.split(expected_entrypoint)
                actual_entrypoint = container["Config"]["Entrypoint"]

                if actual_entrypoint != expected_entrypoint:
                    self.reload_reasons.append(
                        'entrypoint ({0} => {1})'
                        .format(actual_entrypoint, expected_entrypoint)
                    )
                    differing.append(container)
                    continue

            # COMMAND

            expected_command = self.module.params.get('command')
            if expected_command:
                expected_command = shlex.split(expected_command)
                actual_command = container["Config"]["Cmd"]

                if actual_command != expected_command:
                    self.reload_reasons.append('command ({0} => {1})'.format(actual_command, expected_command))
                    differing.append(container)
                    continue

            # EXPOSED PORTS
            expected_exposed_ports = set((image['ContainerConfig'].get('ExposedPorts') or {}).keys())
            for p in (self.exposed_ports or []):
                expected_exposed_ports.add("/".join(p))

            actually_exposed_ports = set((container["Config"].get("ExposedPorts") or {}).keys())

            if actually_exposed_ports != expected_exposed_ports:
                self.reload_reasons.append('exposed_ports ({0} => {1})'.format(actually_exposed_ports, expected_exposed_ports))
                differing.append(container)
                continue

            # VOLUMES

            expected_volume_keys = set((image['ContainerConfig']['Volumes'] or {}).keys())
            if self.volumes:
                expected_volume_keys.update(self.volumes)

            actual_volume_keys = set((container['Config']['Volumes'] or {}).keys())

            if actual_volume_keys != expected_volume_keys:
                self.reload_reasons.append('volumes ({0} => {1})'.format(actual_volume_keys, expected_volume_keys))
                differing.append(container)
                continue

            # ULIMITS

            expected_ulimit_keys = set(map(lambda x: '%s:%s:%s' % (x['name'],x['soft'],x['hard']), self.ulimits or []))
            actual_ulimit_keys = set(map(lambda x: '%s:%s:%s' % (x['Name'],x['Soft'],x['Hard']), (container['HostConfig']['Ulimits'] or [])))

            if actual_ulimit_keys != expected_ulimit_keys:
                self.reload_reasons.append('ulimits ({0} => {1})'.format(actual_ulimit_keys, expected_ulimit_keys))
                differing.append(container)
                continue

            # CPU_SHARES

            expected_cpu_shares = self.module.params.get('cpu_shares')
            actual_cpu_shares = container['HostConfig']['CpuShares']

            if expected_cpu_shares and actual_cpu_shares != expected_cpu_shares:
                self.reload_reasons.append('cpu_shares ({0} => {1})'.format(actual_cpu_shares, expected_cpu_shares))
                differing.append(container)
                continue

            # MEM_LIMIT

            try:
                expected_mem = _human_to_bytes(self.module.params.get('memory_limit'))
            except ValueError as e:
                self.module.fail_json(msg=str(e))

            #For v1.19 API and above use HostConfig, otherwise use Config
            if docker.utils.compare_version('1.19', api_version) >= 0:
                actual_mem = container['HostConfig']['Memory']
            else:
                actual_mem = container['Config']['Memory']

            if expected_mem and actual_mem != expected_mem:
                self.reload_reasons.append('memory ({0} => {1})'.format(actual_mem, expected_mem))
                differing.append(container)
                continue

            # ENVIRONMENT
            # actual_env is likely to include environment variables injected by
            # the Dockerfile.

            expected_env = {}

            for image_env in image['ContainerConfig']['Env'] or []:
                name, value = image_env.split('=', 1)
                expected_env[name] = value

            if self.environment:
                for name, value in self.environment.items():
                    expected_env[name] = str(value)

            actual_env = {}
            for container_env in container['Config']['Env'] or []:
                name, value = container_env.split('=', 1)
                actual_env[name] = value

            if actual_env != expected_env:
                # Don't include the environment difference in the output.
                self.reload_reasons.append('environment {0} => {1}'.format(actual_env, expected_env))
                differing.append(container)
                continue

            # LABELS

            expected_labels = {}
            for name, value in self.module.params.get('labels').items():
                expected_labels[name] = str(value)

            if isinstance(container['Config']['Labels'], dict):
                actual_labels = container['Config']['Labels']
            else:
                for container_label in container['Config']['Labels'] or []:
                    name, value = container_label.split('=', 1)
                    actual_labels[name] = value

            if actual_labels != expected_labels:
                self.reload_reasons.append('labels {0} => {1}'.format(actual_labels, expected_labels))
                differing.append(container)
                continue

            # HOSTNAME

            expected_hostname = self.module.params.get('hostname')
            actual_hostname = container['Config']['Hostname']
            if expected_hostname and actual_hostname != expected_hostname:
                self.reload_reasons.append('hostname ({0} => {1})'.format(actual_hostname, expected_hostname))
                differing.append(container)
                continue

            # DOMAINNAME

            expected_domainname = self.module.params.get('domainname')
            actual_domainname = container['Config']['Domainname']
            if expected_domainname and actual_domainname != expected_domainname:
                self.reload_reasons.append('domainname ({0} => {1})'.format(actual_domainname, expected_domainname))
                differing.append(container)
                continue

            # DETACH

            # We don't have to check for undetached containers. If it wasn't
            # detached, it would have stopped before the playbook continued!

            # NAME

            # We also don't have to check name, because this is one of the
            # criteria that's used to determine which container(s) match in
            # the first place.

            # STDIN_OPEN

            expected_stdin_open = self.module.params.get('stdin_open')
            actual_stdin_open = container['Config']['OpenStdin']
            if actual_stdin_open != expected_stdin_open:
                self.reload_reasons.append('stdin_open ({0} => {1})'.format(actual_stdin_open, expected_stdin_open))
                differing.append(container)
                continue

            # TTY

            expected_tty = self.module.params.get('tty')
            actual_tty = container['Config']['Tty']
            if actual_tty != expected_tty:
                self.reload_reasons.append('tty ({0} => {1})'.format(actual_tty, expected_tty))
                differing.append(container)
                continue

            # -- "start" call differences --

            # LXC_CONF

            if self.lxc_conf:
                expected_lxc = set(self.lxc_conf)
                actual_lxc = set(container['HostConfig']['LxcConf'] or [])
                if actual_lxc != expected_lxc:
                    self.reload_reasons.append('lxc_conf ({0} => {1})'.format(actual_lxc, expected_lxc))
                    differing.append(container)
                    continue

            # BINDS

            expected_binds = set()
            if self.binds:
                for bind in self.binds:
                    expected_binds.add(bind)

            actual_binds = set()
            for bind in (container['HostConfig']['Binds'] or []):
                if len(bind.split(':')) == 2:
                    actual_binds.add(bind + ":rw")
                else:
                    actual_binds.add(bind)

            if actual_binds != expected_binds:
                self.reload_reasons.append('binds ({0} => {1})'.format(actual_binds, expected_binds))
                differing.append(container)
                continue

            # PORT BINDINGS

            expected_bound_ports = {}
            if self.port_bindings:
                for container_port, config in self.port_bindings.items():
                    if isinstance(container_port, int):
                        container_port = "{0}/tcp".format(container_port)
                    if len(config) == 1:
                        expected_bound_ports[container_port] = [{'HostIp': "0.0.0.0", 'HostPort': ""}]
                    elif isinstance(config[0], tuple):
                        expected_bound_ports[container_port] = []
                        for hostip, hostport in config:
                            expected_bound_ports[container_port].append({ 'HostIp': hostip, 'HostPort': str(hostport)})
                    else:
                        expected_bound_ports[container_port] = [{'HostIp': config[0], 'HostPort': str(config[1])}]

            actual_bound_ports = container['HostConfig']['PortBindings'] or {}

            if actual_bound_ports != expected_bound_ports:
                self.reload_reasons.append('port bindings ({0} => {1})'.format(actual_bound_ports, expected_bound_ports))
                differing.append(container)
                continue

            # PUBLISHING ALL PORTS

            # What we really care about is the set of ports that is actually
            # published. That should be caught above.

            # PRIVILEGED

            expected_privileged = self.module.params.get('privileged')
            actual_privileged = container['HostConfig']['Privileged']
            if actual_privileged != expected_privileged:
                self.reload_reasons.append('privileged ({0} => {1})'.format(actual_privileged, expected_privileged))
                differing.append(container)
                continue

            # LINKS

            expected_links = set()
            for link, alias in (self.links or {}).items():
                expected_links.add("/{0}:{1}/{2}".format(link, container["Name"], alias))

            actual_links = set()
            for link in (container['HostConfig']['Links'] or []):
                actual_links.add(link)

            if actual_links != expected_links:
                self.reload_reasons.append('links ({0} => {1})'.format(actual_links, expected_links))
                differing.append(container)
                continue

            # NETWORK MODE

            expected_netmode = self.module.params.get('net') or 'bridge'
            actual_netmode = container['HostConfig']['NetworkMode'] or 'bridge'
            if actual_netmode != expected_netmode:
                self.reload_reasons.append('net ({0} => {1})'.format(actual_netmode, expected_netmode))
                differing.append(container)
                continue

            # DEVICES

            expected_devices = set()
            for device in (self.module.params.get('devices') or []):
                if len(device.split(':')) == 2:
                    expected_devices.add(device + ":rwm")
                else:
                    expected_devices.add(device)

            actual_devices = set()
            for device in (container['HostConfig']['Devices'] or []):
                actual_devices.add("{PathOnHost}:{PathInContainer}:{CgroupPermissions}".format(**device))

            if actual_devices != expected_devices:
                self.reload_reasons.append('devices ({0} => {1})'.format(actual_devices, expected_devices))
                differing.append(container)
                continue

            # DNS

            expected_dns = set(self.module.params.get('dns') or [])
            actual_dns = set(container['HostConfig']['Dns'] or [])
            if actual_dns != expected_dns:
                self.reload_reasons.append('dns ({0} => {1})'.format(actual_dns, expected_dns))
                differing.append(container)
                continue

            # VOLUMES_FROM

            expected_volumes_from = set(self.module.params.get('volumes_from') or [])
            actual_volumes_from = set(container['HostConfig']['VolumesFrom'] or [])
            if actual_volumes_from != expected_volumes_from:
                self.reload_reasons.append('volumes_from ({0} => {1})'.format(actual_volumes_from, expected_volumes_from))
                differing.append(container)

            # LOG_DRIVER

            if self.ensure_capability('log_driver', False):
                expected_log_driver = self.module.params.get('log_driver') or defaults['LoggingDriver']
                actual_log_driver = container['HostConfig']['LogConfig']['Type']
                if actual_log_driver != expected_log_driver:
                    self.reload_reasons.append('log_driver ({0} => {1})'.format(actual_log_driver, expected_log_driver))
                    differing.append(container)
                    continue

            if self.ensure_capability('log_opt', False):
                expected_logging_opts = self.module.params.get('log_opt') or {}
                actual_log_opts = container['HostConfig']['LogConfig']['Config']
                if len(set(expected_logging_opts.items()) - set(actual_log_opts.items())) != 0:
                    log_opt_reasons = {
                        'added': dict(set(expected_logging_opts.items()) - set(actual_log_opts.items())),
                        'removed': dict(set(actual_log_opts.items()) - set(expected_logging_opts.items()))
                    }
                    self.reload_reasons.append('log_opt ({0})'.format(log_opt_reasons))
                    differing.append(container)

        return differing

    def get_deployed_containers(self):
        """
        Return any matching containers that are already present.
        """

        entrypoint = self.module.params.get('entrypoint')
        if entrypoint is not None:
            entrypoint = shlex.split(entrypoint)
        command = self.module.params.get('command')
        if command is not None:
            command = shlex.split(command)
        name = self.module.params.get('name')
        if name and not name.startswith('/'):
            name = '/' + name
        deployed = []

        # "images" will be a collection of equivalent "name:tag" image names
        # that map to the same Docker image.
        inspected = self.get_inspect_image()
        if inspected:
            repo_tags = self.get_image_repo_tags()
        else:
            repo_tags = [normalize_image(self.module.params.get('image'))]

        for container in self.client.containers(all=True):
            details = None

            if name:
                name_list = container.get('Names')
                if name_list is None:
                    name_list = []
                matches = name in name_list
            else:
                details = self.client.inspect_container(container['Id'])
                details = _docker_id_quirk(details)

                running_image = normalize_image(details['Config']['Image'])

                image_matches = running_image in repo_tags

                if command is None:
                    command_matches = True
                else:
                    command_matches = (command == details['Config']['Cmd'])

                if entrypoint is None:
                    entrypoint_matches = True
                else:
                    entrypoint_matches = (
                        entrypoint == details['Config']['Entrypoint']
                    )

                matches = (image_matches and command_matches and
                           entrypoint_matches)

            if matches:
                if not details:
                    details = self.client.inspect_container(container['Id'])
                    details = _docker_id_quirk(details)

                deployed.append(details)

        return deployed

    def get_running_containers(self):
        return [c for c in self.get_deployed_containers() if is_running(c)]

    def pull_image(self):
        extra_params = {}
        if self.module.params.get('insecure_registry'):
            if self.ensure_capability('insecure_registry', fail=False):
                extra_params['insecure_registry'] = self.module.params.get('insecure_registry')

        resource = self.module.params.get('image')
        image, tag = get_split_image_tag(resource)
        if self.module.params.get('username'):
            try:
                self.client.login(
                    self.module.params.get('username'),
                    password=self.module.params.get('password'),
                    email=self.module.params.get('email'),
                    registry=self.module.params.get('registry')
                )
            except Exception as e:
                self.module.fail_json(msg="failed to login to the remote registry, check your username/password.", error=repr(e))
        try:
            changes = list(self.client.pull(image, tag=tag, stream=True, **extra_params))
            pull_success = False
            for change in changes:
                status = json.loads(change).get('status', '')
                if status.startswith('Status: Image is up to date for'):
                    # Image is already up to date. Don't increment the counter.
                    pull_success = True
                    break
                elif (status.startswith('Status: Downloaded newer image for') or
                        status.startswith('Download complete')):
                    # Image was updated. Increment the pull counter.
                    self.increment_counter('pulled')
                    pull_success = True
                    break
            if not pull_success:
                # Unrecognized status string.
                self.module.fail_json(msg="Unrecognized status from pull.", status=status, changes=changes)
        except Exception as e:
            self.module.fail_json(msg="Failed to pull the specified image: %s" % resource, error=repr(e))

    def create_containers(self, count=1):
        try:
            mem_limit = _human_to_bytes(self.module.params.get('memory_limit'))
        except ValueError as e:
            self.module.fail_json(msg=str(e))
        api_version = self.client.version()['ApiVersion']

        params = {'image':        self.module.params.get('image'),
                  'entrypoint':   self.module.params.get('entrypoint'),
                  'command':      self.module.params.get('command'),
                  'ports':        self.exposed_ports,
                  'volumes':      self.volumes,
                  'environment':  self.environment,
                  'labels':       self.module.params.get('labels'),
                  'hostname':     self.module.params.get('hostname'),
                  'domainname':   self.module.params.get('domainname'),
                  'detach':       self.module.params.get('detach'),
                  'name':         self.module.params.get('name'),
                  'stdin_open':   self.module.params.get('stdin_open'),
                  'tty':          self.module.params.get('tty'),
                  'cpuset':       self.module.params.get('cpu_set'),
                  'cpu_shares':   self.module.params.get('cpu_shares'),
                  'user':         self.module.params.get('docker_user'),
                  }
        if self.ensure_capability('host_config', fail=False):
            params['host_config'] = self.create_host_config()

        #For v1.19 API and above use HostConfig, otherwise use Config
        if docker.utils.compare_version('1.19', api_version) < 0:
            params['mem_limit'] = mem_limit
        else:
            params['host_config']['Memory'] = mem_limit

        if self.ulimits is not None:
            self.ensure_capability('ulimits')
            params['host_config']['ulimits'] = self.ulimits

        def do_create(count, params):
            results = []
            for _ in range(count):
                result = self.client.create_container(**params)
                self.increment_counter('created')
                results.append(result)

            return results

        try:
            containers = do_create(count, params)
        except docker.errors.APIError as e:
            if e.response.status_code != 404:
                raise

            self.pull_image()
            containers = do_create(count, params)

        return containers

    def start_containers(self, containers):
        params = {}

        if not self.ensure_capability('host_config', fail=False):
            params = self.get_start_params()

        for i in containers:
            self.client.start(i)
            self.increment_counter('started')

            if not self.module.params.get('detach'):
                status = self.client.wait(i['Id'])
                if status != 0:
                    output = self.client.logs(i['Id'], stdout=True, stderr=True,
                                              stream=False, timestamps=False)
                    self.module.fail_json(status=status, msg=output)

    def stop_containers(self, containers):
        for i in containers:
            self.client.stop(i['Id'], self.module.params.get('stop_timeout'))
            self.increment_counter('stopped')

        return [self.client.wait(i['Id']) for i in containers]

    def remove_containers(self, containers):
        for i in containers:
            self.client.remove_container(i['Id'])
            self.increment_counter('removed')

    def kill_containers(self, containers):
        for i in containers:
            self.client.kill(i['Id'], self.module.params.get('signal'))
            self.increment_counter('killed')

    def restart_containers(self, containers):
        for i in containers:
            self.client.restart(i['Id'])
            self.increment_counter('restarted')


class ContainerSet:

    def __init__(self, manager):
        self.manager = manager
        self.running = []
        self.deployed = []
        self.changed = []

    def refresh(self):
        '''
        Update our view of the matching containers from the Docker daemon.
        '''


        self.deployed = self.manager.get_deployed_containers()
        self.running = [c for c in self.deployed if is_running(c)]

    def notice_changed(self, containers):
        '''
        Record a collection of containers as "changed".
        '''

        self.changed.extend(containers)


def present(manager, containers, count, name):
    '''Ensure that exactly `count` matching containers exist in any state.'''

    containers.refresh()
    delta = count - len(containers.deployed)

    if delta > 0:
        created = manager.create_containers(delta)
        containers.notice_changed(manager.get_inspect_containers(created))

    if delta < 0:
        # If both running and stopped containers exist, remove
        # stopped containers first.
        # Use key param for python 2/3 compatibility.
        containers.deployed.sort(key=is_running)

        to_stop = []
        to_remove = []
        for c in containers.deployed[0:-delta]:
            if is_running(c):
                to_stop.append(c)
            to_remove.append(c)

        manager.stop_containers(to_stop)
        containers.notice_changed(manager.get_inspect_containers(to_remove))
        manager.remove_containers(to_remove)

def started(manager, containers, count, name):
    '''Ensure that exactly `count` matching containers exist and are running.'''

    containers.refresh()
    delta = count - len(containers.running)

    if delta > 0:
        if name and containers.deployed:
            # A stopped container exists with the requested name.
            # Clean it up before attempting to start a new one.
            manager.remove_containers(containers.deployed)

        created = manager.create_containers(delta)
        manager.start_containers(created)
        containers.notice_changed(manager.get_inspect_containers(created))

    if delta < 0:
        excess = containers.running[0:-delta]
        containers.notice_changed(manager.get_inspect_containers(excess))
        manager.stop_containers(excess)
        manager.remove_containers(excess)

def reloaded(manager, containers, count, name):
    '''
    Ensure that exactly `count` matching containers exist and are
    running. If any associated settings have been changed (volumes,
    ports or so on), restart those containers.
    '''

    containers.refresh()

    for container in manager.get_differing_containers():
        manager.stop_containers([container])
        manager.remove_containers([container])

    started(manager, containers, count, name)

def restarted(manager, containers, count, name):
    '''
    Ensure that exactly `count` matching containers exist and are
    running. Unconditionally restart any that were already running.
    '''

    containers.refresh()

    for container in manager.get_differing_containers():
        manager.stop_containers([container])
        manager.remove_containers([container])

    containers.refresh()

    manager.restart_containers(containers.running)
    started(manager, containers, count, name)

def stopped(manager, containers, count, name):
    '''Stop any matching containers that are running.'''

    containers.refresh()

    manager.stop_containers(containers.running)
    containers.notice_changed(manager.get_inspect_containers(containers.running))

def killed(manager, containers, count, name):
    '''Kill any matching containers that are running.'''

    containers.refresh()

    manager.kill_containers(containers.running)
    containers.notice_changed(manager.get_inspect_containers(containers.running))

def absent(manager, containers, count, name):
    '''Stop and remove any matching containers.'''

    containers.refresh()

    manager.stop_containers(containers.running)
    containers.notice_changed(manager.get_inspect_containers(containers.deployed))
    manager.remove_containers(containers.deployed)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            count           = dict(default=1, type='int'),
            image           = dict(required=True),
            pull            = dict(required=False, default='missing', choices=['missing', 'always']),
            entrypoint      = dict(required=False, default=None, type='str'),
            command         = dict(required=False, default=None),
            expose          = dict(required=False, default=None, type='list'),
            ports           = dict(required=False, default=None, type='list'),
            publish_all_ports = dict(default=False, type='bool'),
            volumes         = dict(default=None, type='list'),
            volumes_from    = dict(default=None, type='list'),
            links           = dict(default=None, type='list'),
            devices         = dict(default=None, type='list'),
            memory_limit    = dict(default=0),
            memory_swap     = dict(default=0, type='int'),
            cpu_shares      = dict(default=0, type='int'),
            docker_url      = dict(),
            use_tls         = dict(default=None, choices=['no', 'encrypt', 'verify']),
            tls_client_cert = dict(required=False, default=None, type='path'),
            tls_client_key  = dict(required=False, default=None, type='path'),
            tls_ca_cert     = dict(required=False, default=None, type='path'),
            tls_hostname    = dict(required=False, type='str', default=None),
            docker_api_version = dict(required=False, default=DEFAULT_DOCKER_API_VERSION, type='str'),
            docker_user     = dict(default=None),
            username        = dict(default=None),
            password        = dict(no_log=True),
            email           = dict(),
            registry        = dict(),
            hostname        = dict(default=None),
            domainname      = dict(default=None),
            env             = dict(type='dict'),
            env_file        = dict(default=None),
            dns             = dict(default=None, type='list'),
            detach          = dict(default=True, type='bool'),
            state           = dict(default='started', choices=['present', 'started', 'reloaded', 'restarted', 'stopped', 'killed', 'absent', 'running']),
            signal          = dict(default=None),
            restart_policy  = dict(default=None, choices=['always', 'on-failure', 'no', 'unless-stopped']),
            restart_policy_retry = dict(default=0, type='int'),
            extra_hosts     = dict(type='dict'),
            debug           = dict(default=False, type='bool'),
            privileged      = dict(default=False, type='bool'),
            stdin_open      = dict(default=False, type='bool'),
            tty             = dict(default=False, type='bool'),
            lxc_conf        = dict(default=None, type='list'),
            name            = dict(default=None),
            net             = dict(default=None),
            pid             = dict(default=None),
            insecure_registry = dict(default=False, type='bool'),
            log_driver      = dict(default=None, choices=['json-file', 'none', 'syslog', 'journald', 'gelf', 'fluentd', 'awslogs']),
            log_opt         = dict(default=None, type='dict'),
            cpu_set         = dict(default=None),
            cap_add         = dict(default=None, type='list'),
            cap_drop        = dict(default=None, type='list'),
            read_only       = dict(default=None, type='bool'),
            labels          = dict(default={}, type='dict'),
            stop_timeout    = dict(default=10, type='int'),
            timeout         = dict(required=False, default=DEFAULT_TIMEOUT_SECONDS, type='int'),
            ulimits         = dict(default=None, type='list'),
        ),
        required_together = (
            ['tls_client_cert', 'tls_client_key'],
        ),
    )

    check_dependencies(module)

    try:
        manager = DockerManager(module)
        count = module.params.get('count')
        name = module.params.get('name')
        pull = module.params.get('pull')

        state = module.params.get('state')
        if state == 'running':
            # Renamed running to started in 1.9
            state = 'started'

        if count < 0:
            module.fail_json(msg="Count must be greater than zero")

        if count > 1 and name:
            module.fail_json(msg="Count and name must not be used together")

        # Explicitly pull new container images, if requested. Do this before
        # noticing running and deployed containers so that the image names
        # will differ if a newer image has been pulled.
        # Missing images should be pulled first to avoid downtime when old
        # container is stopped, but image for new one is now downloaded yet.
        # It also prevents removal of running container before realizing
        # that requested image cannot be retrieved.
        if pull == "always" or (state == 'reloaded' and manager.get_inspect_image() is None):
            manager.pull_image()

        containers = ContainerSet(manager)

        if state == 'present':
            present(manager, containers, count, name)
        elif state == 'started':
            started(manager, containers, count, name)
        elif state == 'reloaded':
            reloaded(manager, containers, count, name)
        elif state == 'restarted':
            restarted(manager, containers, count, name)
        elif state == 'stopped':
            stopped(manager, containers, count, name)
        elif state == 'killed':
            killed(manager, containers, count, name)
        elif state == 'absent':
            absent(manager, containers, count, name)
        else:
            module.fail_json(msg='Unrecognized state %s. Must be one of: '
                                 'present; started; reloaded; restarted; '
                                 'stopped; killed; absent.' % state)

        module.exit_json(changed=manager.has_changed(),
                         msg=manager.get_summary_message(),
                         summary=manager.counters,
                         reload_reasons=manager.get_reload_reason_message(),
                         ansible_facts=_ansible_facts(containers.changed))

    except DockerAPIError as e:
        module.fail_json(changed=manager.has_changed(), msg="Docker API Error: %s" % e.explanation)

    except RequestException as e:
        module.fail_json(changed=manager.has_changed(), msg=repr(e))


if __name__ == '__main__':
    main()
