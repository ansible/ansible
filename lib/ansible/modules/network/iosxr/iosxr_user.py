#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: iosxr_user
version_added: "2.4"
author:
  - "Trishna Guha (@trishnaguha)"
  - "Sebastiaan van Doesselaar (@sebasdoes)"
short_description: Manage the aggregate of local users on Cisco IOS XR device
description:
  - This module provides declarative management of the local usernames
    configured on network devices. It allows playbooks to manage
    either individual usernames or the aggregate of usernames in the
    current running config. It also supports purging usernames from the
    configuration that are not explicitly defined.
extends_documentation_fragment: iosxr
notes:
  - Tested against IOS XR 6.1.2
options:
  aggregate:
    description:
      - The set of username objects to be configured on the remote
        Cisco IOS XR device. The list entries can either be the username
        or a hash of username and properties. This argument is mutually
        exclusive with the C(name) argument, alias C(users).
  name:
    description:
      - The username to be configured on the Cisco IOS XR device.
        This argument accepts a string value and is mutually exclusive
        with the C(aggregate) argument.
        Please note that this option is not same as C(provider username).
  configured_password:
    description:
      - The password to be configured on the Cisco IOS XR device. The
        password needs to be provided in clear and it will be encrypted
        on the device.
        Please note that this option is not same as C(provider password).
  update_password:
    description:
      - Since passwords are encrypted in the device running config, this
        argument will instruct the module when to change the password.  When
        set to C(always), the password will always be updated in the device
        and when set to C(on_create) the password will be updated only if
        the username is created.
    default: always
    choices: ['on_create', 'always']
  group:
    description:
      - Configures the group for the username in the
        device running configuration. The argument accepts a string value
        defining the group name. This argument does not check if the group
        has been configured on the device, alias C(role).
  groups:
    version_added: "2.5"
    description:
      - Configures the groups for the username in the device running
        configuration. The argument accepts a list of group names.
        This argument does not check if the group has been configured
        on the device. It is similar to the aggregrate command for
        usernames, but lets you configure multiple groups for the user(s).
  purge:
    description:
      - Instructs the module to consider the
        resource definition absolute. It will remove any previously
        configured usernames on the device with the exception of the
        `admin` user (the current defined set of users).
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
  public_key:
    version_added: "2.5"
    description:
      - Configures the contents of the public keyfile to upload to the IOS-XR node.
        This enables users to login using the accompanying private key. IOS-XR
        only accepts base64 decoded files, so this will be decoded and uploaded
        to the node. Do note that this requires an OpenSSL public key file,
        PuTTy generated files will not work! Mutually exclusive with
        public_key_contents. If used with multiple users in aggregates, then the
        same key file is used for all users.
  public_key_contents:
    version_added: "2.5"
    description:
      - Configures the contents of the public keyfile to upload to the IOS-XR node.
        This enables users to login using the accompanying private key. IOS-XR
        only accepts base64 decoded files, so this will be decoded and uploaded
        to the node. Do note that this requires an OpenSSL public key file,
        PuTTy generated files will not work! Mutually exclusive with
        public_key.If used with multiple users in aggregates, then the
        same key file is used for all users.
requirements:
  - base64 when using I(public_key_contents) or I(public_key)
  - paramiko when using I(public_key_contents) or I(public_key)
"""

EXAMPLES = """
- name: create a new user
  iosxr_user:
    name: ansible
    configured_password: test
    state: present
- name: remove all users except admin
  iosxr_user:
    purge: yes
- name: set multiple users to group sys-admin
  iosxr_user:
    aggregate:
      - name: netop
      - name: netend
    group: sysadmin
    state: present
- name: set multiple users to multiple groups
  iosxr_user:
    aggregate:
      - name: netop
      - name: netend
    groups:
      - sysadmin
      - root-system
    state: present
- name: Change Password for User netop
  iosxr_user:
    name: netop
    configured_password: "{{ new_password }}"
    update_password: always
    state: present
- name: Add private key authentication for user netop
  iosxr_user:
    name: netop
    state: present
    public_key_contents: "{{ lookup('file', '/home/netop/.ssh/id_rsa.pub' }}"
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - username ansible secret password group sysadmin
    - username admin secret admin
"""
from functools import partial

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.iosxr.iosxr import get_config, load_config
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec

try:
    from base64 import b64decode
    HAS_B64 = True
except ImportError:
    HAS_B64 = False

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates

    for w in want:
        name = w['name']
        state = w['state']

        obj_in_have = search_obj_in_list(name, have)

        if state == 'absent' and obj_in_have:
            commands.append('no username ' + name)
        elif state == 'present' and not obj_in_have:
            user_cmd = 'username ' + name
            commands.append(user_cmd)

            if w['configured_password']:
                commands.append(user_cmd + ' secret ' + w['configured_password'])
            if w['group']:
                commands.append(user_cmd + ' group ' + w['group'])
            elif w['groups']:
                for group in w['groups']:
                    commands.append(user_cmd + ' group ' + group)

        elif state == 'present' and obj_in_have:
            user_cmd = 'username ' + name

            if module.params['update_password'] == 'always' and w['configured_password']:
                commands.append(user_cmd + ' secret ' + w['configured_password'])
            if w['group'] and w['group'] != obj_in_have['group']:
                commands.append(user_cmd + ' group ' + w['group'])
            elif w['groups']:
                for group in w['groups']:
                    commands.append(user_cmd + ' group ' + group)

    return commands


def map_config_to_obj(module):
    data = get_config(module, config_filter='username')
    users = data.strip().rstrip('!').split('!')

    if not users:
        return list()

    instances = list()

    for user in users:
        user_config = user.strip().splitlines()

        name = user_config[0].strip().split()[1]
        group = None

        if len(user_config) > 1:
            group_or_secret = user_config[1].strip().split()
            if group_or_secret[0] == 'group':
                group = group_or_secret[1]

        obj = {
            'name': name,
            'state': 'present',
            'configured_password': None,
            'group': group
        }
        instances.append(obj)

    return instances


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
        item['group'] = get_value('group')
        item['groups'] = get_value('groups')
        item['state'] = get_value('state')
        objects.append(item)

    return objects


def convert_key_to_base64(module):
    """ IOS-XR only accepts base64 decoded files, this converts the public key to a temp file.
    """
    if module.params['aggregate']:
        name = 'aggregate'
    else:
        name = module.params['name']

    if module.params['public_key_contents']:
        key = module.params['public_key_contents']
    elif module.params['public_key']:
        readfile = open(module.params['public_key'], 'r')
        key = readfile.read()
    splitfile = key.split()[1]

    base64key = b64decode(splitfile)
    base64file = open('/tmp/publickey_%s.b64' % (name), 'w')
    base64file.write(base64key)
    base64file.close()

    return '/tmp/publickey_%s.b64' % (name)


def copy_key_to_node(module, base64keyfile):
    """ Copy key to IOS-XR node. We use SFTP because older IOS-XR versions don't handle SCP very well.
    """
    if (module.params['host'] is None or module.params['provider']['host'] is None):
        return False

    if (module.params['username'] is None or module.params['provider']['username'] is None):
        return False

    if module.params['aggregate']:
        name = 'aggregate'
    else:
        name = module.params['name']

    src = base64keyfile
    dst = '/harddisk:/publickey_%s.b64' % (name)

    user = module.params['username'] or module.params['provider']['username']
    node = module.params['host'] or module.params['provider']['host']
    password = module.params['password'] or module.params['provider']['password']
    ssh_keyfile = module.params['ssh_keyfile'] or module.params['provider']['ssh_keyfile']

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if not ssh_keyfile:
        ssh.connect(node, username=user, password=password)
    else:
        ssh.connect(node, username=user, allow_agent=True)
    sftp = ssh.open_sftp()
    sftp.put(src, dst)
    sftp.close()
    ssh.close()


def addremovekey(module, command):
    """ Add or remove key based on command
    """
    if (module.params['host'] is None or module.params['provider']['host'] is None):
        return False

    if (module.params['username'] is None or module.params['provider']['username'] is None):
        return False

    user = module.params['username'] or module.params['provider']['username']
    node = module.params['host'] or module.params['provider']['host']
    password = module.params['password'] or module.params['provider']['password']
    ssh_keyfile = module.params['ssh_keyfile'] or module.params['provider']['ssh_keyfile']

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if not ssh_keyfile:
        ssh.connect(node, username=user, password=password)
    else:
        ssh.connect(node, username=user, allow_agent=True)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('%s \r' % (command))
    readmsg = ssh_stdout.read(100)  # We need to read a bit to actually apply for some reason
    if ('already' in readmsg) or ('removed' in readmsg) or ('really' in readmsg):
        ssh_stdin.write('yes\r')
    ssh_stdout.read(1)  # We need to read a bit to actually apply for some reason
    ssh.close()

    return readmsg


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),

        configured_password=dict(no_log=True),
        update_password=dict(default='always', choices=['on_create', 'always']),

        public_key=dict(),
        public_key_contents=dict(),

        group=dict(aliases=['role']),
        groups=dict(type='list', elements='dict'),

        state=dict(default='present', choices=['present', 'absent'])
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
    argument_spec.update(iosxr_argument_spec)
    mutually_exclusive = [('name', 'aggregate'), ('public_key', 'public_key_contents'), ('group', 'groups')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    if (module.params['public_key_contents'] or module.params['public_key']):
        if not HAS_B64:
            module.fail_json(
                msg='library base64 is required but does not appear to be '
                    'installed. It can be installed using `pip install base64`'
            )
        if not HAS_PARAMIKO:
            module.fail_json(
                msg='library paramiko is required but does not appear to be '
                    'installed. It can be installed using `pip install paramiko`'
            )

    warnings = list()
    if module.params['password'] and not module.params['configured_password']:
        warnings.append(
            'The "password" argument is used to authenticate the current connection. ' +
            'To set a user password use "configured_password" instead.'
        )

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)

    if module.params['purge']:
        want_users = [x['name'] for x in want]
        have_users = [x['name'] for x in have]
        for item in set(have_users).difference(want_users):
            if item != 'admin':
                commands.append('no username %s' % item)

    result['commands'] = commands
    result['warnings'] = warnings

    if 'no username admin' in commands:
        module.fail_json(msg='cannot delete the `admin` account')

    if commands:
        commit = not module.check_mode
        diff = load_config(module, commands, commit=commit)
        if diff:
            result['diff'] = dict(prepared=diff)
        result['changed'] = True

    if module.params['state'] == 'present' and (module.params['public_key_contents'] or module.params['public_key']):
        if not module.check_mode:
            key = convert_key_to_base64(module)
            copykeys = copy_key_to_node(module, key)
            if copykeys is False:
                warnings.append('Please set up your provider before running this playbook')

            if module.params['aggregate']:
                for user in module.params['aggregate']:
                    cmdtodo = "admin crypto key import authentication rsa username %s harddisk:/publickey_aggregate.b64" % (user)
                    addremove = addremovekey(module, cmdtodo)
                    if addremove is False:
                        warnings.append('Please set up your provider before running this playbook')
            else:
                cmdtodo = "admin crypto key import authentication rsa username %s harddisk:/publickey_%s.b64" % (module.params['name'], module.params['name'])
                addremove = addremovekey(module, cmdtodo)
                if addremove is False:
                    warnings.append('Please set up your provider before running this playbook')
    elif module.params['state'] == 'absent':
        if not module.check_mode:
            if module.params['aggregate']:
                for user in module.params['aggregate']:
                    cmdtodo = "admin crypto key zeroize authentication rsa username %s" % (user)
                    addremove = addremovekey(module, cmdtodo)
                    if addremove is False:
                        warnings.append('Please set up your provider before running this playbook')
            else:
                cmdtodo = "admin crypto key zeroize authentication rsa username %s" % (module.params['name'])
                addremove = addremovekey(module, cmdtodo)
                if addremove is False:
                    warnings.append('Please set up your provider before running this playbook')
    elif module.params['purge'] is True:
        if not module.check_mode:
            cmdtodo = "admin crypto key zeroize authentication rsa all"
            addremove = addremovekey(module, cmdtodo)
            if addremove is False:
                warnings.append('Please set up your provider before running this playbook')

    module.exit_json(**result)

if __name__ == '__main__':
    main()
