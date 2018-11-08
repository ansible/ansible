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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_vm_facts
short_description: Retrieve facts about one or more oVirt/RHV virtual machines
author: "Ondra Machacek (@machacekondra)"
version_added: "2.3"
description:
    - "Retrieve facts about one or more oVirt/RHV virtual machines."
notes:
    - "This module creates a new top-level C(ovirt_vms) fact, which
       contains a list of virtual machines."
options:
    pattern:
      description:
        - "Search term which is accepted by oVirt/RHV search backend."
        - "For example to search VM X from cluster Y use following pattern:
           name=X and cluster=Y"
    all_content:
      description:
        - "If I(true) all the attributes of the virtual machines should be
           included in the response."
      type: bool
    case_sensitive:
      description:
        - "If I(true) performed search will take case into account."
      type: bool
      default: true
    max:
      description:
        - "The maximum number of results to return."
    next_run:
      description:
        - "Indicates if the returned result describes the virtual machine as it is currently running or if describes
           the virtual machine with the modifications that have already been performed but that will only come into
           effect when the virtual machine is restarted. By default the value is set by engine."
      type: bool
      version_added: "2.8"
extends_documentation_fragment: ovirt_facts
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts about all VMs which names start with C(centos) and
# belong to cluster C(west):
- ovirt_vm_facts:
    pattern: name=centos* and cluster=west
- debug:
    var: ovirt_vms

# Gather info about next run configuration of virtual machine named myvm
- ovirt_vm_facts:
    pattern: name=myvm
    next_run: true
- debug:
    var: ovirt_vms[0]
'''

RETURN = '''
ovirt_vms:
    description: "List of dictionaries describing the VMs. VM attributes are mapped to dictionary keys,
                  all VMs attributes can be found at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/vm."
    returned: On success.
    type: list
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_facts_full_argument_spec,
)


def main():
    argument_spec = ovirt_facts_full_argument_spec(
        pattern=dict(default='', required=False),
        all_content=dict(default=False, type='bool'),
        next_run=dict(default=None, type='bool'),
        case_sensitive=dict(default=True, type='bool'),
        max=dict(default=None, type='int'),
    )
    module = AnsibleModule(argument_spec)

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        vms_service = connection.system_service().vms_service()
        vms = vms_service.list(
            search=module.params['pattern'],
            all_content=module.params['all_content'],
            case_sensitive=module.params['case_sensitive'],
            max=module.params['max'],
        )
        if module.params['next_run']:
            vms = [vms_service.vm_service(vm.id).get(next_run=True) for vm in vms]

        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_vms=[
                    get_dict_of_struct(
                        struct=c,
                        connection=connection,
                        fetch_nested=module.params.get('fetch_nested'),
                        attributes=module.params.get('nested_attributes'),
                    ) for c in vms
                ],
            ),
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
