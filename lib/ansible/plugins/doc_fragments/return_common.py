# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ansible, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):
    # Standard documentation fragment
    RETURN = r"""
changed:
  description: Whether the module affected changes on the target.
  returned: always
  type: bool
  sample: false
failed:
  description: Whether the module failed to execute.
  returned: always
  type: bool
  sample: true
msg:
  description: Human-readable message.
  returned: as needed
  type: str
  sample: all ok
skipped:
  description: Whether the module was skipped.
  returned: always
  type: bool
  sample: false
results:
  description: List of module results.
  returned: when using a loop.
  type: list
  sample: [{changed: True, msg: 'first item changed'}, {changed: False, msg: 'second item ok'}]
exception:
  description: Optional information from a handled error.
  returned: on some errors
  type: str
  sample: Unknown error
"""
