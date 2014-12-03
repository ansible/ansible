#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Taneli Leppä <taneli@crasman.fi>
#
# This file is part of Ansible (sort of)
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


DOCUMENTATION = """
module: glusterfs
short_description: manage GlusterFS
description:
  - Manage GlusterFS volumes
version_added: "1.9"
options:
  action:
    required: true
    choices: [ 'create', 'start', 'stop', 'tune', 'rebalance', 'limit-usage' ]
    description:
      - Indicates the action to take. Create volume, start/stop volume, set tuning options, rebalance or set quota
  name:
    required: true
    description:
      - The volume name
  hosts:
    required: false
    description:
      - List of hosts to use for probing and brick setup
  host:
    required: false
    description:
      - Override local hostname (for peer probing purposes)
  glusterbin:
    required: false
    default: /usr/sbin/gluster
    description:
      - Override gluster cli path
  replica:
    required: false
    description:
      - Replica count for volume
  stripe:
    required: false
    description:
      - Stripe count for volume
  transport:
    required: false
    choices: [ 'tcp', 'rdma', 'tcp,rdma' ]
    description:
      - Transport type for volume
  brick:
    required: false
    description:
      - Brick path on servers
  start:
    required: false
    description:
      - Controls whether the volume is started after creation or not
  rebalance:
    required: false
    description:
      - Controls whether the volume is rebalanced after adding bricks or not
  option:
    required: false
    description:
      - Tuning parameter name when action=tune
  parameter:
    required: false
    description:
      - Tuning parameter value when action=tune
  directory:
    required: false
    description:
      - Directory for limit-usage
  value:
    required: false
    description:
      - Quota value for limit-usage (be sure to use 10.0MB instead of 10MB, see quota list)
notes:
  - "Requires cli tools for GlusterFS on servers"
  - "Will add new bricks, but not remove them"
author: Taneli Leppä
"""

EXAMPLES = """
- name: create gluster volume
  glusterfs: action=create name=test1 brick=/bricks/brick1/g1 rebalance=yes
  args:
    hosts: "{{ play_hosts }}"
  run_once: true

- name: tune
  glusterfs: action=tune name=test1 option=performance.cache-size parameter=256MB
  run_once: true

- name: start gluster volume
  glusterfs: action=start name=test1
  run_once: true

- name: limit usage
  glusterfs: action=limit-usage name=test1 directory=/foo value=20.0MB
  run_once: true

- name: stop gluster volume
  glusterfs: action=stop name=test1
  run_once: true
"""

import os
import shutil
import time
import socket
import re

def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, default=None, choices=[ 'create', 'start', 'stop', 'tune', 'rebalance', 'limit-usage' ]),
            name=dict(required=True, default=None, aliases=['volume']),
            hosts=dict(required=False, default=None, type='list'),
            host=dict(required=False, default=None),
            stripe=dict(required=False, default=None, type='int'),
            replica=dict(required=False, default=None, type='int'),
            transport=dict(required=False, default='tcp', choices=[ 'tcp', 'rdma', 'tcp,rdma' ]),
            brick=dict(required=False, default=None),
            start=dict(required=False, default='1'),
            rebalance=dict(required=False, default='0'),
            option=dict(required=False, default=None),
            parameter=dict(required=False, default=None),
            value=dict(required=False, default=None),
            directory=dict(required=False, default=None),
            glusterbin=dict(required=False, default='/usr/sbin/gluster'),
            )
        )

    changed = False
    action = module.params['action']
    volume_name = module.params['name']
    glusterbin = module.params['glusterbin']
    hosts = module.params['hosts']
    brick_path = module.params['brick']
    stripe = module.params['stripe']
    replica = module.params['replica']
    transport = module.params['transport']
    myhostname = module.params['host']
    start_volume = module.boolean(module.params['start'])
    rebalance = module.boolean(module.params['rebalance'])
    if not myhostname:
        myhostname = socket.gethostname()
    if not os.path.exists(glusterbin):
        module.fail_json(msg='could not find gluster commandline client at %s' % glusterbin)
        
    set_option = module.params['option']
    set_parameter = module.params['parameter']
    value = module.params['value']
    directory = module.params['directory']

    def run_gluster(gargs, **kwargs):
        args = [glusterbin]
        args.extend(gargs)
        rc, out, err = module.run_command(args, **kwargs)
        if rc != 0:
            module.fail_json(msg='error running gluster (%s) command (rc=%d): %s' % (' '.join(args), rc, out if out != '' else err))
        return out

    def run_gluster_nofail(gargs, **kwargs):
        args = [glusterbin]
        args.extend(gargs)
        rc, out, err = module.run_command(args, **kwargs)
        if rc != 0:
            return None
        return out

    def run_gluster_yes(gargs):
        args = [glusterbin]
        args.extend(gargs)
        rc, out, err = module.run_command(args, data='y\n')
        if rc != 0:
            module.fail_json(msg='error running gluster (%s) command (rc=%d): %s' % (' '.join(args), rc, out if out != '' else err))
        return out

    def get_peers():
        out = run_gluster([ 'peer', 'status'])
        i = 0
        peers = {}
        hostname = None
        uuid = None
        state = None
        for row in out.split('\n'):
            if ': ' in row:
                key, value = row.split(': ')
                if key.lower() == 'hostname':
                    hostname = value
                if key.lower() == 'uuid':
                    uuid = value
                if key.lower() == 'state':
                    state = value
                    peers[hostname] = [ uuid, state ]
        return peers

    def get_volumes():
        out = run_gluster([ 'volume', 'info' ])

        volumes = {}
        volume = {}
        for row in out.split('\n'):
            if ': ' in row:
                key, value = row.split(': ')
                if key.lower() == 'volume name':
                    volume['name'] = value
                    volume['options'] = {}
                    volume['quota'] = False
                if key.lower() == 'volume id':
                    volume['id'] = value
                if key.lower() == 'status':
                    volume['status'] = value
                if key.lower() == 'transport-type':
                    volume['transport'] = value
                if key.lower() != 'bricks' and key.lower()[:5] == 'brick':
                    if not 'bricks' in volume:
                        volume['bricks'] = []
                    volume['bricks'].append(value)
                # Volume options
                if '.' in key:
                    if not 'options' in volume:
                        volume['options'] = {}
                    volume['options'][key] = value
                    if key == 'features.quota' and value == 'on':
                        volume['quota'] = True
            else:
                if row.lower() != 'bricks:' and row.lower() != 'options reconfigured:':
                    if len(volume) > 0:
                        volumes[volume['name']] = volume
                    volume = {}
        return volumes

    def get_quotas(name, nofail):
        quotas = {}
        if nofail:
            out = run_gluster_nofail([ 'volume', 'quota', name, 'list' ])
            if not out:
                return quotas
        else:
            out = run_gluster([ 'volume', 'quota', name, 'list' ])
        for row in out.split('\n'):
            if row[:1] == '/':
                q = re.split('\s+', row)
                quotas[q[0]] = q[1]
        return quotas        

    def wait_for_peer(host):
        for x in range(0, 4):
            peers = get_peers()
            if host in peers and peers[host][1].lower().find('peer in cluster') != -1:
                return True
            time.sleep(1)
        return False

    def probe(host):
        run_gluster([ 'peer', 'probe', host ])
        if not wait_for_peer(host):
            module.fail_json(msg='failed to probe peer %s' % host)
        changed = True

    def probe_all_peers(hosts, peers):
        for host in hosts:
            if host not in peers:
                # dont probe ourselves
                if myhostname != host: 
                    probe(host)

    def create_volume(name, stripe, replica, transport, hosts, brick):
        args = [ 'volume', 'create' ]
        args.append(name)
        if stripe:
            args.append('stripe')
            args.append(str(stripe))
        if replica:
            args.append('replica')
            args.append(str(replica))
        args.append('transport')
        args.append(transport)
        for host in hosts:
            args.append(('%s:%s' % (host, brick)))
        run_gluster(args)

    def start_volume(name):
        run_gluster([ 'volume', 'start', name ])
        
    def stop_volume(name):
        run_gluster_yes([ 'volume', 'stop', name ])

    def set_volume_option(name, option, parameter):
        run_gluster([ 'volume', 'set', name, option, parameter ])

    def add_brick(name, brick):
        run_gluster([ 'volume', 'add-brick', name, brick ])

    def rebalance(name):
        run_gluster(['volume', 'rebalance', name, 'start'])

    def enable_quota(name):
        run_gluster([ 'volume', 'quota', name, 'enable' ])
        
    def set_quota(name, directory, value):
        run_gluster([ 'volume', 'quota', name, 'limit-usage', directory, value ])

    #
    peers = get_peers()
    volumes = get_volumes()
    quotas = {}
    if volume_name in volumes and volumes[volume_name]['quota'] and volumes[volume_name]['status'].lower() == 'started':
        quotas = get_quotas(volume_name, True)
    if action == 'create':
        probe_all_peers(hosts, peers)
        if volume_name not in volumes:
            create_volume(volume_name, stripe, replica, transport, hosts, brick_path)
            changed = True
            volumes = get_volumes()
        if volume_name in volumes:
            if volumes[volume_name]['status'].lower() != 'started' and start_volume:
                start_volume(volume_name)
                changed = True

            # switch bricks
            new_bricks = []
            removed_bricks = []
            all_bricks = []
            for host in hosts:
                brick = '%s:%s' % (host, brick_path)
                all_bricks.append(brick)
                if brick not in volumes[volume_name]['bricks']:
                    new_bricks.append(brick)

            # this module does not yet remove bricks, but we check those anyways
            for brick in volumes[volume_name]['bricks']:
                if brick not in all_bricks:
                    removed_bricks.append(brick)
               
            for brick in new_bricks:
                add_brick(volume_name, brick)
                changed = True

            if len(new_bricks) > 0 and rebalance:
                rebalance(volume_name)
                    
        else:
            module.fail_json(msg='failed to create volume %s' % volume_name)
    if action == 'start':
        if volume_name not in volumes:
            module.fail_json(msg='volume not found %s' % volume_name)
        if volumes[volume_name]['status'].lower() != 'started':
            start_volume(volume_name)
            volumes = get_volumes()
            changed = True
    if action == 'rebalance':
        if volume_name not in volumes:
            module.fail_json(msg='volume not found %s' % volume_name)
        rebalance(volume_name)
        changed = True
    if action == 'stop':
        if volume_name not in volumes:
            module.fail_json(msg='volume not found %s' % volume_name)
        if volumes[volume_name]['status'].lower() != 'stopped':
            stop_volume(volume_name)
            volumes = get_volumes()
            changed = True
    if action == 'tune':
        if volume_name not in volumes:
            module.fail_json(msg='volume not found %s' % volume_name)
        if set_option not in volumes[volume_name]['options'] or volumes[volume_name]['options'][set_option] != set_parameter:
            set_volume_option(volume_name, set_option, set_parameter)
            volumes = get_volumes()
            changed = True
    if action == 'limit-usage':
        if volume_name not in volumes:
            module.fail_json(msg='volume not found %s' % volume_name)
        if not volumes[volume_name]['quota']:
            enable_quota(volume_name)

        quotas = get_quotas(volume_name, False)
        if directory not in quotas:
            set_quota(volume_name, directory, value)
            changed = True
        elif quotas[directory] != value:
            set_quota(volume_name, directory, value)
            changed = True
    facts = {}
    facts['glusterfs'] = { 'peers': peers, 'volumes': volumes, 'quotas': quotas }

    module.exit_json(changed=changed, ansible_facts=facts)

# import module snippets
from ansible.module_utils.basic import *
main()
