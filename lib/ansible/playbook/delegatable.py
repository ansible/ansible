# -*- coding: utf-8 -*-
 # Copyright The Ansible project
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.playbook.attribute import FieldAttribute


class Delegatable:
    delegate_to = FieldAttribute(isa='string')
    delegate_facts = FieldAttribute(isa='bool')
