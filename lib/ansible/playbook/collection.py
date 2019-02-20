# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.six import string_types
from ansible.playbook.attribute import FieldAttribute


class Collection:
    _collections = FieldAttribute(isa='list', listof=string_types)

    def __init__(self):
        super(Collection, self).__init__()
