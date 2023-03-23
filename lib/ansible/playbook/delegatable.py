# -*- coding: utf-8 -*-
# Copyright The Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.playbook.attribute import FieldAttribute


class Delegatable:
    delegate_to = FieldAttribute(isa='string')
    delegate_facts = FieldAttribute(isa='bool')

    def _post_validate_delegate_to(self, attr, value, templar):
        """This method exists just to make it clear that ``Task.post_validate``
        does not template this value, it is set via ``TaskExecutor._calculate_delegate_to``
        """
        return value
