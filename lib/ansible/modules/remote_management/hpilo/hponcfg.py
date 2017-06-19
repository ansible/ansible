#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Dag Wieers <dag@wieers.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: hponcfg
author: Dag Wieers (@dagwieers)
version_added: "2.3"
short_description: Configure HP iLO interface using hponcfg
description:
- This modules configures the HP iLO interface using hponcfg.
options:
  path:
    description:
    - The XML file as accepted by hponcfg
    required: true
    aliases: ['src']
  minfw:
    description:
    - The minimum firmware level needed
requirements:
- hponcfg tool
notes:
- You need a working hponcfg on the target system.
'''

EXAMPLES = r'''
- name: Example hponcfg configuration XML
  copy:
    content: |
      <ribcl VERSION="2.0">
        <login USER_LOGIN="user" PASSWORD="password">
          <rib_info MODE="WRITE">
            <mod_global_settings>
              <session_timeout value="0"/>
              <ssh_status value="Y"/>
              <ssh_port value="22"/>
              <serial_cli_status value="3"/>
              <serial_cli_speed value="5"/>
            </mod_global_settings>
          </rib_info>
        </login>
      </ribcl>
    dest: /tmp/enable-ssh.xml

- name: Configure HP iLO using enable-ssh.xml
  hponcfg:
    src: /tmp/enable-ssh.xml
'''

from ansible.module_utils.basic import AnsibleModule

def main():

    module = AnsibleModule(
        argument_spec = dict(
            src = dict(required=True, type='path', aliases=['path']),
            minfw = dict(type='str'),
        )
    )

    # Consider every action a change (not idempotent yet!)
    changed = True

    src = module.params['src']
    minfw = module.params['minfw']

    options = ' -f %s' % src

    # Add -v for debugging
#    options += ' -v'

    if minfw:
        option += ' -m %s' % minfw

    rc, stdout, stderr = module.run_command('hponcfg %s' % options)

    if rc != 0:
        module.fail_json(rc=rc, msg="Failed to run hponcfg", stdout=stdout, stderr=stderr)

    module.exit_json(changed=changed, stdout=stdout, stderr=stderr)

if __name__ == '__main__':
    main()
