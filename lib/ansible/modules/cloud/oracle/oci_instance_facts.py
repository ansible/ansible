#!/usr/bin/python
# Copyright (c) 2017, 2018, 2019, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: oci_instance_facts
short_description: Retrieve details about one or more Compute instances in OCI Compute Service
description:
    - This module retrieves details about a specific Compute instance, or all Compute instances in a specified
      Compartment in a specified Availability Domain in OCI Compute Service.
version_added: "2.9"
options:
    compartment_id:
        description: The OCID of the compartment (either the tenancy or another compartment in the tenancy). Required
                     for retrieving information about all instances in a Compartment/Tenancy.
        type: str
    availability_domain:
        description: The name of the Availability Domain.
        type: str
    instance_id:
        description: The OCID of the instance. Required for retrieving information about a specific instance.
        type: str
        aliases: ['id']
    lifecycle_state:
        description: A filter to only return resources that match the given lifecycle state.  The state value is
                     case-insensitive.
        type: str
        choices: ["PROVISIONING", "RUNNING", "STARTING", "STOPPING", "STOPPED", "CREATING_IMAGE", "TERMINATING",
                  "TERMINATED"]

author: "Sivakumar Thyagarajan (@sivakumart)"
extends_documentation_fragment: [ oracle, oracle_display_name_option ]
"""

EXAMPLES = """
- name: Get details of all the compute instances of a specified compartment in a specified Availability Domain
  oci_instance_facts:
    compartment_id: 'ocid1.compartment.oc1..xxxxxEXAMPLExxxxx...vm62xq'
    availability_domain: "BnQb:PHX-AD-1"

- name: Get details of a specific Compute instance
  oci_instance_facts:
    id:"ocid1.instance.oc1.phx.xxxxxEXAMPLExxxxx...lxiggdq"
"""

RETURN = """
instances:
    description: Information about one or more compute instances
    returned: on success
    type: complex
    contains:
        availability_domain:
            description: The Availability Domain the instance is running in.
            returned: always
            type: string
            sample: BnQb:PHX-AD-1
        boot_volume_attachment:
            description: Information of the boot volume attachment.
            returned: In experimental mode.
            type: dict
            contains:
                availability_domain:
                    description: The Availability Domain of the instance.
                    returned: always
                    type: string
                    sample: BnQb:PHX-AD-1
                boot_volume_id:
                    description: The OCID of the boot volume.
                    returned: always
                    type: string
                    sample: ocid1.bootvolume.oc1.iad.xxxxxEXAMPLExxxxx
                compartment_id:
                    description: The OCID of the compartment.
                    returned: always
                    type: string
                    sample: ocid1.compartment.oc1..xxxxxEXAMPLExxxxx
                display_name:
                    description: A user-friendly name. Does not have to be unique, and it cannot be changed.
                    returned: always
                    type: string
                    sample: My boot volume attachment
                id:
                    description: The OCID of the boot volume attachment.
                    returned: always
                    type: string
                    sample: ocid1.instance.oc1.iad.xxxxxEXAMPLExxxxx
                instance_id:
                    description: The OCID of the instance the boot volume is attached to.
                    returned: always
                    type: string
                    sample: ocid1.instance.oc1.phx.xxxxxEXAMPLExxxxx
                lifecycle_state:
                    description: The current state of the boot volume attachment.
                    returned: always
                    type: string
                    sample: ATTACHED
                time_created:
                    description: The date and time the boot volume was created, in the format defined by RFC3339.
                    returned: always
                    type: string
                    sample: 2016-08-25T21:10:29.600Z
        compartment_id:
            description: The OCID of the compartment that contains the instance.
            returned: always
            type: string
            sample: ocid1.compartment.oc1..xxxxxEXAMPLExxxxx....62xq
        display_name:
            description: A user-friendly name for the instance
            returned: always
            type: string
            sample: ansible-instance-968
        extended_metadata:
            description: Additional key-value pairs associated with the instance
            returned: always
            type: dict(str, str)
            sample: {'foo': 'bar'}
        id:
            description: The OCID of the instance.
            returned: always
            type: string
            sample: ocid1.instance.oc1.phx.xxxxxEXAMPLExxxxx
        image_id:
            description: The OCID of the image that the instance is based on
            returned: always
            type: string
            sample: ocid1.image.oc1.iad.xxxxxEXAMPLExxxxx
        ipxe_script:
            description: A custom iPXE script that will run when the instance boots
            returned: always
            type: string
            sample: null
        lifecycle_state:
            description: The current state of the instance.
            returned: always
            type: string
            sample: TERMINATED
        metadata:
            description: Custom metadata that was associated with the instance
            returned: always
            type: dict(str, str)
            sample: {"foo": "bar"}
        primary_private_ip:
            description: The private IP of the primary VNIC attached to this instance
            returned: always
            type: string
            sample: 10.0.0.10
        primary_public_ip:
            description: The public IP of the primary VNIC attached to this instance
            returned: always
            type: string
            sample: 140.34.93.209
        region:
            description: The region that contains the Availability Domain the instance is running in.
            returned: always
            type: string
            sample: phx
        shape:
            description: The shape of the instance. The shape determines the number of CPUs and the amount of memory
                         allocated to the instance.
            returned: always
            type: string
            sample: BM.Standard1.36
        time_created:
            description: The date and time the instance was created, in the format defined by RFC3339
            returned: always
            type: string
            sample: 2017-11-20T04:52:54.541000+00:00
        volume_attachments:
            description: List of information about volume attachments
            returned: In experimental mode.
            type: complex
            contains:
                attachment_type:
                    description: The type of volume attachment.
                    returned: always
                    type: string
                    sample: iscsi
                availability_domain:
                    description: The Availability Domain of an instance.
                    returned: always
                    type: string
                    sample: BnQb:PHX-AD-1
                chap_secret:
                    description: The Challenge-Handshake-Authentication-Protocol (CHAP) secret valid for the associated CHAP
                         user name. (Also called the "CHAP password".)
                    returned: always
                    type: string
                    sample: d6866c0d-298b-48ba-95af-309b4faux45e
                chap_username:
                    description: The volume's system-generated Challenge-Handshake-Authentication-Protocol (CHAP) user name.
                    returned: always
                    type: string
                    sample: ocid1.volume.oc1.phx.xxxxxEXAMPLExxxxx
                compartment_id:
                    description: The OCID of the compartment.
                    returned: always
                    type: string
                    sample: ocid1.compartment.oc1..xxxxxEXAMPLExxxxx
                display_name:
                    description: A user-friendly name. Does not have to be unique, and it cannot be changed.
                    returned: always
                    type: string
                    sample: My volume attachment
                id:
                    description: The OCID of the volume attachment.
                    returned: always
                    type: string
                    sample: ocid1.volumeattachment.oc1.phx.xxxxxEXAMPLExxxxx
                instance_id:
                    description: The OCID of the instance the volume is attached to.
                    returned: always
                    type: string
                    sample: ocid1.instance.oc1.phx.xxxxxEXAMPLExxxxx
                ipv4:
                    description: The volume's iSCSI IP address.
                    returned: always
                    type: string
                    sample: 169.254.0.2
                iqn:
                    description: The target volume's iSCSI Qualified Name in the format defined by RFC 3720.
                    returned: always
                    type: string
                    sample: iqn.2015-12.us.oracle.com:456b0391-17b8-4122-bbf1-f85fc0bb97d9
                lifecycle_state:
                    description: The current state of the volume attachment.
                    returned: always
                    type: string
                    sample: ATTACHED
                port:
                    description: The volume's iSCSI port.
                    returned: always
                    type: int
                    sample: 3260
                time_created:
                    description: The date and time the volume was created, in the format defined by RFC3339.
                    returned: always
                    type: string
                    sample: 2016-08-25T21:10:29.600Z
                volume_id:
                    description: The OCID of the volume.
                    returned: always
                    type: string
                    sample: ocid1.volume.oc1.phx.xxxxxEXAMPLExxxxx

    sample: {
      "availability_domain": "BnQb:PHX-AD-1",
      "boot_volume_attachment": {
                                  "availability_domain": "IwGV:US-ASHBURN-AD-1",
                                  "boot_volume_id": "ocid1.bootvolume.oc1.iad.xxxxxEXAMPLExxxxx",
                                  "compartment_id": "ocid1.compartment.oc1..xxxxxEXAMPLExxxxx",
                                  "display_name": "Remote boot attachment for instance",
                                  "id": "ocid1.instance.oc1.iad.xxxxxEXAMPLExxxxx",
                                  "instance_id": "ocid1.instance.oc1.iad.xxxxxEXAMPLExxxxx",
                                  "lifecycle_state": "ATTACHED",
                                  "time_created": "2018-01-15T07:23:10.838000+00:00"
      },
      "compartment_id": "ocid1.compartment.oc1..xxxxxEXAMPLExxxxx....62xq",
      "display_name": "ansible-modname-968",
      "extended_metadata": {},
      "id": "ocid1.instance.oc1.phx.xxxxxEXAMPLExxxxx.....2siq",
      "image_id": "ocid1.image.oc1.phx.xxxxxEXAMPLExxxxx....lnoa",
      "ipxe_script": null,
      "lifecycle_state": "TERMINATED",
      "metadata": {
        "baz": "quux",
        "foo": "bar"
      },
      "region": "phx",
      "shape": "BM.Standard1.36",
      "time_created": "2017-11-20T04:52:54.541000+00:00",
      "primary_public_ip": "140.34.93.209",
      "primary_private_ip": "10.0.0.10",
      "volume_attachments":  [{
                                "attachment_type": "iscsi",
                                "availability_domain": "BnQb:PHX-AD-1",
                                "chap_secret": null,
                                "chap_username": null,
                                "compartment_id": "ocid1.compartment.oc1..xxxxxEXAMPLExxxxx",
                                "display_name": "ansible_volume_attachment",
                                "id": "ocid1.volumeattachment.oc1.phx.xxxxxEXAMPLExxxxx",
                                "instance_id": "ocid1.instance.oc1.phx.xxxxxEXAMPLExxxxx",
                                "ipv4": "169.254.2.2",
                                "iqn": "iqn.2015-12.com.oracleiaas:472a085d-41a9-4c18-ae7d-dea5b296dad3",
                                "lifecycle_state": "ATTACHED",
                                "port": 3260,
                                "time_created": "2017-11-23T11:17:50.139000+00:00",
                                "volume_id": "ocid1.volume.oc1.phx.xxxxxEXAMPLExxxxx"
      }]
    }
"""

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.oracle import oci_utils, oci_compute_utils
from ansible.module_utils.oracle.oci_utils import check_mode

try:
    from oci.core.compute_client import ComputeClient
    from oci.core.virtual_network_client import VirtualNetworkClient
    from oci.util import to_dict
    from oci.exceptions import ServiceError

    HAS_OCI_PY_SDK = True
except ImportError:
    HAS_OCI_PY_SDK = False


def list_instances(compute_client, module):
    try:
        cid = module.params["compartment_id"]
        optional_list_method_params = [
            "display_name",
            "availability_domain",
            "lifecycle_state",
        ]
        optional_kwargs = dict(
            (param, module.params[param])
            for param in optional_list_method_params
            if module.params.get(param) is not None
        )
        instances = oci_utils.list_all_resources(
            compute_client.list_instances, compartment_id=cid, **optional_kwargs
        )
    except ServiceError as ex:
        module.fail_json(msg=ex.message)

    return to_dict(instances)


@check_mode
def add_boot_volume_attachment_facts(compute_client, result):
    for instance in result:
        instance[
            "boot_volume_attachment"
        ] = oci_compute_utils.get_boot_volume_attachment(compute_client, instance)


@check_mode
def add_volume_attachment_facts(compute_client, result):
    for instance in result:
        instance["volume_attachments"] = oci_compute_utils.get_volume_attachments(
            compute_client, instance
        )


def add_primary_ips(compute_client, network_client, result, module):
    for instance in result:
        try:
            primary_public_ip, primary_private_ip = oci_compute_utils.get_primary_ips(
                compute_client, network_client, instance
            )
            instance["primary_public_ip"] = primary_public_ip
            instance["primary_private_ip"] = primary_private_ip
        except ServiceError as ex:
            instance["primary_public_ip"] = None
            instance["primary_private_ip"] = None
            module.fail_json(msg=ex.message)


def set_logger(input_logger):
    global logger
    logger = input_logger


def get_logger():
    return logger


def main():
    logger = oci_utils.get_logger("oci_instance_facts")
    set_logger(logger)

    module_args = oci_utils.get_facts_module_arg_spec()
    module_args.update(
        dict(
            compartment_id=dict(type="str", required=False),
            availability_domain=dict(type="str", required=False),
            instance_id=dict(type="str", required=False, aliases=["id"]),
            lifecycle_state=dict(
                type="str",
                required=False,
                choices=[
                    "PROVISIONING",
                    "RUNNING",
                    "STARTING",
                    "STOPPING",
                    "STOPPED",
                    "CREATING_IMAGE",
                    "TERMINATING",
                    "TERMINATED",
                ],
            ),
        )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        mutually_exclusive=[("id", "compartment_id")],
    )

    if not HAS_OCI_PY_SDK:
        module.fail_json(msg=missing_required_lib("oci"))

    compute_client = oci_utils.create_service_client(module, ComputeClient)
    network_client = oci_utils.create_service_client(module, VirtualNetworkClient)

    compartment_id = module.params["compartment_id"]
    id = module.params["instance_id"]

    result = dict(changed=False)

    if compartment_id:
        result = list_instances(compute_client, module)
        add_primary_ips(compute_client, network_client, result, module)
    else:
        try:
            inst = oci_utils.call_with_backoff(
                compute_client.get_instance, instance_id=id
            ).data
            result = to_dict([inst])
        except ServiceError as ex:
            module.fail_json(msg=ex.message)

        # For each instance in the result, add related volume_attachments and boot_volume_attachment facts
        try:
            add_volume_attachment_facts(compute_client, result)
            add_boot_volume_attachment_facts(compute_client, result)
            add_primary_ips(compute_client, network_client, result, module)
        except ServiceError as ex:
            module.fail_json(msg=ex.message)

    module.exit_json(instances=result)


if __name__ == "__main__":
    main()
