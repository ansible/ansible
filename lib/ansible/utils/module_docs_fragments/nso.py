# -*- coding: utf-8 -*-

# Copyright (c) 2017 Cisco and/or its affiliates.
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
#


class ModuleDocFragment(object):

    DOCUMENTATION = '''
notes:
  - Cisco NSO version 4.4.3 or higher required.
options:
  url:
    description: NSO JSON-RPC URL, http://localhost:8080/jsonrpc
    required: true
  username:
    description: NSO username
    required: true
  password:
    description: NSO password
    required: true
requirements:
  - Cisco NSO version 4.4.3 or higher
'''
