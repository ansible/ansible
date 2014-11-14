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
      - Set number of containers to run
    required: False
    default: 1
    aliases: []
  image:
    description:
       - Set container image to use
    required: true
    default: null
    aliases: []
  command:
    description:
       - Set command to run in a container on startup
    required: false
    default: null
    aliases: []
  name:
    description:
       - Set name for container (used to find single container or to provide links)
    required: false
    default: null
    aliases: []
    version_added: "1.5"
  ports:
    description:
      - Set private to public port mapping specification using docker CLI-style syntax [([<host_interface>:[host_port]])|(<host_port>):]<container_port>[/udp]
    required: false
    default: null
    aliases: []
    version_added: "1.5"
  expose:
    description:
      - Set container ports to expose for port mappings or links. (If the port is already exposed using EXPOSE in a Dockerfile, you don't need to expose it again.)
    required: false
    default: null
    aliases: []
    version_added: "1.5"
  publish_all_ports:
    description:
      - Publish all exposed ports to the host interfaces
    required: false
    default: false
    aliases: []
    version_added: "1.5"
  volumes:
    description:
      - Set volume(s) to mount on the container
    required: false
    default: null
    aliases: []
  volumes_from:
    description:
      - Set shared volume(s) from another container
    required: false
    default: null
    aliases: []
  links:
    description:
      - Link container(s) to other container(s) (e.g. links=redis,postgresql:db)
    required: false
    default: null
    aliases: []
    version_added: "1.5"
  memory_limit:
    description:
      - Set RAM allocated to container
    required: false
    default: null
    aliases: []
    default: 256MB
  docker_url:
    description:
      - URL of docker host to issue commands to
    required: false
    default: unix://var/run/docker.sock
    aliases: []
  docker_api_version:
    description:
      - Remote API version to use. This defaults to the current default as specified by docker-py.
    required: false
    default: docker-py default remote API version
    aliases: []
    version_added: "1.8"
  username:
    description:
      - Set remote API username
    required: false
    default: null
    aliases: []
  password:
    description:
      - Set remote API password
    required: false
    default: null
    aliases: []
  hostname:
    description:
      - Set container hostname
    required: false
    default: null
    aliases: []
  env:
    description:
      - Set environment variables (e.g. env="PASSWORD=sEcRe7,WORKERS=4")
    required: false
    default: null
    aliases: []
  dns:
    description:
      - Set custom DNS servers for the container
    required: false
    default: null
    aliases: []
  detach:
    description:
      - Enable detached mode on start up, leaves container running in background
    required: false
    default: true
    aliases: []
  state:
    description:
      - Set the state of the container
    required: false
    default: present
    choices: [ "present", "running", "stopped", "absent", "killed", "restarted" ]
    aliases: []
  privileged:
    description:
      - Set whether the container should run in privileged mode
    required: false
    default: false
    aliases: []
  lxc_conf:
    description:
      - LXC config parameters,  e.g. lxc.aa_profile:unconfined
    required: false
    default:
    aliases: []
  name:
    description:
      - Set the name of the container (cannot use with count)
    required: false
    default: null
    aliases: []
    version_added: "1.5"
  stdin_open:
    description:
      - Keep stdin open
    required: false
    default: false
    aliases: []
    version_added: "1.6"
  tty:
    description:
      - Allocate a pseudo-tty
    required: false
    default: false
    aliases: []
    version_added: "1.6"
  net:
    description:
      - Set Network mode for the container (bridge, none, container:<name|id>, host). Requires docker >= 0.11.
    required: false
    default: false
    aliases: []
    version_added: "1.8"
  registry:
    description:
      - The remote registry URL to use for pulling images.
    required: false
    default: ''
    aliases: []
    version_added: "1.8"

author: Cove Schneider, Joshua Conner, Pavel Antonov
requirements: [ "docker-py >= 0.3.0", "docker >= 0.10.0" ]
'''

EXAMPLES = '''
Start one docker container running tomcat in each host of the web group and bind tomcat's listening port to 8080
on the host:

- hosts: web
  sudo: yes
  tasks:
  - name: run tomcat servers
    docker: image=centos command="service tomcat6 start" ports=8080

The tomcat server's port is NAT'ed to a dynamic port on the host, but you can determine which port the server was
mapped to using docker_containers:

- hosts: web
  sudo: yes
  tasks:
  - name: run tomcat servers
    docker: image=centos command="service tomcat6 start" ports=8080 count=5
  - name: Display IP address and port mappings for containers
    debug: msg={{inventory_hostname}}:{{item['HostConfig']['PortBindings']['8080/tcp'][0]['HostPort']}}
    with_items: docker_containers

Just as in the previous example, but iterates over the list of docker containers with a sequence:

- hosts: web
  sudo: yes
  vars:
    start_containers_count: 5
  tasks:
  - name: run tomcat servers
    docker: image=centos command="service tomcat6 start" ports=8080 count={{start_containers_count}}
  - name: Display IP address and port mappings for containers
    debug: msg="{{inventory_hostname}}:{{docker_containers[{{item}}]['HostConfig']['PortBindings']['8080/tcp'][0]['HostPort']}}"
    with_sequence: start=0 end={{start_containers_count - 1}}

Stop, remove all of the running tomcat containers and list the exit code from the stopped containers:

- hosts: web
  sudo: yes
  tasks:
  - name: stop tomcat servers
    docker: image=centos command="service tomcat6 start" state=absent
  - name: Display return codes from stopped containers
    debug: msg="Returned {{inventory_hostname}}:{{item}}"
    with_items: docker_containers

Create a named container:

- hosts: web
  sudo: yes
  tasks:
  - name: run tomcat server
    docker: image=centos name=tomcat command="service tomcat6 start" ports=8080

Create multiple named containers:

- hosts: web
  sudo: yes
  tasks:
  - name: run tomcat servers
    docker: image=centos name={{item}} command="service tomcat6 start" ports=8080
    with_items:
      - crookshank
      - snowbell
      - heathcliff
      - felix
      - sylvester

Create containers named in a sequence:

- hosts: web
  sudo: yes
  tasks:
  - name: run tomcat servers
    docker: image=centos name={{item}} command="service tomcat6 start" ports=8080
    with_sequence: start=1 end=5 format=tomcat_%d.example.com

Create two linked containers:

- hosts: web
  sudo: yes
  tasks:
  - name: ensure redis container is running
    docker: image=crosbymichael/redis name=redis

  - name: ensure redis_ambassador container is running
    docker: image=svendowideit/ambassador ports=6379:6379 links=redis:redis name=redis_ambassador_ansible

Create containers with options specified as key-value pairs and lists:

- hosts: web
  sudo: yes
  tasks:
  - docker:
        image: namespace/image_name
        links:
          - postgresql:db
          - redis:redis


Create containers with options specified as strings and lists as comma-separated strings:

- hosts: web
  sudo: yes
  tasks:
  docker: image=namespace/image_name links=postgresql:db,redis:redis

Create a container with no networking:

- hosts: web
  sudo: yes
  tasks:
  docker: image=namespace/image_name net=none

'''

HAS_DOCKER_PY = True

import sys
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

class DockerManager:

    counters = {'created':0, 'started':0, 'stopped':0, 'killed':0, 'removed':0, 'restarted':0, 'pull':0}

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
        self.client = docker.Client(base_url=docker_url.geturl(), version=docker_api_version)


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

    def create_containers(self, count=1):
        params = {'image':        self.module.params.get('image'),
                  'command':      self.module.params.get('command'),
                  'ports':        self.exposed_ports,
                  'volumes':      self.volumes,
                  'mem_limit':    _human_to_bytes(self.module.params.get('memory_limit')),
                  'environment':  self.env,
                  'hostname':     self.module.params.get('hostname'),
                  'detach':       self.module.params.get('detach'),
                  'name':         self.module.params.get('name'),
                  'stdin_open':   self.module.params.get('stdin_open'),
                  'tty':          self.module.params.get('tty'),
                  }

        if docker.utils.compare_version('1.10', self.client.version()['ApiVersion']) < 0:
            params['dns'] = self.module.params.get('dns')
            params['volumes_from'] = self.module.params.get('volumes_from')

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
                self.client.pull(image, tag=tag)
            except:
                self.module.fail_json(msg="failed to pull the specified image: %s" % resource)
            self.increment_counter('pull')
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
        if docker.utils.compare_version('1.10', self.client.version()['ApiVersion']) >= 0 and hasattr(docker, '__version__') and docker.__version__ > '0.3.0':
            params['dns'] = self.module.params.get('dns')
            params['volumes_from'] = self.module.params.get('volumes_from')

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


def check_dependencies(module):
    """
    Ensure `docker-py` >= 0.3.0 is installed, and call module.fail_json with a
    helpful error message if it isn't.
    """
    if not HAS_DOCKER_PY:
        module.fail_json(msg="`docker-py` doesn't seem to be installed, but is required for the Ansible Docker module.")
    else:
        HAS_NEW_ENOUGH_DOCKER_PY = False
        if hasattr(docker, '__version__'):
            # a '__version__' attribute was added to the module but not until
            # after 0.3.0 was added pushed to pip. If it's there, use it.
            if docker.__version__ >= '0.3.0':
                HAS_NEW_ENOUGH_DOCKER_PY = True
        else:
            # HACK: if '__version__' isn't there, we check for the existence of
            # `_get_raw_response_socket` in the docker.Client class, which was
            # added in 0.3.0
            if hasattr(docker.Client, '_get_raw_response_socket'):
                HAS_NEW_ENOUGH_DOCKER_PY = True

        if not HAS_NEW_ENOUGH_DOCKER_PY:
            module.fail_json(msg="The Ansible Docker module requires `docker-py` >= 0.3.0.")


def main():
    module = AnsibleModule(
        argument_spec = dict(
            count           = dict(default=1),
            image           = dict(required=True),
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
            docker_api_version = dict(default=docker.client.DEFAULT_DOCKER_API_VERSION),
            username        = dict(default=None),
            password        = dict(),
            email           = dict(),
            registry        = dict(),
            hostname        = dict(default=None),
            env             = dict(type='dict'),
            dns             = dict(),
            detach          = dict(default=True, type='bool'),
            state           = dict(default='running', choices=['absent', 'present', 'running', 'stopped', 'killed', 'restarted']),
            debug           = dict(default=False, type='bool'),
            privileged      = dict(default=False, type='bool'),
            stdin_open      = dict(default=False, type='bool'),
            tty             = dict(default=False, type='bool'),
            lxc_conf        = dict(default=None, type='list'),
            name            = dict(default=None),
            net             = dict(default=None)
        )
    )

    check_dependencies(module)

    try:
        manager = DockerManager(module)
        state = module.params.get('state')
        count = int(module.params.get('count'))
        name = module.params.get('name')
        image = module.params.get('image')

        if count < 0:
            module.fail_json(msg="Count must be greater than zero")
        if count > 1 and name:
            module.fail_json(msg="Count and name must not be used together")

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
                if existing_container and existing_container.get('Config', dict()).get('Image') != image:
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
