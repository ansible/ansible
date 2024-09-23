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

import re

from ansible.module_utils.common.text.converters import to_text


def get_sysctl(module, prefixes):

    sysctl = dict()
    sysctl_cmd = module.get_bin_path('sysctl')
    if sysctl_cmd is not None:

        cmd = [sysctl_cmd]
        cmd.extend(prefixes)

        try:
            rc, out, err = module.run_command(cmd)
        except (IOError, OSError) as e:
            module.warn('Unable to read sysctl: %s' % to_text(e))
            rc = 1

        if rc == 0:
            key = ''
            value = ''
            for line in out.splitlines():
                if not line.strip():
                    continue

                if line.startswith(' '):
                    # handle multiline values, they will not have a starting key
                    # Add the newline back in so people can split on it to parse
                    # lines if they need to.
                    value += '\n' + line
                    continue

                if key:
                    sysctl[key] = value.strip()

                try:
                    (key, value) = re.split(r'\s?=\s?|: ', line, maxsplit=1)
                except Exception as e:
                    module.warn('Unable to split sysctl line (%s): %s' % (to_text(line), to_text(e)))

            if key:
                sysctl[key] = value.strip()

    return sysctl
