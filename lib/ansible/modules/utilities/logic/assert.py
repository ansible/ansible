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
module: assert
short_description: Fail with custom message
description:
     - This module asserts that a given expression is true and can be a simpler alternative to the 'fail' module in some cases.
version_added: "1.5"
options:
  that:
    description:
      - "A string expression of the same form that can be passed to the 'when' statement"
      - "Alternatively, a list of string expressions"
    required: true
author: Michael DeHaan
'''

EXAMPLES = '''
- assert: { that: "ansible_os_family != 'RedHat'" }

- assert: 
    that: 
      - "'foo' in some_command_result.stdout" 
      - "number_of_the_counting == 3"
'''
