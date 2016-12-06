#!/usr/bin/python
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
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: nxos_gir
version_added: "2.2"
short_description: Trigger a graceful removal or insertion (GIR) of the switch.
description:
    - Trigger a graceful removal or insertion (GIR) of the switch.
extends_documentation_fragment: nxos
author:
    - Gabriele Gerbino (@GGabriele)
notes:
    - C(state) has effect only in combination with
      C(system_mode_maintenance_timeout) or
      C(system_mode_maintenance_on_reload_reset_reason).
    - Using C(system_mode_maintenance) and
      C(system_mode_maintenance_dont_generate_profile) would make the module
      fail, but the system mode will be triggered anyway.
options:
    system_mode_maintenance:
        description:
            - When C(system_mode_maintenance=true) it puts all enabled
              protocols in maintenance mode (using the isolate command).
              When C(system_mode_maintenance=false) it puts all enabled
              protocols in normal mode (using the no isolate command).
        required: false
        default: null
        choices: ['true','false']
    system_mode_maintenance_dont_generate_profile:
        description:
            - When C(system_mode_maintenance_dont_generate_profile=true) it
              prevents the dynamic searching of enabled protocols and executes
              commands configured in a maintenance-mode profile.
              Use this option if you want the system to use a maintenance-mode
              profile that you have created.
              When C(system_mode_maintenance_dont_generate_profile=false) it
              prevents the dynamic searching of enabled protocols and executes
              commands configured in a normal-mode profile. Use this option if
              you want the system to use a normal-mode profile that
              you have created.
        required: false
        default: null
        choices: ['true','false']
    system_mode_maintenance_timeout:
        description:
            - Keeps the switch in maintenance mode for a specified
              number of minutes. Range is 5-65535.
        required: false
        default: null
    system_mode_maintenance_shutdown:
        description:
            - Shuts down all protocols, vPC domains, and interfaces except
              the management interface (using the shutdown command).
              This option is disruptive while C(system_mode_maintenance)
              (which uses the isolate command) is not.
        required: false
        default: null
        choices: ['true','false']
    system_mode_maintenance_on_reload_reset_reason:
        description:
            - Boots the switch into maintenance mode automatically in the
              event of a specified system crash.
        required: false
        default: null
        choices: ['hw_error','svc_failure','kern_failure','wdog_timeout',
                  'fatal_error','lc_failure','match_any','manual_reload']
    state:
        description:
            - Specify desired state of the resource.
        required: true
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Trigger system maintenance mode
- nxos_gir:
    system_mode_maintenance: true
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Trigger system normal mode
- nxos_gir:
    system_mode_maintenance: false
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Configure on-reload reset-reason for maintenance mode
- nxos_gir:
    system_mode_maintenance_on_reload_reset_reason: manual_reload
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Add on-reload reset-reason for maintenance mode
- nxos_gir:
    system_mode_maintenance_on_reload_reset_reason: hw_error
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Remove on-reload reset-reason for maintenance mode
- nxos_gir:
    system_mode_maintenance_on_reload_reset_reason: manual_reload
    state: absent
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Set timeout for maintenance mode
- nxos_gir:
    system_mode_maintenance_timeout: 30
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Remove timeout for maintenance mode
- nxos_gir:
    system_mode_maintenance_timeout: 30
    state: absent
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
final_system_mode:
    description: describe the last system mode
    returned: verbose mode
    type: string
    sample: normal
updates:
    description: commands sent to the device
    returned: verbose mode
    type: list
    sample: ["terminal dont-ask", "system mode maintenance timeout 10"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

# COMMON CODE FOR MIGRATION
import re

from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine
from ansible.module_utils.shell import ShellError

try:
    from ansible.module_utils.nxos import get_module
except ImportError:
    from ansible.module_utils.nxos import NetworkModule


def to_list(val):
     if isinstance(val, (list, tuple)):
         return list(val)
     elif val is not None:
         return [val]
     else:
         return list()


class CustomNetworkConfig(NetworkConfig):

    def expand_section(self, configobj, S=None):
        if S is None:
            S = list()
        S.append(configobj)
        for child in configobj.children:
            if child in S:
                continue
            self.expand_section(child, S)
        return S

    def get_object(self, path):
        for item in self.items:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def to_block(self, section):
        return '\n'.join([item.raw for item in section])

    def get_section(self, path):
        try:
            section = self.get_section_objects(path)
            return self.to_block(section)
        except ValueError:
            return list()

    def get_section_objects(self, path):
        if not isinstance(path, list):
            path = [path]
        obj = self.get_object(path)
        if not obj:
            raise ValueError('path does not exist in config')
        return self.expand_section(obj)


    def add(self, lines, parents=None):
        """Adds one or lines of configuration
        """

        ancestors = list()
        offset = 0
        obj = None

        ## global config command
        if not parents:
            for line in to_list(lines):
                item = ConfigLine(line)
                item.raw = line
                if item not in self.items:
                    self.items.append(item)

        else:
            for index, p in enumerate(parents):
                try:
                    i = index + 1
                    obj = self.get_section_objects(parents[:i])[0]
                    ancestors.append(obj)

                except ValueError:
                    # add parent to config
                    offset = index * self.indent
                    obj = ConfigLine(p)
                    obj.raw = p.rjust(len(p) + offset)
                    if ancestors:
                        obj.parents = list(ancestors)
                        ancestors[-1].children.append(obj)
                    self.items.append(obj)
                    ancestors.append(obj)

            # add child objects
            for line in to_list(lines):
                # check if child already exists
                for child in ancestors[-1].children:
                    if child.text == line:
                        break
                else:
                    offset = len(parents) * self.indent
                    item = ConfigLine(line)
                    item.raw = line.rjust(len(line) + offset)
                    item.parents = ancestors
                    ancestors[-1].children.append(item)
                    self.items.append(item)


def get_network_module(**kwargs):
    try:
        return get_module(**kwargs)
    except NameError:
        return NetworkModule(**kwargs)

def get_config(module, include_defaults=False):
    config = module.params['config']
    if not config:
        try:
            config = module.get_config()
        except AttributeError:
            defaults = module.params['include_defaults']
            config = module.config.get_config(include_defaults=defaults)
    return CustomNetworkConfig(indent=2, contents=config)

def load_config(module, candidate):
    config = get_config(module)

    commands = candidate.difference(config)
    commands = [str(c).strip() for c in commands]

    save_config = module.params['save']

    result = dict(changed=False)

    if commands:
        if not module.check_mode:
            try:
                module.configure(commands)
            except AttributeError:
                module.config(commands)

            if save_config:
                try:
                    module.config.save_config()
                except AttributeError:
                    module.execute(['copy running-config startup-config'])

        result['changed'] = True
        result['updates'] = commands

    return result
# END OF COMMON CODE


def execute_show(cmds, module, command_type=None):
    command_type_map = {
        'cli_show': 'json',
        'cli_show_ascii': 'text'
    }

    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending {0}'.format(cmds),
                         error=str(clie))
    except AttributeError:
        try:
            if command_type:
                command_type = command_type_map.get(command_type)
                module.cli.add_commands(cmds, output=command_type)
                response = module.cli.run_commands()
            else:
                module.cli.add_commands(cmds, output=command_type)
                response = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending {0}'.format(cmds),
                             error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show_ascii'):
    cmds = [command]
    if module.params['transport'] == 'cli':
        body = execute_show(cmds, module)
    elif module.params['transport'] == 'nxapi':
        body = execute_show(cmds, module, command_type=command_type)

    return body


def execute_config_command(commands, module):
    try:
        module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)
    except AttributeError:
        try:
            commands.insert(0, 'configure')
            module.cli.add_commands(commands, output='config')
            module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending CLI commands',
                             error=str(clie), commands=commands)


def get_system_mode(module):
    command = 'show system mode'
    body = execute_show_command(command, module)[0]
    if 'normal' in body.lower():
        mode = 'normal'
    else:
        mode = 'maintenance'
    return mode


def get_maintenance_timeout(module):
    command = 'show maintenance timeout'
    body = execute_show_command(command, module)[0]
    timeout = body.split()[4]
    return timeout


def get_reset_reasons(module):
    command = 'show maintenance on-reload reset-reasons'
    body = execute_show_command(command, module)[0]
    return body


def get_commands(module, state, mode):
    commands = list()
    system_mode = ''
    if module.params['system_mode_maintenance'] is True and mode == 'normal':
        commands.append('system mode maintenance')
    elif (module.params['system_mode_maintenance'] is False and
          mode == 'maintenance'):
        commands.append('no system mode maintenance')

    elif (module.params[
         'system_mode_maintenance_dont_generate_profile'] is True and
            mode == 'normal'):
        commands.append('system mode maintenance dont-generate-profile')
    elif (module.params[
          'system_mode_maintenance_dont_generate_profile'] is False and
          mode == 'maintenance'):
        commands.append('no system mode maintenance dont-generate-profile')

    elif module.params['system_mode_maintenance_timeout']:
        timeout = get_maintenance_timeout(module)
        if (state == 'present' and
            timeout != module.params['system_mode_maintenance_timeout']):
            commands.append('system mode maintenance timeout {0}'.format(
                            module.params['system_mode_maintenance_timeout']))
        elif (state == 'absent' and
              timeout == module.params['system_mode_maintenance_timeout']):
            commands.append('no system mode maintenance timeout {0}'.format(
                            module.params['system_mode_maintenance_timeout']))

    elif module.params['system_mode_maintenance_shutdown'] is True:
        commands.append('system mode maintenance shutdown')

    elif module.params['system_mode_maintenance_on_reload_reset_reason']:
        reset_reasons = get_reset_reasons(module)
        if (state == 'present' and
            module.params[
            'system_mode_maintenance_on_reload_reset_reason'].lower() not
            in reset_reasons.lower()):
            commands.append('system mode maintenance on-reload '
                            'reset-reason {0}'.format(
                module.params[
                    'system_mode_maintenance_on_reload_reset_reason']))
        elif (state == 'absent' and
              module.params[
              'system_mode_maintenance_on_reload_reset_reason'].lower() in
              reset_reasons.lower()):
            commands.append('no system mode maintenance on-reload '
                            'reset-reason {0}'.format(
                module.params[
                    'system_mode_maintenance_on_reload_reset_reason']))

    if commands:
        commands.insert(0, 'terminal dont-ask')
    return commands


def main():
    argument_spec = dict(
            system_mode_maintenance=dict(required=False, type='bool'),
            system_mode_maintenance_dont_generate_profile=dict(required=False,
                                                               type='bool'),
            system_mode_maintenance_timeout=dict(required=False, type='str'),
            system_mode_maintenance_shutdown=dict(required=False, type='bool'),
            system_mode_maintenance_on_reload_reset_reason=dict(required=False,
                choices=['hw_error','svc_failure','kern_failure',
                         'wdog_timeout','fatal_error','lc_failure',
                         'match_any','manual_reload']),
            state=dict(choices=['absent', 'present', 'default'],
                       default='present', required=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                mutually_exclusive=[[
                                'system_mode_maintenance',
                                'system_mode_maintenance_dont_generate_profile',
                                'system_mode_maintenance_timeout',
                                'system_mode_maintenance_shutdown',
                                'system_mode_maintenance_on_reload_reset_reason'
                                ]],
                                required_one_of=[[
                                'system_mode_maintenance',
                                'system_mode_maintenance_dont_generate_profile',
                                'system_mode_maintenance_timeout',
                                'system_mode_maintenance_shutdown',
                                'system_mode_maintenance_on_reload_reset_reason'
                                ]],
                                supports_check_mode=True)

    state = module.params['state']
    mode = get_system_mode(module)
    commands = get_commands(module, state, mode)
    changed = False
    if commands:
        if module.check_mode:
            module.exit_json(changed=True, commands=commands)
        else:
            execute_config_command(commands, module)
            changed = True

    result = {}
    result['connected'] = module.connected
    result['changed'] = changed
    if module._verbosity > 0:
        final_system_mode = get_system_mode(module)
        result['final_system_mode'] = final_system_mode
        result['updates'] = commands

    module.exit_json(**result)


if __name__ == '__main__':
    main()