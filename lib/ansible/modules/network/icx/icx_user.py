#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: icx_user
version_added: "1.0"
author: "Ruckus: https://support.ruckuswireless.com/contact-us"
short_description: Manage the user accounts on Ruckus ICX 7000 series switches.
description:
  - This module creates or updates user account on network devices. It allows playbooks to manage
    either individual usernames or the aggregate of usernames in the
    current running config. It also supports purging usernames from the
    configuration that are not explicitly defined.
options:
  aggregate:
    description:
      - The set of username objects to be configured on the remote
        ICX device. The list entries can either be the username
        or a hash of username and properties. This argument is mutually
        exclusive with the C(name) argument.
    aliases: ['users', 'collection']
  name:
    description:
      - The username to be configured on the ICX device.
        This argument accepts a string value and is mutually exclusive
        with the C(aggregate) argument.
        Please note that this option is not same as C(provider username).
    required: true
  configured_password:
    description:
      - The password to be configured on the ICX device.
    note: This is valid only when nopassword is not set to true
  update_password:
    description:
      - This  argument will instruct the module when to change the password.  When
        set to C(always), the password will always be updated in the device
        and when set to C(on_create) the password will be updated only if
        the username is created.
    default: always
    choices: ['on_create', 'always']
  privilege:
    description:
      - The privilege level to be granted to the user
    default: 0
    choice: [0,4,5]
  nopassword:
    description:
      - Defines the username without assigning
        a password. This will allow the user to login to the system
        without being authenticated by a password.
    type: bool
    note: This option is set to true then configured_password should not be used
  purge:
    description:
      - If set to true module will remove any previously
        configured usernames on the device except the current defined set of users.
    type: bool
    default: false
  state:
    description:
      - Configures the state of the username definition
        as it relates to the device operational configuration. When set
        to I(present), the username(s) should be configured in the device active
        configuration and when set to I(absent) the username(s) should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
  check_running_config:
    description:
      - Check running configuration. This can be set as environment variable. Module will use environment variable value(default:True), unless it is overriden, by specifying it as module parameter.
    type: bool
    default: As set in environment variable    
"""

EXAMPLES = """
- name: create a new user without password
  icx_user:
    name: user1
    nopassword: true

- name: Update password of user user1
    icx_user:
      name: user1
      configured_password: test125
      update_password: always

- name: create a new user with password
  icx_user:
    name: user1
    configured_password: 'newpassword'

- name: remove users
  icx_user:
    name: user1
    state: absent

- name: set user privilege level to 5
  icx_user:
    name: user1
    privilege: 5

 - name: purge all the users except user1
   icx_user:
     aggregate:
       - name: user1
     purge: true
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - username ansible nopassword
    - username ansible password-string alethea123
    - no username ansible
    - username ansible privilege 5
    - username ansible enable
"""

from copy import deepcopy

import re
import base64
import hashlib

from functools import partial

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.connection import Connection, ConnectionError,exec_command
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.icx.icx import get_config, load_config

def get_param_value(key, item, module):
    # if key doesn't exist in the item, get it from module.params
    if not item.get(key):
        value = module.params[key]

    # if key does exist, do a type check on it to validate it
    else:
        value_type = module.argument_spec[key].get('type', 'str')
        type_checker = module._CHECK_ARGUMENT_TYPES_DISPATCHER[value_type]
        type_checker(item[key])
        value = item[key]

    # validate the param value (if validator func exists)
    validator = globals().get('validate_%s' % key)
    if all((value, validator)):
        validator(value, module)

    return value

def map_params_to_obj(module):
    users = module.params['aggregate']
    if not users:
        if not module.params['name'] and module.params['purge']:
            return list()
        elif not module.params['name']:
            module.fail_json(msg='username is required')
        else:
            aggregate = [{'name': module.params['name']}]
    else:
        aggregate = list()
        for item in users:
            if not isinstance(item, dict):
                aggregate.append({'name': item})
            elif 'name' not in item:
                module.fail_json(msg='name is required')
            else:
                aggregate.append(item)

    objects = list()

    for item in aggregate:
        get_value = partial(get_param_value, item=item, module=module)
        item['configured_password'] = get_value('configured_password')
        item['nopassword'] = get_value('nopassword')
        item['privilege'] = get_value('privilege')
        item['state'] = get_value('state')
        objects.append(item)

    return objects

def parse_privilege(data):
    match = re.search(r'privilege (\S)', data, re.M)
    if match:
        return match.group(1)

def map_config_to_obj(module):
    compare=module.params['check_running_config']
    data = get_config(module, flags=['| include username'],compare=compare)

    match = re.findall(r'(?:^(?:u|\s{2}u))sername (\S+)', data, re.M)
    if not match:
        return list()

    instances = list()

    for user in set(match):
        regex = r'username %s .+$' % user
        cfg = re.findall(regex, data, re.M)
        cfg = '\n'.join(cfg)
        #sshregex = r'username %s\n\s+key-hash .+$' % user
        #sshcfg = re.findall(sshregex, data, re.M)
        #sshcfg = '\n'.join(sshcfg)
        obj = {
            'name': user,
            'state': 'present',
            'nopassword': 'nopassword' in cfg,
            'configured_password': None,
            'privilege': parse_privilege(cfg)
        }
        instances.append(obj)

    return instances

def map_obj_to_commands(updates, module):
    commands = list()
    state = module.params['state']
    update_password = module.params['update_password']

    def needs_update(want, have, x):
        return want.get(x) and (want.get(x) != have.get(x))

    def add(command, want, x):
        command.append('username %s %s' % (want['name'], x))
    for update in updates:
        want, have = update
        if want['state'] == 'absent':
            commands.append(user_del_cmd(want['name']))

        if needs_update(want, have, 'privilege'):
            add(commands, want, 'privilege %s password %s'%(want['privilege'],want['configured_password']))
        else:
            if needs_update(want, have, 'configured_password'):
                if update_password == 'always' or not have:
                    add(commands, want, '%spassword %s' % ('privilege '+str(have.get('privilege'))+" " if have.get('privilege')!=None else '',want['configured_password']))

        if needs_update(want, have, 'nopassword'):
            if want['nopassword']:
                add(commands, want, 'nopassword')
            #else:
                #add(commands, want, user_del_cmd(want['name']))

        if needs_update(want, have, 'access_time'):
            add(commands, want, 'access-time %s' % want['access_time'])

        if needs_update(want, have, 'expiry_days'):
            add(commands, want, 'expires %s' % want['expiry_days'])

    return commands

def update_objects(want, have):
    updates = list()
    for entry in want:
        item = next((i for i in have if i['name'] == entry['name']), None)

        if all((item is None, entry['state'] == 'present')):
            updates.append((entry, {}))

        elif all((have==[],entry['state'] == 'absent')):
          for key, value in iteritems(entry):
            if not key in ['update_password']:
              updates.append((entry, item))
              break
        elif item:
            for key, value in iteritems(entry):
                if not key in ['update_password']:
                    if value!=None and value != item.get(key):
                        updates.append((entry, item))
                        break
    return updates

def user_del_cmd(username):
    return 'no username %s' % username

def main():
    """entry point for module execution
    """
    element_spec = dict(
        name=dict(),

        configured_password=dict(no_log=True),
        nopassword=dict(type='bool',default=False),
        update_password=dict(default='always', choices=['on_create', 'always']),
        privilege=dict(type='str', choices=['0', '4', '5']),
        access_time=dict(type='str'),
        state=dict(default='present', choices=['present', 'absent']),
        check_running_config=dict(type='bool')
    )
    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec, aliases=['users', 'collection']),
        purge=dict(type='bool', default=False)
    )

    argument_spec.update(element_spec)
    #argument_spec.update(ios_argument_spec)

    mutually_exclusive = [('name', 'aggregate')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    result = {'changed': False}
    exec_command(module,'skip')
    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    commands = map_obj_to_commands(update_objects(want, have), module)

    if module.params['purge']:
        want_users = [x['name'] for x in want]
        have_users = [x['name'] for x in have]
        for item in set(have_users).difference(want_users):
            if item != 'admin':
                commands.append(user_del_cmd(item))

    result["commands"] = commands
    # result["have"] = have
    # result["want"] = want
    #result["update"] = update_objects(want, have)
    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True
    module.exit_json(**result)

if __name__ == '__main__':
    main()
