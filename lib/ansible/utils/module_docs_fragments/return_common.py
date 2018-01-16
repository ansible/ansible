# Copyright (c) 2016 Ansible, Inc
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


class ModuleDocFragment(object):

    # Standard documentation fragment
    RETURN = '''
changed:
    description: Whether the module affected changes on the target.
    returned: always
    type: bool
    sample: False
failed:
    description: Whether the module failed to execute.
    returned: always
    type: bool
    sample: True
msg:
    description: Human-readable message.
    returned: as needed
    type: string
    sample: "all ok"
skipped:
    description: Whether the module was skipped.
    returned: always
    type: bool
    sample: False
results:
    description: List of module results,
    returned: when using a loop.
    type: list
    sample: [{changed: True, msg: 'first item changed'}, {changed: False, msg: 'second item ok'}]
exception:
    description: Optional information from a handled error.
    returned: on some errors
    type: string
    sample: 'Unknown error'
'''
