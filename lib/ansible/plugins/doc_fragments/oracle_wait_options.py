# Copyright (c) 2018, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    DOCUMENTATION = """
    options:
        wait:
            description: Whether to wait for create or delete operation to complete.
            default: yes
            type: bool
        wait_timeout:
            description: Time, in seconds, to wait when I(wait=yes).
            default: 1200
            type: int
        wait_until:
            description: The lifecycle state to wait for the resource to transition into when I(wait=yes). By default,
                         when I(wait=yes), we wait for the resource to get into ACTIVE/ATTACHED/AVAILABLE/PROVISIONED/
                         RUNNING applicable lifecycle state during create operation & to get into DELETED/DETACHED/
                         TERMINATED lifecycle state during delete operation.
            type: str
    """
