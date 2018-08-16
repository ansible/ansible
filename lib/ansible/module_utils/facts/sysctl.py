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

import re


def get_sysctl(module, prefixes):
    sysctl_cmd = module.get_bin_path('sysctl')
    cmd = [sysctl_cmd]
    cmd.extend(prefixes)

    rc, out, err = module.run_command(cmd)
    if rc != 0:
        return dict()

    sysctl = dict()
    for line in out.splitlines():
        if not line:
            continue
        (key, value) = re.split(r'\s?=\s?|: ', line, maxsplit=1)
        sysctl[key] = value.strip()

    return sysctl
