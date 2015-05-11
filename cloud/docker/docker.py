#!/usr/bin/python

# (c) 2013, Cove Schneider
# (c) 2014, Joshua Conner <joshua.conner@gmail.com>
# (c) 2014, Pavel Antonov <antonov@adwz.ru>
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

######################################################################

DOCUMENTATION = '''
---
module: docker
version_added: "1.4"
short_description: manage docker containers
description:
  - Manage the life cycle of docker containers.
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
      - List containing private to public port mapping specification. Use docker
      - 'CLI-style syntax: C(8000), C(9000:8000), or C(0.0.0.0:9000:8000)'
      - where  8000 is a container port, 9000 is a host port, and 0.0.0.0 is
      - a host interface.
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
      - List of volumes to mount within the container using docker CLI-style
      - 'syntax: C(/host:/container[:mode]) where "mode" may be "rw" or "ro".'
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
  dns:
    description:
      - List of custom DNS servers for the container.
    required: false
    default: null
  detach:
    description:
      - Enable detached mode to leave the container running in background.
    default: true
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
  restart_policy:
    description:
      - Container restart policy.
    choices: ["no", "on-failure", "always"]
    default: null
    version_added: "1.9"
  restart_policy_retry:
    description:
      - Maximum number of times to restart a container. Leave as "0" for unlimited
        retries.
    default: 0
    version_added: "1.9"
  extra_hosts:
    description:
    - Dict of custom host-to-IP mappings to be defined in the container
  insecure_registry:
    description:
      - Use insecure private registry by HTTP instead of HTTPS. Needed for
        docker-py >= 0.5.0.
    default: false
    version_added: "1.9"

author: Cove Schneider, Joshua Conner, Pavel Antonov, Ash Wilson
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
# - bind TCP port 9000 within the container to port 8080 on all interfaces
#   on the host.
# - bind UDP port 9001 within the container to port 8081 on the host, only
#   listening on localhost.
# - set the environment variable SECRET_KEY to "ssssh".

- name: application container
  docker:
    name: myapplication
    image: someuser/appimage
    state: reloaded
    pull: always
    links:
    - "myredis:aliasedredis"
    ports:
    - "8080:9000"
    - "127.0.0.1:8081:9001/udp"
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
'''

HAS_DOCKER_PY = True

import sys
import json
import os
import shlex
from urlparse import urlparse
try:
    import docker.client
    import docker.utils
    from requests.exceptions import RequestException
except ImportError:
    HAS_DOCKER_PY = False

if HAS_DOCKER_PY:
    try:
        from docker.errors import APIError as DockerAPIError
    except ImportError:
        from docker.client import APIError as DockerAPIError
    try:
        # docker-py 1.2+
        import docker.constants
        DEFAULT_DOCKER_API_VERSION = docker.constants.DEFAULT_DOCKER_API_VERSION
    except (ImportError, AttributeError):
        # docker-py less than 1.2
        DEFAULT_DOCKER_API_VERSION = docker.client.DEFAULT_DOCKER_API_VERSION


def _human_to_bytes(number):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    if isinstance(number, int):
        return number
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

    # now we can determine if image has a tag
    if ':' in resource:
        resource, tag = resource.split(':', 1)
        if registry:
            resource = '/'.join((registry, resource))
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

    return container['State']['Running'] == True and not container['State'].get('Ghost', False)


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
            'dns': ((0, 3, 0), '1.10'),
            'volumes_from': ((0, 3, 0), '1.10'),
            'restart_policy': ((0, 5, 0), '1.14'),
            'extra_hosts': ((0, 7, 0), '1.3.1'),
            'pid': ((1, 0, 0), '1.17'),
            # Clientside only
            'insecure_registry': ((0, 5, 0), '0.0')
            }

    def __init__(self, module):
        self.module = module

        self.binds = None
        self.volumes = None
        if self.module.params.get('volumes'):
            self.binds = {}
            self.volumes = {}
            vols = self.module.params.get('volumes')
            for vol in vols:
                parts = vol.split(":")
                # host mount (e.g. /mnt:/tmp, bind mounts host's /tmp to /mnt in the container)
                if len(parts) == 2:
                    self.volumes[parts[1]] = {}
                    self.binds[parts[0]] = parts[1]
                # with bind mode
                elif len(parts) == 3:
                    if parts[2] not in ['ro', 'rw']:
                        self.module.fail_json(msg='bind mode needs to either be "ro" or "rw"')
                    ro = parts[2] == 'ro'
                    self.volumes[parts[1]] = {}
                    self.binds[parts[0]] = {'bind': parts[1], 'ro': ro}
                # docker mount (e.g. /www, mounts a docker volume /www on the container at the same location)
                else:
                    self.volumes[parts[0]] = {}

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

        self.env = self.module.params.get('env', None)

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
                                    tls=tls_config)

        self.docker_py_versioninfo = get_docker_py_versioninfo()

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
        for k, v in self.counters.iteritems():
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
        for k, v in self.counters.iteritems():
            msg = msg + "%s %d " % (k, v)

        return msg

    def increment_counter(self, name):
        self.counters[name] = self.counters[name] + 1

    def has_changed(self):
        for k, v in self.counters.iteritems():
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
            expected_exposed_ports = set((image['ContainerConfig']['ExposedPorts'] or {}).keys())
            for p in (self.exposed_ports or []):
                expected_exposed_ports.add("/".join(p))

            actually_exposed_ports = set((container["Config"]["ExposedPorts"] or {}).keys())

            if actually_exposed_ports != expected_exposed_ports:
                self.reload_reasons.append('exposed_ports ({0} => {1})'.format(actually_exposed_ports, expected_exposed_ports))
                differing.append(container)
                continue

            # VOLUMES

            expected_volume_keys = set((image['ContainerConfig']['Volumes'] or {}).keys())
            if self.volumes:
                expected_volume_keys.update(self.volumes.keys())

            actual_volume_keys = set((container['Config']['Volumes'] or {}).keys())

            if actual_volume_keys != expected_volume_keys:
                self.reload_reasons.append('volumes ({0} => {1})'.format(actual_volume_keys, expected_volume_keys))
                differing.append(container)
                continue

            # MEM_LIMIT

            try:
                expected_mem = _human_to_bytes(self.module.params.get('memory_limit'))
            except ValueError as e:
                self.module.fail_json(msg=str(e))

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

            if self.env:
                for name, value in self.env.iteritems():
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
            actual_stdin_open = container['Config']['AttachStdin']
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
                for host_path, config in self.binds.iteritems():
                    if isinstance(config, dict):
                        container_path = config['bind']
                        if config['ro']:
                            mode = 'ro'
                        else:
                            mode = 'rw'
                    else:
                        container_path = config
                        mode = 'rw'
                    expected_binds.add("{0}:{1}:{2}".format(host_path, container_path, mode))

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
                for container_port, config in self.port_bindings.iteritems():
                    if isinstance(container_port, int):
                        container_port = "{0}/tcp".format(container_port)
                    bind = {}
                    if len(config) == 1:
                        bind['HostIp'] = "0.0.0.0"
                        bind['HostPort'] = ""
                    else:
                        bind['HostIp'] = config[0]
                        bind['HostPort'] = str(config[1])

                    expected_bound_ports[container_port] = [bind]

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
            for link, alias in (self.links or {}).iteritems():
                expected_links.add("/{0}:{1}/{2}".format(link, container["Name"], alias))

            actual_links = set(container['HostConfig']['Links'] or [])
            if actual_links != expected_links:
                self.reload_reasons.append('links ({0} => {1})'.format(actual_links, expected_links))
                differing.append(container)
                continue

            # NETWORK MODE

            expected_netmode = self.module.params.get('net') or ''
            actual_netmode = container['HostConfig']['NetworkMode']
            if actual_netmode != expected_netmode:
                self.reload_reasons.append('net ({0} => {1})'.format(actual_netmode, expected_netmode))
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

        return differing

    def get_deployed_containers(self):
        """
        Return any matching containers that are already present.
        """

        command = self.module.params.get('command')
        if command:
            command = command.strip()
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
                running_command = container['Command'].strip()

                image_matches = running_image in repo_tags

                # if a container has an entrypoint, `command` will actually equal
                # '{} {}'.format(entrypoint, command)
                command_matches = (not command or running_command.endswith(command))

                matches = image_matches and command_matches

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
            try:
                last = changes[-1]
            except IndexError:
                last = '{}'
            status = json.loads(last).get('status', '')
            if status.startswith('Status: Image is up to date for'):
                # Image is already up to date. Don't increment the counter.
                pass
            elif (status.startswith('Status: Downloaded newer image for') or
                    status.startswith('Download complete')):
                # Image was updated. Increment the pull counter.
                self.increment_counter('pulled')
            else:
                # Unrecognized status string.
                self.module.fail_json(msg="Unrecognized status from pull.", status=status, changes=changes)
        except Exception as e:
            self.module.fail_json(msg="Failed to pull the specified image: %s" % resource, error=repr(e))

    def create_containers(self, count=1):
        try:
            mem_limit = _human_to_bytes(self.module.params.get('memory_limit'))
        except ValueError as e:
            self.module.fail_json(msg=str(e))

        params = {'image':        self.module.params.get('image'),
                  'command':      self.module.params.get('command'),
                  'ports':        self.exposed_ports,
                  'volumes':      self.volumes,
                  'mem_limit':    mem_limit,
                  'environment':  self.env,
                  'hostname':     self.module.params.get('hostname'),
                  'domainname':   self.module.params.get('domainname'),
                  'detach':       self.module.params.get('detach'),
                  'name':         self.module.params.get('name'),
                  'stdin_open':   self.module.params.get('stdin_open'),
                  'tty':          self.module.params.get('tty'),
                  }

        def do_create(count, params):
            results = []
            for _ in range(count):
                result = self.client.create_container(**params)
                self.increment_counter('created')
                results.append(result)

            return results

        try:
            containers = do_create(count, params)
        except:
            self.pull_image()
            containers = do_create(count, params)

        return containers

    def start_containers(self, containers):
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
        for optional_param in ('dns', 'volumes_from', 'restart_policy',
                'restart_policy_retry', 'pid', 'extra_hosts'):
            optionals[optional_param] = self.module.params.get(optional_param)

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

        if optionals['pid'] is not None:
            self.ensure_capability('pid')
            params['pid_mode'] = optionals['pid']

        if optionals['extra_hosts'] is not None:
            self.ensure_capability('extra_hosts')
            params['extra_hosts'] = optionals['extra_hosts']

        for i in containers:
            self.client.start(i['Id'], **params)
            self.increment_counter('started')

    def stop_containers(self, containers):
        for i in containers:
            self.client.stop(i['Id'])
            self.increment_counter('stopped')

        return [self.client.wait(i['Id']) for i in containers]

    def remove_containers(self, containers):
        for i in containers:
            self.client.remove_container(i['Id'])
            self.increment_counter('removed')

    def kill_containers(self, containers):
        for i in containers:
            self.client.kill(i['Id'])
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
        containers.notice_changed(manager.create_containers(delta))

    if delta < 0:
        # If both running and stopped containers exist, remove
        # stopped containers first.
        containers.deployed.sort(lambda cx, cy: cmp(is_running(cx), is_running(cy)))

        to_stop = []
        to_remove = []
        for c in containers.deployed[0:-delta]:
            if is_running(c):
                to_stop.append(c)
            to_remove.append(c)

        manager.stop_containers(to_stop)
        manager.remove_containers(to_remove)
        containers.notice_changed(to_remove)

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
        containers.notice_changed(created)

    if delta < 0:
        excess = containers.running[0:-delta]
        manager.stop_containers(excess)
        manager.remove_containers(excess)
        containers.notice_changed(excess)

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

    manager.restart_containers(containers.running)
    started(manager, containers, count, name)

def stopped(manager, containers, count, name):
    '''Stop any matching containers that are running.'''

    containers.refresh()

    manager.stop_containers(containers.running)
    containers.notice_changed(containers.running)

def killed(manager, containers, count, name):
    '''Kill any matching containers that are running.'''

    containers.refresh()

    manager.kill_containers(containers.running)
    containers.notice_changed(containers.running)

def absent(manager, containers, count, name):
    '''Stop and remove any matching containers.'''

    containers.refresh()

    manager.stop_containers(containers.running)
    manager.remove_containers(containers.deployed)
    containers.notice_changed(containers.deployed)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            count           = dict(default=1),
            image           = dict(required=True),
            pull            = dict(required=False, default='missing', choices=['missing', 'always']),
            command         = dict(required=False, default=None),
            expose          = dict(required=False, default=None, type='list'),
            ports           = dict(required=False, default=None, type='list'),
            publish_all_ports = dict(default=False, type='bool'),
            volumes         = dict(default=None, type='list'),
            volumes_from    = dict(default=None),
            links           = dict(default=None, type='list'),
            memory_limit    = dict(default=0),
            memory_swap     = dict(default=0),
            docker_url      = dict(),
            use_tls         = dict(default=None, choices=['no', 'encrypt', 'verify']),
            tls_client_cert = dict(required=False, default=None, type='str'),
            tls_client_key  = dict(required=False, default=None, type='str'),
            tls_ca_cert     = dict(required=False, default=None, type='str'),
            tls_hostname    = dict(required=False, type='str', default=None),
            docker_api_version = dict(required=False, default=DEFAULT_DOCKER_API_VERSION, type='str'),
            username        = dict(default=None),
            password        = dict(),
            email           = dict(),
            registry        = dict(),
            hostname        = dict(default=None),
            domainname      = dict(default=None),
            env             = dict(type='dict'),
            dns             = dict(),
            detach          = dict(default=True, type='bool'),
            state           = dict(default='started', choices=['present', 'started', 'reloaded', 'restarted', 'stopped', 'killed', 'absent', 'running']),
            restart_policy  = dict(default=None, choices=['always', 'on-failure', 'no']),
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
        ),
        required_together = (
            ['tls_client_cert', 'tls_client_key'],
        ),
    )

    check_dependencies(module)

    try:
        manager = DockerManager(module)
        count = int(module.params.get('count'))
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

        # Explicitly pull new container images, if requested.
        # Do this before noticing running and deployed containers so that the image names will differ
        # if a newer image has been pulled.
        if pull == "always":
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
                         containers=containers.changed,
                         reload_reasons=manager.get_reload_reason_message(),
                         ansible_facts=_ansible_facts(containers.changed))

    except DockerAPIError as e:
        module.fail_json(changed=manager.has_changed(), msg="Docker API Error: %s" % e.explanation)

    except RequestException as e:
        module.fail_json(changed=manager.has_changed(), msg=repr(e))

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
