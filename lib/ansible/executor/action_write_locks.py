# (c) 2016 - Red Hat, Inc. <info@ansible.com>
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

from multiprocessing import Lock

from ansible.module_utils import six
from ansible.module_utils.facts.system.pkg_mgr import PKG_MGRS
from ansible.utils.multiprocessing import context as multiprocessing_context


try:
    action_write_locks
except (NameError, UnboundLocalError):
    action_manager = multiprocessing_context.Manager()
    if six.PY2:
        action_dict = dict
        action_lock = Lock
    else:
        action_dict = action_manager.dict
        action_lock = action_manager.Lock

    # These plugins are known to be called directly by action plugins
    # with names differing from the action plugin name. We precreate
    # them here as an optimization.
    action_write_locks = action_dict(
        copy=action_lock(),
        file=action_lock(),
        setup=action_lock(),
        slurp=action_lock(),
        stat=action_lock(),
    )

    # Below is a Lock for use when we weren't expecting a named module.  It gets used when an action
    # plugin invokes a module whose name does not match with the action's name.  Slightly less
    # efficient as all processes with unexpected module names will wait on this lock
    action_write_locks[None] = action_lock()

    # If a list of service managers is created in the future we can do the same for them.
    for p in PKG_MGRS:
        action_write_locks[p["name"]] = action_lock()
