# -*- mode: python -*-

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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: remove_host
short_description: remove a host from the ansible-playbook in-memory inventory
description:
  - Use variables to remove hosts from the inventory to ignore them in later
    plays of the same playbook.  Takes variables so you can define the new
    hosts more fully.
version_added: "2.10"
options:
  name:
    description:
    - The hostname of the host to remove to the inventory.
    required: true
notes:
    - This module bypasses the play host loop and only runs once for all the hosts in the play, if you need it
      to iterate use a with directive.
author:
  - James Pic (@jpic)
'''

EXAMPLES = '''
# remove host 'just_created'
- remove_host:
    name: just_created
'''

RETURN = '''
host_name:
    description: Name of the host that has been removed
    returned: success
    type: str
    sample: "example"
'''
