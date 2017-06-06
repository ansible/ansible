#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Den Ivanov <div@urajio.org>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: apache2_conf
version_added: "2.4"
author:
    - Den Ivanov (@urajio)
short_description: Enables or disables a specified site, module or configuration snippet of the Apache2 webserver.
description:
   - This module manage Debian-style Apache configuration, where configuration snippets stored in
     /etc/apache2/[conf|sites|mods]-available dirs, and can be enabled by creating symlinks within corresponding
     /etc/apache2/[conf|sites|mods]-enabled directory. Use a2enconf, a2disconf, a2ensite, a2dissite, a2enmod, a2dismod scripts.
options:
   type:
     description:
        - type of configuration snippet
     required: true
     choices: ['conf', 'site', 'mod']
   name:
     description:
        - name of the configuration snippet. It can be a complete file name or file name without the suffix.
     required: true
   state:
     description:
        - indicate the desired state of the resource
     choices: ['present', 'absent']
     default: present
   force:
     description:
        - force disabling of default modules and override Debian warnings
     required: false
     choices: ['True', 'False']
     default: False
requirements: ["a2enconf","a2disconf","a2ensite","a2dissite","a2enmod","a2dismod"]
'''

EXAMPLES = '''
# enable config fragment charset.conf
- apache2_conf:
    type: conf
    state: present
    name: charset.conf
# disable config fragment using a short name
- apache2_conf:
    type: conf
    state: absent
    name: charset
# disable config fragment
- apache2_conf:
    type: conf
    state: absent
    name: localized-error-pages.conf
# enable default-ssl site
- apache2_conf:
    type: site
    name: default-ssl.conf
# enables the Apache2 module unique_id
- apache2_conf:
    type: mod
    state: present
    name: unique_id.load
# disables the Apache2 module
- apache2_conf:
    type: mod
    state: absent
    name: unique_id.load
# disable essential module for Debian
- apache2_conf:
    type: mod
    state: absent
    name: autoindex.load
    force: True
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts.system.distribution import Distribution
from os.path import basename, join, exists, islink, samefile, splitext
import glob
import shlex


class ApacheFragmentException(Exception):
    pass


class ApacheFragmentFail(ApacheFragmentException):
    def __init__(self, rc=None, stdout=None, stderr=None):
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr


class ApacheFragmentUnsupported(ApacheFragmentException):
    pass


class ApacheFragment(object):
    available_dir = None
    enabled_dir = None
    fragment_suffix = None
    command_names = dict(present=None, absent=None)

    def __init__(self, name):
        for required_dir in (self.available_dir, self.enabled_dir):
            if not exists(required_dir):
                raise ApacheFragmentUnsupported("directory %s not found" % required_dir)

        if name != basename(name):
            raise ApacheFragmentException("Configuration fragment name should not contain path")

        if name.endswith(self.fragment_suffix):
            self.fragment_file = name
            self.fragment_name = splitext(name)[0]
        else:
            self.fragment_file = name + self.fragment_suffix
            self.fragment_name = name
        if not exists(join(self.available_dir, self.fragment_file)):
            raise ApacheFragmentException(
                "Apache config fragment %s not found in %s" % (self.fragment_file, self.available_dir))

    def state(self):
        """
        :return: "present" if fragment enabled, "absent" otherwise.
        """
        available_fragment = join(self.available_dir, self.fragment_file)
        for enabled_fragment in glob.glob(join(self.enabled_dir, '*' + self.fragment_suffix)):
            if islink(enabled_fragment) and samefile(available_fragment, enabled_fragment):
                return "present"
        return "absent"

    def set(self, state=None):
        if module.params['force']:
            force = ' -f'
        else:
            force = None
        command_name = module.get_bin_path(self.command_names[state])
        if command_name is None:
            raise ApacheFragmentUnsupported("command %s not found" % self.command_names[state])
        return module.run_command([command_name, force, self.fragment_name], check_rc=True)


class ApacheSuseVariable(object):
    sysconf_file = '/etc/sysconfig/apache2'
    sysconf_variable = None
    command_names = dict(present=None, absent=None)

    def __init__(self, name):
        # start scripts add '_module' suffix and remove 'mod_' prefix to get module ID
        # then try to find name.so with and without 'mod_' prefix
        # if found - it add LoadModule directive to /etc/apache2/sysconfig.d/loadmodule.conf
        # if not found - this module will be silently ignored
        suffix_position = name.rfind('_module')
        if suffix_position == -1:
            self.name = name
        else:
            self.name = name[0:suffix_position]

    def state(self):
        with open(self.sysconf_file, 'rt') as sysconf:
            lexer = shlex.shlex(sysconf, infile=self.sysconf_file, posix=True)
            for token in lexer:
                if token == self.sysconf_variable:
                    if lexer.get_token() == '=':
                        sysconf_variable_values = lexer.get_token().split()
                        if self.name in sysconf_variable_values:
                            return "present"
                        else:
                            return "absent"
            raise ApacheFragmentException('Can\'t parse variable %s in %s' % (self.sysconf_variable, self.sysconf_file))

    def set(self, state=None):
        command_name = module.get_bin_path(self.command_names[state])
        if command_name is None:
            raise ApacheFragmentUnsupported("command %s not found" % self.command_names[state])
        return module.run_command([command_name, self.name], check_rc=True)


class ApacheConfigFragment(ApacheFragment):
    available_dir = '/etc/apache2/conf-available'
    enabled_dir = '/etc/apache2/conf-enabled'
    fragment_suffix = '.conf'
    command_names = dict(present='a2enconf', absent='a2disconf')


class ApacheSiteFragment(ApacheFragment):
    available_dir = '/etc/apache2/sites-available'
    enabled_dir = '/etc/apache2/sites-enabled'
    fragment_suffix = '.conf'
    command_names = dict(present='a2ensite', absent='a2dissite')


class ApacheModuleFragment(ApacheFragment):
    available_dir = '/etc/apache2/mods-available'
    enabled_dir = '/etc/apache2/mods-enabled'
    fragment_suffix = '.load'
    command_names = dict(present='a2enmod', absent='a2dismod')


class ApacheSuseModuleVariable(ApacheSuseVariable):
    sysconf_variable = 'APACHE_MODULES'
    command_names = dict(present='a2enmod', absent='a2dismod')


class ApacheSuseFlagVariable(ApacheSuseVariable):
    sysconf_variable = 'APACHE_SERVER_FLAGS'
    command_names = dict(present='a2enflag', absent='a2disflag')


def _set_state(state):
    type = module.params['type']
    name = module.params['name']

    distribution = Distribution(module)
    os_family = distribution.get_distribution_facts()['os_family']

    fragment = None
    if os_family == 'Debian':
        if type == 'conf':
            fragment = ApacheConfigFragment(name)
        elif type == 'site':
            fragment = ApacheSiteFragment(name)
        elif type == 'mod':
            fragment = ApacheModuleFragment(name)
    elif os_family == 'Suse':
        if type == 'mod':
            fragment = ApacheSuseModuleVariable(name)
        elif type == 'flag':
            fragment = ApacheSuseFlagVariable(name)

    if fragment is None:
        raise ApacheFragmentUnsupported(os_family)

    if fragment.state() != state:
        if module.check_mode:
            return True

        rc, stdout, stderr = fragment.set(state)

        if fragment.state() == state:
            return True
        else:
            raise ApacheFragmentFail(rc, stdout, stderr)
    else:
        return False


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            type=dict(required=True, choices=['conf', 'site', 'mod']),
            name=dict(required=True),
            state=dict(default='present', choices=['absent', 'present']),
            force=dict(required=False, type='bool', default=False)
        ),
        supports_check_mode=True
    )

    module.warnings = []

    state = module.params['state']
    name = module.params['name']

    state_string = dict(present='enabled', absent='disabled')[state]
    success_msg = "Fragment %s %s" % (name, state_string)
    fail_msg = "Failed to set fragment %s to %s" % (name, state_string)

    try:
        changed = _set_state(state)
    except ApacheFragmentFail as e:
        module.fail_json(msg=fail_msg, rc=e.rc, stdout=e.stdout, stderr=e.stderr)
    except ApacheFragmentUnsupported as e:
        module.fail_json(msg="Unsupported distribution: %s" % e.message)
    except ApacheFragmentException as e:
        module.fail_json(msg=e.message)
    else:
        module.exit_json(changed=changed, result=success_msg, warnings=module.warnings)


if __name__ == '__main__':
    main()
