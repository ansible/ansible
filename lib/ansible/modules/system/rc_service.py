#!/usr/bin/python

# (c) Mattias Lindvall
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


ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = '''
module: rc_service
author:
    - "Mattias Lindvall"
version_added: "2.4"
short_description: Manages services.
description:
    - Manages services with rc style init scripts, and sysrc based configuration.
options:
    name:
        required: true
        description:
            - Name of the service.
        aliases: ['unit', 'service']
    state:
        required: false
        default: null
        choices: ['started', 'stopped', 'restarted']
        description:
            - C(started)/C(stopped) are idempotent actions that will not run commands unless necessary.
              C(restarted) will always restart the service.
    enabled:
        required: false
        default: null
        choices: ['yes', 'no']
        description:
            - Whether the service should be enabled using sysrc.
requirements:
    - A system with rc style init scripts, and sysrc based configuration.
'''

EXAMPLES = '''
- name: Enable nginx
  rc_service: name=nginx enabled=yes

- name: Start nginx
  rc_service name=nginx state=started

- name: Start and enable nginx
  rc_service: name=nginx enabled=yes state=stopped
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.sysrc import get_sysrc_value_bool, sysrc_update


def run_service(module, args):
    bin_path = module.get_bin_path('service', required=True)
    return module.run_command([bin_path] + args)


def service_is_enabled(module, name):
    rc, out, err = run_service(module, [name, 'enabled'])
    return rc == 0


def service_is_running(module, name):
    rc, out, err = run_service(module, [name, 'status'])
    return rc == 0


def handle_enabled(module, result):
    name = module.params.get('name')
    enabled = module.params.get('enabled')

    if enabled is None:
        return

    # set <service>_enabled using sysrc
    changed = sysrc_update(
        module,
        '%s_enable' % name,
        get_sysrc_value_bool(enabled),
    )

    if changed:
        result['changed'] = True


def handle_state(module, result):
    name = module.params.get('name')
    state = module.params.get('state')

    if state is None:
        return

    # ensure service is enabled
    if not service_is_enabled(module, name):
        module.fail_json(msg='Service %s is not enabled' % name)

    command = None

    if state == 'started':
        if not service_is_running(module, name):
            command = 'start'

    elif state == 'stopped':
        if service_is_running(module, name):
            command = 'stop'

    elif state == 'restarted':
        command = 'restart'

    if command:
        rc, out, err = run_service(module, [name, command])

        if rc != 0:
            module.fail_json(msg='Failed to %s service %s' % (command, name))

        result['changed'] = True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(
                type='str',
                required=True,
                aliases=['unit', 'service'],
            ),
            state=dict(
                type='str',
                required=False,
                choices=[
                    'started',
                    'stopped',
                    'restarted',
                ],
            ),
            enabled=dict(
                type='bool',
                required=False,
            ),
        ),
    )

    result = {
        'changed': False,
    }

    handle_enabled(module, result)
    handle_state(module, result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
