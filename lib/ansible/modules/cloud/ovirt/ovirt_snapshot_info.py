#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_snapshot_info
short_description: Retrieve information about one or more oVirt/RHV virtual machine snapshots
author: "Ondra Machacek (@machacekondra)"
version_added: "2.3"
description:
    - "Retrieve information about one or more oVirt/RHV virtual machine snapshots."
    - This module was called C(ovirt_snapshot_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(ovirt_snapshot_info) module no longer returns C(ansible_facts)!
notes:
    - "This module returns a variable C(ovirt_snapshots), which
       contains a list of snapshots. You need to register the result with
       the I(register) keyword to use it."
options:
    vm:
        description:
            - "Name of the VM with snapshot."
        required: true
    description:
        description:
            - "Description of the snapshot, can be used as glob expression."
    snapshot_id:
        description:
            - "Id of the snapshot we want to retrieve information about."
extends_documentation_fragment: ovirt_info
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather information about all snapshots which description start with C(update) for VM named C(centos7):
- ovirt_snapshot_info:
    vm: centos7
    description: update*
  register: result
- debug:
    msg: "{{ result.ovirt_snapshots }}"
'''

RETURN = '''
ovirt_snapshots:
    description: "List of dictionaries describing the snapshot. Snapshot attributes are mapped to dictionary keys,
                  all snapshot attributes can be found at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/snapshot."
    returned: On success.
    type: list
'''


import fnmatch
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_info_full_argument_spec,
    search_by_name,
)


def main():
    argument_spec = ovirt_info_full_argument_spec(
        vm=dict(required=True),
        description=dict(default=None),
        snapshot_id=dict(default=None),
    )
    module = AnsibleModule(argument_spec)
    is_old_facts = module._name == 'ovirt_snapshot_facts'
    if is_old_facts:
        module.deprecate("The 'ovirt_snapshot_facts' module has been renamed to 'ovirt_snapshot_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        vms_service = connection.system_service().vms_service()
        vm_name = module.params['vm']
        vm = search_by_name(vms_service, vm_name)
        if vm is None:
            raise Exception("VM '%s' was not found." % vm_name)

        snapshots_service = vms_service.service(vm.id).snapshots_service()
        if module.params['description']:
            snapshots = [
                e for e in snapshots_service.list()
                if fnmatch.fnmatch(e.description, module.params['description'])
            ]
        elif module.params['snapshot_id']:
            snapshots = [
                snapshots_service.snapshot_service(module.params['snapshot_id']).get()
            ]
        else:
            snapshots = snapshots_service.list()

        result = dict(
            ovirt_snapshots=[
                get_dict_of_struct(
                    struct=c,
                    connection=connection,
                    fetch_nested=module.params.get('fetch_nested'),
                    attributes=module.params.get('nested_attributes'),
                ) for c in snapshots
            ],
        )
        if is_old_facts:
            module.exit_json(changed=False, ansible_facts=result)
        else:
            module.exit_json(changed=False, **result)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
