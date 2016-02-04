#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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
module: fireball
short_description: Enable fireball mode on remote node
version_added: "0.9"
deprecated: "in favor of SSH with ControlPersist"
description:
    - Modern SSH clients support ControlPersist which is just as fast as
      fireball was.  Please enable that in ansible.cfg as a replacement
      for fireball.
    - Removed in ansible 2.0.
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
'''

EXAMPLES = '''
'''

