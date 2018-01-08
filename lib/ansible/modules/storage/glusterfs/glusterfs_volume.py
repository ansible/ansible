#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2015, Nandaja Varma <nvarma@redhat.com>
# Copyright: (c) 2018, Devyani Kota <dkota@redhat.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: glusterfs_volume
short_description: Implementation of GlusterFS
description:
    - A module to set-up a GlusterFS cluster by
      creating volumes out of bricks. The host group on which
      playbooks will be written for this module should contain
      only one hostname which should be a part of the cluster
      and from which all the Gluster commands will be executed.
      This will make sure the commands are only run once.
version_added: "2.5"
options:
    action:
        required: True
        choices: [create, delete, start, stop, add-brick, remove-brick, replace-brick,
                  rebalance, profile_state, bitrot, set, barrier]
    volname:
        required: True
        description: Specifies the name of the Gluster volume to be created.
    hosts:
        required: True
        description: The list of all the hosts that are to be a part of the
                     cluster.
    bricks:
        required: True (If and action is in [create, add-brick, remove-brick])
        description: Specifies the bricks that constitutes the volume if
                     the action is volume create, the new bricks to be
                     added to a volume if the action is volume add-brick
                     and the bricks to be removed out of a volume
                     if the action is volume remove-brick. Format of each
                     brick should be hostname:brick_path.
    force:
        required: False
        description: Specifies if an operation is to be forced.
                     Applicable only to peer detach, volume { create, start,
                     stop, add-brick}
    key:
        required: True if action is set
        description: Set action sets options for the volume. Key
                     specifies which option is to be set
    value:
        required: True if action is set
        description: Specifies the value to be set for the option
                     specified by key.
    transport:
        required: False
        description: Specifies which transport type is to be used
                     while creating the volume. Default is tcp.
    replica:
        required: False
        description: Specifies the volume to be created is of type
                     replicate or not. Can also be used to change the
                     type while adding or removing bricks
    replica_count:
        required: True if replica is yes
        description: Specifies the replica count if the volume type is
                     to be replica
    arbiter_count:
        required: False
        description: If volume is of type replica, arbiter_count will
                     specify the number of bricks that will be configured
                     as arbiter node. If replica_count is 3 and arbiter_count
                     is 1, 3rd brick of the replica is automatically
                     configured as an arbiter node.
    disperse:
        required: False
        choices: [yes, no]
        description: Specifies if the volume is to be disperse or not
    disperse_count:
        required: False
        description: Specifies the number of disperse bricks. If not
        specified, the number of bricks specified is taken as the
        <count> value.
    redundancy_count:
        required: False
        description: Specifies the number of redundancy bricks. If
        if not specified and the volume if of type disperse,
        it's default value is computed so that it generates an
        optimal configuration.
    state:
        required: True
        choices: ["absent", "present", "remove-brick", "started",
                  "stopped", "replace-brick", "rebalance",
                  "add-brick", "profile", "set", "barrier", "bitrot" ]
    profile_state:
        required: False
        choices: [start, stop]
        description: Starts or stops profiling on a given gluster volume
    barrier:
        required: False
        choices: [enable, disable]
        description: Enables or disables volume barrier.
    scrub:
        required: False
        choices: [pause, resume]
        description: Sets Volume bitrot scrub options.
    scrub_throttle:
        required: False
        choices: [lazy, normal, aggressive]
        description: Sets volume bitrot scrub-throttle rate.
    scrub_frequency:
        required: False
        choices: [daily, weekly, biweekly, monthly]
        description: Sets volume bitrot scrub-frequency.
    bitrot_daemon:
        required: False
        choices: [enable, disable]
        description: Enables or disables Volume Bitrot detection daemon
'''

EXAMPLES = '''
---
- name: Create a volume
  glusterfs_volume:
    state=present
    volume="{{ volname }}"
    bricks="{{ bricks }}"
    hosts="{{ gluster_hosts }}"
    transport="{{ transport }}"
    replica_count="{{ replica_count }}"
    arbiter_count="{{ arbiter_count }}"
    disperse="{{ disperse }}"
    disperse_count="{{ disperse_count }}"
    redundancy_count="{{ redundancy_count }}"
    force="{{ force | default('no') }}"

- name: Start volume profiling
  glusterfs_volume:
    state=profile
    volume="{{ volname }}"
    profile_state="start"
  run_once: true

- name: Set volume options
  glusterfs_volume:
    state=set
    volume="{{ volname }}"
    key="performance.cache-size"
    value="256MB"
  run_once: true

- name: Enable volume barrier
  glusterfs_volume:
    state=barrier
    volume="{{ volname }}"
    barrier_state="enable"
  run_once: true

- name: Enable bitrot daemon
  glusterfs_volume:
    state=bitrot
    volume="{{ volname }}"
    bitrot_daemon="enable"

- name: Set bitrot scrub frequency to daily
  glusterfs_volume:
    state=bitrot
    volume="{{ volname }}"
    scrub_frequency="daily"

- name: Set bitrot scrub throttle rate to aggressive
  glusterfs_volume:
    state=bitrot
    volume="{{ volname }}"
    scrub_throttle="aggressive"

- name: Set bitrot scrub to pause
  glusterfs_volume:
    state=bitrot
    volume="{{ volname }}"
    scrub="pause"
'''

import sys
import re

from collections import OrderedDict
from ansible.module_utils.basic import AnsibleModule
from ast import literal_eval


class Glusterfs_Volume(object):

    def __init__(self, module):
        self.module = module
        self.action = self._validated_params('state')
        if self.action == 'present':
            self.action = 'create'
        elif self.action == 'absent':
            self.action = 'delete'
        elif self.action == 'started':
            self.action = 'start'
        elif self.action == 'stopped':
            self.action = 'stop'
        self.force = 'force' if self.module.params.get('force') == 'yes' else ''
        self.gluster_volume_ops()

    def get_playbook_params(self, opt):
        return self.module.params[opt]

    def _validated_params(self, opt):
        value = self.get_playbook_params(opt)
        if value is None:
            msg = "Please provide %s option in the playbook!" % opt
            self.module.fail_json(rc=3, msg=msg)
        return value

    def get_host_names(self, required=False):
        '''
           Something like this can be used in the playbook:
           hosts="{% for host in groups[<group name>] %}
           {{ hostvars[host]['private_ip'] }},{% endfor %}"

        '''
        if not required:
            hosts = self.module.params['hosts']
            if hosts:
                self.hosts = literal_eval(hosts)
        else:
            self.hosts = literal_eval(self._validated_params('hosts'))

    def append_host_name(self):
        brick_list = []
        for host, bricks in zip(self.hosts, self.bricks):
            for brick in bricks.strip('[]').split(','):
                brick_list.append(host + ':' + brick.strip())
        return brick_list

    def get_brick_list_of_all_hosts(self):
        bricks = self._validated_params('bricks')
        if re.search(r'(.*):(.*)', bricks):
            return self.get_brick_list()
        '''
        If the bricks are not given in hostname:brickpath
        format, hostnames are to be provided as
        'hosts' in the playbook.
        This method gets the bricks of all the hosts in the pool.
        Expected to provide 'bricks' in the yml in the same
        order as that of the hosts.
        '''
        if not self.hosts:
            self.module.fail_json(rc=15, msg="Provide the bricks in hostname:brickpath "
                                  " format or provide 'hosts' and 'bricks' should be of a format "
                                  " 'brick1, brick2; bricka, brickb' where brick1, brick2 "
                                  " belongs to host1 and brick1,brickb belongs to host2")
        self.bricks = filter(None, [brick.strip() for brick in
                                    bricks.split(';')])
        return ' '.join(brick_path for brick_path in self.append_host_name())

    def get_volume_configs(self):
        options = ' '
        if int(self.module.params['replica_count']) != 0:
            options += ' replica %s ' % self._validated_params('replica_count')
            arbiter_count = self.module.params['arbiter_count']
            if int(arbiter_count):
                options += ' arbiter %s ' % arbiter_count
        if self.module.params['disperse'] == 'yes':
            disperse_count = self.module.params['disperse_count']
            if int(disperse_count):
                options += ' disperse-data %s ' % disperse_count
            else:
                options += ' disperse '
            redundancy = self.module.params['redundancy_count']
            if int(redundancy):
                options += ' redundancy %s ' % redundancy
        transport = self.module.params['transport']
        if transport:
            options += ' transport %s ' % transport
        return (options + ' ')

    def get_brick_list(self):
        return ' '.join(re.sub('[\[\]\']', '', brick.strip()) for brick in
                        self._validated_params('bricks').split(',') if brick)

    def brick_ops(self):
        options = ' '
        if self.module.params['replica'] == 'yes':
            options += ' replica %s ' % self._validated_params('replica_count')
        new_bricks = self.get_brick_list()
        if self.action == 'remove-brick':
            return options + new_bricks + ' ' + self._validated_params('rebal_state')
        return options + new_bricks

    def gluster_volume_ops(self):
        option_str = ''
        if self.action in ['absent', 'remove-brick']:
            self.force = ''
        if self.action == 'replace-brick':
            self.force = 'commit force'
            option_str = self.get_brick_list()
        volume = self._validated_params('volume')
        if self.action == 'rebalance':
            option_str = self.rebalance_volume()
        if self.action == 'create':
            self.get_host_names()
            option_str = self.get_volume_configs()
            option_str += self.get_brick_list_of_all_hosts()
        if self.action in ['add-brick', 'remove-brick']:
            option_str = self.brick_ops()
        if self.action == 'profile':
            option_str = self._validated_params('profile_state')
        if self.action == 'set':
            option_str = self._validated_params('key') + " "
            option_str += self._validated_params('value')
        if self.action == 'barrier':
            option_str = self._validated_params('barrier_state')
        if self.action == 'bitrot':
            if self.module.params['scrub']:
                option_str = 'scrub ' + self._validated_params('scrub')
            elif self.module.params['scrub_throttle']:
                option_str = 'scrub-throttle '
                option_str += self._validated_params('scrub_throttle')
            elif self.module.params['scrub_frequency']:
                option_str = 'scrub-frequency '
                option_str += self._validated_params('scrub_frequency')
            elif self.module.params['bitrot_daemon']:
                option_str = self._validated_params('bitrot_daemon')

        rc, output, err = self.call_gluster_cmd('volume', self.action,
                                                volume, option_str, self.force)
        self._get_output(rc, output, err)

    def rebalance_volume(self):
        state = self._validated_params('rebal_state')
        if state not in ['start', 'stop', 'fix-layout']:
            self.module.fail_json(rc=20, msg="Invalid state for rebalance action. \n"
                                  "Available options are: start, stop, fix-layout.")
        if state != 'start':
            self.force = ''
        if state == 'fix-layout':
            return state + ' start '
        else:
            return state

    def create_params_dict(self, param_list):
        return OrderedDict((param, self.get_playbook_params(param))
                           for param in param_list)

    def call_gluster_cmd(self, *args, **kwargs):
        params = ' '.join(opt for opt in args)
        key_value_pair = ' '.join(' %s %s ' % (key, value)
                                  for key, value in kwargs)
        return self._run_command('gluster', ' ' + params + ' ' + key_value_pair)

    def _get_output(self, rc, output, err):
        changed = 0 if rc else 1
        if not rc:
            self.module.exit_json(rc=rc, stdout=output, changed=changed)
        else:
            self.module.fail_json(msg=err, rc=rc)

    def _run_command(self, op, opts):
        cmd = self.module.get_bin_path(op, True) + opts + ' --mode=script'
        return self.module.run_command(cmd)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True,
                       choices=["absent", "present", "remove-brick", "started",
                                "stopped", "replace-brick", "rebalance",
                                "add-brick", "profile", "set", "barrier",
                                "bitrot"]),
            hosts=dict(required=True),
            volname=dict(required=True),
            bricks=dict(),
            force=dict(),
            rebal_state=dict(),
            key=dict(),
            value=dict(),
            replica=dict(),
            replica_count=dict(),
            arbiter_count=dict(),
            transport=dict(),
            disperse=dict(),
            disperse_count=dict(),
            redundancy_count=dict(),
            profile_state=dict(),
            barrier_state=dict(),
            scrub=dict(),
            scrub_frequency=dict(),
            scrub_throttle=dict(),
            bitrot_daemon=dict(),
        ),
    )

    Glusterfs_Volume(module)

if __name__ == '__main__':
    main()
