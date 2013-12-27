#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Dag Wieers <dag@wieers.com>
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

DOCUMENTATION = '''
---
module: fail
short_description: Fail with custom message
description:
     - This module fails the progress with a custom message. It can be
       useful for bailing out when a certain condition is met using C(when).
version_added: "0.8"
options:
  msg:
    description:
      - The customized message used for failing execution. If omitted,
        fail will simple bail out with a generic message.
    required: false
    default: "'Failed as requested from task'"

author: Dag Wieers
'''

EXAMPLES = '''
# Example playbook using fail and when together
- fail: msg="The system may not be provisioned according to the CMDB status."
  when: cmdb_status != "to-be-staged"
'''
