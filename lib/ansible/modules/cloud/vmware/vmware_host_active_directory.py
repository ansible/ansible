#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_host_active_directory
short_description: Joins an ESXi host system to an Active Directory domain or leaves it
description:
- This module can be used to join or leave an ESXi host to or from an Active Directory domain.
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  ad_domain:
    description:
        - AD Domain to join.
    type: str
    aliases: [ domain, domain_name ]
  ad_user:
    description:
        - Username for AD domain join.
    type: str
  ad_password:
    description:
        - Password for AD domain join.
    type: str
  ad_state:
     description:
        - Wheter the ESXi host is joined to an AD domain or not.
     type: str
     choices: [ present, absent ]
     default: 'absent'
     aliases: [ state ]
  esxi_hostname:
    description:
    - Name of the host system to work with.
    - This parameter is required if C(cluster_name) is not specified.
    type: str
  cluster_name:
    description:
    - Name of the cluster from which all host systems will be used.
    - This parameter is required if C(esxi_hostname) is not specified.
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Join an AD domain
  vmware_host_active_directory:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    ad_domain: example.local
    ad_user: adjoin
    ad_password: Password123$
    ad_state: present
    validate_certs: no
  delegate_to: localhost

- name: Leave AD domain
  vmware_host_active_directory:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    ad_state: absent
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
results:
    description: metadata about host system's AD domain join state
    returned: always
    type: dict
    sample: {
        "esxi01": {
            "changed": true,
            "domain": "example.local",
            "membership_state": "ok",
            "msg": "Host joined to AD domain",
            "ad_state": "present",
            "ad_state_current": "present",
            "ad_state_previous": "absent",
        },
    }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, TaskError, vmware_argument_spec, wait_for_task
from ansible.module_utils._text import to_native


class VmwareHostAdAuthentication(PyVmomi):
    """Manage Active Directory Authentication for an ESXi host system"""

    def __init__(self, module):
        super(VmwareHostAdAuthentication, self).__init__(module)
        cluster_name = self.params.get('cluster_name')
        esxi_host_name = self.params.get('esxi_hostname')
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system.")

    def ensure(self):
        """Manage Active Directory Authentication for an ESXi host system"""
        results = dict(changed=False, result=dict())
        desired_state = self.params.get('ad_state')
        domain = self.params.get('ad_domain')
        ad_user = self.params.get('ad_user')
        ad_password = self.params.get('ad_password')
        host_change_list = []
        for host in self.hosts:
            changed = False
            results['result'][host.name] = dict(msg='')

            active_directory_info = self.get_ad_info(host)

            results['result'][host.name]['ad_state'] = desired_state
            results['result'][host.name]['ad_domain'] = domain
            if desired_state == 'present':
                # Don't do anything if already enabled and joined
                if active_directory_info.enabled:
                    # Joined and no problems with the domain membership
                    if active_directory_info.domainMembershipStatus == 'ok':
                        results['result'][host.name]['changed'] = False
                        results['result'][host.name]['membership_state'] = active_directory_info.domainMembershipStatus
                        results['result'][host.name]['joined_domain'] = active_directory_info.joinedDomain
                        results['result'][host.name]['trusted_domains'] = active_directory_info.trustedDomain
                        results['result'][host.name]['msg'] = (
                            "Host is joined to AD domain and there are no problems with the domain membership"
                        )
                    # Joined, but problems with the domain membership
                    else:
                        changed = results['result'][host.name]['changed'] = True
                        results['result'][host.name]['membership_state'] = active_directory_info.domainMembershipStatus
                        results['result'][host.name]['joined_domain'] = active_directory_info.joinedDomain
                        results['result'][host.name]['trusted_domains'] = active_directory_info.trustedDomain
                        msg = "Host is joined to AD domain, but "
                        if active_directory_info.domainMembershipStatus == 'clientTrustBroken':
                            msg += "the client side of the trust relationship is broken"
                        elif active_directory_info.domainMembershipStatus == 'inconsistentTrust':
                            msg += "unexpected domain controller responded"
                        elif active_directory_info.domainMembershipStatus == 'noServers':
                            msg += "the host thinks it's part of a domain and " \
                                "no domain controllers could be reached to confirm"
                        elif active_directory_info.domainMembershipStatus == 'serverTrustBroken':
                            msg += "the server side of the trust relationship is broken (or bad machine password)"
                        elif active_directory_info.domainMembershipStatus == 'otherProblem':
                            msg += "there are some problems with the domain membership"
                        elif active_directory_info.domainMembershipStatus == 'unknown':
                            msg += "the Active Directory integration provider does not support domain trust checks"
                        results['result'][host.name]['msg'] = msg
                # Enable and join AD domain
                else:
                    if self.module.check_mode:
                        changed = results['result'][host.name]['changed'] = True
                        results['result'][host.name]['ad_state_previous'] = "absent"
                        results['result'][host.name]['ad_state_current'] = "present"
                        results['result'][host.name]['msg'] = "Host would be joined to AD domain"
                    else:
                        ad_authentication = self.get_ad_auth_object(host)
                        try:
                            try:
                                task = ad_authentication.JoinDomain(
                                    domainName=domain, userName=ad_user, password=ad_password
                                )
                                wait_for_task(task)
                            except TaskError as task_err:
                                self.module.fail_json(
                                    msg="Failed to join domain : %s" % to_native(task_err)
                                )
                            changed = results['result'][host.name]['changed'] = True
                            results['result'][host.name]['ad_state_previous'] = "absent"
                            results['result'][host.name]['ad_state_current'] = "present"
                            results['result'][host.name]['msg'] = "Host joined to AD domain"
                            active_directory_info = self.get_ad_info(host)
                            results['result'][host.name]['membership_state'] = active_directory_info.domainMembershipStatus
                        except vim.fault.InvalidState as invalid_state:
                            self.module.fail_json(
                                msg="The host has already joined a domain : %s" % to_native(invalid_state.msg)
                            )
                        except vim.fault.HostConfigFault as host_fault:
                            self.module.fail_json(
                                msg="The host configuration prevents the join operation from succeeding : %s" %
                                to_native(host_fault.msg)
                            )
                        except vim.fault.InvalidLogin as invalid_login:
                            self.module.fail_json(
                                msg="Credentials aren't valid : %s" % to_native(invalid_login.msg)
                            )
                        except vim.fault.TaskInProgress as task_in_progress:
                            self.module.fail_json(
                                msg="The ActiveDirectoryAuthentication object is busy : %s" %
                                to_native(task_in_progress.msg)
                            )
                        except vim.fault.BlockedByFirewall as blocked_by_firewall:
                            self.module.fail_json(
                                msg="Ports needed by the join operation are blocked by the firewall : %s" %
                                to_native(blocked_by_firewall.msg)
                            )
                        except vim.fault.DomainNotFound as not_found:
                            self.module.fail_json(
                                msg="The domain controller can't be reached : %s" % to_native(not_found.msg)
                            )
                        except vim.fault.NoPermissionOnAD as no_permission:
                            self.module.fail_json(
                                msg="The specified user has no right to add hosts to the domain : %s" %
                                to_native(no_permission.msg)
                            )
                        except vim.fault.InvalidHostName as invalid_host:
                            self.module.fail_json(
                                msg="The domain part of the host's FQDN doesn't match the domain being joined : %s" %
                                to_native(invalid_host.msg)
                            )
                        except vim.fault.ClockSkew as clock_skew:
                            self.module.fail_json(
                                msg="The clocks of the host and the domain controller differ by more "
                                "than the allowed amount of time : %s" % to_native(clock_skew.msg)
                            )
                        except vim.fault.ActiveDirectoryFault as ad_fault:
                            self.module.fail_json(
                                msg="An error occurred during AD join : %s" %
                                to_native(ad_fault.msg)
                            )
            elif desired_state == 'absent':
                # Don't do anything not joined to any AD domain
                if not active_directory_info.enabled:
                    results['result'][host.name]['changed'] = False
                    results['result'][host.name]['ad_state_current'] = "absent"
                    results['result'][host.name]['msg'] = "Host isn't joined to an AD domain"
                # Disable and leave AD domain
                else:
                    if self.module.check_mode:
                        changed = results['result'][host.name]['changed'] = True
                        results['result'][host.name]['ad_state_previous'] = "present"
                        results['result'][host.name]['ad_state_current'] = "absent"
                        results['result'][host.name]['msg'] = "Host would leave the AD domain '%s'" % \
                            active_directory_info.joinedDomain
                    else:
                        ad_authentication = self.get_ad_auth_object(host)
                        try:
                            try:
                                task = ad_authentication.LeaveCurrentDomain(force=True)
                                wait_for_task(task)
                            except TaskError as task_err:
                                self.module.fail_json(
                                    msg="Failed to join domain : %s" % to_native(task_err)
                                )
                            changed = results['result'][host.name]['changed'] = True
                            results['result'][host.name]['ad_state_previous'] = "present"
                            results['result'][host.name]['ad_state_current'] = "absent"
                            results['result'][host.name]['msg'] = "Host left the AD domain '%s'" % \
                                active_directory_info.joinedDomain
                        except vim.fault.InvalidState as invalid_state:
                            self.module.fail_json(
                                msg="The host is not in a domain or there are active permissions for "
                                "Active Directory users : %s" % to_native(invalid_state.msg)
                            )
                        except vim.fault.AuthMinimumAdminPermission as admin_permission:
                            self.module.fail_json(
                                msg="This change would leave the system with no Administrator permission "
                                "on the root node : %s" % to_native(admin_permission.msg)
                            )
                        except vim.fault.TaskInProgress as task_in_progress:
                            self.module.fail_json(
                                msg="The ActiveDirectoryAuthentication object is busy : %s" %
                                to_native(task_in_progress.msg)
                            )
                        except vim.fault.NonADUserRequired as non_ad_user:
                            self.module.fail_json(
                                msg="Only non Active Directory users can initiate the leave domain operation : %s" %
                                to_native(non_ad_user.msg)
                            )
                        except vim.fault.ActiveDirectoryFault as ad_fault:
                            self.module.fail_json(
                                msg="An error occurred during AD leave : %s" %
                                to_native(ad_fault.msg)
                            )

            host_change_list.append(changed)

        if any(host_change_list):
            results['changed'] = True
        self.module.exit_json(**results)

    def get_ad_info(self, host_object):
        """Get info about AD membership"""
        active_directory_info = None
        authentication_store_info = host_object.config.authenticationManagerInfo.authConfig
        for authentication_info in authentication_store_info:
            if isinstance(authentication_info, vim.host.ActiveDirectoryInfo):
                active_directory_info = authentication_info
                break
        if not active_directory_info:
            self.module.fail_json(
                msg="Failed to get Active Directory info from authentication manager"
            )
        return active_directory_info

    def get_ad_auth_object(self, host_object):
        """Get AD authentication managed object"""
        ad_authentication = None
        authentication_store_info = host_object.configManager.authenticationManager.supportedStore
        for store_info in authentication_store_info:
            if isinstance(store_info, vim.host.ActiveDirectoryAuthentication):
                ad_authentication = store_info
                break
        if not ad_authentication:
            self.module.fail_json(
                msg="Failed to get Active Directory authentication managed object from authentication manager"
            )
        return ad_authentication


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        ad_domain=dict(type='str', default='', aliases=['domain', 'domain_name']),
        ad_user=dict(type='str', default=''),
        ad_password=dict(type='str', default='', no_log=True),
        ad_state=dict(default='absent', choices=['present', 'absent'], aliases=['state']),
        esxi_hostname=dict(type='str', required=False),
        cluster_name=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        required_if=[
            ['ad_state', 'present', ['ad_domain', 'ad_user', 'ad_password']],
        ],
        supports_check_mode=True
    )

    ad_auth = VmwareHostAdAuthentication(module)
    ad_auth.ensure()


if __name__ == '__main__':
    main()
