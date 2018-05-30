#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: atomic_container
short_description: Manage the containers on the atomic host platform
description:
    - Manage the containers on the atomic host platform
    - Allows to manage the lifecycle of a container on the atomic host platform
version_added: "2.4"
author: "Giuseppe Scrivano (@giuseppe)"
notes:
    - Host should support C(atomic) command
requirements:
    - atomic
    - "python >= 2.6"
options:
    backend:
        description:
          - Define the backend to use for the container
        required: True
        choices: ["docker", "ostree"]
    name:
        description:
          - Name of the container
        required: True
    image:
        description:
          - The image to use to install the container
        required: True
    rootfs:
        description:
          - Define the rootfs of the image
    state:
        description:
          - State of the container
        required: True
        choices: ["latest", "absent", "rollback"]
        default: "latest"
    mode:
        description:
          - Define if it is an user or a system container
        required: True
        choices: ["user", "system"]
    values:
        description:
            - Values for the installation of the container.  This option is permitted only with mode 'user' or 'system'.
              The values specified here will be used at installation time as --set arguments for atomic install.
'''

EXAMPLES = '''

# Install the etcd system container
- atomic_container:
    name: etcd
    image: rhel/etcd
    backend: ostree
    state: latest
    mode: system
    values:
        - ETCD_NAME=etcd.server

# Uninstall the etcd system container
- atomic_container:
    name: etcd
    image: rhel/etcd
    backend: ostree
    state: absent
    mode: system
'''

RETURN = '''
msg:
    description: The command standard output
    returned: always
    type: string
    sample: [u'Using default tag: latest ...']
'''

# import module snippets
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def do_install(module, mode, rootfs, container, image, values_list, backend):
    system_list = ["--system"] if mode == 'system' else []
    user_list = ["--user"] if mode == 'user' else []
    rootfs_list = ["--rootfs=%s" % rootfs] if rootfs else []
    args = ['atomic', 'install', "--storage=%s" % backend, '--name=%s' % container] + system_list + user_list + rootfs_list + values_list + [image]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
    else:
        changed = "Extracting" in out or "Copying blob" in out
        module.exit_json(msg=out, changed=changed)


def do_update(module, container, image, values_list):
    args = ['atomic', 'containers', 'update', "--rebase=%s" % image] + values_list + [container]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
    else:
        changed = "Extracting" in out or "Copying blob" in out
        module.exit_json(msg=out, changed=changed)


def do_uninstall(module, name, backend):
    args = ['atomic', 'uninstall', "--storage=%s" % backend, name]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
    module.exit_json(msg=out, changed=True)


def do_rollback(module, name):
    args = ['atomic', 'containers', 'rollback', name]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
    else:
        changed = "Rolling back" in out
        module.exit_json(msg=out, changed=changed)


def core(module):
    mode = module.params['mode']
    name = module.params['name']
    image = module.params['image']
    rootfs = module.params['rootfs']
    values = module.params['values']
    backend = module.params['backend']
    state = module.params['state']

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
    out = {}
    err = {}
    rc = 0

    values_list = ["--set=%s" % x for x in values] if values else []

    args = ['atomic', 'containers', 'list', '--no-trunc', '-n', '--all', '-f', 'backend=%s' % backend, '-f', 'container=%s' % name]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
        return
    present = name in out

    if state == 'present' and present:
        module.exit_json(msg=out, changed=False)
    elif (state in ['latest', 'present']) and not present:
        do_install(module, mode, rootfs, name, image, values_list, backend)
    elif state == 'latest':
        do_update(module, name, image, values_list)
    elif state == 'absent':
        if not present:
            module.exit_json(msg="The container is not present", changed=False)
        else:
            do_uninstall(module, name, backend)
    elif state == 'rollback':
        do_rollback(module, name)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            mode=dict(default=None, choices=['user', 'system']),
            name=dict(default=None, required=True),
            image=dict(default=None, required=True),
            rootfs=dict(default=None),
            state=dict(default='latest', choices=['present', 'absent', 'latest', 'rollback']),
            backend=dict(default=None, required=True, choices=['docker', 'ostree']),
            values=dict(type='list', default=[]),
        ),
    )

    if module.params['values'] is not None and module.params['mode'] == 'default':
        module.fail_json(msg="values is supported only with user or system mode")

    # Verify that the platform supports atomic command
    rc, out, err = module.run_command('atomic -v', check_rc=False)
    if rc != 0:
        module.fail_json(msg="Error in running atomic command", err=err)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg='Unanticipated error running atomic: %s' % to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
