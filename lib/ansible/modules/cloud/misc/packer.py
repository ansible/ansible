#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Felix Ehrenpfort <felix.ehrenpfort@codecentric.cloud>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: packer

short_description: "module for packer (https://www.packer.io/)"

version_added: "2.8"

description:
    - "executes packer build for a given template file"

options:
    force:
        default: false
        description: "forces a builder to run when artifacts from a previous build prevent a build from running."
        required: false
        type: bool
    chdir:
        description: "cd into this directory before running packer"
        required: false
        type: path
    exclude:
        default: []
        description: "builds all builds except those"
        required: false
        type: list
    only:
        default: []
        description: "builds only those builds"
        required: false
        type: list
    parallel:
        default: true
        description: "disable parallelization of multiple builders (on by default)."
        required: false
        type: bool
    path:
        description:
            - "path of template json file used by packer build"
        required: true
        type: path
    vars:
        default: {}
        description:
            - "map of variables passed to packer (` -var key=value`)"
        required: false
        type: dict
    var_files:
        default: []
        description: "list of var_file passed to packer (`-var_file`)"
        required: false
        type: list

author:
    - Felix Ehrenpfort (@xinau)
'''

EXAMPLES = '''
---
- name: "packer build plain ubuntu image"
  packer:
    path: "path/to/ubuntu.json"
  register: result

- name: "packer build custom centos image"
  packer:
    path: "path/to/centos.json"
    vars:
      image_name: "custom centos 7"
      is_public: "true"
  register: result
'''

RETURN = '''
cmd:
    description: "packer command executed"
    returned: "success"
    sample: "packer build -color=false -var 'image_name=custom centos 7' ./image.json"
    type: string
'''

import os
from distutils.spawn import find_executable

from ansible.module_utils.basic import AnsibleModule, get_platform
from ansible.module_utils._text import to_bytes


# if file for a given path is readable
def validate_path(module, path, name):
    chdir = module.params['chdir']
    if chdir:
        path = os.path.abspath(chdir) + "/" + path

    b_path = to_bytes(path, errors='surrogate_or_strict')
    if not os.path.exists(b_path):
        module.fail_json(msg="%s %s not found" % (name, path))
    if not os.access(b_path, os.R_OK):
        module.fail_json(msg="%s %s not readable" % (name, path))
    if os.path.isdir(b_path):
        module.fail_json(msg="%s %s is a directory" % (name, path))


# run command with error handling and custom failure msg
def run_command(module, cmd, msg=""):
    rc, out, err = module.run_command(cmd, cwd=module.params['chdir'])
    if rc != 0:
        if msg != "":
            msg += "\n"
        if out:
            msg += "stdout: %s" % (out)
        if err:
            msg += "\n:stderr: %s" % (err)
        module.fail_json(cmd=cmd, msg=msg)
    return (out, err)


def main():
    module_args = dict(
        force=dict(type='bool', required=False, default=False),
        chdir=dict(type='path'),
        exclude=dict(type='list', required=False, default=[]),
        only=dict(type='list', required=False, default=[]),
        parallel=dict(type='bool', required=False, default=True),
        path=dict(type='path', required=True),
        vars=dict(type='dict', required=False, default={}),
        var_files=dict(type='list', required=False, default=[])
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    cmd_args = {}
    force = module.params['force']
    exclude = module.params['exclude']
    only = module.params['only']
    parallel = module.params['parallel']
    path = module.params['path']
    d_vars = module.params['vars']
    var_files = module.params['var_files']

    # check installation of packer
    packer_cmd = find_executable("packer")
    if not packer_cmd:
        module.fail_json(msg="packer command not found in PATH" % (path))

    # check if paths are readable
    validate_path(module, path, "path")
    for p in var_files:
        validate_path(module, p, "var_file")

    # ' -force=false'
    cmd_args['force'] = ""
    if force:
        cmd_args['force'] = " -force=true"

    # ' -parallel=true'
    cmd_args['parallel'] = ""
    if not parallel:
        cmd_args['parallel'] = " -parallel=false"

    # ' -except=foo,bar,baz
    cmd_args['exclude'] = ""
    if exclude != []:
        cmd_args['exclude'] = " -except="
    for i in exclude:
        cmd_args['exclude'] = ",%s" % (i)

    # ' -only=foo,bar,baz
    cmd_args['only'] = ""
    if only != []:
        cmd_args['only'] = " -only="
    for i in only:
        cmd_args['only'] = ",%s" % (i)

    # ' -var bob=foo -var alice=baz'
    cmd_args['vars'] = ""
    for i in d_vars:
        cmd_args['vars'] += " -var '%s=%s'" % (i, d_vars[i])

    # seperation between windows and linux, see: https://www.packer.io/docs/templates/user-variables.html#from-a-file
    sep = "="
    if get_platform() == 'Windows':
        sep = " "

    # ' -var_file=./foo -var_file=./bar'
    cmd_args['var_files'] = ""
    for i in var_files:
        cmd_args['var_files'] += " -var_file%s%s" % (sep, i)

    # construct validate command
    cmd = "packer validate %s %s %s %s %s" % (
        cmd_args['exclude'],
        cmd_args['only'],
        cmd_args['vars'],
        cmd_args['var_files'],
        path
    )
    out, err = run_command(module, cmd, "validation failed")

    if not module.check_mode:
        # construct build command
        cmd = "packer build -color=false %s %s %s %s %s %s %s" % (
            cmd_args['force'],
            cmd_args['exclude'],
            cmd_args['only'],
            cmd_args['parallel'],
            cmd_args['vars'],
            cmd_args['var_files'],
            path
        )
        out, err = run_command(module, cmd, "build failed")

    module.exit_json(changed=True, cmd=cmd, stdout=out, stderr=err)


if __name__ == '__main__':
    main()
