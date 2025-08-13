# -*- coding: utf-8 -*-
# Copyright: (c) , Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


# WARNING: this is mostly here as a convenience for documenting core behaviours, no plugin outside of ansible-core should use this file
class ModuleDocFragment(object):

    # requires action_common
    DOCUMENTATION = r"""
attributes:
    async:
      support: none
    become:
      support: none
    bypass_task_loop:
      description: These tasks ignore the C(loop) and C(with_) keywords
    core:
      description: This is a 'core engine' feature and is not implemented like most task actions, so it is not overridable in any way via the plugin system.
      support: full
    connection:
      support: none
    ignore_conditional:
      support: none
      description: The action is not subject to conditional execution so it will ignore the C(when:) keyword
    platform:
      support: full
      platforms: all
    until:
      description: Denotes if this action obeys until/retry/poll keywords
      support: none
    tags:
      description: Allows for the 'tags' keyword to control the selection of this action for execution
      support: full
"""

    # also requires core above
    IMPORT = r"""
attributes:
    action:
      details: While this action executes locally on the controller it is not governed by an action plugin
      support: none
    bypass_host_loop:
      details: While the import can be host specific and runs per host it is not dealing with all available host variables,
               use an include instead for those cases
      support: partial
    bypass_task_loop:
      details: The task itself is not looped, but the loop is applied to each imported task
      support: partial
    delegation:
      details: Since there are no connection nor facts, there is no sense in delegating imports
      support: none
    ignore_conditional:
      details: While the action itself will ignore the conditional, it will be inherited by the imported tasks themselves
      support: partial
    tags:
      details: Tags are not interpreted for this action, they are applied to the imported tasks
      support: none
    until:
      support: none
"""
    # also requires core above
    INCLUDE = r"""
attributes:
    action:
      details: While this action executes locally on the controller it is not governed by an action plugin
      support: none
    bypass_host_loop:
      support: none
    bypass_task_loop:
      support: none
    delegation:
      details: Since there are no connection nor facts, there is no sense in delegating includes
      support: none
    tags:
      details: Tags are interpreted by this action but are not automatically inherited by the include tasks, see C(apply)
      support: partial
"""
