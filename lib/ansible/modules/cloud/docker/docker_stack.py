#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Dario Zanzico (git@dariozanzico.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: docker_stack
author: "Dario Zanzico (@dariko)"
short_description: docker stack module
description:
  - Manage docker stacks using the 'docker stack' command
    on the target node (see examples).
version_added: "2.8"
options:
  name:
    description:
      - Stack name
    type: str
    required: yes
  state:
    description:
      - Service state.
    type: str
    default: "present"
    choices:
      - present
      - absent
  compose:
    description:
      - List of compose definitions. Any element may be a string
        referring to the path of the compose file on the target host
        or the YAML contents of a compose file nested as dictionary.
    type: list
    default: []
  prune:
    description:
      - If true will add the C(--prune) option to the C(docker stack deploy) command.
        This will have docker remove the services not present in the
        current stack definition.
    type: bool
    default: no
  with_registry_auth:
    description:
      - If true will add the C(--with-registry-auth) option to the C(docker stack deploy) command.
        This will have docker send registry authentication details to Swarm agents.
    type: bool
    default: no
  resolve_image:
    description:
      - If set will add the C(--resolve-image) option to the C(docker stack deploy) command.
        This will have docker query the registry to resolve image digest and
        supported platforms. If not set, docker use "always" by default.
    type: str
    choices: ["always", "changed", "never"]
  absent_retries:
    description:
      - If C(>0) and I(state) is C(absent) the module will retry up to
        I(absent_retries) times to delete the stack until all the
        resources have been effectively deleted.
        If the last try still reports the stack as not completely
        removed the module will fail.
    type: int
    default: 0
  absent_retries_interval:
    description:
      - Interval in seconds between consecutive I(absent_retries).
    type: int
    default: 1

requirements:
  - jsondiff
  - pyyaml
'''

RETURN = '''
stack_spec_diff:
    description: |
        dictionary containing the differences between the 'Spec' field
        of the stack services before and after applying the new stack
        definition.
    sample: >
        "stack_spec_diff":
        {'test_stack_test_service': {u'TaskTemplate': {u'ContainerSpec': {delete: [u'Env']}}}}
    returned: on change
    type: dict
'''

EXAMPLES = '''
  - name: Deploy stack from a compose file
    docker_stack:
      state: present
      name: mystack
      compose:
        - /opt/docker-compose.yml

  - name: Deploy stack from base compose file and override the web service
    docker_stack:
      state: present
      name: mystack
      compose:
        - /opt/docker-compose.yml
        - version: '3'
          services:
            web:
              image: nginx:latest
              environment:
                ENVVAR: envvar

  - name: Remove stack
    docker_stack:
      name: mystack
      state: absent
'''


import json
import tempfile
from ansible.module_utils.six import string_types
from time import sleep

try:
    from jsondiff import diff as json_diff
    HAS_JSONDIFF = True
except ImportError:
    HAS_JSONDIFF = False

try:
    from yaml import dump as yaml_dump
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from ansible.module_utils.basic import AnsibleModule, os


def docker_stack_services(module, stack_name):
    docker_bin = module.get_bin_path('docker', required=True)
    rc, out, err = module.run_command([docker_bin,
                                       "stack",
                                       "services",
                                       stack_name,
                                       "--format",
                                       "{{.Name}}"])
    if err == "Nothing found in stack: %s\n" % stack_name:
        return []
    return out.strip().split('\n')


def docker_service_inspect(module, service_name):
    docker_bin = module.get_bin_path('docker', required=True)
    rc, out, err = module.run_command([docker_bin,
                                       "service",
                                       "inspect",
                                       service_name])
    if rc != 0:
        return None
    else:
        ret = json.loads(out)[0]['Spec']
        return ret


def docker_stack_deploy(module, stack_name, compose_files):
    docker_bin = module.get_bin_path('docker', required=True)
    command = [docker_bin, "stack", "deploy"]
    if module.params["prune"]:
        command += ["--prune"]
    if module.params["with_registry_auth"]:
        command += ["--with-registry-auth"]
    if module.params["resolve_image"]:
        command += ["--resolve-image",
                    module.params["resolve_image"]]
    for compose_file in compose_files:
        command += ["--compose-file",
                    compose_file]
    command += [stack_name]
    return module.run_command(command)


def docker_stack_inspect(module, stack_name):
    ret = {}
    for service_name in docker_stack_services(module, stack_name):
        ret[service_name] = docker_service_inspect(module, service_name)
    return ret


def docker_stack_rm(module, stack_name, retries, interval):
    docker_bin = module.get_bin_path('docker', required=True)
    command = [docker_bin, "stack", "rm", stack_name]

    rc, out, err = module.run_command(command)

    while err != "Nothing found in stack: %s\n" % stack_name and retries > 0:
        sleep(interval)
        retries = retries - 1
        rc, out, err = module.run_command(command)
    return rc, out, err


def main():
    module = AnsibleModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'compose': dict(type='list', default=[]),
            'prune': dict(type='bool', default=False),
            'with_registry_auth': dict(type='bool', default=False),
            'resolve_image': dict(type='str', choices=['always', 'changed', 'never']),
            'state': dict(tpye='str', default='present', choices=['present', 'absent']),
            'absent_retries': dict(type='int', default=0),
            'absent_retries_interval': dict(type='int', default=1)
        },
        supports_check_mode=False
    )

    if not HAS_JSONDIFF:
        return module.fail_json(msg="jsondiff is not installed, try 'pip install jsondiff'")

    if not HAS_YAML:
        return module.fail_json(msg="yaml is not installed, try 'pip install pyyaml'")

    state = module.params['state']
    compose = module.params['compose']
    name = module.params['name']
    absent_retries = module.params['absent_retries']
    absent_retries_interval = module.params['absent_retries_interval']

    if state == 'present':
        if not compose:
            module.fail_json(msg=("compose parameter must be a list "
                                  "containing at least one element"))

        compose_files = []
        for i, compose_def in enumerate(compose):
            if isinstance(compose_def, dict):
                compose_file_fd, compose_file = tempfile.mkstemp()
                module.add_cleanup_file(compose_file)
                with os.fdopen(compose_file_fd, 'w') as stack_file:
                    compose_files.append(compose_file)
                    stack_file.write(yaml_dump(compose_def))
            elif isinstance(compose_def, string_types):
                compose_files.append(compose_def)
            else:
                module.fail_json(msg="compose element '%s' must be a " +
                                 "string or a dictionary" % compose_def)

        before_stack_services = docker_stack_inspect(module, name)

        rc, out, err = docker_stack_deploy(module, name, compose_files)

        after_stack_services = docker_stack_inspect(module, name)

        if rc != 0:
            module.fail_json(msg="docker stack up deploy command failed",
                             out=out,
                             rc=rc, err=err)

        before_after_differences = json_diff(before_stack_services,
                                             after_stack_services)
        for k in before_after_differences.keys():
            if isinstance(before_after_differences[k], dict):
                before_after_differences[k].pop('UpdatedAt', None)
                before_after_differences[k].pop('Version', None)
                if not list(before_after_differences[k].keys()):
                    before_after_differences.pop(k)

        if not before_after_differences:
            module.exit_json(changed=False)
        else:
            module.exit_json(
                changed=True,
                stack_spec_diff=json_diff(before_stack_services,
                                          after_stack_services,
                                          dump=True))

    else:
        if docker_stack_services(module, name):
            rc, out, err = docker_stack_rm(module, name, absent_retries, absent_retries_interval)
            if rc != 0:
                module.fail_json(msg="'docker stack down' command failed",
                                 out=out,
                                 rc=rc,
                                 err=err)
            else:
                module.exit_json(changed=True, msg=out, err=err, rc=rc)
        module.exit_json(changed=False)


if __name__ == "__main__":
    main()
