#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Chris Hoffman <choffman@chathamfinancial.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_service
version_added: "1.7"
short_description: Manages Windows services
description:
    - Manages Windows services
options:
  name:
    description:
      - Name of the service
    required: true
    default: null
    aliases: []
  start_mode:
    description:
      - Set the startup type for the service
    required: false
    choices:
      - auto
      - manual
      - disabled
  state:
    description:
      - C(started)/C(stopped) are idempotent actions that will not run
        commands unless necessary.  C(restarted) will always bounce the
        service.
    required: false
    choices:
      - started
      - stopped
      - restarted
    default: null
    aliases: []
author: Chris Hoffman
'''

EXAMPLES = '''
  # Restart a service
  win_service:
    name: spooler
    state: restarted

  # Set service startup mode to auto and ensure it is started
  win_service:
    name: spooler
    start_mode: auto
    state: started
'''
