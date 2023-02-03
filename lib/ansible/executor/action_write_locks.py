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

from __future__ import annotations

import multiprocessing.synchronize

from multiprocessing import Lock

from ansible.module_utils.facts.system.pkg_mgr import PKG_MGRS

if 'action_write_locks' not in globals():
    # Do not initialize this more than once because it seems to bash
    # the existing one.  multiprocessing must be reloading the module
    # when it forks?
    action_write_locks: dict[str | None, multiprocessing.synchronize.Lock] = dict()

    # Below is a Lock for use when we weren't expecting a named module.  It gets used when an action
    # plugin invokes a module whose name does not match with the action's name.  Slightly less
    # efficient as all processes with unexpected module names will wait on this lock
    action_write_locks[None] = Lock()

    # These plugins are known to be called directly by action plugins with names differing from the
    # action plugin name.  We precreate them here as an optimization.
    # If a list of service managers is created in the future we can do the same for them.
    mods = set(p['name'] for p in PKG_MGRS)

    mods.update(('copy', 'file', 'setup', 'slurp', 'stat'))
    for mod_name in mods:
        action_write_locks[mod_name] = Lock()
