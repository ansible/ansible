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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pwd
import random
import re
import string
import sys

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.utils.ssh_functions import check_for_controlpersist


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__all__ = ['PlayContext']

# the magic variable mapping dictionary below is used to translate
# host/inventory variables to fields in the PlayContext
# object. The dictionary values are tuples, to account for aliases
# in variable names.

MAGIC_VARIABLE_MAPPING = dict(
    connection=('ansible_connection', ),
    remote_addr=('ansible_ssh_host', 'ansible_host'),
    remote_user=('ansible_ssh_user', 'ansible_user'),
    remote_tmp_dir=('ansible_remote_tmp', ),
    port=('ansible_ssh_port', 'ansible_port'),
    timeout=('ansible_ssh_timeout', 'ansible_timeout'),
    ssh_executable=('ansible_ssh_executable', ),
    accelerate_port=('ansible_accelerate_port', ),
    password=('ansible_ssh_pass', 'ansible_password'),
    private_key_file=('ansible_ssh_private_key_file', 'ansible_private_key_file'),
    pipelining=('ansible_ssh_pipelining', 'ansible_pipelining'),
    shell=('ansible_shell_type', ),
    network_os=('ansible_network_os', ),
    become=('ansible_become', ),
    become_method=('ansible_become_method', ),
    become_user=('ansible_become_user', ),
    become_pass=('ansible_become_password', 'ansible_become_pass'),
    become_exe=('ansible_become_exe', ),
    become_flags=('ansible_become_flags', ),
    ssh_common_args=('ansible_ssh_common_args', ),
    docker_extra_args=('ansible_docker_extra_args', ),
    sftp_extra_args=('ansible_sftp_extra_args', ),
    scp_extra_args=('ansible_scp_extra_args', ),
    ssh_extra_args=('ansible_ssh_extra_args', ),
    ssh_transfer_method=('ansible_ssh_transfer_method', ),
    sudo=('ansible_sudo', ),
    sudo_user=('ansible_sudo_user', ),
    sudo_pass=('ansible_sudo_password', 'ansible_sudo_pass'),
    sudo_exe=('ansible_sudo_exe', ),
    sudo_flags=('ansible_sudo_flags', ),
    su=('ansible_su', ),
    su_user=('ansible_su_user', ),
    su_pass=('ansible_su_password', 'ansible_su_pass'),
    su_exe=('ansible_su_exe', ),
    su_flags=('ansible_su_flags', ),
    executable=('ansible_shell_executable', ),
    module_compression=('ansible_module_compression', ),
)

b_SU_PROMPT_LOCALIZATIONS = [
    to_bytes('Password'),
    to_bytes('암호'),
    to_bytes('パスワード'),
    to_bytes('Adgangskode'),
    to_bytes('Contraseña'),
    to_bytes('Contrasenya'),
    to_bytes('Hasło'),
    to_bytes('Heslo'),
    to_bytes('Jelszó'),
    to_bytes('Lösenord'),
    to_bytes('Mật khẩu'),
    to_bytes('Mot de passe'),
    to_bytes('Parola'),
    to_bytes('Parool'),
    to_bytes('Pasahitza'),
    to_bytes('Passord'),
    to_bytes('Passwort'),
    to_bytes('Salasana'),
    to_bytes('Sandi'),
    to_bytes('Senha'),
    to_bytes('Wachtwoord'),
    to_bytes('ססמה'),
    to_bytes('Лозинка'),
    to_bytes('Парола'),
    to_bytes('Пароль'),
    to_bytes('गुप्तशब्द'),
    to_bytes('शब्दकूट'),
    to_bytes('సంకేతపదము'),
    to_bytes('හස්පදය'),
    to_bytes('密码'),
    to_bytes('密碼'),
    to_bytes('口令'),
]

TASK_ATTRIBUTE_OVERRIDES = (
    'become',
    'become_user',
    'become_pass',
    'become_method',
    'become_flags',
    'connection',
    'docker_extra_args',
    'delegate_to',
    'no_log',
    'remote_user',
)

RESET_VARS = (
    'ansible_connection',
    'ansible_docker_extra_args',
    'ansible_ssh_host',
    'ansible_ssh_pass',
    'ansible_ssh_port',
    'ansible_ssh_user',
    'ansible_ssh_private_key_file',
    'ansible_ssh_pipelining',
    'ansible_ssh_executable',
    'ansible_user',
    'ansible_host',
    'ansible_port',
)


class PlayContext(Base):

    '''
    This class is used to consolidate the connection information for
    hosts in a play and child tasks, where the task may override some
    connection/authentication information.
    '''

    # connection fields, some are inherited from Base:
    # (connection, port, remote_user, environment, no_log)
    _docker_extra_args = FieldAttribute(isa='string')
    _remote_addr = FieldAttribute(isa='string')
    _remote_tmp_dir = FieldAttribute(isa='string', default=C.DEFAULT_REMOTE_TMP)
    _password = FieldAttribute(isa='string')
    _private_key_file = FieldAttribute(isa='string', default=C.DEFAULT_PRIVATE_KEY_FILE)
    _timeout = FieldAttribute(isa='int', default=C.DEFAULT_TIMEOUT)
    _shell = FieldAttribute(isa='string')
    _network_os = FieldAttribute(isa='string')
    _connection_user = FieldAttribute(isa='string')
    _ssh_args = FieldAttribute(isa='string', default=C.ANSIBLE_SSH_ARGS)
    _ssh_common_args = FieldAttribute(isa='string')
    _sftp_extra_args = FieldAttribute(isa='string')
    _scp_extra_args = FieldAttribute(isa='string')
    _ssh_extra_args = FieldAttribute(isa='string')
    _ssh_executable = FieldAttribute(isa='string', default=C.ANSIBLE_SSH_EXECUTABLE)
    _ssh_transfer_method = FieldAttribute(isa='string', default=C.DEFAULT_SSH_TRANSFER_METHOD)
    _connection_lockfd = FieldAttribute(isa='int')
    _pipelining = FieldAttribute(isa='bool', default=C.ANSIBLE_SSH_PIPELINING)
    _accelerate = FieldAttribute(isa='bool', default=False)
    _accelerate_ipv6 = FieldAttribute(isa='bool', default=False, always_post_validate=True)
    _accelerate_port = FieldAttribute(isa='int', default=C.ACCELERATE_PORT, always_post_validate=True)
    _executable = FieldAttribute(isa='string', default=C.DEFAULT_EXECUTABLE)
    _module_compression = FieldAttribute(isa='string', default=C.DEFAULT_MODULE_COMPRESSION)

    # privilege escalation fields
    _become = FieldAttribute(isa='bool')
    _become_method = FieldAttribute(isa='string')
    _become_user = FieldAttribute(isa='string')
    _become_pass = FieldAttribute(isa='string')
    _become_exe = FieldAttribute(isa='string')
    _become_flags = FieldAttribute(isa='string')
    _prompt = FieldAttribute(isa='string')

    # backwards compatibility fields for sudo/su
    _sudo_exe = FieldAttribute(isa='string')
    _sudo_flags = FieldAttribute(isa='string')
    _sudo_pass = FieldAttribute(isa='string')
    _su_exe = FieldAttribute(isa='string')
    _su_flags = FieldAttribute(isa='string')
    _su_pass = FieldAttribute(isa='string')

    # general flags
    _verbosity = FieldAttribute(isa='int', default=0)
    _only_tags = FieldAttribute(isa='set', default=set())
    _skip_tags = FieldAttribute(isa='set', default=set())
    _check_mode = FieldAttribute(isa='bool', default=False)
    _force_handlers = FieldAttribute(isa='bool', default=False)
    _start_at_task = FieldAttribute(isa='string')
    _step = FieldAttribute(isa='bool', default=False)
    _diff = FieldAttribute(isa='bool')

    # Fact gathering settings
    _gather_subset = FieldAttribute(isa='string', default=C.DEFAULT_GATHER_SUBSET)
    _gather_timeout = FieldAttribute(isa='string', default=C.DEFAULT_GATHER_TIMEOUT)
    _fact_path = FieldAttribute(isa='string', default=C.DEFAULT_FACT_PATH)

    def __init__(self, play=None, options=None, passwords=None, connection_lockfd=None):

        super(PlayContext, self).__init__()

        if passwords is None:
            passwords = {}

        self.password = passwords.get('conn_pass', '')
        self.become_pass = passwords.get('become_pass', '')

        self.prompt = ''
        self.success_key = ''

        # a file descriptor to be used during locking operations
        self.connection_lockfd = connection_lockfd

        # set options before play to allow play to override them
        if options:
            self.set_options(options)

        if play:
            self.set_play(play)

    def set_play(self, play):
        '''
        Configures this connection information instance with data from
        the play class.
        '''

        # special handling for accelerated mode, as it is set in a separate
        # play option from the connection parameter
        self.accelerate = play.accelerate
        self.accelerate_ipv6 = play.accelerate_ipv6
        self.accelerate_port = play.accelerate_port

        if play.connection:
            self.connection = play.connection

        if play.remote_user:
            self.remote_user = play.remote_user

        if play.port:
            self.port = int(play.port)

        if play.become is not None:
            self.become = play.become
        if play.become_method:
            self.become_method = play.become_method
        if play.become_user:
            self.become_user = play.become_user

        if play.force_handlers is not None:
            self.force_handlers = play.force_handlers

    def set_options(self, options):
        '''
        Configures this connection information instance with data from
        options specified by the user on the command line. These have a
        lower precedence than those set on the play or host.
        '''

        # privilege escalation
        self.become = options.become
        self.become_method = options.become_method
        self.become_user = options.become_user

        self.check_mode = boolean(options.check, strict=False)

        # get ssh options FIXME: make these common to all connections
        for flag in ['ssh_common_args', 'docker_extra_args', 'sftp_extra_args', 'scp_extra_args', 'ssh_extra_args']:
            setattr(self, flag, getattr(options, flag, ''))

        # general flags (should we move out?)
        for flag in ['connection', 'remote_user', 'private_key_file', 'verbosity', 'force_handlers', 'step', 'start_at_task', 'diff']:
            attribute = getattr(options, flag, False)
            if attribute:
                setattr(self, flag, attribute)

        if hasattr(options, 'timeout') and options.timeout:
            self.timeout = int(options.timeout)

        # get the tag info from options. We check to see if the options have
        # the attribute, as it is not always added via the CLI
        if hasattr(options, 'tags'):
            self.only_tags.update(options.tags)

        if len(self.only_tags) == 0:
            self.only_tags = set(['all'])

        if hasattr(options, 'skip_tags'):
            self.skip_tags.update(options.skip_tags)

    def set_task_and_variable_override(self, task, variables, templar):
        '''
        Sets attributes from the task if they are set, which will override
        those from the play.

        :arg task: the task object with the parameters that were set on it
        :arg variables: variables from inventory
        :arg templar: templar instance if templating variables is needed
        '''

        new_info = self.copy()

        # loop through a subset of attributes on the task object and set
        # connection fields based on their values
        for attr in TASK_ATTRIBUTE_OVERRIDES:
            if hasattr(task, attr):
                attr_val = getattr(task, attr)
                if attr_val is not None:
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
            delegated_host_name = templar.template(task.delegate_to)
            delegated_vars = variables.get('ansible_delegated_vars', dict()).get(delegated_host_name, dict())

            delegated_transport = C.DEFAULT_TRANSPORT
            for transport_var in MAGIC_VARIABLE_MAPPING.get('connection'):
                if transport_var in delegated_vars:
                    delegated_transport = delegated_vars[transport_var]
                    break

            # make sure this delegated_to host has something set for its remote
            # address, otherwise we default to connecting to it by name. This
            # may happen when users put an IP entry into their inventory, or if
            # they rely on DNS for a non-inventory hostname
            for address_var in ('ansible_%s_host' % transport_var,) + MAGIC_VARIABLE_MAPPING.get('remote_addr'):
                if address_var in delegated_vars:
                    break
            else:
                display.debug("no remote address found for delegated host %s\nusing its name, so success depends on DNS resolution" % delegated_host_name)
                delegated_vars['ansible_host'] = delegated_host_name

            # reset the port back to the default if none was specified, to prevent
            # the delegated host from inheriting the original host's setting
            for port_var in ('ansible_%s_port' % transport_var,) + MAGIC_VARIABLE_MAPPING.get('port'):
                if port_var in delegated_vars:
                    break
            else:
                if delegated_transport == 'winrm':
                    delegated_vars['ansible_port'] = 5986
                else:
                    delegated_vars['ansible_port'] = C.DEFAULT_REMOTE_PORT

            # and likewise for the remote user
            for user_var in ('ansible_%s_user' % transport_var,) + MAGIC_VARIABLE_MAPPING.get('remote_user'):
                if user_var in delegated_vars and delegated_vars[user_var]:
                    break
            else:
                delegated_vars['ansible_user'] = task.remote_user or self.remote_user
        else:
            delegated_vars = dict()

            # setup shell
            for exe_var in MAGIC_VARIABLE_MAPPING.get('executable'):
                if exe_var in variables:
                    setattr(new_info, 'executable', variables.get(exe_var))

        attrs_considered = []
        for (attr, variable_names) in iteritems(MAGIC_VARIABLE_MAPPING):
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

        # become legacy updates -- from commandline
        if not new_info.become_pass:
            if new_info.become_method == 'sudo' and new_info.sudo_pass:
                new_info.become_pass = new_info.sudo_pass
            elif new_info.become_method == 'su' and new_info.su_pass:
                new_info.become_pass = new_info.su_pass

        # become legacy updates -- from inventory file (inventory overrides
        # commandline)
        for become_pass_name in MAGIC_VARIABLE_MAPPING.get('become_pass'):
            if become_pass_name in variables:
                break
        else:  # This is a for-else
            if new_info.become_method == 'sudo':
                for sudo_pass_name in MAGIC_VARIABLE_MAPPING.get('sudo_pass'):
                    if sudo_pass_name in variables:
                        setattr(new_info, 'become_pass', variables[sudo_pass_name])
                        break
            elif new_info.become_method == 'su':
                for su_pass_name in MAGIC_VARIABLE_MAPPING.get('su_pass'):
                    if su_pass_name in variables:
                        setattr(new_info, 'become_pass', variables[su_pass_name])
                        break

        # make sure we get port defaults if needed
        if new_info.port is None and C.DEFAULT_REMOTE_PORT is not None:
            new_info.port = int(C.DEFAULT_REMOTE_PORT)

        # special overrides for the connection setting
        if len(delegated_vars) > 0:
            # in the event that we were using local before make sure to reset the
            # connection type to the default transport for the delegated-to host,
            # if not otherwise specified
            for connection_type in MAGIC_VARIABLE_MAPPING.get('connection'):
                if connection_type in delegated_vars:
                    break
            else:
                remote_addr_local = new_info.remote_addr in C.LOCALHOST
                inv_hostname_local = delegated_vars.get('inventory_hostname') in C.LOCALHOST
                if remote_addr_local and inv_hostname_local:
                    setattr(new_info, 'connection', 'local')
                elif getattr(new_info, 'connection', None) == 'local' and (not remote_addr_local or not inv_hostname_local):
                    setattr(new_info, 'connection', C.DEFAULT_TRANSPORT)

        # if the final connection type is local, reset the remote_user value to that of the currently logged in user
        # this ensures any become settings are obeyed correctly
        # we store original in 'connection_user' for use of network/other modules that fallback to it as login user
        if new_info.connection == 'local':
            new_info.connection_user = new_info.remote_user
            new_info.remote_user = pwd.getpwuid(os.getuid()).pw_name

        # set no_log to default if it was not previouslly set
        if new_info.no_log is None:
            new_info.no_log = C.DEFAULT_NO_LOG

        if task.always_run:
            display.deprecated("always_run is deprecated. Use check_mode = no instead.", version="2.4", removed=False)
            new_info.check_mode = False

        # check_mode replaces always_run, overwrite always_run if both are given
        if task.check_mode is not None:
            new_info.check_mode = task.check_mode

        return new_info

    def make_become_cmd(self, cmd, executable=None):
        """ helper function to create privilege escalation commands """

        prompt = None
        success_key = None
        self.prompt = None

        if self.become:

            if not executable:
                executable = self.executable

            becomecmd = None
            randbits = ''.join(random.choice(string.ascii_lowercase) for x in range(32))
            success_key = 'BECOME-SUCCESS-%s' % randbits
            success_cmd = shlex_quote('echo %s; %s' % (success_key, cmd))

            if executable:
                command = '%s -c %s' % (executable, success_cmd)
            else:
                command = success_cmd

            # set executable to use for the privilege escalation method, with various overrides
            exe = (
                self.become_exe or
                getattr(self, '%s_exe' % self.become_method, None) or
                C.DEFAULT_BECOME_EXE or
                getattr(C, 'DEFAULT_%s_EXE' % self.become_method.upper(), None) or
                self.become_method
            )

            # set flags to use for the privilege escalation method, with various overrides
            flags = (
                self.become_flags or
                getattr(self, '%s_flags' % self.become_method, None) or
                C.DEFAULT_BECOME_FLAGS or
                getattr(C, 'DEFAULT_%s_FLAGS' % self.become_method.upper(), None) or
                ''
            )

            if self.become_method == 'sudo':
                # If we have a password, we run sudo with a randomly-generated
                # prompt set using -p. Otherwise we run it with default -n, which makes
                # it fail if it would have prompted for a password.
                # Cannot rely on -n as it can be removed from defaults, which should be
                # done for older versions of sudo that do not support the option.
                #
                # Passing a quoted compound command to sudo (or sudo -s)
                # directly doesn't work, so we shellquote it with shlex_quote()
                # and pass the quoted string to the user's shell.

                # force quick error if password is required but not supplied, should prevent sudo hangs.
                if self.become_pass:
                    prompt = '[sudo via ansible, key=%s] password: ' % randbits
                    becomecmd = '%s %s -p "%s" -u %s %s' % (exe, flags.replace('-n', ''), prompt, self.become_user, command)
                else:
                    becomecmd = '%s %s -u %s %s' % (exe, flags, self.become_user, command)

            elif self.become_method == 'su':

                # passing code ref to examine prompt as simple string comparisson isn't good enough with su
                def detect_su_prompt(b_data):
                    b_password_string = b"|".join([b'(\w+\'s )?' + x for x in b_SU_PROMPT_LOCALIZATIONS])
                    # Colon or unicode fullwidth colon
                    b_password_string = b_password_string + to_bytes(u' ?(:|：) ?')
                    b_SU_PROMPT_LOCALIZATIONS_RE = re.compile(b_password_string, flags=re.IGNORECASE)
                    return bool(b_SU_PROMPT_LOCALIZATIONS_RE.match(b_data))
                prompt = detect_su_prompt

                becomecmd = '%s %s %s -c %s' % (exe, flags, self.become_user, shlex_quote(command))

            elif self.become_method == 'pbrun':

                prompt = 'Password:'
                becomecmd = '%s %s -u %s %s' % (exe, flags, self.become_user, success_cmd)

            elif self.become_method == 'ksu':
                def detect_ksu_prompt(b_data):
                    return re.match(b"Kerberos password for .*@.*:", b_data)

                prompt = detect_ksu_prompt
                becomecmd = '%s %s %s -e %s' % (exe, self.become_user, flags, command)

            elif self.become_method == 'pfexec':

                # No user as it uses it's own exec_attr to figure it out
                becomecmd = '%s %s "%s"' % (exe, flags, success_cmd)

            elif self.become_method == 'runas':
                # become is handled inside the WinRM connection plugin
                display.warning("The Windows 'runas' become method is experimental, and may change significantly in future Ansible releases.")

                if not self.become_user:
                    raise AnsibleError(("The 'runas' become method requires a username "
                                        "(specify with the '--become-user' CLI arg, the 'become_user' keyword, or the 'ansible_become_user' variable)"))
                if not self.become_pass:
                    raise AnsibleError(("The 'runas' become method requires a password "
                                       "(specify with the '-K' CLI arg or the 'ansible_become_password' variable)"))
                becomecmd = cmd

            elif self.become_method == 'doas':

                prompt = 'doas (%s@' % self.remote_user
                exe = self.become_exe or 'doas'

                if not self.become_pass:
                    flags += ' -n '

                if self.become_user:
                    flags += ' -u %s ' % self.become_user

                # FIXME: make shell independent
                becomecmd = '%s %s echo %s && %s %s env ANSIBLE=true %s' % (exe, flags, success_key, exe, flags, cmd)

            elif self.become_method == 'dzdo':

                exe = self.become_exe or 'dzdo'
                if self.become_pass:
                    prompt = '[dzdo via ansible, key=%s] password: ' % randbits
                    becomecmd = '%s -p %s -u %s %s' % (exe, shlex_quote(prompt), self.become_user, command)
                else:
                    becomecmd = '%s -u %s %s' % (exe, self.become_user, command)

            elif self.become_method == 'pmrun':

                exe = self.become_exe or 'pmrun'

                prompt = 'Enter UPM user password:'
                becomecmd = '%s %s %s' % (exe, flags, shlex_quote(command))

            else:
                raise AnsibleError("Privilege escalation method not found: %s" % self.become_method)

            if self.become_pass:
                self.prompt = prompt
            self.success_key = success_key
            return becomecmd

        return cmd

    def update_vars(self, variables):
        '''
        Adds 'magic' variables relating to connections to the variable dictionary provided.
        In case users need to access from the play, this is a legacy from runner.
        '''

        for prop, var_list in MAGIC_VARIABLE_MAPPING.items():
            try:
                if 'become' in prop:
                    continue

                var_val = getattr(self, prop)
                for var_opt in var_list:
                    if var_opt not in variables and var_val is not None:
                        variables[var_opt] = var_val
            except AttributeError:
                continue

    def _get_attr_connection(self):
        ''' connections are special, this takes care of responding correctly '''
        conn_type = None
        if self._attributes['connection'] == 'smart':
            conn_type = 'ssh'
            if sys.platform.startswith('darwin') and self.password:
                # due to a current bug in sshpass on OSX, which can trigger
                # a kernel panic even for non-privileged users, we revert to
                # paramiko on that OS when a SSH password is specified
                conn_type = "paramiko"
            else:
                # see if SSH can support ControlPersist if not use paramiko
                if not check_for_controlpersist(self.ssh_executable):
                    conn_type = "paramiko"

        # if someone did `connection: persistent`, default it to using a persistent paramiko connection to avoid problems
        elif self._attributes['connection'] == 'persistent':
            conn_type = 'paramiko'

        if conn_type:
            self.connection = conn_type

        return self._attributes['connection']
