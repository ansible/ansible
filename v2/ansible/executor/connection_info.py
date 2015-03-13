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

from ansible import constants as C
from ansible.template import Templar
from ansible.utils.boolean import boolean


__all__ = ['ConnectionInformation']


class ConnectionInformation:

    '''
    This class is used to consolidate the connection information for
    hosts in a play and child tasks, where the task may override some
    connection/authentication information.
    '''

    def __init__(self, play=None, options=None):
        # FIXME: implement the new methodology here for supporting
        #        various different auth escalation methods (becomes, etc.)

        self.connection  = C.DEFAULT_TRANSPORT
        self.remote_addr = None
        self.remote_user = 'root'
        self.password    = ''
        self.port        = 22
        self.private_key_file = None
        self.verbosity   = 0
        self.only_tags   = set()
        self.skip_tags   = set()

        # privilege escalation
        self.become        = False
        self.become_method = C.DEFAULT_BECOME_METHOD
        self.become_user   = ''
        self.become_pass   = ''

        self.no_log      = False
        self.check_mode  = False

        if play:
            self.set_play(play)

        if options:
            self.set_options(options)

    def __repr__(self):
        value = "CONNECTION INFO:\n"
        fields = self._get_fields()
        fields.sort()
        for field in fields:
            value += "%20s : %s\n" % (field, getattr(self, field))
        return value

    def set_play(self, play):
        '''
        Configures this connection information instance with data from
        the play class.
        '''

        if play.connection:
            self.connection = play.connection

        self.remote_user   = play.remote_user
        self.password      = ''
        self.port          = int(play.port) if play.port else 22
        self.become        = play.become
        self.become_method = play.become_method
        self.become_user   = play.become_user
        self.become_pass   = play.become_pass

        # non connection related
        self.no_log      = play.no_log
        self.environment = play.environment

    def set_options(self, options):
        '''
        Configures this connection information instance with data from
        options specified by the user on the command line. These have a
        higher precedence than those set on the play or host.
        '''

        # FIXME: set other values from options here?

        self.verbosity = options.verbosity
        if options.connection:
            self.connection = options.connection

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

    def set_task_override(self, task):
        '''
        Sets attributes from the task if they are set, which will override
        those from the play.
        '''

        new_info = ConnectionInformation()
        new_info.copy(self)

        for attr in ('connection', 'remote_user', 'become', 'become_user', 'become_pass', 'become_method', 'environment', 'no_log'):
            if hasattr(task, attr):
                attr_val = getattr(task, attr)
                if attr_val:
                    setattr(new_info, attr, attr_val)

        return new_info

    def make_become_cmd(self, cmd, executable, become_settings=None):

        """
        helper function to create privilege escalation commands
        """

        # FIXME: become settings should probably be stored in the connection info itself
        if become_settings is None:
            become_settings = {}

        randbits    = ''.join(chr(random.randint(ord('a'), ord('z'))) for x in xrange(32))
        success_key = 'BECOME-SUCCESS-%s' % randbits
        prompt      = None
        becomecmd   = None

        executable = executable or '$SHELL'

        if self.become:
            if self.become_method == 'sudo':
                # Rather than detect if sudo wants a password this time, -k makes sudo always ask for
                # a password if one is required. Passing a quoted compound command to sudo (or sudo -s)
                # directly doesn't work, so we shellquote it with pipes.quote() and pass the quoted
                # string to the user's shell.  We loop reading output until we see the randomly-generated
                # sudo prompt set with the -p option.
                prompt = '[sudo via ansible, key=%s] password: ' % randbits
                exe = become_settings.get('sudo_exe', C.DEFAULT_SUDO_EXE)
                flags = become_settings.get('sudo_flags', C.DEFAULT_SUDO_FLAGS)
                becomecmd = '%s -k && %s %s -S -p "%s" -u %s %s -c "%s"' % \
                    (exe, exe, flags or C.DEFAULT_SUDO_FLAGS, prompt, self.become_user, executable, 'echo %s; %s' % (success_key, cmd))

            elif self.become_method == 'su':
                exe = become_settings.get('su_exe', C.DEFAULT_SU_EXE)
                flags = become_settings.get('su_flags', C.DEFAULT_SU_FLAGS)
                becomecmd = '%s %s %s -c "%s -c %s"' % (exe, flags, self.become_user, executable, pipes.quote('echo %s; %s' % (success_key, cmd)))

            elif self.become_method == 'pbrun':
                exe = become_settings.get('pbrun_exe', 'pbrun')
                flags = become_settings.get('pbrun_flags', '')
                becomecmd = '%s -b -l %s -u %s "%s"' % (exe, flags, self.become_user, 'echo %s; %s' % (success_key,cmd))

            elif self.become_method == 'pfexec':
                exe = become_settings.get('pfexec_exe', 'pbrun')
                flags = become_settings.get('pfexec_flags', '')
                # No user as it uses it's own exec_attr to figure it out
                becomecmd = '%s %s "%s"' % (exe, flags, 'echo %s; %s' % (success_key,cmd))

            else:
                raise errors.AnsibleError("Privilege escalation method not found: %s" % method)

            return (('%s -c ' % executable) + pipes.quote(becomecmd), prompt, success_key)

        return (cmd, "", "")

    def check_become_success(self, output, become_settings):
        #TODO: implement
        pass

    def _get_fields(self):
        return [i for i in self.__dict__.keys() if i[:1] != '_']

    def post_validate(self, variables, loader):
        '''
        Finalizes templated values which may be set on this objects fields.
        '''

        templar = Templar(loader=loader, variables=variables)
        for field in self._get_fields():
            value = templar.template(getattr(self, field))
            setattr(self, field, value)
