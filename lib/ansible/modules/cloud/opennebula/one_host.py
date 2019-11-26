#!/usr/bin/python
#
# Copyright 2018 www.privaz.io Valletech AB
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: one_host

short_description: Manages OpenNebula Hosts

version_added: "2.6"

requirements:
    - pyone

description:
    - "Manages OpenNebula Hosts"

options:
    name:
        description:
            - Hostname of the machine to manage.
        required: true
    state:
        description:
            - Takes the host to the desired lifecycle state.
            - If C(absent) the host will be deleted from the cluster.
            - If C(present) the host will be created in the cluster (includes C(enabled), C(disabled) and C(offline) states).
            - If C(enabled) the host is fully operational.
            - C(disabled), e.g. to perform maintenance operations.
            - C(offline), host is totally offline.
        choices:
            - absent
            - present
            - enabled
            - disabled
            - offline
        default: present
    im_mad_name:
        description:
            - The name of the information manager, this values are taken from the oned.conf with the tag name IM_MAD (name)
        default: kvm
    vmm_mad_name:
        description:
            - The name of the virtual machine manager mad name, this values are taken from the oned.conf with the tag name VM_MAD (name)
        default: kvm
    cluster_id:
        description:
            - The cluster ID.
        default: 0
    cluster_name:
        description:
            - The cluster specified by name.
    labels:
        description:
            - The labels for this host.
    template:
        description:
            - The template or attribute changes to merge into the host template.
        aliases:
            - attributes

extends_documentation_fragment: opennebula

author:
    - Rafael del Valle (@rvalle)
'''

EXAMPLES = '''
- name: Create a new host in OpenNebula
  one_host:
    name: host1
    cluster_id: 1
    api_url: http://127.0.0.1:2633/RPC2

- name: Create a host and adjust its template
  one_host:
    name: host2
    cluster_name: default
    template:
        LABELS:
            - gold
            - ssd
        RESERVED_CPU: -100
'''

# TODO: pending setting guidelines on returned values
RETURN = '''
'''

# TODO: Documentation on valid state transitions is required to properly implement all valid cases
# TODO: To be coherent with CLI this module should also provide "flush" functionality

from ansible.module_utils.opennebula import OpenNebulaModule

try:
    from pyone import HOST_STATES, HOST_STATUS
except ImportError:
    pass  # handled at module utils


# Pseudo definitions...

HOST_ABSENT = -99  # the host is absent (special case defined by this module)


class HostModule(OpenNebulaModule):

    def __init__(self):

        argument_spec = dict(
            name=dict(type='str', required=True),
            state=dict(choices=['present', 'absent', 'enabled', 'disabled', 'offline'], default='present'),
            im_mad_name=dict(type='str', default="kvm"),
            vmm_mad_name=dict(type='str', default="kvm"),
            cluster_id=dict(type='int', default=0),
            cluster_name=dict(type='str'),
            labels=dict(type='list'),
            template=dict(type='dict', aliases=['attributes']),
        )

        mutually_exclusive = [
            ['cluster_id', 'cluster_name']
        ]

        OpenNebulaModule.__init__(self, argument_spec, mutually_exclusive=mutually_exclusive)

    def allocate_host(self):
        """
        Creates a host entry in OpenNebula
        Returns: True on success, fails otherwise.

        """
        if not self.one.host.allocate(self.get_parameter('name'),
                                      self.get_parameter('vmm_mad_name'),
                                      self.get_parameter('im_mad_name'),
                                      self.get_parameter('cluster_id')):
            self.fail(msg="could not allocate host")
        else:
            self.result['changed'] = True
        return True

    def wait_for_host_state(self, host, target_states):
        """
        Utility method that waits for a host state.
        Args:
            host:
            target_states:

        """
        return self.wait_for_state('host',
                                   lambda: self.one.host.info(host.ID).STATE,
                                   lambda s: HOST_STATES(s).name, target_states,
                                   invalid_states=[HOST_STATES.ERROR, HOST_STATES.MONITORING_ERROR])

    def run(self, one, module, result):

        # Get the list of hosts
        host_name = self.get_parameter("name")
        host = self.get_host_by_name(host_name)

        # manage host state
        desired_state = self.get_parameter('state')
        if bool(host):
            current_state = host.STATE
            current_state_name = HOST_STATES(host.STATE).name
        else:
            current_state = HOST_ABSENT
            current_state_name = "ABSENT"

        # apply properties
        if desired_state == 'present':
            if current_state == HOST_ABSENT:
                self.allocate_host()
                host = self.get_host_by_name(host_name)
                self.wait_for_host_state(host, [HOST_STATES.MONITORED])
            elif current_state in [HOST_STATES.ERROR, HOST_STATES.MONITORING_ERROR]:
                self.fail(msg="invalid host state %s" % current_state_name)

        elif desired_state == 'enabled':
            if current_state == HOST_ABSENT:
                self.allocate_host()
                host = self.get_host_by_name(host_name)
                self.wait_for_host_state(host, [HOST_STATES.MONITORED])
            elif current_state in [HOST_STATES.DISABLED, HOST_STATES.OFFLINE]:
                if one.host.status(host.ID, HOST_STATUS.ENABLED):
                    self.wait_for_host_state(host, [HOST_STATES.MONITORED])
                    result['changed'] = True
                else:
                    self.fail(msg="could not enable host")
            elif current_state in [HOST_STATES.MONITORED]:
                pass
            else:
                self.fail(msg="unknown host state %s, cowardly refusing to change state to enable" % current_state_name)

        elif desired_state == 'disabled':
            if current_state == HOST_ABSENT:
                self.fail(msg='absent host cannot be put in disabled state')
            elif current_state in [HOST_STATES.MONITORED, HOST_STATES.OFFLINE]:
                if one.host.status(host.ID, HOST_STATUS.DISABLED):
                    self.wait_for_host_state(host, [HOST_STATES.DISABLED])
                    result['changed'] = True
                else:
                    self.fail(msg="could not disable host")
            elif current_state in [HOST_STATES.DISABLED]:
                pass
            else:
                self.fail(msg="unknown host state %s, cowardly refusing to change state to disable" % current_state_name)

        elif desired_state == 'offline':
            if current_state == HOST_ABSENT:
                self.fail(msg='absent host cannot be placed in offline state')
            elif current_state in [HOST_STATES.MONITORED, HOST_STATES.DISABLED]:
                if one.host.status(host.ID, HOST_STATUS.OFFLINE):
                    self.wait_for_host_state(host, [HOST_STATES.OFFLINE])
                    result['changed'] = True
                else:
                    self.fail(msg="could not set host offline")
            elif current_state in [HOST_STATES.OFFLINE]:
                pass
            else:
                self.fail(msg="unknown host state %s, cowardly refusing to change state to offline" % current_state_name)

        elif desired_state == 'absent':
            if current_state != HOST_ABSENT:
                if one.host.delete(host.ID):
                    result['changed'] = True
                else:
                    self.fail(msg="could not delete host from cluster")

        # if we reach this point we can assume that the host was taken to the desired state

        if desired_state != "absent":
            # manipulate or modify the template
            desired_template_changes = self.get_parameter('template')

            if desired_template_changes is None:
                desired_template_changes = dict()

            # complete the template with specific ansible parameters
            if self.is_parameter('labels'):
                desired_template_changes['LABELS'] = self.get_parameter('labels')

            if self.requires_template_update(host.TEMPLATE, desired_template_changes):
                # setup the root element so that pyone will generate XML instead of attribute vector
                desired_template_changes = {"TEMPLATE": desired_template_changes}
                if one.host.update(host.ID, desired_template_changes, 1):  # merge the template
                    result['changed'] = True
                else:
                    self.fail(msg="failed to update the host template")

            # the cluster
            if host.CLUSTER_ID != self.get_parameter('cluster_id'):
                if one.cluster.addhost(self.get_parameter('cluster_id'), host.ID):
                    result['changed'] = True
                else:
                    self.fail(msg="failed to update the host cluster")

        # return
        self.exit()


def main():
    HostModule().run_module()


if __name__ == '__main__':
    main()
