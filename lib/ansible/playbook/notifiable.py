# -*- coding: utf-8 -*-
# Copyright The Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.playbook.attribute import FieldAttribute


class Notifiable:
    notify = FieldAttribute(isa='list')
