# Get systemd version and features
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

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts.collector import BaseFactCollector
from ansible.module_utils.facts.system.service_mgr import ServiceMgrFactCollector


class SystemdFactCollector(BaseFactCollector):
    name = "systemd"
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        systemctl_bin = module.get_bin_path("systemctl")
        systemd_facts = {}
        if systemctl_bin and ServiceMgrFactCollector.is_systemd_managed(module):
            rc, stdout, dummy = module.run_command(
                [systemctl_bin, "--version"],
                check_rc=False,
            )

            if rc != 0:
                return systemd_facts

            systemd_facts["systemd"] = {
                "features": str(stdout.split("\n")[1]),
                "version": int(stdout.split(" ")[1]),
            }

        return systemd_facts
