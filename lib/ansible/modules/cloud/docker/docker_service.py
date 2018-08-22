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
  project_name:
      description:
        - Provide a project name. If not provided, the project name is taken from the basename of C(project_src).
        - Required when C(definition) is provided.
  files:
      description:
        - List of file names relative to C(project_src). Overrides docker-compose.yml or docker-compose.yaml.
        - Files are loaded and merged in the order given.
  state:
      description:
        - Desired state of the project.
        - Specifying I(present) is the same as running I(docker-compose up).
        - Specifying I(absent) is the same as running I(docker-compose down).
      choices:
        - absent
        - present
      default: present
  services:
      description:
        - When C(state) is I(present) run I(docker-compose up) on a subset of services.
  scale:
      description:
        - When C(state) is I(present) scale services. Provide a dictionary of key/value pairs where the key
          is the name of the service and the value is an integer count for the number of containers.
  dependencies:
      description:
        - When C(state) is I(present) specify whether or not to include linked services.
      type: bool
      default: 'yes'
  definition:
      description:
        - Provide docker-compose yaml describing one or more services, networks and volumes.
        - Mutually exclusive with C(project_src) and C(files).
  hostname_check:
      description:
        - Whether or not to check the Docker daemon's hostname against the name provided in the client certificate.
      type: bool
      default: 'no'
  recreate:
      description:
        - By default containers will be recreated when their configuration differs from the service definition.
        - Setting to I(never) ignores configuration differences and leaves existing containers unchanged.
        - Setting to I(always) forces recreation of all existing containers.
      required: false
      choices:
        - always
        - never
        - smart
      default: smart
  build:
      description:
        - Use with state I(present) to always build images prior to starting the application.
        - Same as running docker-compose build with the pull option.
        - Images will only be rebuilt if Docker detects a change in the Dockerfile or build directory contents.
        - Use the C(nocache) option to ignore the image cache when performing the build.
        - If an existing image is replaced, services using the image will be recreated unless C(recreate) is I(never).
      type: bool
      default: 'no'
  pull:
      description:
        - Use with state I(present) to always pull images prior to starting the application.
        - Same as running docker-compose pull.
        - When a new image is pulled, services using the image will be recreated unless C(recreate) is I(never).
      type: bool
      default: 'no'
      version_added: "2.2"
  nocache:
      description:
        - Use with the build option to ignore the cache during the image build process.
      type: bool
      default: 'no'
      version_added: "2.2"
  remove_images:
      description:
        - Use with state I(absent) to remove the all images or only local images.
      choices:
          - 'all'
          - 'local'
  remove_volumes:
      description:
        - Use with state I(absent) to remove data volumes.
      type: bool
      default: 'no'
  stopped:
      description:
        - Use with state I(present) to leave the containers in an exited or non-running state.
      type: bool
      default: 'no'
  restarted:
      description:
        - Use with state I(present) to restart all containers.
      type: bool
      default: 'no'
  remove_orphans:
      description:
        - Remove containers for services not defined in the compose file.
      type: bool
      default: false
  timeout:
    description:
        - timeout in seconds for container shutdown when attached or when containers are already running.
    default: 10

extends_documentation_fragment:
    - docker

requirements:
    - "python >= 2.6"
    - "docker-py >= 1.8.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
       install the C(docker) Python module. Note that both modules should I(not)
       be installed at the same time."
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

    - debug:
        var: output

    - docker_service:
        project_src: flask
        build: no
      register: output

    - debug:
        var: output

    - assert:
        that: "not output.changed "

    - docker_service:
        project_src: flask
        build: no
        stopped: true
      register: output

    - debug:
        var: output

    - assert:
        that:
          - "not web.flask_web_1.state.running"
          - "not db.flask_db_1.state.running"

    - docker_service:
        project_src: flask
        build: no
        restarted: true
      register: output

    - debug:
        var: output

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

    - debug:
        var: output

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

    - debug:
        var: output

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

    - debug:
        var: output

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
              pulled_image:
                  description: Provides image details when a new image is pulled for the service.
                  returned: on image pull
                  type: complex
                  contains:
                      name:
                          description: name of the image
                          returned: always
                          type: string
                      id:
                          description: image hash
                          returned: always
                          type: string
              built_image:
                  description: Provides image details when a new image is built for the service.
                  returned: on image build
                  type: complex
                  contains:
                      name:
                          description: name of the image
                          returned: always
                          type: string
                      id:
                          description: image hash
                          returned: always
                          type: string

              action:
                  description: A descriptive name of the action to be performed on the service's containers.
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

import os
import re
import sys
import tempfile
from contextlib import contextmanager
from distutils.version import LooseVersion

try:
    import yaml
    HAS_YAML = True
    HAS_YAML_EXC = None
except ImportError as exc:
    HAS_YAML = False
    HAS_YAML_EXC = str(exc)

try:
    from compose import __version__ as compose_version
    from compose.cli.command import project_from_options
    from compose.service import NoSuchImageError
    from compose.cli.main import convergence_strategy_from_opts, build_action_from_opts, image_type_from_opt
    from compose.const import DEFAULT_TIMEOUT
    HAS_COMPOSE = True
    HAS_COMPOSE_EXC = None
    MINIMUM_COMPOSE_VERSION = '1.7.0'

except ImportError as exc:
    HAS_COMPOSE = False
    HAS_COMPOSE_EXC = str(exc)
    DEFAULT_TIMEOUT = 10

from ansible.module_utils.docker_common import AnsibleDockerClient, DockerBaseClass


AUTH_PARAM_MAPPING = {
    u'docker_host': u'--host',
    u'tls': u'--tls',
    u'cacert_path': u'--tlscacert',
    u'cert_path': u'--tlscert',
    u'key_path': u'--tlskey',
    u'tls_verify': u'--tlsverify'
}


@contextmanager
def stdout_redirector(path_name):
    old_stdout = sys.stdout
    fd = open(path_name, 'w')
    sys.stdout = fd
    try:
        yield
    finally:
        sys.stdout = old_stdout


@contextmanager
def stderr_redirector(path_name):
    old_fh = sys.stderr
    fd = open(path_name, 'w')
    sys.stderr = fd
    try:
        yield
    finally:
        sys.stderr = old_fh


def make_redirection_tempfiles():
    _, out_redir_name = tempfile.mkstemp(prefix="ansible")
    _, err_redir_name = tempfile.mkstemp(prefix="ansible")
    return (out_redir_name, err_redir_name)


def cleanup_redirection_tempfiles(out_name, err_name):
    for i in [out_name, err_name]:
        os.remove(i)


def get_redirected_output(path_name):
    output = []
    with open(path_name, 'r') as fd:
        for line in fd:
            # strip terminal format/color chars
            new_line = re.sub(r'\x1b\[.+m', '', line)
            output.append(new_line)
    os.remove(path_name)
    return output


def attempt_extract_errors(exc_str, stdout, stderr):
    errors = [l.strip() for l in stderr if l.strip().startswith('ERROR:')]
    errors.extend([l.strip() for l in stdout if l.strip().startswith('ERROR:')])

    warnings = [l.strip() for l in stderr if l.strip().startswith('WARNING:')]
    warnings.extend([l.strip() for l in stdout if l.strip().startswith('WARNING:')])

    # assume either the exception body (if present) or the last warning was the 'most'
    # fatal.

    if exc_str.strip():
        msg = exc_str.strip()
    elif errors:
        msg = errors[-1].encode('utf-8')
    else:
        msg = 'unknown cause'

    return {
        'warnings': [w.encode('utf-8') for w in warnings],
        'errors': [e.encode('utf-8') for e in errors],
        'msg': msg,
        'module_stderr': ''.join(stderr),
        'module_stdout': ''.join(stdout)
    }


def get_failure_info(exc, out_name, err_name=None, msg_format='%s'):
    if err_name is None:
        stderr = []
    else:
        stderr = get_redirected_output(err_name)
    stdout = get_redirected_output(out_name)

    reason = attempt_extract_errors(str(exc), stdout, stderr)
    reason['msg'] = msg_format % reason['msg']
    return reason


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
        self.pull = None
        self.nocache = None

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
            self.client.fail("Unable to load docker-compose. Try `pip install docker-compose`. Error: %s" %
                             HAS_COMPOSE_EXC)

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
        result = dict(changed=False, actions=[], ansible_facts=dict())

        up_options = {
            u'--no-recreate': False,
            u'--build': False,
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

        if self.pull:
            pull_output = self.cmd_pull()
            result['changed'] = pull_output['changed']
            result['actions'] += pull_output['actions']

        if self.build:
            build_output = self.cmd_build()
            result['changed'] = build_output['changed']
            result['actions'] += build_output['actions']

        for service in self.project.services:
            if not service_names or service.name in service_names:
                plan = service.convergence_plan(strategy=converge)
                if plan.action != 'noop':
                    result['changed'] = True
                    result_action = dict(service=service.name)
                    result_action[plan.action] = []
                    for container in plan.containers:
                        result_action[plan.action].append(dict(
                            id=container.id,
                            name=container.name,
                            short_id=container.short_id,
                        ))
                    result['actions'].append(result_action)

        if not self.check_mode and result['changed']:
            out_redir_name, err_redir_name = make_redirection_tempfiles()
            try:
                with stdout_redirector(out_redir_name):
                    with stderr_redirector(err_redir_name):
                        do_build = build_action_from_opts(up_options)
                        self.log('Setting do_build to %s' % do_build)
                        self.project.up(
                            service_names=service_names,
                            start_deps=start_deps,
                            strategy=converge,
                            do_build=do_build,
                            detached=detached,
                            remove_orphans=self.remove_orphans,
                            timeout=self.timeout)
            except Exception as exc:
                fail_reason = get_failure_info(exc, out_redir_name, err_redir_name,
                                               msg_format="Error starting project %s")
                self.client.module.fail_json(**fail_reason)
            else:
                cleanup_redirection_tempfiles(out_redir_name, err_redir_name)

        if self.stopped:
            stop_output = self.cmd_stop(service_names)
            result['changed'] = stop_output['changed']
            result['actions'] += stop_output['actions']

        if self.restarted:
            restart_output = self.cmd_restart(service_names)
            result['changed'] = restart_output['changed']
            result['actions'] += restart_output['actions']

        if self.scale:
            scale_output = self.cmd_scale()
            result['changed'] = scale_output['changed']
            result['actions'] += scale_output['actions']

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

    def cmd_pull(self):
        result = dict(
            changed=False,
            actions=[],
        )

        if not self.check_mode:
            for service in self.project.get_services(self.services, include_deps=False):
                if 'image' not in service.options:
                    continue

                self.log('Pulling image for service %s' % service.name)
                # store the existing image ID
                old_image_id = ''
                try:
                    image = service.image()
                    if image and image.get('Id'):
                        old_image_id = image['Id']
                except NoSuchImageError:
                    pass
                except Exception as exc:
                    self.client.fail("Error: service image lookup failed - %s" % str(exc))

                # pull the image
                try:
                    service.pull(ignore_pull_failures=False)
                except Exception as exc:
                    self.client.fail("Error: pull failed with %s" % str(exc))

                # store the new image ID
                new_image_id = ''
                try:
                    image = service.image()
                    if image and image.get('Id'):
                        new_image_id = image['Id']
                except NoSuchImageError as exc:
                    self.client.fail("Error: service image lookup failed after pull - %s" % str(exc))

                if new_image_id != old_image_id:
                    # if a new image was pulled
                    result['changed'] = True
                    result['actions'].append(dict(
                        service=service.name,
                        pulled_image=dict(
                            name=service.image_name,
                            id=new_image_id
                        )
                    ))
        return result

    def cmd_build(self):
        result = dict(
            changed=False,
            actions=[]
        )
        if not self.check_mode:
            for service in self.project.get_services(self.services, include_deps=False):
                if service.can_be_built():
                    self.log('Building image for service %s' % service.name)
                    # store the existing image ID
                    old_image_id = ''
                    try:
                        image = service.image()
                        if image and image.get('Id'):
                            old_image_id = image['Id']
                    except NoSuchImageError:
                        pass
                    except Exception as exc:
                        self.client.fail("Error: service image lookup failed - %s" % str(exc))

                    # build the image
                    try:
                        new_image_id = service.build(pull=self.pull, no_cache=self.nocache)
                    except Exception as exc:
                        self.client.fail("Error: build failed with %s" % str(exc))

                    if new_image_id not in old_image_id:
                        # if a new image was built
                        result['changed'] = True
                        result['actions'].append(dict(
                            service=service.name,
                            built_image=dict(
                                name=service.image_name,
                                id=new_image_id
                            )
                        ))
        return result

    def cmd_down(self):
        result = dict(
            changed=False,
            actions=[]
        )
        for service in self.project.services:
            containers = service.containers(stopped=True)
            if len(containers):
                result['changed'] = True
            result['actions'].append(dict(
                service=service.name,
                deleted=[container.name for container in containers]
            ))
        if not self.check_mode and result['changed']:
            image_type = image_type_from_opt('--rmi', self.remove_images)
            try:
                self.project.down(image_type, self.remove_volumes, self.remove_orphans)
            except Exception as exc:
                self.client.fail("Error stopping project - %s" % str(exc))
        return result

    def cmd_stop(self, service_names):
        result = dict(
            changed=False,
            actions=[]
        )
        for service in self.project.services:
            if not service_names or service.name in service_names:
                service_res = dict(
                    service=service.name,
                    stop=[]
                )
                for container in service.containers(stopped=False):
                    result['changed'] = True
                    service_res['stop'].append(dict(
                        id=container.id,
                        name=container.name,
                        short_id=container.short_id
                    ))
                result['actions'].append(service_res)
        if not self.check_mode and result['changed']:
            out_redir_name, err_redir_name = make_redirection_tempfiles()
            try:
                with stdout_redirector(out_redir_name):
                    with stderr_redirector(err_redir_name):
                        self.project.stop(service_names=service_names, timeout=self.timeout)
            except Exception as exc:
                fail_reason = get_failure_info(exc, out_redir_name, err_redir_name,
                                               msg_format="Error stopping project %s")
                self.client.module.fail_json(**fail_reason)
            else:
                cleanup_redirection_tempfiles(out_redir_name, err_redir_name)
        return result

    def cmd_restart(self, service_names):
        result = dict(
            changed=False,
            actions=[]
        )

        for service in self.project.services:
            if not service_names or service.name in service_names:
                service_res = dict(
                    service=service.name,
                    restart=[]
                )
                for container in service.containers(stopped=True):
                    result['changed'] = True
                    service_res['restart'].append(dict(
                        id=container.id,
                        name=container.name,
                        short_id=container.short_id
                    ))
                result['actions'].append(service_res)

        if not self.check_mode and result['changed']:
            out_redir_name, err_redir_name = make_redirection_tempfiles()
            try:
                with stdout_redirector(out_redir_name):
                    with stderr_redirector(err_redir_name):
                        self.project.restart(service_names=service_names, timeout=self.timeout)
            except Exception as exc:
                fail_reason = get_failure_info(exc, out_redir_name, err_redir_name,
                                               msg_format="Error restarting project %s")
                self.client.module.fail_json(**fail_reason)
            else:
                cleanup_redirection_tempfiles(out_redir_name, err_redir_name)
        return result

    def cmd_scale(self):
        result = dict(
            changed=False,
            actions=[]
        )
        for service in self.project.services:
            if service.name in self.scale:
                service_res = dict(
                    service=service.name,
                    scale=0
                )
                containers = service.containers(stopped=True)
                if len(containers) != self.scale[service.name]:
                    result['changed'] = True
                    service_res['scale'] = self.scale[service.name] - len(containers)
                    if not self.check_mode:
                        try:
                            service.scale(int(self.scale[service.name]))
                        except Exception as exc:
                            self.client.fail("Error scaling %s - %s" % (service.name, str(exc)))
                    result['actions'].append(service_res)
        return result


def main():
    argument_spec = dict(
        project_src=dict(type='path'),
        project_name=dict(type='str',),
        files=dict(type='list'),
        state=dict(type='str', choices=['absent', 'present'], default='present'),
        definition=dict(type='dict'),
        hostname_check=dict(type='bool', default=False),
        recreate=dict(type='str', choices=['always', 'never', 'smart'], default='smart'),
        build=dict(type='bool', default=False),
        remove_images=dict(type='str', choices=['all', 'local']),
        remove_volumes=dict(type='bool', default=False),
        remove_orphans=dict(type='bool', default=False),
        stopped=dict(type='bool', default=False),
        restarted=dict(type='bool', default=False),
        scale=dict(type='dict'),
        services=dict(type='list'),
        dependencies=dict(type='bool', default=True),
        pull=dict(type='bool', default=False),
        nocache=dict(type='bool', default=False),
        debug=dict(type='bool', default=False),
        timeout=dict(type='int', default=DEFAULT_TIMEOUT)
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
