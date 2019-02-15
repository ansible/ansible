#!/usr/bin/python
# coding: utf8

# Copyright: (c) 2019, Christian Sandrini <mail@chrissandrini.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: serviceguard_facts

short_description: HP ServiceGuard facts module

version_added: "2.8"

description:
    - Returns facts of a HP ServiceGuard cluster

options:
    path:
        description:
            - Path of the cmcluster binaries
        required: false
        default: /usr/local/cmcluster/bin
author:
    - Christian Sandrini (@sandrich)
    - Sergio Pérez Fernández (@sergioperez)
'''

EXAMPLES = '''
# Get the SG Cluster facts into the sg_facts variable
- name: Get ServiceGuard facts from the node
  serviceguard_facts:
  register: sg_facts
'''

RETURN = '''
auto_start_timeout:
    description: Auto start timeout
    returned: always
    type: str
cluster_formation_time:
    description: Cluster formation time
    returned: always
    type: str
cluster_pr_mode:
    description: Cluster pr mode
    returned: always
    type: str
configuration_data_version:
    description: Configuration data version
    returned: always
    type: str
configured_io_timeout_extension:
    description: Configured IO timeout extension
    returned: always
    type: str
coordinator:
    description: Cluster coordinator
    returned: always
    type: str
hostname_address_family:
    description: Hostname address family
    returned: always
    type: str
id:
    description: Cluster id
    returned: always
    type: str
incarnation:
    description: Incarnation
    returned: always
    type: str
io_timeout_extension:
    description: IO timeout extension
    returned: always
    type: str
max_configured_packages:
    description: Max configured packages
    returned: always
    type: str
max_reformation_duration:
    description: Max reformation duration
    returned: always
    type: str
member_timeout:
    description: Member timeout
    returned: always
    type: str
name:
    description: Cluster name
    returned: always
    type: str
network_polling_interval:
    description: Network polling interval
    returned: always
    type: str
nodes:
    description: Information about nodes
    returned: always
    type: complex
    contains:
        id:
            description: Node id
            returned: always
            type: str
        initial_incarnation:
            description: Node initial incarnation
            returned: always
            type: str
        name:
            description: Node name
            returned: always
            type: str
        node_pr_key:
            description: Node pr key
            returned: always
            type: str
        os_status:
            description: Node os status
            returned: always
            type: str
        sg_version:
            description: Node sg version
            returned: always
            type: str
        state:
            description: Node state
            returned: always
            type: str
        status:
            description: Node status
            returned: always
            type: str
        summary:
            description: Node summary
            returned: always
            type: str
        uuid:
            description: Node uuid
            returned: always
            type: str
        virt_tech:
            description: Node virt_tech
            returned: always
            type: str
pkgs:
    description: Information about packages
    returned: always
    type: complex
    contains:
        autorun:
            description: Package autorun
            returned: always
            type: str
        concurrent_fsck_operations:
            description: Package concurrent fsck operations
            returned: always
            type: str
        concurrent_mount_and_umount_operations:
            description: Package concurrent mount and umount operations
            returned: always
            type: str
        deactivation_retry_count:
            description: Package deactivation retry count
            returned: always
            type: str
        failback_policy:
            description: Package fialback policy
            returned: always
            type: str
        failfast:
            description: Package failfast
            returned: always
            type: str
        failvoer_policy:
            description: Package failover_policy
            returned: always
            type: str
        fs_mount_retry_count:
            description: Package fs mount retry count
            returned: always
            type: str
        fs_umount_retry_count:
            description: Package fs umount retry count
            returned: always
            type: str
        halt_script_timeout:
            description: Package halt script timeout
            returned: always
            type: str
        highly_available:
            description: Package highly available
            returned: always
            type: str
        id:
            description: Package id
            returned: always
            type: str
        initial_autorun:
            description: Package initial autorun
            returned: always
            type: str
        kill_processes_accessing_raw_devices:
            description: Package kill processes accessing raw devices
            returned: always
            type: str
        owner:
            description: Package owner
            returned: always
            type: str
        description:
            description: Package description
            returned: always
            type: str
        state:
            description: Package state
            returned: always
            type: str
        status:
            description: Package status
            returned: always
            type: str
        style:
            description: Package style
            returned: always
            type: str
        summary:
            description: Package summary
            returned: always
            type: str
        type:
            description: Package type
            returned: always
            type: str
state:
    description: Cluster state
    returned: always
    type: str
status:
    description: Cluster status
    returned: always
    type: str
summary:
    description: Cluster summary
    returned: always
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.serviceguard import parse_cluster_state


def main():
    module_args = dict(
        path=dict(type='str', required=False, default='/usr/local/cmcluster/bin')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    state = parse_cluster_state(module)
    module.exit_json(**state)


if __name__ == '__main__':
    main()
