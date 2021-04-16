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
    until:
      description: Usable inside until/retry loops
      support: full
    windows:
      description: Can be run against Windows OS targets
      support: none
'''
