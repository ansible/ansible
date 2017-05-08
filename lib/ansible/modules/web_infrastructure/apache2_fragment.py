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
module: apache2_fragment
version_added: 2.4
author:
    - Den Ivanov (@urajio)
short_description: enables/disables a configuration fragment of the Apache2 webserver
description:
   - Enables or disables a specified module, site or configuration snippet of the Apache2 webserver.
options:
   type:
     description:
        - type of fragment
     required: true
     choices: ['conf', 'site', 'mod']
   name:
     description:
        - name of the configuration fragment to enable/disable
     required: true
   force:
     description:
        - force disabling of default modules and override Debian warnings
     required: false
     choices: ['True', 'False']
     default: False
   state:
     description:
        - indicate the desired state of the resource
     choices: ['present', 'absent']
     default: present
requirements: ["a2enmod","a2dismod","a2enconf","a2disconf","a2ensite","a2dismod"]
'''

EXAMPLES = '''
# enables the Apache2 module "wsgi"
- apache2_fragment:
    type: mod
    state: present
    name: wsgi
# disables the Apache2 module "wsgi"
- apache2_fragment:
    type: mod
    state: absent
    name: wsgi
# disable default config
- apache2_fragment:
    type: conf
    state: absent
    name: localized-error-pages
# enable default-ssl site
- apache2_fragment:
    type: site
    name: default-ssl
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
from os.path import basename, join, exists, islink, samefile, splitext
import glob


class ApacheFragmentException(Exception):
    pass


class ApacheFragment(object):
    available_dir = None
    enabled_dir = None
    fragment_suffix = None

    def __init__(self, name):
        self.fragment_file = basename(name)

    def is_enabled(self):
        """
        :return: True if fragment enabled, False otherwise. Raise exception if fragment not found.  
        """
        available_fragment = join(self.available_dir, self.fragment_file)
        if not exists(available_fragment):
            raise ApacheFragmentException(
                "Apache config fragment %s not found in %s" % (self.fragment_file, self.available_dir))
        for enabled_fragment in glob.glob(join(self.enabled_dir, '*' + self.fragment_suffix)):
            if islink(enabled_fragment) and samefile(available_fragment, enabled_fragment):
                return True
        return False

    def name(self):
        """
        :return: Short name of fragment: without path and suffix 
        """
        return splitext(self.fragment_file)[0]


class ApacheConfigFragment(ApacheFragment):
    available_dir = '/etc/apache2/conf-available'
    enabled_dir = '/etc/apache2/conf-enabled'
    fragment_suffix = '.conf'


class ApacheSiteFragment(ApacheFragment):
    available_dir = '/etc/apache2/sites-available'
    enabled_dir = '/etc/apache2/sites-enabled'
    fragment_suffix = '.conf'


class ApacheCommand(object):
    command_names = {'present': None, 'absent': None}

    def __init__(self, module):
        self.module = module

    def name(self, state, force=None):
        command_name = self.module.get_bin_path(self.command_names[state], required=True)
        if force:
            command_name += ' -f'
        return command_name

    def set(self, fragment=None, state=None, force=None):
        return self.module.run_command("%s %s" % (self.name(state, force), fragment.name()), check_rc=True)


class ApacheConfigCommand(ApacheCommand):
    command_names = {'present': 'a2enconf', 'absent': 'a2disconf'}


class ApacheSiteCommand(ApacheCommand):
    command_names = {'present': 'a2ensite', 'absent': 'a2dissite'}


def _set_state(module, state):
    type = module.params['type']
    name = module.params['name']
    force = module.params['force']

    want_enabled = state == 'present'
    state_string = {'present': 'enabled', 'absent': 'disabled'}[state]
    success_msg = "Fragment %s %s" % (name, state_string)

    if type == 'conf':
        fragment = ApacheConfigFragment(name)
        command = ApacheConfigCommand(module)
    elif type == 'site':
        fragment = ApacheSiteFragment(name)
        command = ApacheSiteCommand(module)
    else:
        raise ApacheFragmentException("Unknown Apache fragment type: %s" % type)

    if fragment.is_enabled() != want_enabled:
        # state must be changed
        if module.check_mode:
            return True, success_msg

        result, stdout, stderr = command.set(fragment, state, force)

        if fragment.is_enabled() == want_enabled:
            return True, success_msg
        else:
            raise ApacheFragmentException("Failed to set module %s to %s: %s" % (name, state_string, stdout))
    else:
        return False, success_msg


def main():
    module = AnsibleModule(
        argument_spec=dict(
            type=dict(required=True, choices=['conf', 'site', 'mod']),
            name=dict(required=True),
            force=dict(required=False, type='bool', default=False),
            state=dict(default='present', choices=['absent', 'present'])
        ),
        supports_check_mode=True
    )

    module.warnings = []

    try:
        (changed, msg) = _set_state(module, module.params['state'])
        module.exit_json(changed=changed, result=msg, warnings=module.warnings)
    except ApacheFragmentException as e:
        module.fail_json(msg=e.message)


if __name__ == '__main__':
    main()
