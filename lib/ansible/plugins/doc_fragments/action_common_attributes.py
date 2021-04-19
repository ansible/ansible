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
      support: none
    action_group:
      description: If module_defaults are settable for this action, as it is part of an action_group
      support: none
      membership: []
    async:
      description: Supports being used with the ``async`` keyword
      support: full
    become:
      description: Is usable alongside become keywords
      support: full
    bypass_host_loop:
      description: Forces a 'global' task that does not execute per host, cannot be used in non lockstep strategies
      support: none
    check_mode:
      description: Can run in check_mode and return changed status prediction
      support: none
    connection:
      description: Uses the target's configured connection information to execute code on it
      support: full
    conditional:
      description: Will respect the `when` keyword  per item loop or task (when no loop is present)
      support: full
    delegation:
      description: Can be used in conjunction with delegate_to and related keywords
      support: full
    diff:
      description: Will return details on what has changed when in diff is enabled
      support: none
    facts:
      description: Action returns an ``ansible_facts`` dictionary that will update existing host facts
      support: none
    forced_local:
      description: The connection itself is passed to the action while the code is still executed on the controller
      support: none
    forced_action_plugin:
      description: This action uses a specific action plugin instead of 'normal' or matching by name
      support: none
      action_plugin: none
    info:
      description: This returns general info (not facts) that you might want to register into a variable for later use
      support: none
    loops:
      description: both ``loop`` and ``with_`` looping keywords will be honored.
      support: full
    proprietary:
      description: Can only be run against specific proprietary OS, normally a network appliance or similar
      support: none
    posix:
      description: Can be run against most POSIX (and GNU/Linux) OS targets
      support: full
    tags:
      description: Tags will determine if this task considered for execution
      support: full
    tty:
      description: requires direct access to a TTY
      support: none
    turbo:
      description: Uses an Ansible supplied caching mechanism (Turbo!) on the remote for authentication and
                   3rd party libraries to speed up recurrent execution.
      support: none
    until:
      description: Usable with until/retry loops
      support: full
    windows:
      description: Can be run against Windows OS targets
      support: none
'''
