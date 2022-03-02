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

import shlex
import os

from ansible.module_utils.facts.utils import get_file_content

from ansible.module_utils.facts.collector import BaseFactCollector


def parse_file(file_content):
    result = {}
    for line in file_content.splitlines():
        if line.startswith('#'):
            continue
        for t in shlex.split(line):
            (k, v) = t.split('=', 1)
            result[k] = v
    return result


class OSReleaseFactCollector(BaseFactCollector):
    name = 'os-release'
    _fact_ids = set(['os_release'])

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}
        path = None
        # /etc/os-release take precedence, per
        # https://www.freedesktop.org/software/systemd/man/os-release.html
        for f in ['/usr/lib/os-release', '/etc/os-release']:
            if os.path.exists(f):
                path = f
        if path:
            facts_dict['os_release'] = parse_file(get_file_content(path))
        return facts_dict
