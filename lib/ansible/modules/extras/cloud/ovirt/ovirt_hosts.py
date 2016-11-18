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

try:
    import ovirtsdk4 as sdk
    import ovirtsdk4.types as otypes

    from ovirtsdk4.types import HostStatus as hoststate
except ImportError:
    pass

from ansible.module_utils.ovirt import *


DOCUMENTATION = '''
---
module: ovirt_hosts
short_description: Module to manage hosts in oVirt
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage hosts in oVirt"
options:
    name:
        description:
            - "Name of the the host to manage."
        required: true
    state:
        description:
            - "State which should a host to be in after successful completion."
        choices: ['present', 'absent', 'maintenance', 'upgraded', 'started', 'restarted', 'stopped']
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
    force:
        description:
            - "If True host will be forcibly moved to desired state."
        default: False
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add host with username/password
- ovirt_hosts:
    cluster: Default
    name: myhost
    address: 10.34.61.145
    password: secret

# Add host using public key
- ovirt_hosts:
    public_key: true
    cluster: Default
    name: myhost2
    address: 10.34.61.145

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
    description: "Dictionary of all the host attributes. Host attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/host."
    returned: On success if host is found.
'''


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
                authentication_method='publickey',
            ) if self._module.params['public_key'] else None,
            kdump_status=otypes.KdumpStatus(
                self._module.params['kdump_integration']
            ) if self._module.params['kdump_integration'] else None,
            spm=otypes.Spm(
                priority=self._module.params['spm_priority'],
            ) if self._module.params['spm_priority'] else None,
            override_iptables=self._module.params['override_iptables'],
        )

    def update_check(self, entity):
        return (
            equal(self._module.params.get('comment'), entity.comment) and
            equal(self._module.params.get('kdump_integration'), entity.kdump_status) and
            equal(self._module.params.get('spm_priority'), entity.spm.priority)
        )

    def pre_remove(self, entity):
        self.action(
            entity=entity,
            action='deactivate',
            action_condition=lambda h: h.status != hoststate.MAINTENANCE,
            wait_condition=lambda h: h.status == hoststate.MAINTENANCE,
        )

    def post_update(self, entity):
        if entity.status != hoststate.UP:
            if not self._module.check_mode:
                self._service.host_service(entity.id).activate()
            self.changed = True


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
        raise Exception("Not possible to manage host '%s'." % host.name)
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


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent', 'maintenance', 'upgraded', 'started', 'restarted', 'stopped'],
            default='present',
        ),
        name=dict(required=True),
        comment=dict(default=None),
        cluster=dict(default=None),
        address=dict(default=None),
        password=dict(default=None),
        public_key=dict(default=False, type='bool', aliases=['ssh_public_key']),
        kdump_integration=dict(default=None, choices=['enabled', 'disabled']),
        spm_priority=dict(default=None, type='int'),
        override_iptables=dict(default=None, type='bool'),
        force=dict(default=False, type='bool'),
        timeout=dict(default=600, type='int'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        hosts_service = connection.system_service().hosts_service()
        hosts_module = HostsModule(
            connection=connection,
            module=module,
            service=hosts_service,
        )

        state = module.params['state']
        control_state(hosts_module)
        if state == 'present':
            ret = hosts_module.create()
            hosts_module.action(
                action='activate',
                action_condition=lambda h: h.status == hoststate.MAINTENANCE,
                wait_condition=lambda h: h.status == hoststate.UP,
                fail_condition=failed_state,
            )
        elif state == 'absent':
            ret = hosts_module.remove()
        elif state == 'maintenance':
            ret = hosts_module.action(
                action='deactivate',
                action_condition=lambda h: h.status != hoststate.MAINTENANCE,
                wait_condition=lambda h: h.status == hoststate.MAINTENANCE,
                fail_condition=failed_state,
            )
        elif state == 'upgraded':
            ret = hosts_module.action(
                action='upgrade',
                action_condition=lambda h: h.update_available,
                wait_condition=lambda h: h.status == hoststate.UP,
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
                wait_condition=lambda h: h.status == hoststate.DOWN,
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


        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e))
    finally:
        connection.close(logout=False)


from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
