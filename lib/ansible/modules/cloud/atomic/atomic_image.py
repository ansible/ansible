#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: atomic_image
short_description: Manage the container images on the atomic host platform
description:
    - Manage the container images on the atomic host platform
    - Allows to execute the commands specified by the RUN label in the container image when present
version_added: "2.2"
author: "Saravanan KR @krsacme"
notes:
    - Host should support C(atomic) command
requirements:
  - atomic
  - "python >= 2.6"
options:
    backend:
        description:
          - Define the backend where the image is pulled.
        required: False
        choices: ["docker", "ostree"]
        default: None
        version_added: "2.4"
    name:
        description:
          - Name of the container image
        required: True
        default: null
    state:
        description:
          - The state of the container image.
          - The state C(latest) will ensure container image is upgraded to the latest version and forcefully restart container, if running.
        required: False
        choices: ["present", "absent", "latest"]
        default: latest
    started:
        description:
          - Start or Stop the container
        required: False
        choices: ["yes", "no"]
        default: yes
'''

EXAMPLES = '''

# Execute the run command on rsyslog container image (atomic run rhel7/rsyslog)
- atomic_image:
    name: rhel7/rsyslog
    state: latest

# Pull busybox to the OSTree backend
- atomic_image:
    name: busybox
    state: latest
    backend: ostree
'''

RETURN = '''
msg:
    description: The command standard output
    returned: always
    type: string
    sample: [u'Using default tag: latest ...']
'''
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def do_upgrade(module, image):
    args = ['atomic', 'update', '--force', image]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0: # something went wrong emit the msg
        module.fail_json(rc=rc, msg=err)
    elif 'Image is up to date' in out:
        return False

    return True


def core(module):
    image = module.params['name']
    state = module.params['state']
    started = module.params['started']
    backend = module.params['backend']
    is_upgraded = False

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
    out = {}
    err = {}
    rc = 0

    if backend:
        if state == 'present' or state == 'latest':
            args = ['atomic', 'pull', "--storage=%s" % backend, image]
            rc, out, err = module.run_command(args, check_rc=False)
            if rc < 0:
                module.fail_json(rc=rc, msg=err)
            else:
                out_run = ""
                if started:
                    args = ['atomic', 'run', "--storage=%s" % backend, image]
                    rc, out_run, err = module.run_command(args, check_rc=False)
                    if rc < 0:
                        module.fail_json(rc=rc, msg=err)

                changed = "Extracting" in out or "Copying blob" in out
                module.exit_json(msg=(out + out_run), changed=changed)
        elif state == 'absent':
            args = ['atomic', 'images', 'delete',  "--storage=%s" % backend, image]
            if rc < 0:
                module.fail_json(rc=rc, msg=err)
            else:
                changed = "Unable to find" not in out
                module.exit_json(msg=out, changed=changed)
        return

    if state == 'present' or state == 'latest':
        if state == 'latest':
            is_upgraded = do_upgrade(module, image)

        if started:
            args = ['atomic', 'run', image]
        else:
            args = ['atomic', 'install', image]
    elif state == 'absent':
        args = ['atomic', 'uninstall', image]

    rc, out, err = module.run_command(args, check_rc=False)

    if rc < 0:
        module.fail_json(rc=rc, msg=err)
    elif rc == 1 and 'already present' in err:
        module.exit_json(restult=err, changed=is_upgraded)
    elif started and 'Container is running' in out:
        module.exit_json(result=out, changed=is_upgraded)
    else:
        module.exit_json(msg=out, changed=True)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            backend=dict(default=None, choices=['docker', 'ostree']),
            name=dict(default=None, required=True),
            state=dict(default='latest', choices=['present', 'absent', 'latest']),
            started=dict(default='yes', type='bool'),
            ),
        )

    # Verify that the platform supports atomic command
    rc, out, err = module.run_command('atomic -v', check_rc=False)
    if rc != 0:
        module.fail_json(msg="Error in running atomic command", err=err)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
