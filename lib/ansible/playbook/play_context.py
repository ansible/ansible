# -*- coding: utf-8 -*-

# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from __future__ import annotations

import typing as t

from ansible import constants as C
from ansible import context
from ansible.playbook.attribute import FieldAttribute, NonInheritableFieldAttribute, _DeprecatedFieldAttribute
from ansible.playbook.base import Base
from ansible.utils.display import Display


display = Display()


__all__ = ['PlayContext']


TASK_ATTRIBUTE_OVERRIDES = (
    'become',
    'become_user',
    'become_pass',
    'become_method',
    'become_flags',
    'connection',
    'docker_extra_args',  # TODO: remove
    'delegate_to',
    'no_log',
    'remote_user',
)

RESET_VARS = (
    'ansible_connection',
    'ansible_user',
    'ansible_host',
    'ansible_port',

    # TODO: ???
    'ansible_docker_extra_args',
    'ansible_ssh_host',
    'ansible_ssh_pass',
    'ansible_ssh_port',
    'ansible_ssh_user',
    'ansible_ssh_private_key_file',
    'ansible_ssh_pipelining',
    'ansible_ssh_executable',
)


class PlayContext(Base):

    """
    This class is used to consolidate the connection information for
    hosts in a play and child tasks, where the task may override some
    connection/authentication information.
    """

    _post_validate_object = True

    # Attributes inherited from Base, redeclared here so PlayContext lists everything it exposes. These must match the
    # Base definition unless noted otherwise. When one of these is removed it must be replaced with
    # _RemovedFieldAttribute, as simply deleting the declaration would expose the Base attribute again.
    name = NonInheritableFieldAttribute(isa='string', default='', always_post_validate=True)
    connection = FieldAttribute(isa='string', default=context.cliargs_deferred_get('connection'))
    port = FieldAttribute(isa='int')
    remote_user = FieldAttribute(isa='string', default=context.cliargs_deferred_get('remote_user'))
    vars = NonInheritableFieldAttribute(isa='dict', priority=100, static=True, default=dict)
    no_log = FieldAttribute(isa='bool', default=C.DEFAULT_NO_LOG)
    check_mode = FieldAttribute(isa='bool', default=context.cliargs_deferred_get('check'))
    diff = FieldAttribute(isa='bool', default=context.cliargs_deferred_get('diff'))
    # the connection timeout (-T), not the task timeout keyword which Base defines under the same name
    timeout = FieldAttribute(isa='int', default=C.DEFAULT_TIMEOUT)
    # the become fields have no CLI defaults here, the CLI values arrive through the task/play overrides
    become = FieldAttribute(isa='bool')
    become_method = FieldAttribute(isa='string')
    become_user = FieldAttribute(isa='string')
    # deprecated: description='replace the deprecated PlayContext attribute with _RemovedFieldAttribute' core_version='2.26'
    become_flags = _DeprecatedFieldAttribute(
        isa='string', default=C.DEFAULT_BECOME_FLAGS, version='2.26',
        help_text="Use the become plugin's 'become_flags' option instead, e.g. connection.become.get_option('become_flags').",
    )
    become_exe = _DeprecatedFieldAttribute(
        isa='string', default=C.DEFAULT_BECOME_EXE, version='2.26',
        help_text="Use the become plugin's 'become_exe' option instead, e.g. connection.become.get_option('become_exe').",
    )
    module_defaults = _DeprecatedFieldAttribute(
        isa='list', extend=True, prepend=True, version='2.26',
        help_text="Never populated on PlayContext, use the task's 'module_defaults' attribute instead, e.g. task.module_defaults.",
    )
    environment = _DeprecatedFieldAttribute(
        isa='list', extend=True, prepend=True, version='2.26',
        help_text="Never populated on PlayContext, use the task's 'environment' attribute instead, e.g. task.environment.",
    )
    run_once = _DeprecatedFieldAttribute(
        isa='bool', version='2.26',
        help_text="Never populated on PlayContext, use the task's 'run_once' attribute instead, e.g. task.run_once.",
    )
    ignore_errors = _DeprecatedFieldAttribute(
        isa='bool', version='2.26',
        help_text="Never populated on PlayContext, use the task's 'ignore_errors' attribute instead, e.g. task.ignore_errors.",
    )
    ignore_unreachable = _DeprecatedFieldAttribute(
        isa='bool', version='2.26',
        help_text="Never populated on PlayContext, use the task's 'ignore_unreachable' attribute instead, e.g. task.ignore_unreachable.",
    )
    any_errors_fatal = _DeprecatedFieldAttribute(
        isa='bool', default=C.ANY_ERRORS_FATAL, version='2.26',
        help_text="Never populated on PlayContext, use the task's 'any_errors_fatal' attribute instead, e.g. task.any_errors_fatal.",
    )
    throttle = _DeprecatedFieldAttribute(
        isa='int', default=0, version='2.26',
        help_text="Never populated on PlayContext, use the task's 'throttle' attribute instead, e.g. task.throttle.",
    )
    debugger = _DeprecatedFieldAttribute(
        isa='string', version='2.26',
        help_text="Never populated on PlayContext, use the task's 'debugger' attribute instead, e.g. task.debugger.",
    )

    # Attributes defined only by PlayContext. These can simply be deleted when removed.
    shell = FieldAttribute(isa='string')
    executable = FieldAttribute(isa='string', default=C.DEFAULT_EXECUTABLE)
    remote_addr = FieldAttribute(isa='string')
    password = FieldAttribute(isa='string')
    connection_user = FieldAttribute(isa='string')
    private_key_file = FieldAttribute(isa='string', default=C.DEFAULT_PRIVATE_KEY_FILE)
    network_os = FieldAttribute(isa='string')
    docker_extra_args = FieldAttribute(isa='string')
    become_pass = FieldAttribute(isa='string')
    # These are populated from MAGIC_VARIABLE_MAPPING or TASK_ATTRIBUTE_OVERRIDES and fed back into the task vars by
    # update_vars(). A new mechanism for deprecating those mapping vars is needed before these can be deprecated.
    module_compression = FieldAttribute(isa='string', default=C.DEFAULT_MODULE_COMPRESSION)
    pipelining = FieldAttribute(isa='bool', default=C.ANSIBLE_PIPELINING)
    ssh_executable = FieldAttribute(isa='string')
    ssh_common_args = FieldAttribute(isa='string')
    sftp_extra_args = FieldAttribute(isa='string')
    scp_extra_args = FieldAttribute(isa='string')
    ssh_extra_args = FieldAttribute(isa='string')
    ssh_transfer_method = FieldAttribute(isa='string')
    delegate_to = FieldAttribute(isa='string')
    # deprecated: description='remove the deprecated PlayContext attribute' core_version='2.26'
    connection_lockfd = _DeprecatedFieldAttribute(isa='int', version='2.26')
    prompt = _DeprecatedFieldAttribute(
        isa='string', version='2.26',
        help_text="Use the become plugin's 'prompt' attribute instead, e.g. connection.become.prompt.",
    )
    start_at_task = _DeprecatedFieldAttribute(
        isa='string', version='2.26',
        help_text="Use the command line option instead, e.g. ansible.context.CLIARGS.get('start_at_task').",
    )
    step = _DeprecatedFieldAttribute(
        isa='bool', default=False, version='2.26',
        help_text="Use the command line option instead, e.g. ansible.context.CLIARGS.get('step').",
    )
    # 2.7 was the last version of Ansible where this attribute was relevant. No
    # public collections reference it, we don't add help_text because there is
    # no public alterantive.
    force_handlers = _DeprecatedFieldAttribute(isa='bool', default=False, version='2.26')
    success_key = _DeprecatedFieldAttribute(
        isa='string', default='', version='2.26',
        help_text="Use the become plugin's 'success_key' attribute instead, e.g. connection.become.success_key.",
    )

    def __init__(self, play=None, passwords=None, connection_lockfd=None):
        # Note: play is really not optional.  The only time it could be omitted is when we create
        # a PlayContext just so we can invoke its deserialize method to load it from a serialized
        # data source.

        super(PlayContext, self).__init__()

        if passwords is None:
            passwords = {}

        self._set_field('password', passwords.get('conn_pass', ''))
        self._set_field('become_pass', passwords.get('become_pass', ''))

        self._become_plugin = None  # deprecated: description='remove the deprecated PlayContext attribute' core_version='2.26'

        # a file descriptor to be used during locking operations
        self._connection_lockfd = connection_lockfd  # deprecated: description='remove the deprecated PlayContext attribute' core_version='2.26'

        # set options before play to allow play to override them
        if context.CLIARGS:
            self.set_attributes_from_cli()

        if play:
            self.set_attributes_from_play(play)

    def set_attributes_from_play(self, play):
        self._force_handlers = play.force_handlers  # deprecated: description='remove the deprecated PlayContext attribute' core_version='2.26'

    def _set_field(self, name: str, value: t.Any) -> None:
        """
        Set a field attribute, populating deprecated ones without triggering their deprecation warning.
        Names which are not (or no longer) fields are ignored, so TASK_ATTRIBUTE_OVERRIDES and MAGIC_VARIABLE_MAPPING
        need not change when an attribute is removed.
        """
        if (attribute := self.fattributes.get(name)) is None:
            return  # unknown, or removed via _RemovedFieldAttribute which excludes it from fattributes

        if isinstance(attribute, _DeprecatedFieldAttribute):
            setattr(self, f'_{name}', value)
        else:
            setattr(self, name, value)

    def set_attributes_from_cli(self):
        """
        Configures this connection information instance with data from
        options specified by the user on the command line. These have a
        lower precedence than those set on the play or host.
        """
        if context.CLIARGS.get('timeout', False):
            self._set_field('timeout', int(context.CLIARGS['timeout']))

        # From the command line.  These should probably be used directly by plugins instead
        # For now, they are likely to be moved to FieldAttribute defaults
        self._set_field('private_key_file', context.CLIARGS.get('private_key_file'))  # Else default

        # Not every cli that uses PlayContext has these command line args so have a default
        # deprecated: description='remove the deprecated PlayContext attribute' core_version='2.26'
        self._start_at_task = context.CLIARGS.get('start_at_task', None)

    def set_task_and_variable_override(self, task, variables, templar):
        """
        Sets attributes from the task if they are set, which will override
        those from the play.

        :arg task: the task object with the parameters that were set on it
        :arg variables: variables from inventory
        :arg templar: templar instance if templating variables is needed
        """

        new_info = self.copy()

        # loop through a subset of attributes on the task object and set
        # connection fields based on their values
        for attr in TASK_ATTRIBUTE_OVERRIDES:
            if (attr_val := getattr(task, attr, None)) is not None:
                new_info._set_field(attr, attr_val)

        # next, use the MAGIC_VARIABLE_MAPPING dictionary to update this
        # connection info object with 'magic' variables from the variable list.
        # If the value 'ansible_delegated_vars' is in the variables, it means
        # we have a delegated-to host, so we check there first before looking
        # at the variables in general
        if task.delegate_to is not None:
            # In the case of a loop, the delegated_to host may have been
            # templated based on the loop variable, so we try and locate
            # the host name in the delegated variable dictionary here
            delegated_vars = variables.get('ansible_delegated_vars', dict()).get(task.delegate_to, dict())

            delegated_transport = C.DEFAULT_TRANSPORT
            for transport_var in C.MAGIC_VARIABLE_MAPPING.get('connection'):
                if transport_var in delegated_vars:
                    delegated_transport = delegated_vars[transport_var]
                    break

            # make sure this delegated_to host has something set for its remote
            # address, otherwise we default to connecting to it by name. This
            # may happen when users put an IP entry into their inventory, or if
            # they rely on DNS for a non-inventory hostname
            for address_var in ('ansible_%s_host' % delegated_transport,) + C.MAGIC_VARIABLE_MAPPING.get('remote_addr'):
                if address_var in delegated_vars:
                    break
            else:
                display.debug("no remote address found for delegated host %s\nusing its name, so success depends on DNS resolution" % task.delegate_to)
                delegated_vars['ansible_host'] = task.delegate_to

            # reset the port back to the default if none was specified, to prevent
            # the delegated host from inheriting the original host's setting
            for port_var in ('ansible_%s_port' % delegated_transport,) + C.MAGIC_VARIABLE_MAPPING.get('port'):
                if port_var in delegated_vars:
                    break
            else:
                if delegated_transport == 'winrm':
                    delegated_vars['ansible_port'] = 5986
                else:
                    delegated_vars['ansible_port'] = C.DEFAULT_REMOTE_PORT

            # and likewise for the remote user
            for user_var in ('ansible_%s_user' % delegated_transport,) + C.MAGIC_VARIABLE_MAPPING.get('remote_user'):
                if user_var in delegated_vars and delegated_vars[user_var]:
                    break
            else:
                delegated_vars['ansible_user'] = task.remote_user or self.remote_user
        else:
            delegated_vars = dict()

            # setup shell
            for exe_var in C.MAGIC_VARIABLE_MAPPING.get('executable'):
                if exe_var in variables:
                    new_info._set_field('executable', variables.get(exe_var))

        attrs_considered = []
        for (attr, variable_names) in C.MAGIC_VARIABLE_MAPPING.items():
            for variable_name in variable_names:
                if attr in attrs_considered:
                    continue
                # if delegation task ONLY use delegated host vars, avoid delegated FOR host vars
                if task.delegate_to is not None:
                    if isinstance(delegated_vars, dict) and variable_name in delegated_vars:
                        new_info._set_field(attr, delegated_vars[variable_name])
                        attrs_considered.append(attr)
                elif variable_name in variables:
                    new_info._set_field(attr, variables[variable_name])
                    attrs_considered.append(attr)
                # no else, as no other vars should be considered

        # become legacy updates -- from inventory file (inventory overrides
        # commandline)
        for become_pass_name in C.MAGIC_VARIABLE_MAPPING.get('become_pass'):
            if become_pass_name in variables:
                break

        # make sure we get port defaults if needed
        if new_info.port is None and C.DEFAULT_REMOTE_PORT is not None:
            new_info._set_field('port', int(C.DEFAULT_REMOTE_PORT))

        # special overrides for the connection setting
        if len(delegated_vars) > 0:
            # in the event that we were using local before make sure to reset the
            # connection type to the default transport for the delegated-to host,
            # if not otherwise specified
            for connection_type in C.MAGIC_VARIABLE_MAPPING.get('connection'):
                if connection_type in delegated_vars:
                    break
            else:
                remote_addr_local = new_info.remote_addr in C.LOCALHOST
                inv_hostname_local = delegated_vars.get('inventory_hostname') in C.LOCALHOST
                if remote_addr_local and inv_hostname_local:
                    new_info._set_field('connection', 'local')
                elif getattr(new_info, 'connection', None) == 'local' and (not remote_addr_local or not inv_hostname_local):
                    new_info._set_field('connection', C.DEFAULT_TRANSPORT)

        # we store original in 'connection_user' for use of network/other modules that fallback to it as login user
        # connection_user to be deprecated once connection=local is removed for, as local resets remote_user
        if new_info.connection == 'local':
            if not new_info.connection_user:
                new_info._set_field('connection_user', new_info.remote_user)

        # for case in which connection plugin still uses pc.remote_addr and in it's own options
        # specifies 'default: inventory_hostname', but never added to vars:
        if new_info.remote_addr == 'inventory_hostname':
            new_info._set_field('remote_addr', variables.get('inventory_hostname'))
            display.warning('The "%s" connection plugin has an improperly configured remote target value, '
                            'forcing "inventory_hostname" templated value instead of the string' % new_info.connection)

        if task.check_mode is not None:
            new_info._set_field('check_mode', task.check_mode)

        if task.diff is not None:
            new_info._set_field('diff', task.diff)

        return new_info

    # deprecated: description='remove the deprecated PlayContext attribute' core_version='2.26'
    def set_become_plugin(self, plugin):
        display.deprecated(
            msg='The PlayContext.set_become_plugin() method is deprecated.',
            version='2.26',
            help_text="Use the connection plugin's set_become_plugin() method instead, e.g. connection.set_become_plugin(become_plugin).",
        )

        self._become_plugin = plugin

    def update_vars(self, variables):
        """
        Adds 'magic' variables relating to connections to the variable dictionary provided.
        In case users need to access from the play, this is a legacy from runner.
        """

        for prop, var_list in C.MAGIC_VARIABLE_MAPPING.items():
            try:
                if 'become' in prop:
                    continue

                var_val = getattr(self, prop)
                for var_opt in var_list:
                    if var_opt not in variables and var_val is not None:
                        variables[var_opt] = var_val
            except AttributeError:
                continue

    def deserialize(self, data):
        """Do not use this method. Backward compatibility for network connections plugins that rely on it."""
        self.from_attrs(data)
