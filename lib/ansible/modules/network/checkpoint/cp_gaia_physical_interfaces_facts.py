#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage CheckPoint Firewall (c) 2019
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

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: cp_gaia_physical_interfaces_facts
author: Yuval Feiger (@chkp-yuvalfe)
description:
- Show Physical interfaces
short_description: Show Physical interfaces
version_added: '2.9'
options:
  name:
    description: interface name to show.
    required: false
    type: str

"""

EXAMPLES = """
- name: Show physical interfaces
  cp_gaia_physical_interfaces_facts:

- name: Show physical interface by specifying it name
  cp_gaia_physical_interfaces_facts:
    name: eth0

"""

RETURN = """
cp_gaia_physical_interface:
  description: The interface/s facts.
  returned: always.
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import api_call_gaia


def main():
    # arguments for the module:
    fields = dict(
        name=dict(required=False, type="str")
    )
    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)
    was_changed = False
    module_key_params = dict((k, v) for k, v in module.params.items() if k in ["name"] and v is not None)

    if len(module_key_params) > 0:
        res = api_call_gaia(module=module, api_call_object="show-physical-interface")
    else:
        res = api_call_gaia(module=module, api_call_object="show-physical-interfaces")
    module.exit_json(response=res, changed=was_changed)


if __name__ == "__main__":
    main()
