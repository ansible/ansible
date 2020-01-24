# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Or Soffer <orso@checkpoint.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  state:
    description:
      - State of the access rule (present or absent). Defaults to present.
    type: str
    default: present
    choices:
      - 'present'
      - 'absent'
  auto_publish_session:
    description:
      - Publish the current session if changes have been performed
        after task completes.
    type: bool
  wait_for_task:
    description:
      - Wait for the task to end. Such as publish task.
    type: bool
    default: True
  version:
    description:
      - Version of checkpoint. If not given one, the latest version taken.
    type: str
'''
