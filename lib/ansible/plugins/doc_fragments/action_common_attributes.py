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
      description: Indicates this has a corresponding action plugin so some parts of the options can be executed on the controller.
      support: no
    async:
      description: Supports being used with the ``async`` keyword
      support: full
    bypass_host_loop:
      description: Forces a 'global' task that does not execute per host, cannot be used in non lockstep strategies
      support: no
    check_mode:
      description: Can run in check_mode and return changed status prediction
      support: no
    connection:
      description: Uses the target's configured connection information to execute code on it
      support: full
    delegation:
      description: Can be used in conjunction with delegate_to and related keywords
      support: full
    diff_mode:
      description: Will return details on what has changed when in diff mode
      support: no
    facts:
      description: Action returns an ``ansible_facts`` dictionary that will update existing host facts
      support: no
'''
