# Copyright (c) 2019 Marco Marinello <me@marcomarinello.it>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Shutdown a *nix host

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from . import reboot

class ActionModule(reboot.ActionModule):
    DEFAULT_REBOOT_MESSAGE = 'Shutdown initiated by Ansible'
    DEFAULT_SHUTDOWN_COMMAND_ARGS = '-h {delay_min} "{message}"'

    SHUTDOWN_COMMAND_ARGS = {
        'alpine': '',
        'freebsd': '-h +{delay_sec}s "{message}"',
        'linux': DEFAULT_SHUTDOWN_COMMAND_ARGS,
        'macosx': '-h +{delay_min} "{message}"',
        'openbsd': '-h +{delay_min} "{message}"',
        'solaris': '-y -g {delay_sec} -i 6 "{message}"',
        'sunos': '-y -g {delay_sec} -i 6 "{message}"',
        'vmkernel': '-d {delay_sec}',
        'aix': '-F',
    }
