#!/usr/bin/python
# coding: utf-8 -*-

# Adapted by Sean Reifschneider <jafo00@gmail.com>
# Adapted from apache2_module.py by:
# (c) 2013-2014, Christian Berendt <berendt@b1-systems.de>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: apache2_enable
version_added: 2.5
author:
    - Sean Reifschneider (@linsomniac)
    - Christian Berendt (@berendt)
    - Ralf Hertel (@n0trax)
    - Robin Roth (@robinro)
short_description: enables/disables a site/conf/module in the Apache2 webserver
description:
   - Used to manage the "enabled" links in Apache configurations for
     en/disabling sites, modules, and configurations, using "a2ensite" and
     similar.
options:
   name:
     description:
        - name of the site/conf/module to enable/disable
     required: true
   type:
     description:
        - The type of the object to enable/disable.
     choices: ['module', 'site', 'conf']
     required: true
   state:
     description:
        - indicate the desired state of the resource
     choices: ['present', 'absent']
     default: present
   force:
     description:
        - force disabling of default modules and override Debian warnings (for
          modules only).
     required: false
     choices: ['True', 'False']
     default: False
     version_added: "2.1"
   ignore_configcheck:
     description:
        - Ignore configuration checks about inconsistent module configuration.
          Especially for mpm_* modules.
     choices: ['True', 'False']
     default: False
     version_added: "2.3"
requirements: ["a2ensite","a2dissite", "a2enmod", "a2dismod", "a2enconf",
               "a2disconf"]
'''

EXAMPLES = '''
# enables the site "public"
- apache2_enable:
    name: public
    type: site
    state: present
# disables the site "public"
- apache2_enable:
    name: public
    type: site
    state: absent
# enables the module "proxy"
- apache2_enable:
    name: proxy
    type: module
# disable default site for Debian and ignore any config warnings
- apache2_enable:
    state: absent
    name: 000-default
    type: site
    ignore_configcheck: True
'''

RETURN = '''
result:
    description: message about action taken
    returned: always
    type: string
warnings:
    description: list of warning messages
    returned: when needed
    type: list
rc:
    description: return code of underlying command
    returned: failed
    type: int
stdout:
    description: stdout of underlying command
    returned: failed
    type: string
stderr:
    description: stderr of underlying command
    returned: failed
    type: string
'''

import re
import os


def _run_threaded(item):
    control_binary = _get_control_binary(item)

    result, stdout, stderr = item.run_command("%s -V" % control_binary)

    return bool(re.search(r'threaded:[ ]*yes', stdout))


def _get_binary(item, *commands):
    '''Find the path for the first of the specified commands.'''
    for command in commands:
        command_path = item.get_bin_path(command)
        if command_path is not None:
            return command_path

    item.fail_json(msg=(
        'No path to required program "%s" found.' % '" or "'.join(commands)))


def _get_control_binary(item):
    return _get_binary(item, 'apache2ctl', 'apachectl')


def _get_serverroot(item):
    control_binary = _get_control_binary(item)
    ignore_configcheck = item.params['ignore_configcheck']

    result, stdout, stderr = item.run_command(
        "%s -t -D DUMP_RUN_CFG" % control_binary)

    if result != 0:
        error_msg = "Error executing %s: %s" % (control_binary, stderr)
        if ignore_configcheck:
            item.warnings.append(error_msg)
            return False
        else:
            item.fail_json(msg=error_msg)

    m = re.search(r'^ServerRoot: "([^"]+)"$', stdout, re.MULTILINE)
    if not m:
        item.fail_json(
            msg='Unable to determine Server Root via '
            '"%s -t -D DUMP_RUN_CFG"' % control_binary)
        return False

    return m.group(1)


def create_apache_identifier(name):
    """
    By convention if a module is loaded via name, it appears in
    "apache2ctl -M" as name_module.

    Some modules don't follow this convention and we use replacements
    for those."""

    # a2enmod name replacement to apache2ctl -M names
    text_workarounds = [
        ('shib2', 'mod_shib'),
        ('evasive', 'evasive20_module'),
    ]

    # re expressions to extract subparts of names
    re_workarounds = [
        ('php', r'^(php\d)\.'),
    ]

    for a2enmod_spelling, module_name in text_workarounds:
        if a2enmod_spelling in name:
            return module_name

    for search, reexpr in re_workarounds:
        if search in name:
            rematch = re.search(reexpr, name)
            return rematch.group(1) + '_module'

    return name + '_module'


def _module_is_enabled(module):
    control_binary = _get_control_binary(module)
    name = module.params['name']
    ignore_configcheck = module.params['ignore_configcheck']

    result, stdout, stderr = module.run_command("%s -M" % control_binary)

    if result != 0:
        error_msg = "Error executing %s: %s" % (control_binary, stderr)
        if ignore_configcheck:
            if 'AH00534' in stderr and 'mpm_' in name:
                module.warnings.append(
                    'No MPM module loaded! apache2 reload AND other module '
                    'actions will fail if no MPM module is loaded immediately.'
                )
            else:
                module.warnings.append(error_msg)
            return False
        else:
            module.fail_json(msg=error_msg)

    searchstring = ' ' + create_apache_identifier(name)
    return searchstring in stdout


def _is_enabled(item):
    name = item.params['name']
    typ = item.params['type']

    if typ == 'module':
        return _module_is_enabled(item)
    elif typ == 'conf' or typ == 'site':
        server_root = _get_serverroot(item)
        dirname = {'site': 'sites', 'conf': 'conf'}[typ]
        return os.path.exists(os.path.join(
            server_root, '%s-enabled' % dirname, name + '.conf'))


def _set_state(item, state):
    name = item.params['name']
    typ = item.params['type']
    typUpper = typ[0].upper() + typ[1:]

    want_enabled = state == 'present'
    state_string = {'present': 'enabled', 'absent': 'disabled'}[state]
    success_msg = "%s %s %s" % (typUpper, name, state_string)
    binary_name_map = {
        ('conf', 'present'): 'a2enconf',
        ('conf', 'absent'): 'a2disconf',
        ('site', 'present'): 'a2ensite',
        ('site', 'absent'): 'a2dissite',
        ('module', 'present'): 'a2enmod',
        ('module', 'absent'): 'a2dismod',
    }

    if _is_enabled(item) != want_enabled:
        if item.check_mode:
            item.exit_json(
                changed=True, result=success_msg, warnings=item.warnings)

        binary_name = binary_name_map[(typ, state)]
        a2binary = item.get_bin_path(binary_name)
        if a2binary is None:
            item.fail_json(
                msg='%s not found. Perhaps this system does not use %s'
                ' to manage apache' % (a2binary, a2binary))

        result, stdout, stderr = item.run_command(
            "%s %s" % (a2binary, name))

        if _is_enabled(item) == want_enabled:
            item.exit_json(
                changed=True, result=success_msg, warnings=item.warnings)
        else:
            item.fail_json(
                msg="Failed to set site %s to %s: %s"
                % (name, state_string, stdout),
                rc=result, stdout=stdout, stderr=stderr)
    else:
        item.exit_json(
            changed=False, result=success_msg, warnings=item.warnings)


def main():
    item = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            type=dict(required=True),
            force=dict(required=False, type='bool', default=False),
            state=dict(default='present', choices=['absent', 'present']),
            ignore_configcheck=dict(
                required=False, type='bool', default=False),
        ),
        supports_check_mode=True,
    )

    item.warnings = []

    name = item.params['name']
    typ = item.params['type']

    if typ == 'module' and name == 'cgi' and _run_threaded(item):
        item.fail_json(
            msg='Your MPM seems to be threaded. No automatic actions on '
            'module %s possible.' % name)

    if item.params['state'] in ['present', 'absent']:
        _set_state(item, item.params['state'])

# import module snippets
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
