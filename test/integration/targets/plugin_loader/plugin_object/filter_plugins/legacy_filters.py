# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ansible_name = None
ansible_aliases = None


def legacy_filter(data):
    return {'filter_file_name': ansible_name, 'filter_file_aliases': ansible_aliases}


class FilterModule(object):
    def filters(self):
        global ansible_name
        global ansible_aliases
        ansible_name = self.ansible_name
        ansible_aliases = self.ansible_aliases

        return {
            'legacy_filter': legacy_filter
        }
