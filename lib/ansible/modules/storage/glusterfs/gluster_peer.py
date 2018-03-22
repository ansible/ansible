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
       choices: ["yes", "no"]
       default: "no"
       description:
          - Applicable only while removing the nodes from the pool. gluster
            will refuse to detach a node from the pool if any one of the node
            is down, in such cases force can be used.
requirements:
  - PyYAML
  - GlusterFS > 3.2
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
         force: yes
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ast import literal_eval


class Peer(object):
    def __init__(self, module):
        self.module = module
        self.state = self._validated_params('state')

    def _validated_params(self, opt):
        if self.module.params[opt] is None:
            msg = "Please provide %s option in the playbook!" % opt
            self.module.fail_json(rc=4, msg=msg)
        return self.module.params[opt]

    def get_nodes(self):
        nodes = literal_eval(self._validated_params('nodes'))
        if nodes[0] is None:
            # Found a list with None as its first element
            self.module.exit_json(rc=1, msg="No nodes found, provide at least "
                                  "one node.")
        return nodes

    def gluster_peer_ops(self):
        nodes = self.get_nodes()
        force = 'force' if self.module.params.get('force') == 'yes' else ''
        if self.state == 'present':
            nodes = self.get_to_be_probed_hosts(nodes)
            action = 'probe'
        elif self.state == 'absent':
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
            self.module.exit_json(rc=0, changed=1)
        else:
            self.module.fail_json(rc=1, msg='\n'.join(errors))

    def _run_command(self, op, opts):
        cmd = self.module.get_bin_path(op, True) + opts + ' --mode=script'
        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            force=dict(choices=["yes", "no"]),
            nodes=dict(),
            state=dict(required=True, choices=["absent", "present"]),
        ),
    )
    pops = Peer(module)
    cmds = pops.gluster_peer_ops()
    errors = pops.call_peer_commands(cmds)
    pops.get_output(errors)


if __name__ == "__main__":
    main()
