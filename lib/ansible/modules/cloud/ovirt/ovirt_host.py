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
module: ovirt_host
short_description: Module to manage hosts in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage hosts in oVirt/RHV"
options:
    id:
        description:
            - "ID of the host to manage."
        version_added: "2.8"
    name:
        description:
            - "Name of the host to manage."
        required: true
    state:
        description:
            - "State which should a host to be in after successful completion."
            - "I(iscsilogin) and I(iscsidiscover) are supported since version 2.4."
        choices: [
            'present', 'absent', 'maintenance', 'upgraded', 'started',
            'restarted', 'stopped', 'reinstalled', 'iscsidiscover', 'iscsilogin'
        ]
        default: present
    comment:
        description:
            - "Description of the host."
    timeout:
        description:
            - "The amount of time in seconds the module should wait for the host to
               get into desired state."
        default: 600
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
        type: bool
        aliases: ['ssh_public_key']
    kdump_integration:
        description:
            - "Specify if host will have enabled Kdump integration."
        choices: ['enabled', 'disabled']
    spm_priority:
        description:
            - "SPM priority of the host. Integer value from 1 to 10, where higher number means higher priority."
    override_iptables:
        description:
            - "If True host iptables will be overridden by host deploy script."
            - "Note that C(override_iptables) is I(false) by default in oVirt/RHV."
        type: bool
    force:
        description:
            - "Indicates that the host should be removed even if it is non-responsive,
               or if it is part of a Gluster Storage cluster and has volume bricks on it."
            - "WARNING: It doesn't forcibly remove the host if another host related operation is being executed on the host at the same time."
        default: False
        type: bool
    override_display:
        description:
            - "Override the display address of all VMs on this host with specified address."
        type: bool
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
               to be I(reinstalled) successfully and then to be I(rebooted) for kernel boot parameters
               to be applied."
    hosted_engine:
        description:
            - "If I(deploy) it means this host should deploy also hosted engine
               components."
            - "If I(undeploy) it means this host should un-deploy hosted engine
               components and this host will not function as part of the High
               Availability cluster."
        choices:
            - 'deploy'
            - 'undeploy'
    power_management_enabled:
        description:
            - "Enable or disable power management of the host."
            - "For more comprehensive setup of PM use C(ovirt_host_pm) module."
        version_added: 2.4
        type: bool
    activate:
        description:
            - "If C(state) is I(present) activate the host."
            - "This parameter is good to disable, when you don't want to change
               the state of host when using I(present) C(state)."
        default: True
        type: bool
        version_added: 2.4
    iscsi:
        description:
          - "If C(state) is I(iscsidiscover) it means that the iscsi attribute is being
             used to discover targets"
          - "If C(state) is I(iscsilogin) it means that the iscsi attribute is being
             used to login to the specified targets passed as part of the iscsi attribute"
        version_added: "2.4"
    check_upgrade:
        description:
            - "If I(true) and C(state) is I(upgraded) run check for upgrade
               action before executing upgrade action."
        default: True
        type: bool
        version_added: 2.4
    reboot_after_upgrade:
        description:
            - "If I(true) and C(state) is I(upgraded) reboot host after successful upgrade."
        default: True
        type: bool
        version_added: 2.6
    vgpu_placement:
        description:
            - If I(consolidated), each vGPU is placed on the first physical card with
              available space. This is the default placement, utilizing all available
              space on the physical cards.
            - If I(separated), each vGPU is placed on a separate physical card, if
              possible. This can be useful for improving vGPU performance.
        choices: ['consolidated', 'separated']
        version_added: 2.8
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add host with username/password supporting SR-IOV.
# Note that override_iptables is false by default in oVirt/RHV:
- ovirt_host:
    cluster: Default
    name: myhost
    address: 10.34.61.145
    password: secret
    override_iptables: true
    kernel_params:
      - intel_iommu=on

# Add host using public key
- ovirt_host:
    public_key: true
    cluster: Default
    name: myhost2
    address: 10.34.61.145
    override_iptables: true

# Deploy hosted engine host
- ovirt_host:
    cluster: Default
    name: myhost2
    password: secret
    address: 10.34.61.145
    override_iptables: true
    hosted_engine: deploy

# Maintenance
- ovirt_host:
    state: maintenance
    name: myhost

# Restart host using power management:
- ovirt_host:
    state: restarted
    name: myhost

# Upgrade host
- ovirt_host:
    state: upgraded
    name: myhost

# discover iscsi targets
- ovirt_host:
    state: iscsidiscover
    name: myhost
    iscsi:
      username: iscsi_user
      password: secret
      address: 10.34.61.145
      port: 3260


# login to iscsi targets
- ovirt_host:
    state: iscsilogin
    name: myhost
    iscsi:
      username: iscsi_user
      password: secret
      address: 10.34.61.145
      target: "iqn.2015-07.com.mlipchuk2.redhat:444"
      port: 3260


# Reinstall host using public key
- ovirt_host:
    state: reinstalled
    name: myhost
    public_key: true

# Remove host
- ovirt_host:
    state: absent
    name: myhost
    force: True

# Retry removing host when failed (https://bugzilla.redhat.com/show_bug.cgi?id=1719271)
- ovirt_host:
    state: absent
    name: myhost
  register: result
  until: not result.failed
  retries: 6
  delay: 20

# Change host Name
- ovirt_host:
    id: 00000000-0000-0000-0000-000000000000
    name: "new host name"
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
iscsi_targets:
    description: "List of host iscsi targets"
    returned: On success if host is found and state is iscsidiscover.
    type: list
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
    get_id_by_name,
    ovirt_full_argument_spec,
    wait,
)


class HostsModule(BaseModule):
    def __init__(self, start_event=None, *args, **kwargs):
        super(HostsModule, self).__init__(*args, **kwargs)
        self.start_event = start_event

    def build_entity(self):
        return otypes.Host(
            id=self._module.params.get('id'),
            name=self.param('name'),
            cluster=otypes.Cluster(
                name=self.param('cluster')
            ) if self.param('cluster') else None,
            comment=self.param('comment'),
            address=self.param('address'),
            root_password=self.param('password'),
            ssh=otypes.Ssh(
                authentication_method=otypes.SshAuthenticationMethod.PUBLICKEY,
            ) if self.param('public_key') else None,
            spm=otypes.Spm(
                priority=self.param('spm_priority'),
            ) if self.param('spm_priority') else None,
            override_iptables=self.param('override_iptables'),
            display=otypes.Display(
                address=self.param('override_display'),
            ) if self.param('override_display') else None,
            os=otypes.OperatingSystem(
                custom_kernel_cmdline=' '.join(self.param('kernel_params')),
            ) if self.param('kernel_params') else None,
            power_management=otypes.PowerManagement(
                enabled=self.param('power_management_enabled'),
                kdump_detection=self.param('kdump_integration') == 'enabled',
            ) if self.param('power_management_enabled') is not None or self.param('kdump_integration') else None,
            vgpu_placement=otypes.VgpuPlacement(
                self.param('vgpu_placement')
            ) if self.param('vgpu_placement') is not None else None,
        )

    def update_check(self, entity):
        kernel_params = self.param('kernel_params')
        return (
            equal(self.param('comment'), entity.comment) and
            equal(self.param('kdump_integration'), 'enabled' if entity.power_management.kdump_detection else 'disabled') and
            equal(self.param('spm_priority'), entity.spm.priority) and
            equal(self.param('name'), entity.name) and
            equal(self.param('power_management_enabled'), entity.power_management.enabled) and
            equal(self.param('override_display'), getattr(entity.display, 'address', None)) and
            equal(self.param('vgpu_placement'), str(entity.vgpu_placement)) and
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

    def post_reinstall(self, host):
        wait(
            service=self._service.service(host.id),
            condition=lambda h: h.status != hoststate.MAINTENANCE,
            fail_condition=failed_state,
            wait=self.param('wait'),
            timeout=self.param('timeout'),
        )

    def raise_host_exception(self):
        events = self._connection.system_service().events_service().list(from_=int(self.start_event.index))
        error_events = [
            event.description for event in events
            if event.host is not None and (event.host.id == self.param('id') or event.host.name == self.param('name')) and
            event.severity in [otypes.LogSeverity.WARNING, otypes.LogSeverity.ERROR]
        ]
        if error_events:
            raise Exception("Error message: %s" % error_events)
        return True

    def failed_state_after_reinstall(self, host, count=0):
        if host.status in [
            hoststate.ERROR,
            hoststate.INSTALL_FAILED,
            hoststate.NON_OPERATIONAL,
        ]:
            return self.raise_host_exception()

        # If host is in non-responsive state after upgrade/install
        # let's wait for few seconds and re-check again the state:
        if host.status == hoststate.NON_RESPONSIVE:
            if count <= 3:
                time.sleep(20)
                return self.failed_state_after_reinstall(
                    self._service.service(host.id).get(),
                    count + 1,
                )
            else:
                return self.raise_host_exception()

        return False


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
                'restarted', 'stopped', 'reinstalled', 'iscsidiscover', 'iscsilogin'
            ],
            default='present',
        ),
        name=dict(required=True),
        id=dict(default=None),
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
        power_management_enabled=dict(default=None, type='bool'),
        activate=dict(default=True, type='bool'),
        iscsi=dict(default=None, type='dict'),
        check_upgrade=dict(default=True, type='bool'),
        reboot_after_upgrade=dict(default=True, type='bool'),
        vgpu_placement=dict(default=None, choices=['consolidated', 'separated']),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'iscsidiscover', ['iscsi']],
            ['state', 'iscsilogin', ['iscsi']]
        ]
    )

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        hosts_service = connection.system_service().hosts_service()
        start_event = connection.system_service().events_service().list(max=1)[0]
        hosts_module = HostsModule(
            connection=connection,
            module=module,
            service=hosts_service,
            start_event=start_event,
        )

        state = module.params['state']
        host = control_state(hosts_module)
        if state == 'present':
            ret = hosts_module.create(
                deploy_hosted_engine=(
                    module.params.get('hosted_engine') == 'deploy'
                ) if module.params.get('hosted_engine') is not None else None,
                activate=module.params['activate'],
                result_state=(hoststate.MAINTENANCE if module.params['activate'] is False else hoststate.UP) if host is None else None,
                fail_condition=hosts_module.failed_state_after_reinstall if host is None else lambda h: False,
            )
            if module.params['activate'] and host is not None:
                ret = hosts_module.action(
                    action='activate',
                    action_condition=lambda h: h.status != hoststate.UP,
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
            events_service = connection.system_service().events_service()
            last_event = events_service.list(max=1)[0]

            if module.params['check_upgrade']:
                hosts_module.action(
                    action='upgrade_check',
                    action_condition=lambda host: not host.update_available,
                    wait_condition=lambda host: host.update_available or (
                        len([
                            event
                            for event in events_service.list(
                                from_=int(last_event.id),
                                search='type=885',
                                # Uncomment when 4.1 is EOL, and remove the cond:
                                # if host.name in event.description
                                # search='type=885 and host.name=%s' % host.name,
                            ) if host.name in event.description
                        ]) > 0
                    ),
                    fail_condition=lambda host: len([
                        event
                        for event in events_service.list(
                            from_=int(last_event.id),
                            search='type=839 or type=887 and host.name=%s' % host.name,
                        )
                    ]) > 0,
                )
                # Set to False, because upgrade_check isn't 'changing' action:
                hosts_module._changed = False
            ret = hosts_module.action(
                action='upgrade',
                action_condition=lambda h: h.update_available,
                wait_condition=lambda h: h.status == result_state,
                post_action=lambda h: time.sleep(module.params['poll_interval']),
                fail_condition=lambda h: hosts_module.failed_state_after_reinstall(h) or (
                    len([
                        event
                        for event in events_service.list(
                            from_=int(last_event.id),
                            # Fail upgrade if migration fails:
                            # 17: Failed to switch Host to Maintenance mode
                            # 65, 140: Migration failed
                            # 166: No available host was found to migrate VM
                            search='type=65 or type=140 or type=166 or type=17',
                        ) if host.name in event.description
                    ]) > 0
                ),
                reboot=module.params['reboot_after_upgrade'],
            )
        elif state == 'iscsidiscover':
            host_id = get_id_by_name(hosts_service, module.params['name'])
            iscsi_param = module.params['iscsi']
            iscsi_targets = hosts_service.service(host_id).iscsi_discover(
                iscsi=otypes.IscsiDetails(
                    port=int(iscsi_param.get('port', 3260)),
                    username=iscsi_param.get('username'),
                    password=iscsi_param.get('password'),
                    address=iscsi_param.get('address'),
                ),
            )
            ret = {
                'changed': False,
                'id': host_id,
                'iscsi_targets': iscsi_targets,
            }
        elif state == 'iscsilogin':
            host_id = get_id_by_name(hosts_service, module.params['name'])
            iscsi_param = module.params['iscsi']
            ret = hosts_module.action(
                action='iscsi_login',
                iscsi=otypes.IscsiDetails(
                    port=int(iscsi_param.get('port', 3260)),
                    username=iscsi_param.get('username'),
                    password=iscsi_param.get('password'),
                    address=iscsi_param.get('address'),
                    target=iscsi_param.get('target'),
                ),
            )
        elif state == 'started':
            ret = hosts_module.action(
                action='fence',
                action_condition=lambda h: h.status == hoststate.DOWN,
                wait_condition=lambda h: h.status in [hoststate.UP, hoststate.MAINTENANCE],
                fail_condition=hosts_module.failed_state_after_reinstall,
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
                fail_condition=hosts_module.failed_state_after_reinstall,
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
                fail_condition=hosts_module.failed_state_after_reinstall,
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
