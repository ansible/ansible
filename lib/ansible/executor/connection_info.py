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

import pipes
import random
import re

from ansible import constants as C
from ansible.template import Templar
from ansible.utils.boolean import boolean
from ansible.errors import AnsibleError

__all__ = ['ConnectionInformation']

SU_PROMPT_LOCALIZATIONS = [
    'Password',
    '암호',
    'パスワード',
    'Adgangskode',
    'Contraseña',
    'Contrasenya',
    'Hasło',
    'Heslo',
    'Jelszó',
    'Lösenord',
    'Mật khẩu',
    'Mot de passe',
    'Parola',
    'Parool',
    'Pasahitza',
    'Passord',
    'Passwort',
    'Salasana',
    'Sandi',
    'Senha',
    'Wachtwoord',
    'ססמה',
    'Лозинка',
    'Парола',
    'Пароль',
    'गुप्तशब्द',
    'शब्दकूट',
    'సంకేతపదము',
    'හස්පදය',
    '密码',
    '密碼',
]

# the magic variable mapping dictionary below is used to translate
# host/inventory variables to fields in the ConnectionInformation
# object. The dictionary values are tuples, to account for aliases
# in variable names.

MAGIC_VARIABLE_MAPPING = dict(
   connection       = ('ansible_connection',),
   remote_addr      = ('ansible_ssh_host', 'ansible_host'),
   remote_user      = ('ansible_ssh_user', 'ansible_user'),
   port             = ('ansible_ssh_port', 'ansible_port'),
   password         = ('ansible_ssh_pass', 'ansible_password'),
   private_key_file = ('ansible_ssh_private_key_file', 'ansible_private_key_file'),
   shell            = ('ansible_shell_type',),
   become           = ('ansible_become',),
   become_method    = ('ansible_become_method',),
   become_user      = ('ansible_become_user',),
   become_pass      = ('ansible_become_password','ansible_become_pass'),
   become_exe       = ('ansible_become_exe',),
   become_flags     = ('ansible_become_flags',),
   sudo             = ('ansible_sudo',),
   sudo_user        = ('ansible_sudo_user',),
   sudo_pass        = ('ansible_sudo_password',),
   sudo_exe         = ('ansible_sudo_exe',),
   sudo_flags       = ('ansible_sudo_flags',),
   su               = ('ansible_su',),
   su_user          = ('ansible_su_user',),
   su_pass          = ('ansible_su_password',),
   su_exe           = ('ansible_su_exe',),
   su_flags         = ('ansible_su_flags',),
)

SU_PROMPT_LOCALIZATIONS = [
    'Password',
    '암호',
    'パスワード',
    'Adgangskode',
    'Contraseña',
    'Contrasenya',
    'Hasło',
    'Heslo',
    'Jelszó',
    'Lösenord',
    'Mật khẩu',
    'Mot de passe',
    'Parola',
    'Parool',
    'Pasahitza',
    'Passord',
    'Passwort',
    'Salasana',
    'Sandi',
    'Senha',
    'Wachtwoord',
    'ססמה',
    'Лозинка',
    'Парола',
    'Пароль',
    'गुप्तशब्द',
    'शब्दकूट',
    'సంకేతపదము',
    'හස්පදය',
    '密码',
    '密碼',
]

class ConnectionInformation:

    '''
    This class is used to consolidate the connection information for
    hosts in a play and child tasks, where the task may override some
    connection/authentication information.
    '''

    def __init__(self, play=None, options=None, passwords=None):

        if passwords is None:
            passwords = {}

        # connection
        self.connection       = None
        self.remote_addr      = None
        self.remote_user      = None
        self.password         = passwords.get('conn_pass','')
        self.port             = None
        self.private_key_file = C.DEFAULT_PRIVATE_KEY_FILE
        self.timeout          = C.DEFAULT_TIMEOUT
        self.shell            = None

        # privilege escalation
        self.become        = None
        self.become_method = None
        self.become_user   = None
        self.become_pass   = passwords.get('become_pass','')
        self.become_exe    = None
        self.become_flags  = None

        # backwards compat
        self.sudo_exe    = None
        self.sudo_flags  = None
        self.su_exe      = None
        self.su_flags    = None

        # general flags (should we move out?)
        self.verbosity   = 0
        self.only_tags   = set()
        self.skip_tags   = set()
        self.no_log      = False
        self.check_mode  = False

        #TODO: just pull options setup to above?
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

        if play.connection:
            self.connection = play.connection

        if play.remote_user:
            self.remote_user   = play.remote_user

        if play.port:
            self.port          = int(play.port)

        if play.become is not None:
            self.become        = play.become
        if play.become_method:
            self.become_method = play.become_method
        if play.become_user:
            self.become_user   = play.become_user

        # non connection related
        self.no_log      = play.no_log
        self.environment = play.environment

    def set_options(self, options):
        '''
        Configures this connection information instance with data from
        options specified by the user on the command line. These have a
        higher precedence than those set on the play or host.
        '''

        if options.connection:
            self.connection = options.connection

        self.remote_user = options.remote_user
        self.private_key_file = options.private_key_file

        # privilege escalation
        self.become        = options.become
        self.become_method = options.become_method
        self.become_user   = options.become_user

        # general flags (should we move out?)
        if options.verbosity:
            self.verbosity  = options.verbosity
        #if options.no_log:
        #    self.no_log     = boolean(options.no_log)
        if options.check:
            self.check_mode = boolean(options.check)

        # get the tag info from options, converting a comma-separated list
        # of values into a proper list if need be. We check to see if the
        # options have the attribute, as it is not always added via the CLI
        if hasattr(options, 'tags'):
            if isinstance(options.tags, list):
                self.only_tags.update(options.tags)
            elif isinstance(options.tags, basestring):
                self.only_tags.update(options.tags.split(','))

        if len(self.only_tags) == 0:
            self.only_tags = set(['all'])

        if hasattr(options, 'skip_tags'):
            if isinstance(options.skip_tags, list):
                self.skip_tags.update(options.skip_tags)
            elif isinstance(options.skip_tags, basestring):
                self.skip_tags.update(options.skip_tags.split(','))

    def copy(self, ci):
        '''
        Copies the connection info from another connection info object, used
        when merging in data from task overrides.
        '''

        for field in self._get_fields():
            value = getattr(ci, field, None)
            if isinstance(value, dict):
                setattr(self, field, value.copy())
            elif isinstance(value, set):
                setattr(self, field, value.copy())
            elif isinstance(value, list):
                setattr(self, field, value[:])
            else:
                setattr(self, field, value)

    def set_task_and_host_override(self, task, host):
        '''
        Sets attributes from the task if they are set, which will override
        those from the play.
        '''

        new_info = ConnectionInformation()
        new_info.copy(self)

        # loop through a subset of attributes on the task object and set
        # connection fields based on their values
        for attr in ('connection', 'remote_user', 'become', 'become_user', 'become_pass', 'become_method', 'environment', 'no_log'):
            if hasattr(task, attr):
                attr_val = getattr(task, attr)
                if attr_val is not None:
                    setattr(new_info, attr, attr_val)

        # finally, use the MAGIC_VARIABLE_MAPPING dictionary to update this
        # connection info object with 'magic' variables from inventory
        variables = host.get_vars()
        for (attr, variable_names) in MAGIC_VARIABLE_MAPPING.iteritems():
            for variable_name in variable_names:
                if variable_name in variables:
                    setattr(new_info, attr, variables[variable_name])

        return new_info

    def make_become_cmd(self, cmd, executable=C.DEFAULT_EXECUTABLE):
        """ helper function to create privilege escalation commands """

        prompt      = None
        success_key = None

        if self.become:

            becomecmd   = None
            randbits    = ''.join(chr(random.randint(ord('a'), ord('z'))) for x in xrange(32))
            success_key = 'BECOME-SUCCESS-%s' % randbits
            executable = executable or '$SHELL'
            success_cmd = pipes.quote('echo %s; %s' % (success_key, cmd))

            if self.become_method == 'sudo':
                # Rather than detect if sudo wants a password this time, -k makes sudo always ask for
                # a password if one is required. Passing a quoted compound command to sudo (or sudo -s)
                # directly doesn't work, so we shellquote it with pipes.quote() and pass the quoted
                # string to the user's shell.  We loop reading output until we see the randomly-generated
                # sudo prompt set with the -p option.
                prompt = '[sudo via ansible, key=%s] password: ' % randbits
                exe = self.become_exe or self.sudo_exe or 'sudo'
                flags = self.become_flags or self.sudo_flags or ''
                becomecmd = '%s -k && %s %s -S -p "%s" -u %s %s -c %s' % \
                    (exe, exe, flags or C.DEFAULT_SUDO_FLAGS, prompt, self.become_user, executable, success_cmd)

            elif self.become_method == 'su':

                def detect_su_prompt(data):
                    SU_PROMPT_LOCALIZATIONS_RE = re.compile("|".join(['(\w+\'s )?' + x + ' ?: ?' for x in SU_PROMPT_LOCALIZATIONS]), flags=re.IGNORECASE)
                    return bool(SU_PROMPT_LOCALIZATIONS_RE.match(data))

                prompt = detect_su_prompt
                exe = self.become_exe or self.su_exe or 'su'
                flags = self.become_flags or self.su_flags or ''
                becomecmd = '%s %s %s -c "%s -c %s"' % (exe, flags, self.become_user, executable, success_cmd)

            elif self.become_method == 'pbrun':

                prompt='assword:'
                exe = self.become_exe or 'pbrun'
                flags = self.become_flags or ''
                becomecmd = '%s -b -l %s -u %s %s' % (exe, flags, self.become_user, success_cmd)

            elif self.become_method == 'pfexec':

                exe = self.become_exe or 'pfexec'
                flags = self.become_flags or ''
                # No user as it uses it's own exec_attr to figure it out
                becomecmd = '%s %s "%s"' % (exe, flags, success_cmd)

            else:
                raise AnsibleError("Privilege escalation method not found: %s" % self.become_method)

            return (('%s -c ' % executable) + pipes.quote(becomecmd), prompt, success_key)

        return (cmd, prompt, success_key)

    def _get_fields(self):
        return [i for i in self.__dict__.keys() if i[:1] != '_']

    def post_validate(self, templar):
        '''
        Finalizes templated values which may be set on this objects fields.
        '''

        for field in self._get_fields():
            value = templar.template(getattr(self, field))
            setattr(self, field, value)

    def update_vars(self, variables):
        '''
        Adds 'magic' variables relating to connections to the variable dictionary provided.
        In case users need to access from the play, this is a legacy from runner.
        '''

        #FIXME: remove password? possibly add become/sudo settings
        for special_var in  ['ansible_connection', 'ansible_ssh_host', 'ansible_ssh_pass', 'ansible_ssh_port', 'ansible_ssh_user', 'ansible_ssh_private_key_file']:
            if special_var not in variables:
                for prop, varnames in MAGIC_VARIABLE_MAPPING.items():
                    if special_var in varnames:
                        variables[special_var] = getattr(self, prop)
