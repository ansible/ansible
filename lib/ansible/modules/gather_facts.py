#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: gather_facts
version_added: 2.8
short_description: Gathers facts about remote hosts
extends_documentation_fragment:
  -  action_common_attributes
  -  action_common_attributes.facts
  -  action_common_attributes.flow
description:
     - This module takes care of executing the R(configured facts modules,FACTS_MODULES), the default is to use the M(ansible.builtin.setup) module.
     - This module is automatically called by playbooks to gather useful variables about remote hosts that can be used in playbooks.
     - It can also be executed directly by C(/usr/bin/ansible) to check what variables are available to a host.
     - Ansible provides many I(facts) about the system, automatically.
options:
    parallel:
        description:
            - A toggle that controls if the fact modules are executed in parallel or serially and in order.
              This can guarantee the merge order of module facts at the expense of performance.
            - By default it will be true if more than one fact module is used.
        type: bool
attributes:
    action:
        support: full
    async:
        details: multiple modules can be executed in parallel or serially, but the action itself will not be async
        support: partial
    bypass_host_loop:
        support: none
    check_mode:
        details: since this action should just query the target system info it always runs in check mode
        support: full
    diff_mode:
        support: none
    facts:
        support: full
    platform:
        details: The action plugin should be able to automatically select the specific platform modules automatically or can be configured manually
        platforms: all
notes:
    - This is mostly a wrapper around other fact gathering modules.
    - Options passed into this action must be supported by all the underlying fact modules configured.
    - Facts returned by each module will be merged, conflicts will favor 'last merged'.
      Order is not guaranteed, when doing parallel gathering on multiple modules.
author:
    - "Ansible Core Team"
'''

RETURN = """
# depends on the fact module called
"""

EXAMPLES = """
# Display facts from all hosts and store them indexed by hostname at /tmp/facts.
# ansible all -m gather_facts --tree /tmp/facts
"""
