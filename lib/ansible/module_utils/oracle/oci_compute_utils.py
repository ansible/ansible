# Copyright (c) 2018, 2019, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.oracle import oci_utils

try:
    from oci.util import to_dict
    from oci.exceptions import ServiceError

    HAS_OCI_PY_SDK = True
except ImportError:
    HAS_OCI_PY_SDK = False


logger = oci_utils.get_logger("oci_compute_utils")


def _debug(s):
    get_logger().debug(s)


def get_logger():
    return logger


def get_volume_attachments(compute_client, instance):
    param_map = {
        "instance_id": instance["id"],
        "compartment_id": instance["compartment_id"],
    }

    volume_attachments = to_dict(
        oci_utils.list_all_resources(
            compute_client.list_volume_attachments, **param_map
        )
    )
    return volume_attachments


def get_boot_volume_attachment(compute_client, instance):
    param_map = {
        "availability_domain": instance["availability_domain"],
        "instance_id": instance["id"],
        "compartment_id": instance["compartment_id"],
    }

    boot_volume_attachments = to_dict(
        oci_utils.list_all_resources(
            compute_client.list_boot_volume_attachments, **param_map
        )
    )

    if boot_volume_attachments:
        return boot_volume_attachments[0]
    return None


def get_primary_ips(compute_client, network_client, instance):
    primary_public_ip = None
    primary_private_ip = None

    vnic_attachments = oci_utils.list_all_resources(
        compute_client.list_vnic_attachments,
        compartment_id=instance["compartment_id"],
        instance_id=instance["id"],
    )

    if vnic_attachments:
        for vnic_attachment in vnic_attachments:
            if vnic_attachment.lifecycle_state == "ATTACHED":
                try:
                    vnic = network_client.get_vnic(vnic_attachment.vnic_id).data
                    if vnic.is_primary:
                        if vnic.public_ip:
                            primary_public_ip = vnic.public_ip
                        if vnic.private_ip:
                            primary_private_ip = vnic.private_ip
                except ServiceError as ex:
                    if ex.status == 404:
                        get_logger().debug(
                            "Either VNIC with ID %s does not exist or you are not authorized to access it.",
                            vnic_attachment.vnic_id,
                        )

    return primary_public_ip, primary_private_ip
