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
short_description: enables/disables a configuration snippet of the Apache2 webserver
description:
   - Enables or disables a specified site or configuration snippet of the Apache2 webserver.
     This module support Debian/Ubuntu based systems, and requires a2enconf, a2disconf, a2ensite, a2dissite scripts.
options:
   type:
     description:
        - type of fragment
     required: true
     choices: ['conf', 'site']
   name:
     description:
        - name of the configuration snippet to enable/disable
     required: true
   state:
     description:
        - indicate the desired state of the resource
     choices: ['present', 'absent']
     default: present
requirements: ["a2enconf","a2disconf","a2ensite","a2dissite"]
'''

EXAMPLES = '''
# enable config fragment charset.conf
- apache2_conf:
    type: conf
    state: present
    name: charset.conf
# disable config fragment
- apache2_conf:
    type: conf
    state: absent
    name: localized-error-pages.conf
# enable default-ssl site
- apache2_conf:
    type: site
    name: default-ssl.conf
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

from module_utils.basic import AnsibleModule
from os.path import basename, join, exists, islink, samefile, splitext
import glob


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
    fragment_suffix = '.conf'
    command_names = dict(present=None, absent=None)

    def __init__(self, name):
        self.fragment_file = basename(name)
        for required_dir in (self.available_dir, self.enabled_dir):
            if not exists(required_dir):
                raise ApacheFragmentUnsupported("directory %s not found" % required_dir)

    def state(self):
        """
        :return: "present" if fragment enabled, "absent" otherwise. Raise exception if fragment not found.
        """
        available_fragment = join(self.available_dir, self.fragment_file)
        if not exists(available_fragment):
            raise ApacheFragmentException(
                "Apache config fragment %s not found in %s" % (self.fragment_file, self.available_dir))
        for enabled_fragment in glob.glob(join(self.enabled_dir, '*' + self.fragment_suffix)):
            if islink(enabled_fragment) and samefile(available_fragment, enabled_fragment):
                return "present"
        return "absent"

    def set(self, state=None):
        command_name = module.get_bin_path(self.command_names[state])
        if command_name is None:
            raise ApacheFragmentUnsupported("command %s not found" % self.command_names[state])
        # Short name of fragment: without path and suffix
        fragment_name = splitext(self.fragment_file)[0]
        return module.run_command([command_name, fragment_name], check_rc=True)


class ApacheConfigFragment(ApacheFragment):
    available_dir = '/etc/apache2/conf-available'
    enabled_dir = '/etc/apache2/conf-enabled'
    command_names = dict(present='a2enconf', absent='a2disconf')


class ApacheSiteFragment(ApacheFragment):
    available_dir = '/etc/apache2/sites-available'
    enabled_dir = '/etc/apache2/sites-enabled'
    command_names = dict(present='a2ensite', absent='a2dissite')


def _set_state(state):
    type = module.params['type']
    name = module.params['name']

    if type == 'conf':
        fragment = ApacheConfigFragment(name)
    elif type == 'site':
        fragment = ApacheSiteFragment(name)

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
            type=dict(required=True, choices=['conf', 'site']),
            name=dict(required=True),
            state=dict(default='present', choices=['absent', 'present'])
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
