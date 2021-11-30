# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = r'''
attributes:
    check_mode:
      description: Can run in check_mode and return changed status prediction withought modifying target
    diff_mode:
      description: Will return details on what has changed (or possibly needs changing in check_mode), when in diff mode
    platform:
      description: Target OS/families that can be operated against
      support: N/A
'''

    ACTIONGROUPS = r'''
attributes:
    action_group:
      description: Action is part of action_group(s), for convenient setting of module_defaults.
      support: N/A
      membership: []
'''

    CONN = r'''
attributes:
    become:
      description: Is usable alongside become keywords
    connection:
      description: Uses the target's configured connection information to execute code on it
    delegation:
      description: Can be used in conjunction with delegate_to and related keywords
'''

    FACTS = r'''
attributes:
    facts:
      description: Action returns an C(ansible_facts) dictionary that will update existing host facts
'''

    FILES = r'''
attributes:
    safe_file_operations:
      description: Uses Ansbile's strict file operation functions to ensure proper permissions and avoid data corruption
    vault:
      description: Can automatically decrypt Ansible vaulted files
'''

    FLOW = r'''
attributes:
    action:
      description: Indicates this has a corresponding action plugin so some parts of the options can be executed on the controller
    async:
      description: Supports being used with the C(async) keyword
    bypass_host_loop:
      description:
            - Forces a 'global' task that does not execute per host, this bypasses per host templating and serial,
              throttle and other loop considerations
            - Conditionals will work as if C(run_once) is being used, variables used will be from the first available host
            - This action will not work normally outside of lockstep strategies
'''
    RAW = r'''
attributes:
    raw:
      description: Indicates if an action takes a 'raw' or 'free form' string as an option and has it's own special parsing of it
'''
