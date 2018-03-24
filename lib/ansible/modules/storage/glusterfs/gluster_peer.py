#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Nandaja Varma <nvarma@redhat.com>
# Copyright 2018 Red Hat, Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gluster_peer
short_description: Attach/Detach peers to/from the cluster
description:
  - Create or diminish a GlusterFS trusted storage pool. A set of nodes can be
    added into an existing trusted storage pool or a new storage pool can be
    formed. Or, nodes can be removed from an existing trusted storage pool.
version_added: "2.6"
author: Sachidananda Urs (@sac)
options:
    state:
       choices: ["present", "absent"]
       description:
          - Determines whether the nodes should be attached to the pool or
            removed from the pool. If the state is present, nodes will be
            attached to the pool. If state is absent, nodes will be detached
            from the pool.
       required: true
    nodes:
       description:
          - List of nodes that have to be probed into the pool.
       required: true
    force:
       type: bool
       default: "false"
       description:
          - Applicable only while removing the nodes from the pool. gluster
            will refuse to detach a node from the pool if any one of the node
            is down, in such cases force can be used.
requirements:
  - GlusterFS > 3.2
notes:
  - This module does not support check mode.
'''

EXAMPLES = '''
- name: Create a trusted storage pool
  gluster_pool:
        state: present
        nodes:
             - 10.0.1.5
             - 10.0.1.10

- name: Delete a node from the trusted storage pool
  gluster_pool:
         state: absent
         nodes:
              - 10.0.1.10

- name: Delete a node from the trusted storage pool by force
  gluster_pool:
         state: absent
         nodes:
              - 10.0.0.1
         force: true
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ast import literal_eval
from distutils.version import LooseVersion


class Peer(object):
    def __init__(self, module):
        self.module = module
        self.state = self.module.params['state']

    def gluster_peer_ops(self):
        try:
            nodes = literal_eval(self.module.params['nodes'])
        except ValueError:
            self.module.fail_json(msg="nodes must be a list")
        if not nodes:
            self.module.fail_json(msg="nodes list cannot be empty")
        # There is a possiblitity of nodes getting other type of data
        # structures. For example a dictionary
        if not isinstance(nodes, list):
            self.module.fail_json(msg="nodes must be a list")
        force = 'force' if self.module.params.get('force') else ''
        if self.state == 'present':
            nodes = self.get_to_be_probed_hosts(nodes)
            action = 'probe'
        else:
            action = 'detach'
        cmd = []
        for node in nodes:
            cmd.append(' peer ' + action + ' ' + node + ' ' + force)
        return cmd

    def get_to_be_probed_hosts(self, hosts):
        rc, output, err = self.module.run_command("gluster pool list")
        peers_in_cluster = [line.split('\t')[1].strip() for
                            line in filter(None, output.split('\n')[1:])]
        try:
            peers_in_cluster.remove('localhost')
        except ValueError:
            # It is ok not to have localhost in list
            pass
        hosts_to_be_probed = [host for host in hosts if host not in
                              peers_in_cluster]
        return hosts_to_be_probed

    def call_peer_commands(self, cmds):
        errors = []
        for cmd in cmds:
            rc, out, err = self._run_command('gluster', cmd)
            if rc:
                errors.append(err)
        return errors

    def get_output(self, errors):
        if not errors:
            self.module.exit_json(rc=0, changed=True)
        else:
            self.module.fail_json(rc=1, msg='\n'.join(errors))

    def _run_command(self, op, opts):
        cmd = self.module.get_bin_path(op, True) + opts + ' --mode=script'
        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            force=dict(type='bool', required=False),
            nodes=dict(required=True),
            state=dict(required=True, choices=["absent", "present"]),
        ),
    )
    pops = Peer(module)
    required_version = "3.2"
    # Verify if required GlusterFS version is installed
    if is_invalid_gluster_version(module, required_version):
        module.fail_json(msg="GlusterFS version > %s is required" %
                         required_version)
    cmds = pops.gluster_peer_ops()
    errors = pops.call_peer_commands(cmds)
    pops.get_output(errors)


def is_invalid_gluster_version(module, required_version):
    cmd = module.get_bin_path('gluster', True) + ' --version'
    result = module.run_command(cmd)
    ver_line = result[1].split('\n')[0]
    version = ver_line.split(' ')[1]
    # If the installed version is less than 3.2, it is an invalid version
    # return True
    return LooseVersion(version) < LooseVersion(required_version)


if __name__ == "__main__":
    main()
