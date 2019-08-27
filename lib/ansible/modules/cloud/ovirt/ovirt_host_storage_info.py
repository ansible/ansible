#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovirt_host_storage_info
short_description: Retrieve information about one or more oVirt/RHV HostStorages (applicable only for block storage)
author: "Daniel Erez (@derez)"
version_added: "2.4"
description:
    - "Retrieve information about one or more oVirt/RHV HostStorages (applicable only for block storage)."
    - This module was called C(ovirt_host_storage_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(ovirt_host_storage_info) module no longer returns C(ansible_facts)!
options:
    host:
        description:
            - "Host to get device list from."
        required: true
    iscsi:
        description:
            - "Dictionary with values for iSCSI storage type:"
            - "C(address) - Address of the iSCSI storage server."
            - "C(target) - The target IQN for the storage device."
            - "C(username) - A CHAP user name for logging into a target."
            - "C(password) - A CHAP password for logging into a target."
    fcp:
        description:
            - "Dictionary with values for fibre channel storage type:"
            - "C(address) - Address of the fibre channel storage server."
            - "C(port) - Port of the fibre channel storage server."
            - "C(lun_id) - LUN id."
extends_documentation_fragment: ovirt_info
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather information about HostStorages with specified target and address:
- ovirt_host_storage_info:
    host: myhost
    iscsi:
      target: iqn.2016-08-09.domain-01:nickname
      address: 10.34.63.204
  register: result
- debug:
    msg: "{{ result.ovirt_host_storages }}"
'''

RETURN = '''
ovirt_host_storages:
    description: "List of dictionaries describing the HostStorage. HostStorage attributes are mapped to dictionary keys,
                  all HostStorage attributes can be found at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/host_storage."
    returned: On success.
    type: list
'''

import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_info_full_argument_spec,
    get_id_by_name,
)


def _login(host_service, iscsi):
    host_service.iscsi_login(
        iscsi=otypes.IscsiDetails(
            username=iscsi.get('username'),
            password=iscsi.get('password'),
            address=iscsi.get('address'),
            target=iscsi.get('target'),
        ),
    )


def _get_storage_type(params):
    for sd_type in ['iscsi', 'fcp']:
        if params.get(sd_type) is not None:
            return sd_type


def main():
    argument_spec = ovirt_info_full_argument_spec(
        host=dict(required=True),
        iscsi=dict(default=None, type='dict'),
        fcp=dict(default=None, type='dict'),
    )
    module = AnsibleModule(argument_spec)
    is_old_facts = module._name == 'ovirt_host_storage_facts'
    if is_old_facts:
        module.deprecate("The 'ovirt_host_storage_facts' module has been renamed to 'ovirt_host_storage_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)

        # Get Host
        hosts_service = connection.system_service().hosts_service()
        host_id = get_id_by_name(hosts_service, module.params['host'])
        storage_type = _get_storage_type(module.params)
        host_service = hosts_service.host_service(host_id)

        if storage_type == 'iscsi':
            # Login
            iscsi = module.params.get('iscsi')
            _login(host_service, iscsi)

        # Get LUNs exposed from the specified target
        host_storages = host_service.storage_service().list()

        if storage_type == 'iscsi':
            filterred_host_storages = [host_storage for host_storage in host_storages
                                       if host_storage.type == otypes.StorageType.ISCSI]
            if 'target' in iscsi:
                filterred_host_storages = [host_storage for host_storage in filterred_host_storages
                                           if iscsi.get('target') == host_storage.logical_units[0].target]
        elif storage_type == 'fcp':
            filterred_host_storages = [host_storage for host_storage in host_storages
                                       if host_storage.type == otypes.StorageType.FCP]

        result = dict(
            ovirt_host_storages=[
                get_dict_of_struct(
                    struct=c,
                    connection=connection,
                    fetch_nested=module.params.get('fetch_nested'),
                    attributes=module.params.get('nested_attributes'),
                ) for c in filterred_host_storages
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
