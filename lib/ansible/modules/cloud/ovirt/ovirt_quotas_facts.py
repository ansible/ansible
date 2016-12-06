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

import fnmatch
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_full_argument_spec,
    search_by_name,
)


ANSIBLE_METADATA = {'status': 'preview',
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: ovirt_quotas_facts
short_description: Retrieve facts about one or more oVirt quotas
version_added: "2.3"
description:
    - "Retrieve facts about one or more oVirt quotas."
notes:
    - "This module creates a new top-level C(ovirt_quotas) fact, which
       contains a list of quotas."
options:
    datacenter:
        description:
            - "Name of the datacenter where quota resides."
        required: true
    name:
        description:
            - "Name of the quota, can be used as glob expression."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts about quota named C<myquota> in Default datacenter:
- ovirt_quotas_facts:
    datacenter: Default
    name: myquota
- debug:
    var: ovirt_quotas
'''

RETURN = '''
ovirt_quotas:
    description: "List of dictionaries describing the quotas. Quota attribues are mapped to dictionary keys,
                  all quotas attributes can be found at following url: https://ovirt.example.com/ovirt-engine/api/model#types/quota."
    returned: On success.
    type: list
'''


def main():
    argument_spec = ovirt_full_argument_spec(
        datacenter=dict(required=True),
        name=dict(default=None),
    )
    module = AnsibleModule(argument_spec)
    check_sdk(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        datacenters_service = connection.system_service().data_centers_service()
        dc_name = module.params['datacenter']
        dc = search_by_name(datacenters_service, dc_name)
        if dc is None:
            raise Exception("Datacenter '%s' was not found." % dc_name)

        quotas_service = datacenters_service.service(dc.id).quotas_service()
        if module.params['name']:
            quotas = [
                e for e in quotas_service.list()
                if fnmatch.fnmatch(e.name, module.params['name'])
            ]
        else:
            quotas = quotas_service.list()

        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_quotas=[
                    get_dict_of_struct(c) for c in quotas
                ],
            ),
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=False)


if __name__ == '__main__':
    main()
