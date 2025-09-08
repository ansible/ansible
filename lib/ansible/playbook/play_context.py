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

from ansible import constants as C
from ansible import context
from ansible.playbook.attribute import FieldAttribute
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

    # base
    module_compression = FieldAttribute(isa='string', default=C.DEFAULT_MODULE_COMPRESSION)
    shell = FieldAttribute(isa='string')
    executable = FieldAttribute(isa='string', default=C.DEFAULT_EXECUTABLE)

    # connection fields, some are inherited from Base:
    # (connection, port, remote_user, environment, no_log)
    remote_addr = FieldAttribute(isa='string')
    password = FieldAttribute(isa='string')
    timeout = FieldAttribute(isa='int', default=C.DEFAULT_TIMEOUT)
    connection_user = FieldAttribute(isa='string')
    private_key_file = FieldAttribute(isa='string', default=C.DEFAULT_PRIVATE_KEY_FILE)
    pipelining = FieldAttribute(isa='bool', default=C.ANSIBLE_PIPELINING)

    # networking modules
    network_os = FieldAttribute(isa='string')

    # FIXME: docker - remove these
    docker_extra_args = FieldAttribute(isa='string')

    # ???
    connection_lockfd = FieldAttribute(isa='int')

    # privilege escalation fields
    become = FieldAttribute(isa='bool')
    become_method = FieldAttribute(isa='string')
    become_user = FieldAttribute(isa='string')
    become_pass = FieldAttribute(isa='string')
    become_exe = FieldAttribute(isa='string', default=C.DEFAULT_BECOME_EXE)
    become_flags = FieldAttribute(isa='string', default=C.DEFAULT_BECOME_FLAGS)
    prompt = FieldAttribute(isa='string')

    start_at_task = FieldAttribute(isa='string')
    step = FieldAttribute(isa='bool', default=False)

    # "PlayContext.force_handlers should not be used, the calling code should be using play itself instead"
    force_handlers = FieldAttribute(isa='bool', default=False)

    def __init__(self, play=None, passwords=None, connection_lockfd=None):
        # Note: play is really not optional.  The only time it could be omitted is when we create
        # a PlayContext just so we can invoke its deserialize method to load it from a serialized
        # data source.

        super(PlayContext, self).__init__()

        if passwords is None:
            passwords = {}

        self.password = passwords.get('conn_pass', '')
        self.become_pass = passwords.get('become_pass', '')

        self._become_plugin = None

        self.prompt = ''
        self.success_key = ''

        # a file descriptor to be used during locking operations
        self.connection_lockfd = connection_lockfd

        # set options before play to allow play to override them
        if context.CLIARGS:
            self.set_attributes_from_cli()
        else:
            self._internal_verbosity = 0

        if play:
            self.set_attributes_from_play(play)

    def set_attributes_from_plugin(self, plugin):
        # generic derived from connection plugin, temporary for backwards compat, in the end we should not set play_context properties

        # get options for plugins
        options = C.config.get_configuration_definitions(plugin.plugin_type, plugin._load_name)
        for option in options:
            if option:
                flag = options[option].get('name')
                if flag:
                    setattr(self, flag, plugin.get_option(flag))

    def set_attributes_from_play(self, play):
        self.force_handlers = play.force_handlers

    def set_attributes_from_cli(self):
        """
        Configures this connection information instance with data from
        options specified by the user on the command line. These have a
        lower precedence than those set on the play or host.
        """
        if context.CLIARGS.get('timeout', False):
            self.timeout = int(context.CLIARGS['timeout'])

        # From the command line.  These should probably be used directly by plugins instead
        # For now, they are likely to be moved to FieldAttribute defaults
        self.private_key_file = context.CLIARGS.get('private_key_file')  # Else default
        self._internal_verbosity = context.CLIARGS.get('verbosity')  # Else default

        # Not every cli that uses PlayContext has these command line args so have a default
        self.start_at_task = context.CLIARGS.get('start_at_task', None)  # Else default

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
                setattr(new_info, attr, attr_val)

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
                    setattr(new_info, 'executable', variables.get(exe_var))

        attrs_considered = []
        for (attr, variable_names) in C.MAGIC_VARIABLE_MAPPING.items():
            for variable_name in variable_names:
                if attr in attrs_considered:
                    continue
                # if delegation task ONLY use delegated host vars, avoid delegated FOR host vars
                if task.delegate_to is not None:
                    if isinstance(delegated_vars, dict) and variable_name in delegated_vars:
                        setattr(new_info, attr, delegated_vars[variable_name])
                        attrs_considered.append(attr)
                elif variable_name in variables:
                    setattr(new_info, attr, variables[variable_name])
                    attrs_considered.append(attr)
                # no else, as no other vars should be considered

        # become legacy updates -- from inventory file (inventory overrides
        # commandline)
        for become_pass_name in C.MAGIC_VARIABLE_MAPPING.get('become_pass'):
            if become_pass_name in variables:
                break

        # make sure we get port defaults if needed
        if new_info.port is None and C.DEFAULT_REMOTE_PORT is not None:
            new_info.port = int(C.DEFAULT_REMOTE_PORT)

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
                    setattr(new_info, 'connection', 'local')
                elif getattr(new_info, 'connection', None) == 'local' and (not remote_addr_local or not inv_hostname_local):
                    setattr(new_info, 'connection', C.DEFAULT_TRANSPORT)

        # we store original in 'connection_user' for use of network/other modules that fallback to it as login user
        # connection_user to be deprecated once connection=local is removed for, as local resets remote_user
        if new_info.connection == 'local':
            if not new_info.connection_user:
                new_info.connection_user = new_info.remote_user

        # for case in which connection plugin still uses pc.remote_addr and in it's own options
        # specifies 'default: inventory_hostname', but never added to vars:
        if new_info.remote_addr == 'inventory_hostname':
            new_info.remote_addr = variables.get('inventory_hostname')
            display.warning('The "%s" connection plugin has an improperly configured remote target value, '
                            'forcing "inventory_hostname" templated value instead of the string' % new_info.connection)

        if task.check_mode is not None:
            new_info.check_mode = task.check_mode

        if task.diff is not None:
            new_info.diff = task.diff

        return new_info

    def set_become_plugin(self, plugin):
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
