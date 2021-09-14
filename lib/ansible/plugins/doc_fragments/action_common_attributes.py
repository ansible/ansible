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
      default_support_value: none
    action_group:
      description: Action is part of action_group(s), for convenient setting of module_defaults.
      default_support_value: none
      membership: []
    api:
      description: Instead of executing code on a target, this action interacts with an API on behalf of the target.
      default_support_value: none
    async:
      description: Supports being used with the ``async`` keyword
      default_support_value: full
    become:
      description: Is usable alongside become keywords
      default_support_value: full
    bypass_host_loop:
      description: Forces a 'global' task that does not execute per host, this bypasses per host templating and serial,
                   throttle and other loop considerations.  Also, this action cannot be used in non lockstep strategies
      default_support_value: none
    check_mode:
      description: Can run in check_mode and return changed status prediction withought modifying target
      default_support_value: none
    connection:
      description: Uses the target's configured connection information to execute code on it
      default_support_value: full
    conditional:
      description: Will respect the `when` keyword  per item loop or task (when no loop is present)
      default_support_value: full
    delegation:
      description: Can be used in conjunction with delegate_to and related keywords
      default_support_value: full
    diff_mode:
      description: Will return details on what has changed (or possibly needs changing in check_mode), when in diff mode
      default_support_value: none
    facts:
      description: Action returns an ``ansible_facts`` dictionary that will update existing host facts
      default_support_value: none
    forced_local:
      description: The connection itself is passed to the action while the code is still executed on the controller
      default_support_value: none
    forced_action_plugin:
      description: This action uses a specific action plugin instead of 'normal' or matching by name
      default_support_value: none
      action_plugin: none
    info:
      description: This returns general info (not facts) that you might want to register into a variable for later use
      default_support_value: none
    loops:
      description: both ``loop`` and ``with_`` looping keywords will be honored
      default_support_value: full
    proprietary:
      description: Designed to only be run against specific proprietary OS(s), normally a network appliance or similar
      default_support_value: none
      platforms: []
    posix:
      description: Can be run against most POSIX (and GNU/Linux) OS targets
      default_support_value: full
    safe_file_operations:
      description: Uses Ansbile's strict file operation functions to ensure proper permissions and avoid data corruption
      default_support_value: none
    tags:
      description: Tags will be evaluated to determine if this task considered for execution
      default_support_value: full
    tty:
      description: requires direct access to a TTY
      default_support_value: none
    turbo:
      description: Uses an Ansible supplied caching mechanism (Turbo!) on the remote for authentication and
                   3rd party libraries to speed up recurrent execution
      default_support_value: none
    until:
      description: Usable with until/retry loops
      default_support_value: full
    vault:
      description: Can automatically decrypt Ansible vaulted files
      default_support_value: none
    windows:
      description: Can be run against Windows OS targets
      default_support_value: none
'''
