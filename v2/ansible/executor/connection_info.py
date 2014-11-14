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
        self.remote_user = 'root'
        self.password    = ''
        self.port        = 22
        self.su          = False
        self.su_user     = ''
        self.su_pass     = ''
        self.sudo        = False
        self.sudo_user   = ''
        self.sudo_pass   = ''
        self.verbosity   = 0
        self.only_tags   = set()
        self.skip_tags   = set()

        if play:
            self.set_play(play)

        if options:
            self.set_options(options)

    def set_play(self, play):
        '''
        Configures this connection information instance with data from
        the play class.
        '''

        if play.connection:
            self.connection = play.connection

        self.remote_user = play.remote_user
        self.password    = ''
        self.port        = int(play.port) if play.port else 22
        self.su          = play.su
        self.su_user     = play.su_user
        self.su_pass     = play.su_pass
        self.sudo        = play.sudo
        self.sudo_user   = play.sudo_user
        self.sudo_pass   = play.sudo_pass

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

        # get the tag info from options, converting a comma-separated list
        # of values into a proper list if need be
        if isinstance(options.tags, list):
            self.only_tags.update(options.tags)
        elif isinstance(options.tags, basestring):
            self.only_tags.update(options.tags.split(','))
        if isinstance(options.skip_tags, list):
            self.skip_tags.update(options.skip_tags)
        elif isinstance(options.skip_tags, basestring):
            self.skip_tags.update(options.skip_tags.split(','))

    def copy(self, ci):
        '''
        Copies the connection info from another connection info object, used
        when merging in data from task overrides.
        '''

        self.connection  = ci.connection
        self.remote_user = ci.remote_user
        self.password    = ci.password
        self.port        = ci.port
        self.su          = ci.su
        self.su_user     = ci.su_user
        self.su_pass     = ci.su_pass
        self.sudo        = ci.sudo
        self.sudo_user   = ci.sudo_user
        self.sudo_pass   = ci.sudo_pass
        self.verbosity   = ci.verbosity
        self.only_tags   = ci.only_tags.copy()
        self.skip_tags   = ci.skip_tags.copy()

    def set_task_override(self, task):
        '''
        Sets attributes from the task if they are set, which will override
        those from the play.
        '''

        new_info = ConnectionInformation()
        new_info.copy(self)

        for attr in ('connection', 'remote_user', 'su', 'su_user', 'su_pass', 'sudo', 'sudo_user', 'sudo_pass'):
            if hasattr(task, attr):
                attr_val = getattr(task, attr)
                if attr_val:
                    setattr(new_info, attr, attr_val)

        return new_info

    def make_sudo_cmd(self, sudo_exe, executable, cmd):
        """
        Helper function for wrapping commands with sudo.

        Rather than detect if sudo wants a password this time, -k makes
        sudo always ask for a password if one is required. Passing a quoted
        compound command to sudo (or sudo -s) directly doesn't work, so we
        shellquote it with pipes.quote() and pass the quoted string to the
        user's shell.  We loop reading output until we see the randomly-
        generated sudo prompt set with the -p option.
        """

        randbits = ''.join(chr(random.randint(ord('a'), ord('z'))) for x in xrange(32))
        prompt = '[sudo via ansible, key=%s] password: ' % randbits
        success_key = 'SUDO-SUCCESS-%s' % randbits

        sudocmd = '%s -k && %s %s -S -p "%s" -u %s %s -c %s' % (
            sudo_exe, sudo_exe, C.DEFAULT_SUDO_FLAGS, prompt,
            self.sudo_user, executable or '$SHELL',
            pipes.quote('echo %s; %s' % (success_key, cmd))
        )

        #return ('/bin/sh -c ' + pipes.quote(sudocmd), prompt, success_key)
        return (sudocmd, prompt, success_key)

