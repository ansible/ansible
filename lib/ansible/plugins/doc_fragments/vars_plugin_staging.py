# -*- coding: utf-8 -*-

# Copyright: (c) 2019,  Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  stage:
    description:
      - Control when this vars plugin may be executed.
      - Setting this option to V(all) will run the vars plugin after importing inventory and whenever it is demanded by a task.
      - Setting this option to V(task) will only run the vars plugin whenever it is demanded by a task.
      - Setting this option to V(inventory) will only run the vars plugin after parsing inventory.
      - If this option is omitted, the global C(RUN_VARS_PLUGINS) configuration is used to determine when to execute the vars plugin.
    choices: ['all', 'task', 'inventory']
    version_added: "2.10"
    type: str
'''
