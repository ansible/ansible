#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Joris Weijters <joris.weijters@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}



DOCUMENTATION = '''
---
author: "Joris Weijters (@molekuul)"
module: aix_inittab
short_description: Manages the inittab on AIX.
description:
    - Manages the inittab on AIX.
version_added: "2.3"
options:
  name:
    description:
    - Name of the inittab entry.
    required: True
    aliases: ['service']
  runlevel:
    description:
    - Runlevel of the entry.
    required: True
  action:
    description:
    - Action what the init has to do with this entry.
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
  command:
    description:
    - What command has to run.
    required: True
  insertafter:
    description:
    - After which inittabline should the new entry inserted.
  state:
    description:
    - Whether the entry should be present or absent in the inittab file
    choices: [ "present", "absent" ]
    default: present
notes:
  - The changes are persistent across reboots, you need root rights to read or adjust the inittab with the lsitab, chitab,
    mkitab or rmitab commands.
  - tested on AIX 7.1.
requirements: [ 'itertools']
'''

EXAMPLES = '''
# Add service startmyservice to the inittab, directly after service existingservice.
- name: Add startmyservice to inittab
  aix_inittab:
    name: startmyservice
    runlevel: 4
    action: once
    command: "echo hello"
    insertafter: existingservice
    state: present
  become: yes

# Change inittab entry startmyservice to runlevel "2" and processaction "wait".
- name: Change startmyservice to inittab
  aix_inittab:
    name: startmyservice
    runlevel: 2
    action: wait
    command: "echo hello"
    state: present
  become: yes

# Remove inittab entry startmyservice.
- name: remove startmyservice from inittab
  aix_inittab:
    name: startmyservice
    runlevel: 2
    action: wait
    command: "echo hello"
    state: absent
  become: yes
'''

RETURN = '''
name:
    description: name of the adjusted inittab entry
    returned: always
    type: string
    sample: startmyservice
msg:
    description: action done with the inittab entry
    returned: changed
    type: string
    sample: changed inittab entry startmyservice
changed:
    description: whether the inittab changed or not
    returned: always
    type: boolean
    sample: true
'''

# Import necessary libraries
import itertools
from ansible.module_utils.basic import AnsibleModule

# end import modules
# start defining the functions


def check_current_entry(module):
    # Check if entry exists, if not return False in exists in return dict,
    # if true return True and the entry in return dict
    existsdict = {'exist': False}
    lsitab = module.get_bin_path('lsitab')
    (rc, out, err) = module.run_command([lsitab, module.params['name']])
    if rc == 0:
        keys = ('name', 'runlevel', 'action', 'command')
        values = out.split(":")
        # strip non readable characters as \n
        values = map(lambda s: s.strip(), values)
        existsdict = dict(itertools.izip(keys, values))
        existsdict.update({'exist': True})
    return existsdict


def main():
    # initialize
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str', aliases=['service']),
            runlevel=dict(required=True, type='str'),
            action=dict(choices=[
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
            command=dict(required=True, type='str'),
            insertafter=dict(type='str'),
            state=dict(choices=[
                'present',
                'absent',
            ], required=True, type='str'),
        ),
        supports_check_mode=True,
    )

    result = {
        'name': module.params['name'],
        'changed': False,
        'msg': ""
    }

    # Find commandline strings
    mkitab = module.get_bin_path('mkitab')
    rmitab = module.get_bin_path('rmitab')
    chitab = module.get_bin_path('chitab')
    rc = 0

    # check if the new entry exists
    current_entry = check_current_entry(module)

    # if action is install or change,
    if module.params['state'] == 'present':

        # create new entry string
        new_entry = module.params['name'] + ":" + module.params['runlevel'] + \
            ":" + module.params['action'] + ":" + module.params['command']

        # If current entry exists or fields are different(if the entry does not
        # exists, then the entry wil be created
        if (not current_entry['exist']) or (
                module.params['runlevel'] != current_entry['runlevel'] or
                module.params['action'] != current_entry['action'] or
                module.params['command'] != current_entry['command']):

            # If the entry does exist then change the entry
            if current_entry['exist']:
                if not module.check_mode:
                    (rc, out, err) = module.run_command([chitab, new_entry])
                if rc != 0:
                    module.fail_json(
                        msg="could not change inittab", rc=rc, err=err)
                result['msg'] = "changed inittab entry" + " " + current_entry['name']
                result['changed'] = True

            # If the entry does not exist create the entry
            elif not current_entry['exist']:
                if module.params['insertafter']:
                    if not module.check_mode:
                        (rc, out, err) = module.run_command(
                            [mkitab, '-i', module.params['insertafter'], new_entry])
                else:
                    if not module.check_mode:
                        (rc, out, err) = module.run_command(
                            [mkitab, new_entry])

                if rc != 0:
                    module.fail_json(msg="could not adjust inittab", rc=rc, err=err)
                result['msg'] = "add inittab entry" + " " + module.params['name']
                result['changed'] = True

    elif module.params['state'] == 'absent':
        # If the action is remove and the entry exists then remove the entry
        if current_entry['exist']:
            if not module.check_mode:
                (rc, out, err) = module.run_command(
                    [rmitab, module.params['name']])
                if rc != 0:
                    module.fail_json(
                        msg="could not remove entry grom inittab)", rc=rc, err=err)
            result['msg'] = "removed inittab entry" + " " + current_entry['name']
            result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
