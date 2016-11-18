#!/usr/bin/python
# -*- coding: utf-8 -*-

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

DOCUMENTATION='''
---
module: atomic_image
short_description: Manage the container images on the atomic host platform
description:
    - Manage the container images on the atomic host platform
    - Allows to execute the commands on the container images
version_added: "2.2"
author: "Saravanan KR @krsacme"
notes:
    - Host should be support C(atomic) command
requirements:
  - atomic
  - "python >= 2.6"
options:
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
          - Start or Stop the continer
        required: False
        choices: ["yes", "no"]
        default: yes
'''

EXAMPLES = '''

# Execute the run command on rsyslog container image (atomic run rhel7/rsyslog)
- atomic_image:
    name: rhel7/rsyslog
    state: latest

'''

RETURN = '''
msg:
    description: The command standard output
    returned: always
    type: string
    sample: [u'Using default tag: latest ...']
'''

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
    is_upgraded = False

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')

    if state == 'present' or state == 'latest':
        if state == 'latest':
            is_upgraded = do_upgrade(module, image)

        if started:
            args = ['atomic', 'run', image]
        else:
            args = ['atomic', 'install', image]
    elif state == 'absent':
        args = ['atomic', 'uninstall', image]

    out = {}
    err = {}
    rc = 0
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
                argument_spec = dict(
                    name    = dict(default=None, required=True),
                    state   = dict(default='latest', choices=['present', 'absent', 'latest']),
                    started = dict(default='yes', type='bool'),
                ),
            )

    # Verify that the platform supports atomic command
    rc, out, err = module.run_command('atomic -v', check_rc=False)
    if rc != 0:
        module.fail_json(msg="Error in running atomic command", err=err)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=str(e))


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
