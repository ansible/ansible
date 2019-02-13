# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, Dimension Data
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Authors:
#   - Adam Friedman  <tintoy@tintoy.io>


class ModuleDocFragment(object):

    # Dimension Data ("wait-for-completion" parameters) doc fragment
    DOCUMENTATION = r'''

options:
  wait:
    description:
      - Should we wait for the task to complete before moving onto the next.
    type: bool
    default: no
  wait_time:
    description:
      - The maximum amount of time (in seconds) to wait for the task to complete.
      - Only applicable if I(wait=true).
    type: int
    default: 600
  wait_poll_interval:
    description:
      - The amount of time (in seconds) to wait between checks for task completion.
      - Only applicable if I(wait=true).
    type: int
    default: 2
    '''
