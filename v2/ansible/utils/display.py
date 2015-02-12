# (c) 2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# FIXME: copied mostly from old code, needs py3 improvements

import textwrap

from ansible import constants as C
from ansible.errors import *
from ansible.utils.color import stringc

class Display:

    def __init__(self, conn_info=None):
        if conn_info:
            self._verbosity = conn_info.verbosity
        else:
            self._verbosity = 0

        # list of all deprecation messages to prevent duplicate display
        self._deprecations = {}
        self._warns        = {}

    def display(self, msg, color=None, stderr=False, screen_only=False, log_only=False):
        msg2 = msg
        if color:
            msg2 = stringc(msg, color)
        if not log_only:
            if not stderr:
                try:
                    print msg2
                except UnicodeEncodeError:
                    print msg2.encode('utf-8')
            else:
                try:
                    print >>sys.stderr, msg2
                except UnicodeEncodeError:
                    print >>sys.stderr, msg2.encode('utf-8')
        if C.DEFAULT_LOG_PATH != '':
            while msg.startswith("\n"):
                msg = msg.replace("\n","")
            # FIXME: logger stuff needs to be implemented
            #if not screen_only:
            #    if color == 'red':
            #        logger.error(msg)
            #    else:
            #        logger.info(msg)

    def vv(self, msg, host=None):
        return self.verbose(msg, host=host, caplevel=1)

    def vvv(self, msg, host=None):
        return self.verbose(msg, host=host, caplevel=2)

    def vvvv(self, msg, host=None):
        return self.verbose(msg, host=host, caplevel=3)

    def verbose(self, msg, host=None, caplevel=2):
        # FIXME: this needs to be implemented
        #msg = utils.sanitize_output(msg)
        if self._verbosity > caplevel:
            if host is None:
                self.display(msg, color='blue')
            else:
                self.display("<%s> %s" % (host, msg), color='blue')

    def deprecated(self, msg, version, removed=False):
        ''' used to print out a deprecation message.'''

        if not removed and not C.DEPRECATION_WARNINGS:
            return

        if not removed:
            if version:
                new_msg = "\n[DEPRECATION WARNING]: %s. This feature will be removed in version %s." % (msg, version)
            else:
                new_msg = "\n[DEPRECATION WARNING]: %s. This feature will be removed in a future release." % (msg)
            new_msg = new_msg + " Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.\n\n"
        else:
            raise AnsibleError("[DEPRECATED]: %s.  Please update your playbooks." % msg)

        wrapped = textwrap.wrap(new_msg, 79)
        new_msg = "\n".join(wrapped) + "\n"

        if new_msg not in deprecations:
            self._display(new_msg, color='purple', stderr=True)
            self._deprecations[new_msg] = 1

    def warning(self, msg):
        new_msg = "\n[WARNING]: %s" % msg
        wrapped = textwrap.wrap(new_msg, 79)
        new_msg = "\n".join(wrapped) + "\n"
        if new_msg not in warns:
            self._display(new_msg, color='bright purple', stderr=True)
            self._warns[new_msg] = 1

    def system_warning(self, msg):
        if C.SYSTEM_WARNINGS:
            self._warning(msg)

