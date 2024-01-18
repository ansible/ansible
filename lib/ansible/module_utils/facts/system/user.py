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

import getpass
import os
import pwd

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts.collector import BaseFactCollector


class UserFactCollector(BaseFactCollector):
    name = 'user'
    _fact_ids = set(['user_id', 'user_uid', 'user_gid',
                     'user_gecos', 'user_dir', 'user_shell',
                     'real_user_id', 'effective_user_id',
                     'effective_group_ids'])  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        user_facts = {}

        user_facts['user_id'] = getpass.getuser()

        try:
            pwent = pwd.getpwnam(getpass.getuser())
        except KeyError:
            pwent = pwd.getpwuid(os.getuid())

        user_facts['user_uid'] = pwent.pw_uid
        user_facts['user_gid'] = pwent.pw_gid
        user_facts['user_gecos'] = pwent.pw_gecos
        user_facts['user_dir'] = pwent.pw_dir
        user_facts['user_shell'] = pwent.pw_shell
        user_facts['real_user_id'] = os.getuid()
        user_facts['effective_user_id'] = os.geteuid()
        user_facts['real_group_id'] = os.getgid()
        user_facts['effective_group_id'] = os.getgid()

        return user_facts
