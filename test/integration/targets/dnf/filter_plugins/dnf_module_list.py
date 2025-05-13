# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from collections import Counter


def parse_module_list(stdout):
    lines = stdout.splitlines()
    name_offset = 0
    empty_offset = -1
    modules = []
    for i, line in enumerate(lines):
        if line.startswith('Name '):
            name_offset = i + 1
        if not line.strip():
            empty_offset = i
    for line in lines[name_offset:empty_offset]:
        cols = line.split()[:3]
        modules.append({
            'name': cols[0],
            'version': cols[1],
            'profile': cols[2].rstrip(','),  # Just the first profile
        })
    return modules


def get_first_single_version_module(stdout):
    modules = parse_module_list(stdout)
    name = Counter([m['name'] for m in modules]).most_common()[-1][0]
    module, = [m for m in modules if m['name'] == name]
    return module


class FilterModule:
    def filters(self):
        return {
            'get_first_single_version_module': get_first_single_version_module,
        }
