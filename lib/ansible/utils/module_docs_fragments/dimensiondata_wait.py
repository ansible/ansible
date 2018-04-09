# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Dimension Data
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   - Adam Friedman  <tintoy@tintoy.io>


class ModuleDocFragment(object):

    # Dimension Data ("wait-for-completion" parameters) doc fragment
    DOCUMENTATION = '''

options:
  wait:
    description:
      - Should we wait for the task to complete before moving onto the next.
    required: false
    default: false
  wait_time:
    description:
      - The maximum amount of time (in seconds) to wait for the task to complete.
      - Only applicable if I(wait=true).
    required: false
    default: 600
  wait_poll_interval:
    description:
      - The amount of time (in seconds) to wait between checks for task completion.
      - Only applicable if I(wait=true).
    required: false
    default: 2
    '''
