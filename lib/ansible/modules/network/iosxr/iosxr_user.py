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
  - "Kedar Kekan (@kedarX)"
short_description: Manage the aggregate of local users on Cisco IOS XR device
description:
  - This module provides declarative management of the local usernames
    configured on network devices. It allows playbooks to manage
    either individual usernames or the aggregate of usernames in the
    current running config. It also supports purging usernames from the
    configuration that are not explicitly defined.
extends_documentation_fragment: iosxr
notes:
  - This module works with connection C(network_cli) and C(netconf). See L(the IOS-XR Platform Options,../network/user_guide/platform_iosxr.html).
  - Tested against IOS XRv 6.1.3
options:
  aggregate:
    description:
      - The set of username objects to be configured on the remote
        Cisco IOS XR device. The list entries can either be the username
        or a hash of username and properties. This argument is mutually
        exclusive with the C(name) argument.
    aliases: ['users', 'collection']
  name:
    description:
      - The username to be configured on the Cisco IOS XR device.
        This argument accepts a string value and is mutually exclusive
        with the C(aggregate) argument.
        Please note that this option is not same as C(provider username).
  configured_password:
    description:
      - The password to be configured on the Cisco IOS XR device. The password
        needs to be provided in clear text. Password is encrypted on the device
        when used with I(cli) and by Ansible when used with I(netconf)
        using the same MD5 hash technique with salt size of 3.
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
        has been configured on the device.
    aliases: ['role']
  groups:
    version_added: "2.5"
    description:
      - Configures the groups for the username in the device running
        configuration. The argument accepts a list of group names.
        This argument does not check if the group has been configured
        on the device. It is similar to the aggregate command for
        usernames, but lets you configure multiple groups for the user(s).
  purge:
    description:
      - Instructs the module to consider the
        resource definition absolute. It will remove any previously
        configured usernames on the device with the exception of the
        `admin` user and the current defined set of users.
    type: bool
    default: false
  admin:
    description:
      - Enters into administration configuration mode for making config
        changes to the device.
      - Applicable only when using network_cli transport
    type: bool
    default: false
    version_added: "2.8"
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
  - ncclient >= 0.5.3 when using netconf
  - lxml >= 4.1.1 when using netconf
  - base64 when using I(public_key_contents) or I(public_key)
  - paramiko when using I(public_key_contents) or I(public_key)
"""

EXAMPLES = """
- name: create a new user
  iosxr_user:
    name: ansible
    configured_password: mypassword
    state: present
- name: create a new user in admin configuration mode
  iosxr_user:
    name: ansible
    configured_password: mypassword
    admin: True
    state: present
- name: remove all users except admin
  iosxr_user:
    purge: True
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
xml:
  description: NetConf rpc xml sent to device with transport C(netconf)
  returned: always (empty list when no xml rpc to send)
  type: list
  version_added: 2.5
  sample:
    - '<config xmlns:xc=\"urn:ietf:params:xml:ns:netconf:base:1.0\">
    <aaa xmlns=\"http://cisco.com/ns/yang/Cisco-IOS-XR-aaa-lib-cfg\">
    <usernames xmlns=\"http://cisco.com/ns/yang/Cisco-IOS-XR-aaa-locald-cfg\">
    <username xc:operation=\"merge\">
    <name>test7</name>
    <usergroup-under-usernames>
    <usergroup-under-username>
    <name>sysadmin</name>
    </usergroup-under-username>
    </usergroup-under-usernames>
    <secret>$1$ZsXC$zZ50wqhDC543ZWQkkAHLW0</secret>
    </username>
    </usernames>
    </aaa>
    </config>'
"""

import os
from functools import partial
from copy import deepcopy
import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.compat.paramiko import paramiko
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.iosxr.iosxr import get_config, load_config, is_netconf, is_cliconf
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec, build_xml, etree_findall

try:
    from base64 import b64decode
    HAS_B64 = True
except ImportError:
    HAS_B64 = False


class PublicKeyManager(object):
    def __init__(self, module, result):
        self._module = module
        self._result = result

    def convert_key_to_base64(self):
        """ IOS-XR only accepts base64 decoded files, this converts the public key to a temp file.
        """
        if self._module.params['aggregate']:
            name = 'aggregate'
        else:
            name = self._module.params['name']

        if self._module.params['public_key_contents']:
            key = self._module.params['public_key_contents']
        elif self._module.params['public_key']:
            readfile = open(self._module.params['public_key'], 'r')
            key = readfile.read()
        splitfile = key.split()[1]

        base64key = b64decode(splitfile)
        base64file = open('/tmp/publickey_%s.b64' % (name), 'wb')
        base64file.write(base64key)
        base64file.close()

        return '/tmp/publickey_%s.b64' % (name)

    def copy_key_to_node(self, base64keyfile):
        """ Copy key to IOS-XR node. We use SFTP because older IOS-XR versions don't handle SCP very well.
        """
        if (self._module.params['host'] is None or self._module.params['provider']['host'] is None):
            return False

        if (self._module.params['username'] is None or self._module.params['provider']['username'] is None):
            return False

        if self._module.params['aggregate']:
            name = 'aggregate'
        else:
            name = self._module.params['name']

        src = base64keyfile
        dst = '/harddisk:/publickey_%s.b64' % (name)

        user = self._module.params['username'] or self._module.params['provider']['username']
        node = self._module.params['host'] or self._module.params['provider']['host']
        password = self._module.params['password'] or self._module.params['provider']['password']
        ssh_keyfile = self._module.params['ssh_keyfile'] or self._module.params['provider']['ssh_keyfile']

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

    def addremovekey(self, command):
        """ Add or remove key based on command
        """
        if (self._module.params['host'] is None or self._module.params['provider']['host'] is None):
            return False

        if (self._module.params['username'] is None or self._module.params['provider']['username'] is None):
            return False

        user = self._module.params['username'] or self._module.params['provider']['username']
        node = self._module.params['host'] or self._module.params['provider']['host']
        password = self._module.params['password'] or self._module.params['provider']['password']
        ssh_keyfile = self._module.params['ssh_keyfile'] or self._module.params['provider']['ssh_keyfile']

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

    def run(self):
        if self._module.params['state'] == 'present':
            if not self._module.check_mode:
                key = self.convert_key_to_base64()
                copykeys = self.copy_key_to_node(key)
                if copykeys is False:
                    self._result['warnings'].append('Please set up your provider before running this playbook')

                if self._module.params['aggregate']:
                    for user in self._module.params['aggregate']:
                        cmdtodo = "admin crypto key import authentication rsa username %s harddisk:/publickey_aggregate.b64" % (user)
                        addremove = self.addremovekey(cmdtodo)
                        if addremove is False:
                            self._result['warnings'].append('Please set up your provider before running this playbook')
                else:
                    cmdtodo = "admin crypto key import authentication rsa username %s harddisk:/publickey_%s.b64" % \
                              (self._module.params['name'], self._module.params['name'])
                    addremove = self.addremovekey(cmdtodo)
                    if addremove is False:
                        self._result['warnings'].append('Please set up your provider before running this playbook')
        elif self._module.params['state'] == 'absent':
            if not self._module.check_mode:
                if self._module.params['aggregate']:
                    for user in self._module.params['aggregate']:
                        cmdtodo = "admin crypto key zeroize authentication rsa username %s" % (user)
                        addremove = self.addremovekey(cmdtodo)
                        if addremove is False:
                            self._result['warnings'].append('Please set up your provider before running this playbook')
                else:
                    cmdtodo = "admin crypto key zeroize authentication rsa username %s" % (self._module.params['name'])
                    addremove = self.addremovekey(cmdtodo)
                    if addremove is False:
                        self._result['warnings'].append('Please set up your provider before running this playbook')
        elif self._module.params['purge'] is True:
            if not self._module.check_mode:
                cmdtodo = "admin crypto key zeroize authentication rsa all"
                addremove = self.addremovekey(cmdtodo)
                if addremove is False:
                    self._result['warnings'].append('Please set up your provider before running this playbook')

        return self._result


def search_obj_in_list(name, lst):
    for o in lst:
        if o['name'] == name:
            return o

    return None


class ConfigBase(object):
    def __init__(self, module, result, flag=None):
        self._module = module
        self._result = result
        self._want = list()
        self._have = list()

    def get_param_value(self, key, item):
        # if key doesn't exist in the item, get it from module.params
        if not item.get(key):
            value = self._module.params[key]

        # if key does exist, do a type check on it to validate it
        else:
            value_type = self._module.argument_spec[key].get('type', 'str')
            type_checker = self._module._CHECK_ARGUMENT_TYPES_DISPATCHER[value_type]
            type_checker(item[key])
            value = item[key]

        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if all((value, validator)):
            validator(value, self._module)

        return value

    def map_params_to_obj(self):
        users = self._module.params['aggregate']

        aggregate = list()
        if not users:
            if not self._module.params['name'] and self._module.params['purge']:
                pass
            elif not self._module.params['name']:
                self._module.fail_json(msg='username is required')
            else:
                aggregate = [{'name': self._module.params['name']}]
        else:
            for item in users:
                if not isinstance(item, dict):
                    aggregate.append({'name': item})
                elif 'name' not in item:
                    self._module.fail_json(msg='name is required')
                else:
                    aggregate.append(item)

        for item in aggregate:
            get_value = partial(self.get_param_value, item=item)
            item['configured_password'] = get_value('configured_password')
            item['group'] = get_value('group')
            item['groups'] = get_value('groups')
            item['state'] = get_value('state')
            self._want.append(item)


class CliConfiguration(ConfigBase):
    def __init__(self, module, result):
        super(CliConfiguration, self).__init__(module, result)

    def map_config_to_obj(self):
        data = get_config(self._module, config_filter='username')
        users = data.strip().rstrip('!').split('!')

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
            self._have.append(obj)

    def map_obj_to_commands(self):
        commands = list()

        for w in self._want:
            name = w['name']
            state = w['state']

            obj_in_have = search_obj_in_list(name, self._have)

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

                if self._module.params['update_password'] == 'always' and w['configured_password']:
                    commands.append(user_cmd + ' secret ' + w['configured_password'])
                if w['group'] and w['group'] != obj_in_have['group']:
                    commands.append(user_cmd + ' group ' + w['group'])
                elif w['groups']:
                    for group in w['groups']:
                        commands.append(user_cmd + ' group ' + group)

        if self._module.params['purge']:
            want_users = [x['name'] for x in self._want]
            have_users = [x['name'] for x in self._have]
            for item in set(have_users).difference(set(want_users)):
                if item != 'admin':
                    commands.append('no username %s' % item)

        if 'no username admin' in commands:
            self._module.fail_json(msg='cannot delete the `admin` account')

        self._result['commands'] = []
        if commands:
            commit = not self._module.check_mode
            admin = self._module.params['admin']
            diff = load_config(self._module, commands, commit=commit, admin=admin)
            if diff:
                self._result['diff'] = dict(prepared=diff)

            self._result['commands'] = commands
            self._result['changed'] = True

    def run(self):
        self.map_params_to_obj()
        self.map_config_to_obj()
        self.map_obj_to_commands()

        return self._result


class NCConfiguration(ConfigBase):
    def __init__(self, module, result):
        super(NCConfiguration, self).__init__(module, result)
        self._locald_meta = collections.OrderedDict()
        self._locald_group_meta = collections.OrderedDict()

    def generate_md5_hash(self, arg):
        '''
        Generate MD5 hash with randomly generated salt size of 3.
        :param arg:
        :return passwd:
        '''
        cmd = "openssl passwd -salt `openssl rand -base64 3` -1 "
        return os.popen(cmd + arg).readlines()[0].strip()

    def map_obj_to_xml_rpc(self):
        self._locald_meta.update([
            ('aaa_locald', {'xpath': 'aaa/usernames', 'tag': True, 'ns': True}),
            ('username', {'xpath': 'aaa/usernames/username', 'tag': True, 'attrib': "operation"}),
            ('a:name', {'xpath': 'aaa/usernames/username/name'}),
            ('a:configured_password', {'xpath': 'aaa/usernames/username/secret', 'operation': 'edit'}),
        ])

        self._locald_group_meta.update([
            ('aaa_locald', {'xpath': 'aaa/usernames', 'tag': True, 'ns': True}),
            ('username', {'xpath': 'aaa/usernames/username', 'tag': True, 'attrib': "operation"}),
            ('a:name', {'xpath': 'aaa/usernames/username/name'}),
            ('usergroups', {'xpath': 'aaa/usernames/username/usergroup-under-usernames', 'tag': True, 'operation': 'edit'}),
            ('usergroup', {'xpath': 'aaa/usernames/username/usergroup-under-usernames/usergroup-under-username', 'tag': True, 'operation': 'edit'}),
            ('a:group', {'xpath': 'aaa/usernames/username/usergroup-under-usernames/usergroup-under-username/name', 'operation': 'edit'}),
        ])

        state = self._module.params['state']
        _get_filter = build_xml('aaa', opcode="filter")
        running = get_config(self._module, source='running', config_filter=_get_filter)

        elements = etree_findall(running, 'username')
        users = list()
        for element in elements:
            name_list = etree_findall(element, 'name')
            users.append(name_list[0].text)
            list_size = len(name_list)
            if list_size == 1:
                self._have.append({'name': name_list[0].text, 'group': None, 'groups': None})
            elif list_size == 2:
                self._have.append({'name': name_list[0].text, 'group': name_list[1].text, 'groups': None})
            elif list_size > 2:
                name_iter = iter(name_list)
                next(name_iter)
                tmp_list = list()
                for name in name_iter:
                    tmp_list.append(name.text)

                self._have.append({'name': name_list[0].text, 'group': None, 'groups': tmp_list})

        locald_params = list()
        locald_group_params = list()
        opcode = None

        if state == 'absent':
            opcode = "delete"
            for want_item in self._want:
                if want_item['name'] in users:
                    want_item['configured_password'] = None
                    locald_params.append(want_item)
        elif state == 'present':
            opcode = "merge"
            for want_item in self._want:
                if want_item['name'] not in users:
                    want_item['configured_password'] = self.generate_md5_hash(want_item['configured_password'])
                    locald_params.append(want_item)

                    if want_item['group'] is not None:
                        locald_group_params.append(want_item)
                    if want_item['groups'] is not None:
                        for group in want_item['groups']:
                            want_item['group'] = group
                            locald_group_params.append(want_item.copy())
                else:
                    if self._module.params['update_password'] == 'always' and want_item['configured_password'] is not None:
                        want_item['configured_password'] = self.generate_md5_hash(want_item['configured_password'])
                        locald_params.append(want_item)
                    else:
                        want_item['configured_password'] = None

                    obj_in_have = search_obj_in_list(want_item['name'], self._have)
                    if want_item['group'] is not None and want_item['group'] != obj_in_have['group']:
                        locald_group_params.append(want_item)
                    elif want_item['groups'] is not None:
                        for group in want_item['groups']:
                            want_item['group'] = group
                            locald_group_params.append(want_item.copy())

        purge_params = list()
        if self._module.params['purge']:
            want_users = [x['name'] for x in self._want]
            have_users = [x['name'] for x in self._have]
            for item in set(have_users).difference(set(want_users)):
                if item != 'admin':
                    purge_params.append({'name': item})

        self._result['xml'] = []
        _edit_filter_list = list()
        if opcode is not None:
            if locald_params:
                _edit_filter_list.append(build_xml('aaa', xmap=self._locald_meta,
                                                   params=locald_params, opcode=opcode))

            if locald_group_params:
                _edit_filter_list.append(build_xml('aaa', xmap=self._locald_group_meta,
                                                   params=locald_group_params, opcode=opcode))

            if purge_params:
                _edit_filter_list.append(build_xml('aaa', xmap=self._locald_meta,
                                                   params=purge_params, opcode="delete"))

        diff = None
        if _edit_filter_list:
            commit = not self._module.check_mode
            diff = load_config(self._module, _edit_filter_list, commit=commit, running=running,
                               nc_get_filter=_get_filter)

        if diff:
            if self._module._diff:
                self._result['diff'] = dict(prepared=diff)

            self._result['xml'] = _edit_filter_list
            self._result['changed'] = True

    def run(self):
        self.map_params_to_obj()
        self.map_obj_to_xml_rpc()

        return self._result


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),

        configured_password=dict(no_log=True),
        update_password=dict(default='always', choices=['on_create', 'always']),

        admin=dict(type='bool', default=False),

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

    mutually_exclusive = [('name', 'aggregate'), ('public_key', 'public_key_contents'), ('group', 'groups')]

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec, aliases=['users', 'collection'],
                       mutually_exclusive=mutually_exclusive),
        purge=dict(type='bool', default=False)
    )

    argument_spec.update(element_spec)
    argument_spec.update(iosxr_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    if (module.params['public_key_contents'] or module.params['public_key']):
        if not HAS_B64:
            module.fail_json(
                msg='library base64 is required but does not appear to be '
                    'installed. It can be installed using `pip install base64`'
            )
        if paramiko is None:
            module.fail_json(
                msg='library paramiko is required but does not appear to be '
                    'installed. It can be installed using `pip install paramiko`'
            )

    result = {'changed': False, 'warnings': []}
    if module.params['password'] and not module.params['configured_password']:
        result['warnings'].append(
            'The "password" argument is used to authenticate the current connection. ' +
            'To set a user password use "configured_password" instead.'
        )

    config_object = None
    if is_cliconf(module):
        # Commenting the below cliconf deprecation support call for Ansible 2.9 as it'll be continued to be supported
        # module.deprecate("cli support for 'iosxr_interface' is deprecated. Use transport netconf instead",
        #                  version='2.9')
        config_object = CliConfiguration(module, result)
    elif is_netconf(module):
        config_object = NCConfiguration(module, result)

    if config_object:
        result = config_object.run()

    if module.params['public_key_contents'] or module.params['public_key']:
        pubkey_object = PublicKeyManager(module, result)
        result = pubkey_object.run()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
