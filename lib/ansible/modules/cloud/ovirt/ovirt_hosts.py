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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_hosts
short_description: Module to manage hosts in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage hosts in oVirt/RHV"
options:
    name:
        description:
            - "Name of the host to manage."
        required: true
    state:
        description:
            - "State which should a host to be in after successful completion."
        choices: [
            'present', 'absent', 'maintenance', 'upgraded', 'started',
            'restarted', 'stopped', 'reinstalled'
        ]
        default: present
    comment:
        description:
            - "Description of the host."
    cluster:
        description:
            - "Name of the cluster, where host should be created."
    address:
        description:
            - "Host address. It can be either FQDN (preferred) or IP address."
    password:
        description:
            - "Password of the root. It's required in case C(public_key) is set to I(False)."
    public_key:
        description:
            - "I(True) if the public key should be used to authenticate to host."
            - "It's required in case C(password) is not set."
        default: False
        aliases: ['ssh_public_key']
    kdump_integration:
        description:
            - "Specify if host will have enabled Kdump integration."
        choices: ['enabled', 'disabled']
        default: enabled
    spm_priority:
        description:
            - "SPM priority of the host. Integer value from 1 to 10, where higher number means higher priority."
    override_iptables:
        description:
            - "If True host iptables will be overridden by host deploy script."
            - "Note that C(override_iptables) is I(false) by default in oVirt/RHV."
    force:
        description:
            - "If True host will be forcibly moved to desired state."
        default: False
    override_display:
        description:
            - "Override the display address of all VMs on this host with specified address."
    kernel_params:
        description:
            - "List of kernel boot parameters."
            - "Following are most common kernel parameters used for host:"
            - "Hostdev Passthrough & SR-IOV: intel_iommu=on"
            - "Nested Virtualization: kvm-intel.nested=1"
            - "Unsafe Interrupts: vfio_iommu_type1.allow_unsafe_interrupts=1"
            - "PCI Reallocation: pci=realloc"
            - "C(Note:)"
            - "Modifying kernel boot parameters settings can lead to a host boot failure.
               Please consult the product documentation before doing any changes."
            - "Kernel boot parameters changes require host deploy and restart. The host needs
               to be I(reinstalled) suceesfully and then to be I(rebooted) for kernel boot parameters
               to be applied."
    hosted_engine:
        description:
            - "If I(deploy) it means this host should deploy also hosted engine
               components."
            - "If I(undeploy) it means this host should un-deploy hosted engine
               components and this host will not function as part of the High
               Availability cluster."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add host with username/password supporting SR-IOV.
# Note that override_iptables is false by default in oVirt/RHV:
- ovirt_hosts:
    cluster: Default
    name: myhost
    address: 10.34.61.145
    password: secret
    override_iptables: true
    kernel_params:
      - intel_iommu=on

# Add host using public key
- ovirt_hosts:
    public_key: true
    cluster: Default
    name: myhost2
    address: 10.34.61.145
    override_iptables: true

# Deploy hosted engine host
- ovirt_hosts:
    cluster: Default
    name: myhost2
    password: secret
    address: 10.34.61.145
    override_iptables: true
    hosted_engine: deploy

# Maintenance
- ovirt_hosts:
    state: maintenance
    name: myhost

# Restart host using power management:
- ovirt_hosts:
    state: restarted
    name: myhost

# Upgrade host
- ovirt_hosts:
    state: upgraded
    name: myhost

# Reinstall host using public key
- ovirt_hosts:
    state: reinstalled
    name: myhost
    public_key: true

# Remove host
- ovirt_hosts:
    state: absent
    name: myhost
    force: True
'''

RETURN = '''
id:
    description: ID of the host which is managed
    returned: On success if host is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
host:
    description: "Dictionary of all the host attributes. Host attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/host."
    returned: On success if host is found.
    type: dict
'''

import time
import traceback

try:
    import ovirtsdk4.types as otypes

    from ovirtsdk4.types import HostStatus as hoststate
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    ovirt_full_argument_spec,
    wait,
)


class HostsModule(BaseModule):

    def build_entity(self):
        return otypes.Host(
            name=self._module.params['name'],
            cluster=otypes.Cluster(
                name=self._module.params['cluster']
            ) if self._module.params['cluster'] else None,
            comment=self._module.params['comment'],
            address=self._module.params['address'],
            root_password=self._module.params['password'],
            ssh=otypes.Ssh(
                authentication_method=otypes.SshAuthenticationMethod.PUBLICKEY,
            ) if self._module.params['public_key'] else None,
            kdump_status=otypes.KdumpStatus(
                self._module.params['kdump_integration']
            ) if self._module.params['kdump_integration'] else None,
            spm=otypes.Spm(
                priority=self._module.params['spm_priority'],
            ) if self._module.params['spm_priority'] else None,
            override_iptables=self._module.params['override_iptables'],
            display=otypes.Display(
                address=self._module.params['override_display'],
            ) if self._module.params['override_display'] else None,
            os=otypes.OperatingSystem(
                custom_kernel_cmdline=' '.join(self._module.params['kernel_params']),
            ) if self._module.params['kernel_params'] else None,
        )

    def update_check(self, entity):
        kernel_params = self._module.params.get('kernel_params')
        return (
            equal(self._module.params.get('comment'), entity.comment) and
            equal(self._module.params.get('kdump_integration'), entity.kdump_status) and
            equal(self._module.params.get('spm_priority'), entity.spm.priority) and
            equal(self._module.params.get('override_display'), getattr(entity.display, 'address', None)) and
            equal(
                sorted(kernel_params) if kernel_params else None,
                sorted(entity.os.custom_kernel_cmdline.split(' '))
            )
        )

    def pre_remove(self, entity):
        self.action(
            entity=entity,
            action='deactivate',
            action_condition=lambda h: h.status != hoststate.MAINTENANCE,
            wait_condition=lambda h: h.status == hoststate.MAINTENANCE,
        )

    def post_update(self, entity):
        if entity.status != hoststate.UP and self._module.params['state'] == 'present':
            if not self._module.check_mode:
                self._service.host_service(entity.id).activate()
            self.changed = True

    def post_reinstall(self, host):
        wait(
            service=self._service.service(host.id),
            condition=lambda h: h.status != hoststate.MAINTENANCE,
            fail_condition=failed_state,
            wait=self._module.params['wait'],
            timeout=self._module.params['timeout'],
        )


def failed_state(host):
    return host.status in [
        hoststate.ERROR,
        hoststate.INSTALL_FAILED,
        hoststate.NON_RESPONSIVE,
        hoststate.NON_OPERATIONAL,
    ]


def control_state(host_module):
    host = host_module.search_entity()
    if host is None:
        return

    state = host_module._module.params['state']
    host_service = host_module._service.service(host.id)
    if failed_state(host):
        # In case host is in INSTALL_FAILED status, we can reinstall it:
        if hoststate.INSTALL_FAILED == host.status and state != 'reinstalled':
            raise Exception(
                "Not possible to manage host '%s' in state '%s'." % (
                    host.name,
                    host.status
                )
            )
    elif host.status in [
        hoststate.REBOOT,
        hoststate.CONNECTING,
        hoststate.INITIALIZING,
        hoststate.INSTALLING,
        hoststate.INSTALLING_OS,
    ]:
        wait(
            service=host_service,
            condition=lambda host: host.status == hoststate.UP,
            fail_condition=failed_state,
        )
    elif host.status == hoststate.PREPARING_FOR_MAINTENANCE:
        wait(
            service=host_service,
            condition=lambda host: host.status == hoststate.MAINTENANCE,
            fail_condition=failed_state,
        )

    return host


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=[
                'present', 'absent', 'maintenance', 'upgraded', 'started',
                'restarted', 'stopped', 'reinstalled',
            ],
            default='present',
        ),
        name=dict(required=True),
        comment=dict(default=None),
        cluster=dict(default=None),
        address=dict(default=None),
        password=dict(default=None, no_log=True),
        public_key=dict(default=False, type='bool', aliases=['ssh_public_key']),
        kdump_integration=dict(default=None, choices=['enabled', 'disabled']),
        spm_priority=dict(default=None, type='int'),
        override_iptables=dict(default=None, type='bool'),
        force=dict(default=False, type='bool'),
        timeout=dict(default=600, type='int'),
        override_display=dict(default=None),
        kernel_params=dict(default=None, type='list'),
        hosted_engine=dict(default=None, choices=['deploy', 'undeploy']),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        hosts_service = connection.system_service().hosts_service()
        hosts_module = HostsModule(
            connection=connection,
            module=module,
            service=hosts_service,
        )

        state = module.params['state']
        host = control_state(hosts_module)
        if state == 'present':
            hosts_module.create(
                deploy_hosted_engine=(
                    module.params.get('hosted_engine') == 'deploy'
                ) if module.params.get('hosted_engine') is not None else None,
            )
            ret = hosts_module.action(
                action='activate',
                action_condition=lambda h: h.status == hoststate.MAINTENANCE,
                wait_condition=lambda h: h.status == hoststate.UP,
                fail_condition=failed_state,
            )
        elif state == 'absent':
            ret = hosts_module.remove()
        elif state == 'maintenance':
            hosts_module.action(
                action='deactivate',
                action_condition=lambda h: h.status != hoststate.MAINTENANCE,
                wait_condition=lambda h: h.status == hoststate.MAINTENANCE,
                fail_condition=failed_state,
            )
            ret = hosts_module.create()
        elif state == 'upgraded':
            result_state = hoststate.MAINTENANCE if host.status == hoststate.MAINTENANCE else hoststate.UP
            ret = hosts_module.action(
                action='upgrade',
                action_condition=lambda h: h.update_available,
                wait_condition=lambda h: h.status == result_state,
                post_action=lambda h: time.sleep(module.params['poll_interval']),
                fail_condition=failed_state,
            )
        elif state == 'started':
            ret = hosts_module.action(
                action='fence',
                action_condition=lambda h: h.status == hoststate.DOWN,
                wait_condition=lambda h: h.status in [hoststate.UP, hoststate.MAINTENANCE],
                fail_condition=failed_state,
                fence_type='start',
            )
        elif state == 'stopped':
            hosts_module.action(
                action='deactivate',
                action_condition=lambda h: h.status not in [hoststate.MAINTENANCE, hoststate.DOWN],
                wait_condition=lambda h: h.status in [hoststate.MAINTENANCE, hoststate.DOWN],
                fail_condition=failed_state,
            )
            ret = hosts_module.action(
                action='fence',
                action_condition=lambda h: h.status != hoststate.DOWN,
                wait_condition=lambda h: h.status == hoststate.DOWN if module.params['wait'] else True,
                fail_condition=failed_state,
                fence_type='stop',
            )
        elif state == 'restarted':
            ret = hosts_module.action(
                action='fence',
                wait_condition=lambda h: h.status == hoststate.UP,
                fail_condition=failed_state,
                fence_type='restart',
            )
        elif state == 'reinstalled':
            # Deactivate host if not in maintanence:
            hosts_module.action(
                action='deactivate',
                action_condition=lambda h: h.status not in [hoststate.MAINTENANCE, hoststate.DOWN],
                wait_condition=lambda h: h.status in [hoststate.MAINTENANCE, hoststate.DOWN],
                fail_condition=failed_state,
            )

            # Reinstall host:
            hosts_module.action(
                action='install',
                action_condition=lambda h: h.status == hoststate.MAINTENANCE,
                post_action=hosts_module.post_reinstall,
                wait_condition=lambda h: h.status == hoststate.MAINTENANCE,
                fail_condition=failed_state,
                host=otypes.Host(
                    override_iptables=module.params['override_iptables'],
                ) if module.params['override_iptables'] else None,
                root_password=module.params['password'],
                ssh=otypes.Ssh(
                    authentication_method=otypes.SshAuthenticationMethod.PUBLICKEY,
                ) if module.params['public_key'] else None,
                deploy_hosted_engine=(
                    module.params.get('hosted_engine') == 'deploy'
                ) if module.params.get('hosted_engine') is not None else None,
                undeploy_hosted_engine=(
                    module.params.get('hosted_engine') == 'undeploy'
                ) if module.params.get('hosted_engine') is not None else None,
            )

            # Activate host after reinstall:
            ret = hosts_module.action(
                action='activate',
                action_condition=lambda h: h.status == hoststate.MAINTENANCE,
                wait_condition=lambda h: h.status == hoststate.UP,
                fail_condition=failed_state,
            )
        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
