#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_vnic_profile_info
short_description: Retrieve information about one or more oVirt/RHV vnic profiles
author: "Martin Necas (@mnecas)"
version_added: "2.10"
description:
    - "Retrieve information about one or more oVirt/RHV vnic profiles."
notes:
    - "This module returns a variable C(ovirt_vnic_profiles), which
       contains a list of vnic profiles. You need to register the result with
       the I(register) keyword to use it."
options:
    max:
        description:
            - "The maximum number of results to return."
        type: int
    name:
        description:
            - "Name of vnic profile."
        type: str
extends_documentation_fragment: ovirt_info
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather information 10 vnic profiles
- ovirt_vnic_profile_info:
    max: 10
  register: result
- debug:
    msg: "{{ result.ovirt_vnic_profiles }}"
'''

RETURN = '''
ovirt_vnic_profiles:
    description: "List of dictionaries describing the vnic profiles. Vnic_profile attributes are mapped to dictionary keys,
                  all vnic profiles attributes can be found at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/vnic_profile."
    returned: On success.
    type: list
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_info_full_argument_spec,
)


def main():
    argument_spec = ovirt_info_full_argument_spec(
        max=dict(default=None, type='int'),
        name=dict(default=None),
    )
    module = AnsibleModule(argument_spec)
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        vnic_profiles_service = connection.system_service().vnic_profiles_service()
        vnic_profiles = vnic_profiles_service.list(max=module.params.get('max'))
        if module.params.get('name') and vnic_profiles:
            vnic_profiles = [vnic_profile for vnic_profile in vnic_profiles if vnic_profile.name == module.params.get("name")]

        result = dict(
            ovirt_vnic_profiles=[
                get_dict_of_struct(
                    struct=c,
                    connection=connection,
                    fetch_nested=module.params.get('fetch_nested'),
                    attributes=module.params.get('nested_attributes'),
                ) for c in vnic_profiles
            ],
        )
        module.exit_json(changed=False, **result)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
