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
-   Manage docker stacks using the 'docker stack' command
    on the target node
    (see examples)
version_added: "2.8"
options:
    name:
        required: true
        description:
        -   Stack name
    state:
        description:
        -   Service state.
        default: "present"
        choices:
        -   present
        -   absent
    compose:
        required: true
        description:
        -   List of compose definitions. Any element may be a string
            referring to the path of the compose file on the target host
            or the YAML contents of a compose file nested as dictionary.
    prune:
        required: false
        default: false
        description:
        -   If true will add the `--prune` option to the `docker stack deploy` command.
            This will have docker remove the services not present in the
            current stack definition.
        type: bool
    with_registry_auth:
        required: false
        default: false
        description:
        -   If true will add the `--with-registry-auth` option to the `docker stack deploy` command.
            This will have docker send registry authentication details to Swarm agents.
        type: bool
    resolve_image:
        required: false
        choices: ["always", "changed", "never"]
        description:
        -   If set will add the `--resolve-image` option to the `docker stack deploy` command.
            This will have docker query the registry to resolve image digest and
            supported platforms. If not set, docker use "always" by default.

requirements:
-   jsondiff
-   pyyaml
'''

RETURN = '''
docker_stack_spec_diff:
    description: |
        dictionary containing the differences between the 'Spec' field
        of the stack services before and after applying the new stack
        definition.
    sample: >
        "docker_stack_specs_diff":
        {'test_stack_test_service': {u'TaskTemplate': {u'ContainerSpec': {delete: [u'Env']}}}}
    returned: on change
    type: dict
'''

EXAMPLES = '''
-   name: deploy 'stack1' stack from file
    docker_stack:
        state: present
        name: stack1
        compose:
        -   /opt/stack.compose

-   name: deploy 'stack2' from base file and yaml overrides
    docker_stack:
        state: present
        name: stack2
        compose:
        -   /opt/stack.compose
        -   version: '3'
            services:
                web:
                    image: nginx:latest
                    environment:
                        ENVVAR: envvar

-   name: deprovision 'stack1'
    docker_stack:
        state: absent
'''


import json
import tempfile
from ansible.module_utils.six import string_types
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
    if out != ("Nothing found in stack %s\n" % stack_name):
        return out.strip().split('\n')
    return []


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


def main():
    module = AnsibleModule(
        argument_spec={
            'name': dict(required=True, type='str'),
            'compose': dict(required=False, type='list'),
            'prune': dict(default=False, type='bool'),
            'with_registry_auth': dict(default=False, type='bool'),
            'resolve_image': dict(type='str', choices=['always', 'changed', 'never']),
            'state': dict(default='present', choices=['present', 'absent'])
        },
        supports_check_mode=False
    )

    if not HAS_JSONDIFF:
        return module.fail_json(msg="jsondiff is not installed, try `pip install jsondiff`")

    if not HAS_YAML:
        return module.fail_json(msg="yaml is not installed, try `pip install pyyaml`")

    state = module.params['state']
    compose = module.params['compose']
    name = module.params['name']

    if state == 'present':
        try:
            compose_files = []
            temp_files = []
            for i, compose_def in enumerate(compose):
                if isinstance(compose_def, dict):
                    compose_file_fd, compose_file = tempfile.mkstemp()
                    with os.fdopen(compose_file_fd, 'w') as stack_file:
                        temp_files.append(compose_file)
                        compose_files.append(compose_file)
                        stack_file.write(yaml_dump(compose_def))
                elif isinstance(compose_def, string_types):
                    compose_files.append(compose_def)
                else:
                    module.fail_json(msg="compose %s is not a string " +
                                     "or a dictionary" % compose_def)

            before_stack_services = docker_stack_inspect(module, name)

            rc, out, err = docker_stack_deploy(module, name, compose_files)

            after_stack_services = docker_stack_inspect(module, name)

        finally:
            for temp_file in temp_files:
                os.remove(temp_file)

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
                docker_stack_spec_diff=str(before_after_differences))

    else:
        docker_bin = module.get_bin_path('docker', required=True)
        rc, out, err = module.run_command([docker_bin,
                                           "stack",
                                           "down",
                                           name])

        if rc != 0:
            module.fail_json(msg="'docker stack down' command failed",
                             out=out,
                             rc=rc,
                             err=err)

        module.exit_json(changed=True, msg=out, err=err)


if __name__ == "__main__":
    main()
