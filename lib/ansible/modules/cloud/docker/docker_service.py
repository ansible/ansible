#!/usr/bin/python
#
# Copyright 2016 Red Hat | Ansible
#
# This file is part of Ansible
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

DOCUMENTATION = '''

module: docker_service

short_description: Manage docker services and containers.

version_added: "2.1"

author: "Chris Houseknecht (@chouseknecht)"

description:
  - Consumes docker compose to start, shutdown and scale services.
  - Works with compose versions 1 and 2.
  - Compose can be read from a docker-compose.yml (or .yaml) file or inline using the C(definition) option.
  - See the examples for more details.
  - Supports check mode.

options:
  project_src:
      description:
        - Path to a directory containing a docker-compose.yml or docker-compose.yaml file.
        - Mutually exclusive with C(definition).
        - Required when no C(definition) is provided.
      type: path
      required: false
  project_name:
      description:
        - Provide a project name. If not provided, the project name is taken from the basename of C(project_src).
        - Required when no C(definition) is provided.
      type: str
      required: false
  files:
      description:
        - List of file names relative to C(project_src). Overrides docker-compose.yml or docker-compose.yaml.
        - Files are loaded and merged in the order given.
      type: list
      required: false
  state:
      description:
        - Desired state of the project.
        - Specifying I(present) is the same as running I(docker-compose up).
        - Specifying I(absent) is the same as running I(docker-compose down).
      choices:
        - absent
        - present
      default: present
      type: str
      required: false
  services:
      description:
        - When C(state) is I(present) run I(docker-compose up) on a subset of services.
      type: list
      required: false
  scale:
      description:
        - When C(sate) is I(present) scale services. Provide a dictionary of key/value pairs where the key
          is the name of the service and the value is an integer count for the number of containers.
      type: complex
      required: false
  dependencies:
      description:
        - When C(state) is I(present) specify whether or not to include linked services.
      type: bool
      required: false
      default: true
  definition:
      description:
        - Provide docker-compose yaml describing one or more services, networks and volumes.
        - Mutually exclusive with C(project_src) and C(project_files).
      type: complex
      required: false
  hostname_check:
      description:
        - Whether or not to check the Docker daemon's hostname against the name provided in the client certificate.
      type: bool
      required: false
      default: false
  recreate:
      description:
        - By default containers will be recreated when their configuration differs from the service definition.
        - Setting to I(never) ignores configuration differences and leaves existing containers unchanged.
        - Setting to I(always) forces recreation of all existing containers.
      type: str
      required: false
      choices:
        - always
        - never
        - smart
      default: smart
  build:
      description:
        - Whether or not to build images before starting containers.
        - Missing images will always be built.
        - If an image is present and C(build) is false, the image will not be built.
        - If an image is present and C(build) is true, the image will be built.
      type: bool
      required: false
      default: true
  remove_images:
      description:
        - Use with state I(absent) to remove the all images or only local images.
      type: str
      required: false
      default: null
  remove_volumes:
      description:
        - Use with state I(absent) to remove data volumes.
      required: false
      type: bool
      default: false
  stopped:
      description:
        - Use with state I(present) to leave the containers in an exited or non-running state.
      required: false
      type: bool
      default: false
  restarted:
      description:
        - Use with state I(present) to restart all containers.
      required: false
      type: bool
      default: false
  debug:
      description:
        - Include I(actions) in the return values.
      required: false
      type: bool
      default: false

extends_documentation_fragment:
    - docker

requirements:
    - "python >= 2.6"
    - "docker-compose >= 1.7.0"
    - "Docker API >= 1.20"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
# Examples use the django example at U(https://docs.docker.com/compose/django/). Follow it to create the flask
# directory

- name: Run using a project directory
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - docker_service:
        project_src: flask
        state: absent

    - docker_service:
        project_src: flask
      register: output

    - debug: var=output

    - docker_service:
        project_src: flask
        build: no
      register: output

    - debug: var=output

    - assert:
        that: "not output.changed "

    - docker_service:
        project_src: flask
        build: no
        stopped: true
      register: output

    - debug: var=output

    - assert:
        that:
          - "not web.flask_web_1.state.running"
          - "not db.flask_db_1.state.running"

    - docker_service:
        project_src: flask
        build: no
        restarted: true
      register: output

    - debug: var=output

    - assert:
        that:
          - "web.flask_web_1.state.running"
          - "db.flask_db_1.state.running"

- name: Scale the web service to 2
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - docker_service:
        project_src: flask
        scale:
          web: 2
      register: output

    - debug: var=output

- name: Run with inline v2 compose
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - docker_service:
        project_src: flask
        state: absent

    - docker_service:
        project_name: flask
        definition:
          version: '2'
          services:
            db:
              image: postgres
            web:
              build: "{{ playbook_dir }}/flask"
              command: "python manage.py runserver 0.0.0.0:8000"
              volumes:
                - "{{ playbook_dir }}/flask:/code"
              ports:
                - "8000:8000"
              depends_on:
                - db
      register: output

    - debug: var=output

    - assert:
        that:
          - "web.flask_web_1.state.running"
          - "db.flask_db_1.state.running"

- name: Run with inline v1 compose
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - docker_service:
        project_src: flask
        state: absent

    - docker_service:
        project_name: flask
        definition:
            db:
              image: postgres
            web:
              build: "{{ playbook_dir }}/flask"
              command: "python manage.py runserver 0.0.0.0:8000"
              volumes:
                - "{{ playbook_dir }}/flask:/code"
              ports:
                - "8000:8000"
              links:
                - db
      register: output

    - debug: var=output

    - assert:
        that:
          - "web.flask_web_1.state.running"
          - "db.flask_db_1.state.running"
'''

RETURN = '''
service:
  description: Name of the service.
  returned: success
  type: complex
  contains:
      container_name:
          description: Name of the container. Format is I(project_service_#).
          returned: success
          type: complex
          contains:
              cmd:
                  description: One or more commands to be executed in the container.
                  returned: success
                  type: list
                  example: ["postgres"]
              image:
                  description: Name of the image from which the container was built.
                  returned: success
                  type: str
                  example: postgres
              labels:
                  description: Meta data assigned to the container.
                  returned: success
                  type: complex
                  example: {...}
              networks:
                  description: Contains a dictionary for each network to which the container is a member.
                  returned: success
                  type: complex
                  contains:
                      IPAddress:
                          description: The IP address assigned to the container.
                          returned: success
                          type: string
                          example: 172.17.0.2
                      IPPrefixLen:
                          description: Number of bits used by the subnet.
                          returned: success
                          type: int
                          example: 16
                      aliases:
                          description: Aliases assigned to the container by the network.
                          returned: success
                          type: list
                          example: ['db']
                      globalIPv6:
                          description: IPv6 address assigned to the container.
                          returned: success
                          type: str
                          example: ''
                      globalIPv6PrefixLen:
                          description: IPv6 subnet length.
                          returned: success
                          type: int
                          example: 0
                      links:
                          description: List of container names to which this container is linked.
                          returned: success
                          type: list
                          example: null
                      macAddress:
                          description: Mac Address assigned to the virtual NIC.
                          returned: success
                          type: str
                          example: "02:42:ac:11:00:02"
              state:
                  description: Information regarding the current disposition of the container.
                  returned: success
                  type: complex
                  contains:
                      running:
                          description: Whether or not the container is up with a running process.
                          returned: success
                          type: bool
                          example: true
                      status:
                          description: Description of the running state.
                          returned: success
                          type: str
                          example: running

actions:
  description: Provides the actions to be taken on each service as determined by compose.
  returned: when in check mode or I(debug) true
  type: complex
  contains:
      service_name:
          description: Name of the service.
          returned: always
          type: complex
          contains:
              action:
                  description: A descriptive name of the action to be performed on the set of containers
                               within the service.
                  returned: always
                  type: list
                  contains:
                      id:
                          description: the container's long ID
                          returned: always
                          type: string
                      name:
                          description: the container's name
                          returned: always
                          type: string
                      short_id:
                          description: the container's short ID
                          returned: always
                          type: string
'''

HAS_YAML = True
HAS_YAML_EXC = None
HAS_COMPOSE = True
HAS_COMPOSE_EXC = None
MINIMUM_COMPOSE_VERSION = '1.7.0'

try:
    import yaml
except ImportError as exc:
    HAS_YAML = False
    HAS_YAML_EXC = str(exc)

from distutils.version import LooseVersion
from ansible.module_utils.basic import *

try:
    from compose import __version__ as compose_version
    from compose.cli.command import project_from_options
    from compose.service import ConvergenceStrategy
    from compose.cli.main import convergence_strategy_from_opts, build_action_from_opts, image_type_from_opt
except ImportError as exc:
    HAS_COMPOSE = False
    HAS_COMPOSE_EXC = str(exc)

from ansible.module_utils.docker_common import *


AUTH_PARAM_MAPPING = {
    u'docker_host': u'--host',
    u'tls': u'--tls',
    u'cacert_path': u'--tlscacert',
    u'cert_path': u'--tlscert',
    u'key_path': u'--tlskey',
    u'tls_verify': u'--tlsverify'
}


class ContainerManager(DockerBaseClass):

    def __init__(self, client):

        super(ContainerManager, self).__init__()

        self.client = client
        self.project_src = None
        self.files = None
        self.project_name = None
        self.state = None
        self.definition = None
        self.hostname_check = None
        self.timeout = None
        self.remove_images = None
        self.remove_orphans = None
        self.remove_volumes = None
        self.stopped = None
        self.restarted = None
        self.recreate = None
        self.build = None
        self.dependencies = None
        self.services = None
        self.scale = None
        self.debug = None

        for key, value in client.module.params.items():
            setattr(self, key, value)

        self.check_mode = client.check_mode

        if not self.debug:
            self.debug = client.module._debug

        self.options = dict()
        self.options.update(self._get_auth_options())
        self.options[u'--skip-hostname-check'] = (not self.hostname_check)

        if self.project_name:
            self.options[u'--project-name'] = self.project_name

        if self.files:
            self.options[u'--file'] = self.files

        if not HAS_COMPOSE:
            self.client.fail("Unable to load docker-compose. Try `pip install docker-compose`. Error: %s" % HAS_COMPOSE_EXC)

        if LooseVersion(compose_version) < LooseVersion(MINIMUM_COMPOSE_VERSION):
            self.client.fail("Found docker-compose version %s. Minimum required version is %s. "
                             "Upgrade docker-compose to a min version of %s." %
                             (compose_version, MINIMUM_COMPOSE_VERSION, MINIMUM_COMPOSE_VERSION))

        self.log("options: ")
        self.log(self.options, pretty_print=True)

        if self.definition:
            if not HAS_YAML:
                self.client.fail("Unable to load yaml. Try `pip install PyYAML`. Error: %s" % HAS_YAML_EXC)

            if not self.project_name:
                self.client.fail("Parameter error - project_name required when providing definition.")

            self.project_src = tempfile.mkdtemp(prefix="ansible")
            compose_file = os.path.join(self.project_src, "docker-compose.yml")
            try:
                self.log('writing: ')
                self.log(yaml.dump(self.definition, default_flow_style=False))
                with open(compose_file, 'w') as f:
                    f.write(yaml.dump(self.definition, default_flow_style=False))
            except Exception as exc:
                self.client.fail("Error writing to %s - %s" % (compose_file, str(exc)))
        else:
            if not self.project_src:
                self.client.fail("Parameter error - project_src required.")

        try:
            self.log("project_src: %s" % self.project_src)
            self.project = project_from_options(self.project_src, self.options)
        except Exception as exc:
            self.client.fail("Configuration error - %s" % str(exc))

    def exec_module(self):
        result = dict()

        if self.state == 'present':
            result = self.cmd_up()
        elif self.state == 'absent':
            result = self.cmd_down()

        if self.definition:
            compose_file = os.path.join(self.project_src, "docker-compose.yml")
            self.log("removing %s" % compose_file)
            os.remove(compose_file)
            self.log("removing %s" % self.project_src)
            os.rmdir(self.project_src)

        if not self.check_mode and not self.debug and result.get('actions'):
            result.pop('actions')

        return result

    def _get_auth_options(self):
        options = dict()
        for key, value in self.client.auth_params.items():
            if value is not None:
                option = AUTH_PARAM_MAPPING.get(key)
                if option:
                    options[option] = value
        return options

    def cmd_up(self):

        start_deps = self.dependencies
        service_names = self.services
        detached = True
        result = dict(changed=False, actions=dict(), ansible_facts=dict())

        up_options = {
            u'--no-recreate': False,
            u'--build': self.build,
            u'--no-build': False,
            u'--no-deps': False,
            u'--force-recreate': False,
        }

        if self.recreate == 'never':
            up_options[u'--no-recreate'] = True
        elif self.recreate == 'always':
            up_options[u'--force-recreate'] = True

        if self.remove_orphans:
            up_options[u'--remove-orphans'] = True

        converge = convergence_strategy_from_opts(up_options)
        self.log("convergence strategy: %s" % converge)

        for service in self.project.services:
            if not service_names or service.name in service_names:
                plan = service.convergence_plan(strategy=converge)
                if plan.action != 'noop':
                    result['changed'] = True
                if self.debug or self.check_mode:
                    result['actions'][service.name] = dict()
                    result['actions'][service.name][plan.action] = []
                    for container in plan.containers:
                        result['actions'][service.name][plan.action].append(dict(
                            id=container.id,
                            name=container.name,
                            short_id=container.short_id,
                        ))

        if not self.check_mode and result['changed']:
            try:
                self.project.up(
                    service_names=service_names,
                    start_deps=start_deps,
                    strategy=converge,
                    do_build=build_action_from_opts(up_options),
                    detached=detached,
                    remove_orphans=self.remove_orphans)
            except Exception as exc:
                self.client.fail("Error bring %s up - %s" % (self.project.name, str(exc)))

        if self.stopped:
            result.update(self.cmd_stop(service_names))

        if self.restarted:
            result.update(self.cmd_restart(service_names))

        if self.scale:
            result.update(self.cmd_scale())

        for service in self.project.services:
            result['ansible_facts'][service.name] = dict()
            for container in service.containers(stopped=True):
                inspection = container.inspect()
                # pare down the inspection data to the most useful bits
                facts = dict(
                    cmd=[],
                    labels=dict(),
                    image=None,
                    state=dict(
                        running=None,
                        status=None
                    ),
                    networks=dict()
                )
                if inspection['Config'].get('Cmd', None) is not None:
                    facts['cmd'] = inspection['Config']['Cmd']
                if inspection['Config'].get('Labels', None) is not None:
                    facts['labels'] = inspection['Config']['Labels']
                if inspection['Config'].get('Image', None) is not None:
                    facts['image'] = inspection['Config']['Image']
                if inspection['State'].get('Running', None) is not None:
                    facts['state']['running'] = inspection['State']['Running']
                if inspection['State'].get('Status', None) is not None:
                    facts['state']['status'] = inspection['State']['Status']

                if inspection.get('NetworkSettings') and inspection['NetworkSettings'].get('Networks'):
                    networks = inspection['NetworkSettings']['Networks']
                    for key in networks:
                        facts['networks'][key] = dict(
                            aliases=[],
                            globalIPv6=None,
                            globalIPv6PrefixLen=0,
                            IPAddress=None,
                            IPPrefixLen=0,
                            links=None,
                            macAddress=None,
                        )
                        if networks[key].get('Aliases', None) is not None:
                            facts['networks'][key]['aliases'] = networks[key]['Aliases']
                        if networks[key].get('GlobalIPv6Address', None) is not None:
                            facts['networks'][key]['globalIPv6'] = networks[key]['GlobalIPv6Address']
                        if networks[key].get('GlobalIPv6PrefixLen', None) is not None:
                            facts['networks'][key]['globalIPv6PrefixLen'] = networks[key]['GlobalIPv6PrefixLen']
                        if networks[key].get('IPAddress', None) is not None:
                            facts['networks'][key]['IPAddress'] = networks[key]['IPAddress']
                        if networks[key].get('IPPrefixLen', None) is not None:
                            facts['networks'][key]['IPPrefixLen'] = networks[key]['IPPrefixLen']
                        if networks[key].get('Links', None) is not None:
                            facts['networks'][key]['links'] = networks[key]['Links']
                        if networks[key].get('MacAddress', None) is not None:
                            facts['networks'][key]['macAddress'] = networks[key]['MacAddress']

                result['ansible_facts'][service.name][container.name] = facts

        return result

    def cmd_down(self):
        result = dict(
            changed=False,
            actions=dict(),
        )

        for service in self.project.services:
            containers = service.containers(stopped=True)
            if len(containers):
                result['changed'] = True
            if self.debug or self.check_mode:
                result['actions'][service.name] = dict()
                result['actions'][service.name]['deleted'] = [container.name for container in containers]

        if not self.check_mode and result['changed']:
            image_type = image_type_from_opt('--rmi', self.remove_images)
            try:
                self.project.down(image_type, self.remove_volumes, self.remove_orphans)
            except Exception as exc:
                self.client.fail("Error bringing %s down - %s" % (self.project.name, str(exc)))

        return result

    def cmd_stop(self, service_names):
        result = dict(
            changed=False,
            actions=dict()
        )
        for service in self.project.services:
            if not service_names or service.name in service_names:
                result['actions'][service.name] = dict()
                result['actions'][service.name]['stop'] = []
                for container in service.containers(stopped=False):
                    result['changed'] = True
                    if self.debug:
                        result['actions'][service.name]['stop'].append(dict(
                            id=container.id,
                            name=container.name,
                            short_id=container.short_id,
                        ))

        if not self.check_mode and result['changed']:
            try:
                self.project.stop(service_names=service_names)
            except Exception as exc:
                self.client.fail("Error stopping services for %s - %s" % (self.project.name, str(exc)))

        return result

    def cmd_restart(self, service_names):
        result = dict(
            changed=False,
            actions=dict()
        )

        for service in self.project.services:
            if not service_names or service.name in service_names:
                result['actions'][service.name] = dict()
                result['actions'][service.name]['restart'] = []
                for container in service.containers(stopped=True):
                    result['changed'] = True
                    if self.debug or self.check_mode:
                        result['actions'][service.name]['restart'].append(dict(
                            id=container.id,
                            name=container.name,
                            short_id=container.short_id,
                        ))

        if not self.check_mode and result['changed']:
            try:
                self.project.restart(service_names=service_names)
            except Exception as exc:
                self.client.fail("Error restarting services for %s - %s" % (self.project.name, str(exc)))

        return result

    def cmd_scale(self):
        result = dict(
            changed=False,
            actions=dict()
        )

        for service in self.project.services:
            if service.name in self.scale:
                result['actions'][service.name] = dict()
                containers = service.containers(stopped=True)
                if len(containers) != self.scale[service.name]:
                    result['changed'] = True
                    if self.debug or self.check_mode:
                        result['actions'][service.name]['scale'] = self.scale[service.name] - len(containers)
                    if not self.check_mode:
                        try:
                            service.scale(self.scale[service.name])
                        except Exception as exc:
                            self.client.fail("Error scaling %s - %s" % (service.name, str(exc)))
        return result


def main():
    argument_spec = dict(
        project_src=dict(type='path'),
        project_name=dict(type='str',),
        files=dict(type='list'),
        state=dict(type='str', choices=['absent', 'present'], default='present'),
        definition=dict(type='dict'),
        hostname_check=dict(type='bool', default=False),
        recreate=dict(type='str', choices=['always','never','smart'], default='smart'),
        build=dict(type='bool', default=True),
        remove_images=dict(type='str', choices=['all', 'local']),
        remove_volumes=dict(type='bool', default=False),
        remove_orphans=dict(type='bool', default=False),
        stopped=dict(type='bool', default=False),
        restarted=dict(type='bool', default=False),
        scale=dict(type='dict'),
        services=dict(type='list'),
        dependencies=dict(type='bool', default=True),
        debug=dict(type='bool', default=False)
    )

    mutually_exclusive = [
        ('definition', 'project_src'),
        ('definition', 'files')
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True
    )

    result = ContainerManager(client).exec_module()
    client.module.exit_json(**result)


if __name__ == '__main__':
    main()
