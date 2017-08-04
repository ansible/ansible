#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Chatham Financial <oss@chathamfinancial.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_user
short_description: Adds or removes users to RabbitMQ
description:
  - Add or remove users to RabbitMQ and assign permissions
version_added: "1.1"
author: '"Chris Hoffman (@chrishoffman)"'
options:
  user:
    description:
      - Name of user to add
    required: true
    default: null
    aliases: [username, name]
  password:
    description:
      - Password of user to add.
      - To change the password of an existing user for RabbitMQ < 3.6.5,
        you must also specify C(force=yes).
    required: false
    default: null
  tags:
    description:
      - User tags specified as comma delimited
    required: false
    default: null
  permissions:
    description:
      - a list of dicts, each dict contains vhost, configure_priv, write_priv, and read_priv,
        and represents a permission rule for that vhost.
      - This option should be preferable when you care about all permissions of the user.
      - You should use vhost, configure_priv, write_priv, and read_priv options instead
        if you care about permissions for just some vhosts.
    required: false
    default: []
  vhost:
    description:
      - vhost to apply access privileges.
      - This option will be ignored when permissions option is used.
    required: false
    default: /
  node:
    description:
      - erlang node name of the rabbit we wish to configure
    required: false
    default: rabbit
    version_added: "1.2"
  configure_priv:
    description:
      - Regular expression to restrict configure actions on a resource
        for the specified vhost.
      - By default all actions are restricted.
      - This option will be ignored when permissions option is used.
    required: false
    default: ^$
  write_priv:
    description:
      - Regular expression to restrict configure actions on a resource
        for the specified vhost.
      - By default all actions are restricted.
      - This option will be ignored when permissions option is used.
    required: false
    default: ^$
  read_priv:
    description:
      - Regular expression to restrict configure actions on a resource
        for the specified vhost.
      - By default all actions are restricted.
      - This option will be ignored when permissions option is used.
    required: false
    default: ^$
  force:
    description:
      - Deletes and recreates the user.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  state:
    description:
      - Specify if user is to be added or removed
    required: false
    default: present
    choices: [present, absent]
'''

EXAMPLES = '''
# Add user to server and assign full access control on / vhost.
# The user might have permission rules for other vhost but you don't care.
- rabbitmq_user:
    user: joe
    password: changeme
    vhost: /
    configure_priv: .*
    read_priv: .*
    write_priv: .*
    state: present

# Add user to server and assign full access control on / vhost.
# The user doesn't have permission rules for other vhosts
- rabbitmq_user:
    user: joe
    password: changeme
    permissions:
      - vhost: /
        configure_priv: .*
        read_priv: .*
        write_priv: .*
    state: present
'''

from ansible.module_utils.basic import AnsibleModule


class RabbitMqUser(object):
    def __init__(self, module, username, password, tags, permissions,
                 node, bulk_permissions=False):
        self.module = module
        self.username = username
        self.password = password
        self.node = node
        if not tags:
            self.tags = list()
        else:
            self.tags = tags.split(',')

        self.permissions = permissions
        self.bulk_permissions = bulk_permissions

        self._tags = None
        self._permissions = []
        self._rabbitmqctl = module.get_bin_path('rabbitmqctl', True)

    def _exec(self, args, run_in_check_mode=False, check_rc=True):
        if not self.module.check_mode or run_in_check_mode:
            cmd = [self._rabbitmqctl, '-q']
            if self.node is not None:
                cmd.extend(['-n', self.node])
            rc, out, err = self.module.run_command(cmd + args, check_rc=check_rc)
            return out.splitlines(), rc
        return list(), 0

    def get(self):
        users, rc = self._exec(['list_users'], run_in_check_mode=True)

        for user_tag in users:
            if '\t' not in user_tag:
                continue

            user, tags = user_tag.split('\t')

            if user == self.username:
                for c in ['[', ']', ' ']:
                    tags = tags.replace(c, '')

                if tags != '':
                    self._tags = tags.split(',')
                else:
                    self._tags = list()

                self._permissions = self._get_permissions()
                return True
        return False

    def _get_permissions(self):
        perms_out, rc = self._exec(['list_user_permissions', self.username], run_in_check_mode=True)

        perms_list = list()
        for perm in perms_out:
            vhost, configure_priv, write_priv, read_priv = perm.split('\t')
            if not self.bulk_permissions:
                if vhost == self.permissions[0]['vhost']:
                    perms_list.append(dict(vhost=vhost, configure_priv=configure_priv,
                                           write_priv=write_priv, read_priv=read_priv))
                    break
            else:
                perms_list.append(dict(vhost=vhost, configure_priv=configure_priv,
                                       write_priv=write_priv, read_priv=read_priv))
        return perms_list

    def add(self):
        if self.password is not None:
            self._exec(['add_user', self.username, self.password])
        else:
            self._exec(['add_user', self.username, ''])
            self._exec(['clear_password', self.username])

    def delete(self):
        self._exec(['delete_user', self.username])

    def set_tags(self):
        self._exec(['set_user_tags', self.username] + self.tags)

    def set_permissions(self):
        for permission in self._permissions:
            if permission not in self.permissions:
                cmd = ['clear_permissions', '-p']
                cmd.append(permission['vhost'])
                cmd.append(self.username)
                self._exec(cmd)
        for permission in self.permissions:
            if permission not in self._permissions:
                cmd = ['set_permissions', '-p']
                cmd.append(permission['vhost'])
                cmd.append(self.username)
                cmd.append(permission['configure_priv'])
                cmd.append(permission['write_priv'])
                cmd.append(permission['read_priv'])
                self._exec(cmd)

    def has_tags_modifications(self):
        return set(self.tags) != set(self._tags)

    def has_permissions_modifications(self):
        return sorted(self._permissions) != sorted(self.permissions)

    def has_password_modification(self):
        _, rc = self._exec(['authenticate_user', self.username, self.password], run_in_check_mode=True, check_rc=False)
        # 'EX_NOUSER' (The user specified does not exist) from https://github.com/rabbitmq/rabbitmq-server/blob/master/include/rabbit_cli.hrl#L70
        return rc == 67

    def set_password(self):
        self._exec(['change_password', self.username, self.password])

def main():
    arg_spec = dict(
        user=dict(required=True, aliases=['username', 'name']),
        password=dict(default=None, no_log=True),
        tags=dict(default=None),
        permissions=dict(default=list(), type='list'),
        vhost=dict(default='/'),
        configure_priv=dict(default='^$'),
        write_priv=dict(default='^$'),
        read_priv=dict(default='^$'),
        force=dict(default='no', type='bool'),
        state=dict(default='present', choices=['present', 'absent']),
        node=dict(default=None)
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    username = module.params['user']
    password = module.params['password']
    tags = module.params['tags']
    permissions = module.params['permissions']
    vhost = module.params['vhost']
    configure_priv = module.params['configure_priv']
    write_priv = module.params['write_priv']
    read_priv = module.params['read_priv']
    force = module.params['force']
    state = module.params['state']
    node = module.params['node']

    bulk_permissions = True
    if not permissions:
        perm = {
            'vhost': vhost,
            'configure_priv': configure_priv,
            'write_priv': write_priv,
            'read_priv': read_priv
        }
        permissions.append(perm)
        bulk_permissions = False

    rabbitmq_user = RabbitMqUser(module, username, password, tags, permissions,
                                 node, bulk_permissions=bulk_permissions)

    result = dict(changed=False, user=username, state=state)

    if rabbitmq_user.get():
        if state == 'absent':
            rabbitmq_user.delete()
            result['changed'] = True
        else:
            if force:
                rabbitmq_user.delete()
                rabbitmq_user.add()
                rabbitmq_user.get()
                result['changed'] = True

            if rabbitmq_user.has_tags_modifications():
                rabbitmq_user.set_tags()
                result['changed'] = True

            if rabbitmq_user.has_permissions_modifications():
                rabbitmq_user.set_permissions()
                result['changed'] = True

            if rabbitmq_user.has_password_modification():
                rabbitmq_user.set_password()
                result['changed'] = True
    elif state == 'present':
        rabbitmq_user.add()
        rabbitmq_user.set_tags()
        rabbitmq_user.set_permissions()
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
