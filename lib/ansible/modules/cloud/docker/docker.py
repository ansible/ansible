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
    - If "missing," images will be pulled only when missing from the host; if
    - '"always," the registry will be checked for a newer version of the image'
    - each time the task executes.
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
    - are used to uniquely identify a single container or to link among
    - containers. Mutually exclusive with a "count" other than "1".
    default: null
    version_added: "1.5"
  ports:
    description:
     - List containing private to public port mapping specification. Use docker
     - 'CLI-style syntax: C(8000), C(9000:8000), or C(0.0.0.0:9000:8000) where'
     - 8000 is a container port, 9000 is a host port, and 0.0.0.0 is a host
     - interface.
    default: null
    version_added: "1.5"
  expose:
    description:
    - List of additional container ports to expose for port mappings or links.
    - If the port is already exposed using EXPOSE in a Dockerfile, you don't
    - need to expose it again.
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
    required: false
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
    - string like "512MB". Leave as "0" to specify no limit.
    required: false
    default: null
    aliases: []
    default: 256MB
  docker_url:
    description:
    - URL of the host running the docker daemon. This will default to the env
    - var DOCKER_HOST if unspecified.
    default: ${DOCKER_HOST} or unix://var/run/docker.sock
  docker_tls_cert:
    description:
    - Path to a PEM-encoded client certificate to secure the Docker connection.
    default: ${DOCKER_CERT_PATH}/cert.pem
  docker_tls_key:
    description:
    - Path to a PEM-encoded client key to secure the Docker connection.
    default: ${DOCKER_CERT_PATH}/key.pem
  docker_tls_cacert:
    description:
    - Path to a PEM-encoded certificate authority to secure the Docker connection.
    default: ${DOCKER_CERT_PATH}/ca.pem
  docker_api_version:
    description:
    - Remote API version to use. This defaults to the current default as
    - specified by docker-py.
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
    - matching containers exist. "started" asserts that the matching containers
    - both exist and are running, but takes no action if any configuration has
    - changed. "reloaded" asserts that all matching containers are running and
    - restarts any that have any images or configuration out of date. "restarted"
    - unconditionally restarts (or starts) the matching containers. "stopped" and
    - '"killed" stop and kill all matching containers. "absent" stops and then'
    - removes any matching containers.
    required: false
    default: present
    choices:
    - present
    - started
    - reloaded
    - restarted
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
    - retries.
    default: 0
    version_added: "1.9"
  insecure_registry:
    description:
    - Use insecure private registry by HTTP instead of HTTPS. Needed for
    - docker-py >= 0.5.0.
    default: false
    version_added: "1.9"

author: Cove Schneider, Joshua Conner, Pavel Antonov, Ash Wilson
requirements: [ "docker-py >= 0.3.0", "docker >= 0.10.0" ]
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
import re
from urlparse import urlparse
try:
    import docker.client
    import docker.utils
    from requests.exceptions import *
except ImportError, e:
    HAS_DOCKER_PY = False

if HAS_DOCKER_PY:
    try:
        from docker.errors import APIError as DockerAPIError
    except ImportError:
        from docker.client import APIError as DockerAPIError


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

    print "failed=True msg='Could not convert %s to integer'" % (number)
    sys.exit(1)

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

    counters = {'created':0, 'started':0, 'stopped':0, 'killed':0, 'removed':0, 'restarted':0, 'pull':0}
    _capabilities = set()
    # Map optional parameters to minimum (docker-py version, server APIVersion)
    # docker-py version is a tuple of ints because we have to compare them
    # server APIVersion is passed to a docker-py function that takes strings
    _cap_ver_req = {
            'dns': ((0, 3, 0), '1.10'),
            'volumes_from': ((0, 3, 0), '1.10'),
            'restart_policy': ((0, 5, 0), '1.14'),
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
                parts = option.split(':')
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

        # connect to docker server
        docker_url = urlparse(module.params.get('docker_url'))
        docker_api_version = module.params.get('docker_api_version')
        if not docker_api_version:
            docker_api_version=docker.client.DEFAULT_DOCKER_API_VERSION
        self.client = docker.Client(base_url=docker_url.geturl(), version=docker_api_version)

        self.docker_py_versioninfo = get_docker_py_versioninfo()

    def _check_capabilties(self):
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
            self._check_capabilties()

        if capability in self._capabilities:
            return True

        if not fail:
            return False

        api_version = self.client.version()['ApiVersion']
        self.module.fail_json(msg='Specifying the `%s` parameter requires'
                ' docker-py: %s, docker server apiversion %s; found'
                ' docker-py: %s, server: %s' % (
                    capability,
                    '.'.join(self._cap_ver_req[capability][0]),
                    self._cap_ver_req[capability][1],
                    '.'.join(self.docker_py_versioninfo),
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
                # to a dynamically allocacted port of IP `parts[0]`.
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
        image, tag = get_split_image_tag(self.module.params.get('image'))
        if tag is None:
            tag = 'latest'
        resource = '%s:%s' % (image, tag)

        matching_image = None
        for image in self.client.images(name=image):
            if resource in image.get('RepoTags', []):
                matching_image = image
        return matching_image

    def get_inspect_containers(self, containers):
        inspect = []
        for i in containers:
            details = self.client.inspect_container(i['Id'])
            details = _docker_id_quirk(details)
            inspect.append(details)

        return inspect

    def get_deployed_containers(self):
        """determine which images/commands are running already"""
        image = self.module.params.get('image')
        command = self.module.params.get('command')
        if command:
            command = command.strip()
        name = self.module.params.get('name')
        if name and not name.startswith('/'):
            name = '/' + name
        deployed = []

        # if we weren't given a tag with the image, we need to only compare on the image name, as that
        # docker will give us back the full image name including a tag in the container list if one exists.
        image, tag = get_split_image_tag(image)

        for i in self.client.containers(all=True):
            running_image, running_tag = get_split_image_tag(i['Image'])
            running_command = i['Command'].strip()

            name_matches = False
            if i["Names"]:
                name_matches = (name and name in i['Names'])
            image_matches = (running_image == image)
            tag_matches = (not tag or running_tag == tag)
            # if a container has an entrypoint, `command` will actually equal
            # '{} {}'.format(entrypoint, command)
            command_matches = (not command or running_command.endswith(command))

            if name_matches or (name is None and image_matches and tag_matches and command_matches):
                details = self.client.inspect_container(i['Id'])
                details = _docker_id_quirk(details)
                deployed.append(details)

        return deployed

    def get_running_containers(self):
        running = []
        for i in self.get_deployed_containers():
            if i['State']['Running'] == True and i['State'].get('Ghost', False) == False:
                running.append(i)

        return running

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
            except:
                self.module.fail_json(msg="failed to login to the remote registry, check your username/password.")
        try:
            last = None
            for line in self.client.pull(image, tag=tag, stream=True, **extra_params):
                last = line
            status = json.loads(last).get('status', '')
            if status.startswith('Status: Image is up to date for'):
                # Image is already up to date. Don't increment the counter.
                pass
            elif status.startswith('Status: Downloaded newer image for'):
                # Image was updated. Increment the pull counter.
                self.increment_counter('pull')
            else:
                # Unrecognized status string.
                self.module.fail_json(msg="Unrecognized status from pull", status=status)
        except:
            self.module.fail_json(msg="failed to pull the specified image: %s" % resource)

    def create_containers(self, count=1):
        params = {'image':        self.module.params.get('image'),
                  'command':      self.module.params.get('command'),
                  'ports':        self.exposed_ports,
                  'volumes':      self.volumes,
                  'mem_limit':    _human_to_bytes(self.module.params.get('memory_limit')),
                  'environment':  self.env,
                  'hostname':     self.module.params.get('hostname'),
                  'domainname':   self.module.params.get('domainname'),
                  'detach':       self.module.params.get('detach'),
                  'name':         self.module.params.get('name'),
                  'stdin_open':   self.module.params.get('stdin_open'),
                  'tty':          self.module.params.get('tty'),
                  'volumes_from': self.module.params.get('volumes_from'),
                  }
        if docker.utils.compare_version('1.10', self.client.version()['ApiVersion']) >= 0:
            params['volumes_from'] = ""

        if params['volumes_from'] is not None:
            self.ensure_capability('volumes_from')

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
            'privileged':   self.module.params.get('privileged'),
            'links': self.links,
            'network_mode': self.module.params.get('net'),
        }

        optionals = {}
        for optional_param in ('dns', 'volumes_from', 'restart_policy', 'restart_policy_retry'):
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
            docker_url      = dict(default='unix://var/run/docker.sock'),
            docker_api_version = dict(),
            username        = dict(default=None),
            password        = dict(),
            email           = dict(),
            registry        = dict(),
            hostname        = dict(default=None),
            domainname      = dict(default=None),
            env             = dict(type='dict'),
            dns             = dict(),
            detach          = dict(default=True, type='bool'),
            state           = dict(default='running', choices=['absent', 'present', 'running', 'stopped', 'killed', 'restarted']),
            restart_policy  = dict(default=None, choices=['always', 'on-failure', 'no']),
            restart_policy_retry = dict(default=0, type='int'),
            debug           = dict(default=False, type='bool'),
            privileged      = dict(default=False, type='bool'),
            stdin_open      = dict(default=False, type='bool'),
            tty             = dict(default=False, type='bool'),
            lxc_conf        = dict(default=None, type='list'),
            name            = dict(default=None),
            net             = dict(default=None),
            insecure_registry = dict(default=False, type='bool'),
        )
    )

    check_dependencies(module)

    try:
        manager = DockerManager(module)
        state = module.params.get('state')
        count = int(module.params.get('count'))
        name = module.params.get('name')
        image = module.params.get('image')
        pull = module.params.get('pull')

        if count < 0:
            module.fail_json(msg="Count must be greater than zero")
        if count > 1 and name:
            module.fail_json(msg="Count and name must not be used together")

        # Explicitly pull new container images, if requested.
        # Do this before noticing running and deployed containers so that the image names will differ
        # if a newer image has been pulled.
        if pull == "always":
            manager.pull_image()

        # Find the ID of the requested image and tag, if available.
        image_id = None
        inspected_image = manager.get_inspect_image()
        if inspected_image:
            image_id = inspected_image.get('Id')

        running_containers = manager.get_running_containers()
        running_count = len(running_containers)
        delta = count - running_count
        deployed_containers = manager.get_deployed_containers()
        facts = None
        failed = False
        changed = False

        # start/stop containers
        if state in [ "running", "present" ]:

            # make sure a container with `name` exists, if not create and start it
            if name:
                # first determine if a container with this name exists
                existing_container = None
                for deployed_container in deployed_containers:
                    if deployed_container.get('Name') == '/%s' % name:
                        existing_container = deployed_container
                        break

                # the named container is running, but with a
                # different image or tag, so we stop it first
                if existing_container and (image_id is None or existing_container.get('Image') != image_id):
                    manager.stop_containers([existing_container])
                    manager.remove_containers([existing_container])
                    running_containers = manager.get_running_containers()
                    deployed_containers = manager.get_deployed_containers()
                    existing_container = None

                # if the container isn't running (or if we stopped the
                # old version above), create and (maybe) start it up now
                if not existing_container:
                    containers = manager.create_containers(1)
                    if state == "present": # otherwise it get (re)started later anyways..
                        manager.start_containers(containers)
                        running_containers = manager.get_running_containers()
                    deployed_containers = manager.get_deployed_containers()

            if state == "running":
                # make sure a container with `name` is running
                if name and "/" + name not in map(lambda x: x.get('Name'), running_containers):
                    manager.start_containers(deployed_containers)

                # start more containers if we don't have enough
                elif delta > 0:
                    containers = manager.create_containers(delta)
                    manager.start_containers(containers)

                # stop containers if we have too many
                elif delta < 0:
                    containers_to_stop = running_containers[0:abs(delta)]
                    containers = manager.stop_containers(containers_to_stop)
                    manager.remove_containers(containers_to_stop)

                facts = manager.get_running_containers()
            else:
                facts = manager.get_deployed_containers()

        # stop and remove containers
        elif state == "absent":
            facts = manager.stop_containers(deployed_containers)
            manager.remove_containers(deployed_containers)

        # stop containers
        elif state == "stopped":
            facts = manager.stop_containers(running_containers)

        # kill containers
        elif state == "killed":
            manager.kill_containers(running_containers)

        # restart containers
        elif state == "restarted":
            manager.restart_containers(running_containers)
            facts = manager.get_inspect_containers(running_containers)

        msg = "%s container(s) running image %s with command %s" % \
                (manager.get_summary_counters_msg(), module.params.get('image'), module.params.get('command'))
        changed = manager.has_changed()

        module.exit_json(failed=failed, changed=changed, msg=msg, ansible_facts=_ansible_facts(facts))

    except DockerAPIError, e:
        changed = manager.has_changed()
        module.exit_json(failed=True, changed=changed, msg="Docker API error: " + e.explanation)

    except RequestException, e:
        changed = manager.has_changed()
        module.exit_json(failed=True, changed=changed, msg=repr(e))

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
