# (c) 2016, Steve Kuznetsov <skuznets@redhat.com>
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

from units.compat import unittest
from units.compat.mock import MagicMock

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.playbook import Playbook
from ansible.plugins.callback import CallbackBase
from ansible.utils import context_objects as co

__metaclass__ = type


class TestTaskQueueManagerCallbacks(unittest.TestCase):
    # FIXME: callbacks now occur in the results proc, but
    #        the TQM can still send direct callbacks there
    #        so we may want to rewrite this test.
    pass
