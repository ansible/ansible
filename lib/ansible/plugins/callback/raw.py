# (c) 2012-2014, Ansible, Inc
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    '''
    This callback prings results in json format.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'raw'

    def v2_runner_on_ok(self, result):
        print(self._dump_results(result._result), end='')

    def v2_runner_on_failed(self, result):
        print(self._dump_results(results._result), end='')

    def v2_runner_on_unreachable(self, result):
        print(self._dump_results(results._result), end='')
