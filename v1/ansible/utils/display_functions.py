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

import textwrap

from ansible import constants as C
from ansible import errors
from ansible.callbacks import display

__all__ = ['deprecated', 'warning', 'system_warning']

# list of all deprecation messages to prevent duplicate display
deprecations = {}
warns = {}

def deprecated(msg, version, removed=False):
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
        raise errors.AnsibleError("[DEPRECATED]: %s.  Please update your playbooks." % msg)

    wrapped = textwrap.wrap(new_msg, 79)
    new_msg = "\n".join(wrapped) + "\n"

    if new_msg not in deprecations:
        display(new_msg, color='purple', stderr=True)
        deprecations[new_msg] = 1

def warning(msg):
    new_msg = "\n[WARNING]: %s" % msg
    wrapped = textwrap.wrap(new_msg, 79)
    new_msg = "\n".join(wrapped) + "\n"
    if new_msg not in warns:
        display(new_msg, color='bright purple', stderr=True)
        warns[new_msg] = 1

def system_warning(msg):
    if C.SYSTEM_WARNINGS:
        warning(msg)

