#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Chatham Financial <oss@chathamfinancial.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_user
short_description: Manage RabbitMQ users
description:
  - Add or remove users to RabbitMQ and assign permissions
version_added: "1.1"
author: Chris Hoffman (@chrishoffman)
options:
  user:
    description:
      - Name of user to add
    required: true
    aliases: [username, name]
  password:
    description:
      - Password of user to add.
      - To change the password of an existing user, you must also specify
        C(update_password=always).
  tags:
    description:
      - User tags specified as comma delimited
  permissions:
    description:
      - a list of dicts, each dict contains vhost, configure_priv, write_priv, and read_priv,
        and represents a permission rule for that vhost.
      - This option should be preferable when you care about all permissions of the user.
      - You should use vhost, configure_priv, write_priv, and read_priv options instead
        if you care about permissions for just some vhosts.
    default: []
  vhost:
    description:
      - vhost to apply access privileges.
      - This option will be ignored when permissions option is used.
    default: /
  node:
    description:
      - erlang node name of the rabbit we wish to configure
    default: rabbit
    version_added: "1.2"
  configure_priv:
    description:
      - Regular expression to restrict configure actions on a resource
        for the specified vhost.
      - By default all actions are restricted.
      - This option will be ignored when permissions option is used.
    default: ^$
  write_priv:
    description:
      - Regular expression to restrict configure actions on a resource
        for the specified vhost.
      - By default all actions are restricted.
      - This option will be ignored when permissions option is used.
    default: ^$
  read_priv:
    description:
      - Regular expression to restrict configure actions on a resource
        for the specified vhost.
      - By default all actions are restricted.
      - This option will be ignored when permissions option is used.
    default: ^$
  force:
    description:
      - Deletes and recreates the user.
    type: bool
    default: 'no'
  state:
    description:
      - Specify if user is to be added or removed
    default: present
    choices: [present, absent]
  update_password:
    description:
      - C(on_create) will only set the password for newly created users.  C(always) will update passwords if they differ.
    required: false
    default: on_create
    choices: [ on_create, always ]
    version_added: "2.6"
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

import distutils.version
import json
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.collections import count


def normalized_permissions(vhost_permission_list):
    """Older versions of RabbitMQ output permissions with slightly different names.

    In older versions of RabbitMQ, the names of the permissions had the `_priv` suffix, which was removed in versions
    >= 3.7.6. For simplicity we only check the `configure` permission. If it's in the old format then all the other
    ones will be wrong too.
    """
    for vhost_permission in vhost_permission_list:
        if 'configure_priv' in vhost_permission:
            yield {
                'configure': vhost_permission['configure_priv'],
                'read': vhost_permission['read_priv'],
                'write': vhost_permission['write_priv'],
                'vhost': vhost_permission['vhost']
            }
        else:
            yield vhost_permission


def as_permission_dict(vhost_permission_list):
    return dict([(vhost_permission['vhost'], vhost_permission) for vhost_permission
                 in normalized_permissions(vhost_permission_list)])


def only(vhost, vhost_permissions):
    return {vhost: vhost_permissions.get(vhost, {})}


def first(iterable):
    return next(iter(iterable))


class RabbitMqUser(object):
    def __init__(self, module, username, password, tags, permissions,
                 node, bulk_permissions=False):
        self.module = module
        self.username = username
        self.password = password or ''
        self.node = node
        self.tags = list() if not tags else tags.replace(' ', '').split(',')
        self.permissions = as_permission_dict(permissions)
        self.bulk_permissions = bulk_permissions

        self.existing_tags = None
        self.existing_permissions = dict()
        self._rabbitmqctl = module.get_bin_path('rabbitmqctl', True)
        self._version = self._check_version()

    def _check_version(self):
        """Get the version of the RabbitMQ server."""
        version = self._rabbitmq_version_post_3_7(fail_on_error=False)
        if not version:
            version = self._rabbitmq_version_pre_3_7(fail_on_error=False)
        if not version:
            self.module.fail_json(msg="Could not determine the version of the RabbitMQ server.")
        return version

    def _fail(self, msg, stop_execution=False):
        if stop_execution:
            self.module.fail_json(msg=msg)
        # This is a dummy return to prevent linters from throwing errors.
        return None

    def _rabbitmq_version_post_3_7(self, fail_on_error=False):
        """Use the JSON formatter to get a machine readable output of the version.

        At this point we do not know which RabbitMQ server version we are dealing with and which
        version of `rabbitmqctl` we are using, so we will try to use the JSON formatter and see
        what happens. In some versions of
        """
        def int_list_to_str(ints):
            return ''.join([chr(i) for i in ints])

        rc, output, err = self._exec(['status', '--formatter', 'json'], check_rc=False)
        if rc != 0:
            return self._fail(msg="Could not parse the version of the RabbitMQ server, "
                                  "because `rabbitmqctl status` returned no output.",
                              stop_execution=fail_on_error)
        try:
            status_json = json.loads(output)
            if 'rabbitmq_version' in status_json:
                return distutils.version.StrictVersion(status_json['rabbitmq_version'])
            for application in status_json.get('running_applications', list()):
                if application[0] == 'rabbit':
                    if isinstance(application[1][0], int):
                        return distutils.version.StrictVersion(int_list_to_str(application[2]))
                    else:
                        return distutils.version.StrictVersion(application[1])
            return self._fail(msg="Could not find RabbitMQ version of `rabbitmqctl status` command.",
                              stop_execution=fail_on_error)
        except ValueError as e:
            return self._fail(msg="Could not parse output of `rabbitmqctl status` as JSON: {exc}.".format(exc=repr(e)),
                              stop_execution=fail_on_error)

    def _rabbitmq_version_pre_3_7(self, fail_on_error=False):
        """Get the version of the RabbitMQ Server.

        Before version 3.7.6 the `rabbitmqctl` utility did not support the
        `--formatter` flag, so the output has to be parsed using regular expressions.
        """
        version_reg_ex = r"{rabbit,\"RabbitMQ\",\"([0-9]+\.[0-9]+\.[0-9]+)\"}"
        rc, output, err = self._exec(['status'], check_rc=False)
        if rc != 0:
            if fail_on_error:
                self.module.fail_json(msg="Could not parse the version of the RabbitMQ server, because"
                                          " `rabbitmqctl status` returned no output.")
            else:
                return None
        reg_ex_res = re.search(version_reg_ex, output, re.IGNORECASE)
        if not reg_ex_res:
            return self._fail(msg="Could not parse the version of the RabbitMQ server from the output of "
                                  "`rabbitmqctl status` command: {output}.".format(output=output),
                              stop_execution=fail_on_error)
        try:
            return distutils.version.StrictVersion(reg_ex_res.group(1))
        except ValueError as e:
            return self._fail(msg="Could not parse the version of the RabbitMQ server: {exc}.".format(exc=repr(e)),
                              stop_execution=fail_on_error)

    def _exec(self, args, check_rc=True):
        """Execute a command using the `rabbitmqctl` utility.

        By default the _exec call will cause the module to fail, if the error code is non-zero. If the `check_rc`
        flag is set to False, then the exit_code, stdout and stderr will be returned to the calling function to
        perform whatever error handling it needs.

        :param args: the arguments to pass to the `rabbitmqctl` utility
        :param check_rc: when set to True, fail if the utility's exit code is non-zero
        :return: the output of the command or all the outputs plus the error code in case of error
        """
        cmd = [self._rabbitmqctl, '-q']
        if self.node:
            cmd.extend(['-n', self.node])
        rc, out, err = self.module.run_command(cmd + args)
        if check_rc and rc != 0:
            # check_rc is not passed to the `run_command` method directly to allow for more fine grained checking of
            # error messages returned by `rabbitmqctl`.
            user_error_msg_regex = r"(Only root or .* .* run rabbitmqctl)"
            user_error_msg = re.search(user_error_msg_regex, out)
            if user_error_msg:
                self.module.fail_json(msg="Wrong user used to run the `rabbitmqctl` utility: {err}"
                                      .format(err=user_error_msg.group(1)))
            else:
                self.module.fail_json(msg="rabbitmqctl exited with non-zero code: {err}".format(err=err),
                                      rc=rc, stdout=out)
        return out if check_rc else (rc, out, err)

    def get(self):
        """Retrieves the list of registered users from the node.

        If the user is already present, the node will also be queried for the user's permissions.
        If the version of the node is >= 3.7.6 the JSON formatter will be used, otherwise the plaintext will be
        parsed.
        """
        if self._version >= distutils.version.StrictVersion('3.7.6'):
            users = dict([(user_entry['user'], user_entry['tags'])
                          for user_entry in json.loads(self._exec(['list_users', '--formatter', 'json']))])
        else:
            users = self._exec(['list_users'])

            def process_tags(tags):
                if not tags:
                    return list()
                return tags.replace('[', '').replace(']', '').replace(' ', '').strip('\t').split(',')

            users_and_tags = [user_entry.split('\t') for user_entry in users.strip().split('\n')]
            users = dict([(user, process_tags(tags)) for user, tags in users_and_tags])

        self.existing_tags = users.get(self.username, list())
        self.existing_permissions = self._get_permissions() if self.username in users else dict()
        return self.username in users

    def _get_permissions(self):
        """Get permissions of the user from RabbitMQ."""
        if self._version >= distutils.version.StrictVersion('3.7.6'):
            permissions = json.loads(self._exec(['list_user_permissions', self.username, '--formatter', 'json']))
        else:
            output = self._exec(['list_user_permissions', self.username]).strip().split('\n')
            perms_out = [perm.split('\t') for perm in output if perm.strip()]
            # Filter out headers from the output of the command in case they are still present
            perms_out = [perm for perm in perms_out if perm != ["vhost", "configure", "write", "read"]]

            permissions = list()
            for vhost, configure, write, read in perms_out:
                permissions.append(dict(vhost=vhost, configure=configure, write=write, read=read))

        if self.bulk_permissions:
            return as_permission_dict(permissions)
        else:
            return only(first(self.permissions.keys()), as_permission_dict(permissions))

    def check_password(self):
        """Return `True` if the user can authenticate successfully."""
        rc, out, err = self._exec(['authenticate_user', self.username, self.password], check_rc=False)
        return rc == 0

    def add(self):
        self._exec(['add_user', self.username, self.password or ''])
        if not self.password:
            self._exec(['clear_password', self.username])

    def delete(self):
        self._exec(['delete_user', self.username])

    def change_password(self):
        if self.password:
            self._exec(['change_password', self.username, self.password])
        else:
            self._exec(['clear_password', self.username])

    def set_tags(self):
        self._exec(['set_user_tags', self.username] + self.tags)

    def set_permissions(self):
        permissions_to_add = list()
        for vhost, permission_dict in self.permissions.items():
            if permission_dict != self.existing_permissions.get(vhost, {}):
                permissions_to_add.append(permission_dict)

        permissions_to_clear = list()
        for vhost in self.existing_permissions.keys():
            if vhost not in self.permissions:
                permissions_to_clear.append(vhost)

        for vhost in permissions_to_clear:
            cmd = 'clear_permissions -p {vhost} {username}'.format(username=self.username, vhost=vhost)
            self._exec(cmd.split(' '))
        for permissions in permissions_to_add:
            cmd = ('set_permissions -p {vhost} {username} {configure} {write} {read}'
                   .format(username=self.username, **permissions))
            self._exec(cmd.split(' '))
        self.existing_permissions = self._get_permissions()

    def has_tags_modifications(self):
        return set(self.tags) != set(self.existing_tags)

    def has_permissions_modifications(self):
        return self.existing_permissions != self.permissions


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
        node=dict(default='rabbit'),
        update_password=dict(default='on_create', choices=['on_create', 'always'])
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
    update_password = module.params['update_password']

    if permissions:
        vhosts = [permission.get('vhost', '/') for permission in permissions]
        if any([vhost_count > 1 for vhost_count in count(vhosts).values()]):
            module.fail_json(msg="Error parsing vhost permissions: You can't "
                                 "have two permission dicts for the same vhost")
        bulk_permissions = True
    else:
        perm = {
            'vhost': vhost,
            'configure_priv': configure_priv,
            'write_priv': write_priv,
            'read_priv': read_priv
        }
        permissions.append(perm)
        bulk_permissions = False

    for permission in permissions:
        if not permission['vhost']:
            module.fail_json(msg="Error parsing vhost permissions: You can't"
                                 "have an empty vhost when setting permissions")

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
            elif update_password == 'always':
                if not rabbitmq_user.check_password():
                    rabbitmq_user.change_password()
                    result['changed'] = True

            if rabbitmq_user.has_tags_modifications():
                rabbitmq_user.set_tags()
                result['changed'] = True

            if rabbitmq_user.has_permissions_modifications():
                rabbitmq_user.set_permissions()
                result['changed'] = True
    elif state == 'present':
        rabbitmq_user.add()
        rabbitmq_user.set_tags()
        rabbitmq_user.set_permissions()
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
