#!/usr/bin/python
# Copyright (c) 2017, 2018, Oracle and/or its affiliates.
# This software is made available to you under the terms of the GPL 3.0 license or the Apache 2.0 license.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Apache License v2.0
# See LICENSE.TXT for details.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: oci_vcn
short_description: Manage Virtual Cloud Networks(VCN) in OCI
description:
    - This module allows the user to create, delete and update virtual cloud networks(VCNs) in OCI.
version_added: "2.8"
options:
    cidr_block:
        description: The CIDR IP address block of the VCN. Required when creating a VCN with I(state=present).
        required: false
    compartment_id:
        description: The OCID of the compartment to contain the VCN. Required when creating a VCN with I(state=present).
                     This option is mutually exclusive with I(vcn_id).
        type: str
    display_name:
        description: A user-friendly name. Does not have to be unique, and it's changeable.
        type: str
        aliases: [ 'name' ]
    dns_label:
        description: A DNS label for the VCN, used in conjunction with the VNIC's hostname and subnet's DNS label to
                     form a fully qualified domain name (FQDN) for each VNIC within this subnet (for example,
                     bminstance-1.subnet123.vcn1.oraclevcn.com). Not required to be unique, but it's a best practice
                     to set unique DNS labels for VCNs in your tenancy. Must be an alphanumeric string that begins
                     with a letter. The value cannot be changed.
        type: str
    state:
        description: Create or update a VCN with I(state=present). Use I(state=absent) to delete a VCN.
        type: str
        default: present
        choices: ['present', 'absent']
    vcn_id:
        description: The OCID of the VCN. Required when deleting a VCN with I(state=absent) or updating a VCN
                     with I(state=present). This option is mutually exclusive with I(compartment_id).
        type: str
        aliases: [ 'id' ]
author: "Rohit Chaware (@rohitChaware)"
extends_documentation_fragment: [ oracle, oracle_creatable_resource, oracle_wait_options, oracle_tags ]
"""

EXAMPLES = """
- name: Create a VCN
  oci_vcn:
    cidr_block: '10.0.0.0/16'
    compartment_id: 'ocid1.compartment.oc1..xxxxxEXAMPLExxxxx'
    display_name: my_vcn
    dns_label: ansiblevcn

- name: Updates the specified VCN's display name
  oci_vcn:
    vcn_id: ocid1.vcn.oc1.phx.xxxxxEXAMPLExxxxx
    display_name: ansible_vcn

- name: Delete the specified VCN
  oci_vcn:
    vcn_id: ocid1.vcn.oc1.phx.xxxxxEXAMPLExxxxx
    state: absent
"""

RETURN = """
vcn:
    description: Information about the VCN
    returned: On successful create and update operation
    type: dict
    sample: {
            "cidr_block": "10.0.0.0/16",
            compartment_id": "ocid1.compartment.oc1..xxxxxEXAMPLExxxxx",
            "default_dhcp_options_id": "ocid1.dhcpoptions.oc1.phx.xxxxxEXAMPLExxxxx",
            "default_route_table_id": "ocid1.routetable.oc1.phx.xxxxxEXAMPLExxxxx",
            "default_security_list_id": "ocid1.securitylist.oc1.phx.xxxxxEXAMPLExxxxx",
            "display_name": "ansible_vcn",
            "dns_label": "ansiblevcn",
            "id": "ocid1.vcn.oc1.phx.xxxxxEXAMPLExxxxx",
            "lifecycle_state": "AVAILABLE",
            "time_created": "2017-11-13T20:22:40.626000+00:00",
            "vcn_domain_name": "ansiblevcn.oraclevcn.com"
        }
"""

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.oracle import oci_utils

try:
    from oci.core.virtual_network_client import VirtualNetworkClient
    from oci.core.models import CreateVcnDetails
    from oci.core.models import UpdateVcnDetails

    HAS_OCI_PY_SDK = True
except ImportError:
    HAS_OCI_PY_SDK = False


def delete_vcn(virtual_network_client, module):
    result = oci_utils.delete_and_wait(
        resource_type="vcn",
        client=virtual_network_client,
        get_fn=virtual_network_client.get_vcn,
        kwargs_get={"vcn_id": module.params["vcn_id"]},
        delete_fn=virtual_network_client.delete_vcn,
        kwargs_delete={"vcn_id": module.params["vcn_id"]},
        module=module,
    )
    return result


def update_vcn(virtual_network_client, module):
    result = oci_utils.check_and_update_resource(
        resource_type="vcn",
        client=virtual_network_client,
        get_fn=virtual_network_client.get_vcn,
        kwargs_get={"vcn_id": module.params["vcn_id"]},
        update_fn=virtual_network_client.update_vcn,
        primitive_params_update=["vcn_id"],
        kwargs_non_primitive_update={UpdateVcnDetails: "update_vcn_details"},
        module=module,
        update_attributes=UpdateVcnDetails().attribute_map.keys(),
    )
    return result


def create_vcn(virtual_network_client, module):
    create_vcn_details = CreateVcnDetails()
    for attribute in create_vcn_details.attribute_map.keys():
        if attribute in module.params:
            setattr(create_vcn_details, attribute, module.params[attribute])

    result = oci_utils.create_and_wait(
        resource_type="vcn",
        create_fn=virtual_network_client.create_vcn,
        kwargs_create={"create_vcn_details": create_vcn_details},
        client=virtual_network_client,
        get_fn=virtual_network_client.get_vcn,
        get_param="vcn_id",
        module=module,
    )
    return result


def main():
    module_args = oci_utils.get_taggable_arg_spec(
        supports_create=True, supports_wait=True
    )
    module_args.update(
        dict(
            cidr_block=dict(type="str", required=False),
            compartment_id=dict(type="str", required=False),
            display_name=dict(type="str", required=False, aliases=["name"]),
            dns_label=dict(type="str", required=False),
            state=dict(
                type="str",
                required=False,
                default="present",
                choices=["absent", "present"],
            ),
            vcn_id=dict(type="str", required=False, aliases=["id"]),
        )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        mutually_exclusive=[["compartment_id", "vcn_id"]],
    )

    if not HAS_OCI_PY_SDK:
        module.fail_json(msg=missing_required_lib("oci"))

    virtual_network_client = oci_utils.create_service_client(
        module, VirtualNetworkClient
    )

    exclude_attributes = {"display_name": True, "dns_label": True}
    state = module.params["state"]
    vcn_id = module.params["vcn_id"]

    if state == "absent":
        if vcn_id is not None:
            result = delete_vcn(virtual_network_client, module)
        else:
            module.fail_json(
                msg="Specify vcn_id with state as 'absent' to delete a VCN."
            )

    else:
        if vcn_id is not None:
            result = update_vcn(virtual_network_client, module)
        else:
            result = oci_utils.check_and_create_resource(
                resource_type="vcn",
                create_fn=create_vcn,
                kwargs_create={
                    "virtual_network_client": virtual_network_client,
                    "module": module,
                },
                list_fn=virtual_network_client.list_vcns,
                kwargs_list={"compartment_id": module.params["compartment_id"]},
                module=module,
                model=CreateVcnDetails(),
                exclude_attributes=exclude_attributes,
            )

    module.exit_json(**result)


if __name__ == "__main__":
    main()
