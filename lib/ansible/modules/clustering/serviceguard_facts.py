#!/usr/bin/python
# coding: utf8

# Copyright: (c) 2019, Christian Sandrini <mail@chrissandrini.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: serviceguard_facts

short_description: HP ServiceGuard facts module

version_added: "2.7"

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
cluster_formation_time:
    description: Cluster formation time
    returned: always
cluster_pr_mode:
    description: Cluster pr mode
    returned: always
configuration_data_version:
    description: Configuration data version
    returned: always
configured_io_timeout_extension:
    description: Configured IO timeout extension
    returned: always
coordinator:
    description: Cluster coordinator
    returned: always
hostname_address_family:
    description: Hostname address family
    returned: always
id:
    description: Cluster id
    returned: always
incarnation:
    description: Incarnation
    returned: always
io_timeout_extension:
    description: IO timeout extension
    returned: always
max_configured_packages: 
    description: Max configured packages
    returned: always
max_reformation_duration:
    description: Max reformation duration
    returned: always
member_timeout:
    description: Member timeout
    returned: always
name:
    description: Cluster name
    returned: always
network_polling_interval:
    description: Network polling interval
    returned: always
nodes.nodename.id:
    description: Node id
    returned: always
nodes.nodename.initial_incarnation:
    description: Node initial incarnation
    returned: always
nodes.nodename.name:
    description: Node name
    returned: always
nodes.nodename.node_pr_key:
    description: Node pr key
    returned: always
nodes.nodename.os_status:
    description: Node os status
    returned: always
nodes.nodename.sg_version:
    description: Node sg version
    returned: always
nodes.nodename.state:
    description: Node state
    returned: always
nodes.nodename.status:
    description: Node status
    returned: always
nodes.nodename.summary:
    description: Node summary
    returned: always
nodes.nodename.uuid:
    description: Node uuid
    returned: always
nodes.nodename.virt_tech:
    description: Node virt_tech
    returned: always
pkgs.pkgname.autorun
    description: Package autorun
    returned: always
pkgs.pkgname.concurrent_fsck_operations:
    description: Package concurrent fsck operations
    returned: always
pkgs.pkgname.concurrent_mount_and_umount_operations:
    description: Package concurrent mount and umount operations
    returned: always
pkgs.pkgname.deactivation_retry_count:
    description: Package deactivation retry count
    returned: always
pkgs.pkgname.failback_policy:
    description: Package fialback policy
    returned: always
pkgs.pkgname.failfast:
    description: Package failfast
    returned: always
pkgs.pkgname.failvoer_policy:
    description: Package failover_policy
    returned: always
pkgs.pkgname.fs_mount_retry_count:
    description: Package fs mount retry count
    returned: always
pkgs.pkgname.fs_umount_retry_count:
    description: Package fs umount retry count
    returned: always
pkgs.pkgname.halt_script_timeout:
    description: Package halt script timeout
    returned: always
pkgs.pkgname.highly_available:
    description: Package highly available
    returned: always
pkgs.pkgname.id:
    description: Package id
    returned: always
pkgs.pkgname.initial_autorun:
    description: Package initial autorun
    returned: always
pkgs.pkgname.kill_processes_accessing_raw_devices:
    description: Package kill processes accessing raw devices
    returned: always
pkgs.pkgname.owner:
    description: Package owner
    returned: always
pkgs.pkgname.description:
    description: Package description
    returned: always
pkgs.pkgname.state:
    description: Package state
    returned: always
pkgs.pkgname.status:
    description: Package status
    returned: always
pkgs.pkgname.style:
    description: Package style
    returned: always
pkgs.pkgname.summary:
    description: Package summary
    returned: always
pkgs.pkgname.type:
    description: Package type
    returned: always
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
