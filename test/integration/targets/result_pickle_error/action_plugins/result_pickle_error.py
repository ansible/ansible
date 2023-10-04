# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.plugins.action import ActionBase
from jinja2 import Undefined


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        return {'obj': Undefined('obj')}
