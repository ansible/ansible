# unit tests for ansible system lsb fact collectors
# -*- coding: utf-8 -*-
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
#

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.facts.system.user import UserFactCollector

import os


def test_logname():
    """ Test if ``UserFactCollector`` still works with LOGNAME set """
    collector = UserFactCollector()

    unmodified_facts = collector.collect()
    # Change logname env var and check if the collector still finds
    # the pw entry.
    os.environ["LOGNAME"] = "NONEXISTINGUSERDONTEXISTPLEASE"
    modified_facts = collector.collect()

    # Set logname should be different to the real name.
    assert unmodified_facts['user_id'] != modified_facts['user_id']
    # Actual UID is the same.
    assert unmodified_facts['user_uid'] == modified_facts['user_uid']
