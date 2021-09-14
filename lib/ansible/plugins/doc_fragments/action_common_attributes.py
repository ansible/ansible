# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Ansible, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = r'''
attributes:
    action:
      description: Indicates this has a corresponding action plugin so some parts of the options can be executed on the controller
      support: unknown
    action_group:
      description: Action is part of action_group(s), for convenient setting of module_defaults.
      support: unknown
      membership: []
    api:
      description: Instead of executing code on a target, this action interacts with an API on behalf of the target.
      support: unknown
    async:
      description: Supports being used with the ``async`` keyword
      support: unknown
    become:
      description: Is usable alongside become keywords
      support: unknown
    bypass_host_loop:
      description: Forces a 'global' task that does not execute per host, this bypasses per host templating and serial,
                   throttle and other loop considerations.  Also, this action cannot be used in non lockstep strategies
      support: unknown
    check_mode:
      description: Can run in check_mode and return changed status prediction withought modifying target
      support: unknown
    connection:
      description: Uses the target's configured connection information to execute code on it
      support: unknown
    conditional:
      description: Will respect the `when` keyword  per item loop or task (when no loop is present)
      support: unknown
    delegation:
      description: Can be used in conjunction with delegate_to and related keywords
      support: unknown
    diff_mode:
      description: Will return details on what has changed (or possibly needs changing in check_mode), when in diff mode
      support: unknown
    facts:
      description: Action returns an ``ansible_facts`` dictionary that will update existing host facts
      support: unknown
    forced_local:
      description: The connection itself is passed to the action while the code is still executed on the controller
      support: unknown
    forced_action_plugin:
      description: This action uses a specific action plugin instead of 'normal' or matching by name
      support: unknown
      action_plugin: none
    info:
      description: This returns general info (not facts) that you might want to register into a variable for later use
      support: unknown
    loops:
      description: both ``loop`` and ``with_`` looping keywords will be honored
      support: unknown
    proprietary:
      description: Designed to only be run against specific proprietary OS(s), normally a network appliance or similar
      support: unknown
      platforms: []
    posix:
      description: Can be run against most POSIX (and GNU/Linux) OS targets
      support: unknown
    safe_file_operations:
      description: Uses Ansbile's strict file operation functions to ensure proper permissions and avoid data corruption
      support: unknown
    tags:
      description: Tags will be evaluated to determine if this task considered for execution
      support: unknown
    tty:
      description: requires direct access to a TTY
      support: unknown
    turbo:
      description: Uses an Ansible supplied caching mechanism (Turbo!) on the remote for authentication and
                   3rd party libraries to speed up recurrent execution
      support: unknown
    until:
      description: Usable with until/retry loops
      support: unknown
    vault:
      description: Can automatically decrypt Ansible vaulted files
      support: unknown
    windows:
      description: Can be run against Windows OS targets
      support: unknown
'''

    ANSIBLE_CORE_DEFAULTS = r'''
attributes:
    action:
      support: none
    action_group:
      support: none
    api:
      support: none
    async:
      support: full
    become:
      support: full
    bypass_host_loop:
      support: none
    check_mode:
      support: none
    connection:
      support: full
    conditional:
      support: full
    delegation:
      support: full
    diff_mode:
      support: none
    facts:
      support: none
    forced_local:
      support: none
    forced_action_plugin:
      support: none
    info:
      support: none
    loops:
      support: full
    proprietary:
      support: none
    posix:
      support: full
    safe_file_operations:
      support: none
    tags:
      support: full
    tty:
      support: none
    turbo:
      support: none
    until:
      support: full
    vault:
      support: none
    windows:
      support: none
'''
