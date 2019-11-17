# (c) 2019, Red Hat, Inc.
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

import os

from abc import abstractmethod
from ansible.utils.multiprocessing import context as multiprocessing_context


class AnsibleProcessBase(multiprocessing_context.Process):

    __metaclass__ = type

    def _hard_exit(self, e):
        try:
            display.debug(u"WORKER HARD EXIT: %s" % to_text(e))
        except BaseException:
            pass
        os._exit(1)

    def run(self):
        try:
            return self._run()
        except BaseException as e:
            self._hard_exit(e)

    @abstractmethod
    def _run(self):
        pass
