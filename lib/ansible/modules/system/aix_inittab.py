#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Joris Weijters <joris.weijters@gmail.com>
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
author: "Joris Weijters (@molekuul)"
module: aix_inittab
short_description: Manages the inittab at AIX.
description:
    - Manages the inittab at AIX.
version_added: "2.3"
options:
  name:
    description: Name of the inittab entry.
    required: True
    alias: service
    type: string
    default: null
  runlevel:
    description: Runlevel of the entry.
    required: True
    type: string
    default: null
  processaction:
    description: Action what the init has to do with this entry.
    required: True
    choices: [
               'respawn',
               'wait',
               'once',
               'boot',
               'bootwait',
               'powerfail',
               'powerwait',
               'off',
               'hold',
               'ondemand',
               'initdefault',
               'sysinit'
              ]
    type: string
    default: null
  command:
    description: What command has to run.
    requred: True
    type: string
    default: null
  follow:
    description: After which inittabline shoud the new entry follow.
    required: False
    type: string
    default: null
  action:
    description: What action has to be done.
    required: True
    type: string
    choices: [
               'install',
               'change',
               'remove'
              ]
    default: null
notes:
  - The changes are persisten across reboot.
  - You need root rights to read or adjust the inittab with the lsitab, chitab,
    mkitab or rmitab commands.
  - tested at AIX 7.1.
requirements: [ 'itertools']
'''

EXAMPLES = '''
# Add service startmyservice to the inittab, directly after service existingservice.
- name: Add startmyservice to inittab
  aix_inittab:
    name: startmyservice
    runlevel: 4
    processaction: once
    command: "echo hello"
    follow: existingservice
    action: install
  become: yes

# Change inittab enrty startmyservice to runlevel "2" and processactio "wait".
- name: Change startmyservice to inittab
  aix_inittab:
    name: startmyservice
    runlevel: 2
    processaction: wait
    command: "echo hello"
    action: change
  become: yes

# Remove inittab entry startmyservice.
- name: remove startmyservice from inittab
  aix_inittab:
    name: startmyservice
    runlevel: 2
    processaction: wait
    command: "echo hello"
    action: remove
  become: yes
'''

RETURN = '''
# description: The result is deliverd in an dictionary.
- return:
  changed: true
  msg: []
  name: "startmyservice"
  status: "changed inittab entry startmyservice"
  warnings: []
'''

# Import necessary libraries
import itertools

try:
    import json
except ImportError:
    import simplejson as json

from ansible.module_utils.basic import AnsibleModule

# end import modules
# start defining the functions


def check_current_entry(module):
    # Check if entry exists, if not return False in exists in return dict,
    # if true return True and the entry in return dict
    existsdict = { 'exist' : False }
    (rc, out, err) = module.run_command(['lsitab', module.params['name']])
    if rc == 0:
        keys = ('name', 'runlevel', 'processaction', 'command')
        values = out.split(":")
        values = map(lambda s: s.strip(), values)  # strip non readable characters as \n
        existsdict = dict(itertools.izip(keys,values))
        existsdict.update({ 'exist' : True })
    return existsdict


def main():
    # initialize
    module = AnsibleModule(
        argument_spec = dict(
            name = dict( required=True, type='str', aliases=['service']),
            runlevel = dict( required=True, type='str'),
            processaction = dict( choices=[
                                  'respawn',
                                  'wait',
                                  'once',
                                  'boot',
                                  'bootwait',
                                  'powerfail',
                                  'powerwait',
                                  'off',
                                  'hold',
                                  'ondemand',
                                  'initdefault',
                                  'sysinit'
                                  ], type='str'),
            command = dict( required=True, type='str' ),
            follow = dict( type='str' ),
            action = dict( choices=[
                           'install',
                           'change',
                           'remove'
                           ], required=True, type='str'),
        )
        )

    result = {
        'name':  module.params['name'],
        'changed': False,
        'status': {},
        'warnings': [],
        'msg': [],
    }

    # Find commandline strings
    lsitab = module.get_bin_path('lsitab')
    mkitab = module.get_bin_path('mkitab')
    rmitab = module.get_bin_path('rmitab')

    # check if the new entry exists
    current_entry = check_current_entry(module)


    # if action is install or change,
    if module.params['action'] == 'install' or module.params['action'] == 'change':

        # create new entry string
        new_entry = module.params['name']+":"+module.params['runlevel']+":"+module.params['processaction']+":"+module.params['command']

        # If current entry exists or fields are different(if the entry does not exists, then the entry wil be created
        if ( not current_entry['exist'] ) or (
                module.params['runlevel'] != current_entry['runlevel'] or
                module.params['processaction'] != current_entry['processaction'] or
                module.params['command'] != current_entry['command'] ):

            # If the entry does exist then change the entry
            if current_entry['exist']:
                (rc, out, err) = module.run_command(['chitab', new_entry])
                if rc != 0:
                    result['warnings']= "could not change"+" "+current_entry['name']
                    module.fail_json(rc=rc, err=err, msg=result['warnings'] )
                result['status'] = "changed inittab entry"+" "+current_entry['name']
                result['changed'] = True

            # If the entry does not exist create the entry
            elif not current_entry['exist']:

                if module.params['follow']:
                    (rc, out, err) = module.run_command(['mkitab', '-i',  module.params['follow'], new_entry ])
                else:
                    (rc, out, err) = module.run_command(['mkitab', new_entry ])

                if rc != 0:
                    result['warnings']= "could not add"+" "+module.params['name']
                    module.fail_json(rc=rc, err=err, msg=result['warnings'])
                result['status'] = "add inittab entry"+" "+module.params['name']
                result['changed'] = True


    elif module.params['action'] == 'remove':
        # If the action is remove and the entry exists then remove the entry
        if current_entry['exist']:
            (rc, out, err) = module.run_command(['rmitab',  module.params['name']])
            if rc != 0:
                result['warnings']= "could not remove"+" "+current_entry['name']
                module.fail_json(rc=rc, err=err, msg=result['warnings'] )
            result['status'] = "removed inittab entry"+" "+current_entry['name']
            result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()

