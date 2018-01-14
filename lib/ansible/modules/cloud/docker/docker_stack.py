#!/usr/bin/python
# Copyright (c) 2018 Dario Zanzico (git@dariozanzico.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: docker_stack
author: "Dario Zanzico (@dariko)"
short_description: docker stack module
description: |
    Manage docker stacks using the 'docker stack' command
    on the target node
    (see examples)
version_added: "2.5"
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
    compose_yaml:
        required: false
        default: ""
        description:
        -   String containing the yaml definition of the stack.
        -   Must be in compose format.
    compose_file:
        required: false
        default: ""
        description:
        -   Path of the stack file on the remote/target machine.
    prune:
        required: false
        default: false
        description:
        -   >
            If true will add the `--prune` option to the docker command.
            This will have docker remove the services not present in the
            current stack definition.

requirements:
-   "jsondiff"
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
        compose_file: /opt/stack.compose

-   name: deploy 'stack2' from yaml
    docker_stack:
        state: present
        name: stack2
        compose_yaml: |
            version: '3'
            services:
                web:
                    image: nginx
                    ports:
                    -   "80:80"

-   name: deprovision 'stack1'
    docker_stack:
        state: absent
'''

from ansible.module_utils.basic import AnsibleModule, os
from tempfile import mkstemp
import json
from jsondiff import diff as json_diff


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


def docker_stack_deploy(module, stack_name, compose_file):
    docker_bin = module.get_bin_path('docker', required=True)
    command = [docker_bin, "stack", "deploy"]
    if module.params["prune"]:
        command += ["--prune"]
    command += ["--compose-file",
                compose_file,
                stack_name]
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
            'compose_yaml': dict(),
            'compose_file': dict(),
            'prune': dict(default=False, type='bool'),
            'state': dict(default='present', choices=['present', 'absent'])
        },
        supports_check_mode=False,
        mutually_exclusive=[['compose_yaml', 'compose_file']]
    )

    state = module.params['state']
    compose_yaml = module.params['compose_yaml']
    compose_file = module.params['compose_file']
    name = module.params['name']

    if state == 'present':
        try:
            if compose_yaml:
                compose_file_fd, compose_file = mkstemp()
                with os.fdopen(compose_file_fd, 'w') as stack_file:
                    stack_file.write(compose_yaml)
            elif not compose_file:
                module.fail_json(msg="compose_yaml or compose_file " +
                                     "parameters required if state=='present'")

            before_stack_services = docker_stack_inspect(module, name)

            rc, out, err = docker_stack_deploy(module, name, compose_file)

            after_stack_services = docker_stack_inspect(module, name)

        finally:
            if compose_yaml and compose_file:
                os.remove(compose_file)
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

main()
