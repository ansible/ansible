#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# openvz.py
#
# Copyright 2014 jordonr <jordon@beamsyn.net>
#
# This file is part of Ansible.
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
# Inspired by libvirt_lxc.py inventory script
# https://github.com/ansible/ansible/blob/e5ef0eca03cbb6c8950c06dc50d0ca22aa8902f4/plugins/inventory/libvirt_lxc.py
#
# Groups are determined by the description field of openvz guests
# multiple groups can be separated by commas: webserver,dbserver

from subprocess import Popen, PIPE
import sys
import json


# List openvz hosts
vzhosts = ['vzhost1', 'vzhost2', 'vzhost3']
# Add openvz hosts to the inventory and Add "_meta" trick
inventory = {'vzhosts': {'hosts': vzhosts}, '_meta': {'hostvars': {}}}
# default group, when description not defined
default_group = ['vzguest']


def get_guests():
    # Loop through vzhosts
    for h in vzhosts:
        # SSH to vzhost and get the list of guests in json
        pipe = Popen(['ssh', h, 'vzlist', '-j'], stdout=PIPE, universal_newlines=True)

        # Load Json info of guests
        json_data = json.loads(pipe.stdout.read())

        # loop through guests
        for j in json_data:
            # Add information to host vars
            inventory['_meta']['hostvars'][j['hostname']] = {
                'ctid': j['ctid'],
                'veid': j['veid'],
                'vpsid': j['vpsid'],
                'private_path': j['private'],
                'root_path': j['root'],
                'ip': j['ip']
            }

            # determine group from guest description
            if j['description'] is not None:
                groups = j['description'].split(",")
            else:
                groups = default_group

            # add guest to inventory
            for g in groups:
                if g not in inventory:
                    inventory[g] = {'hosts': []}

                inventory[g]['hosts'].append(j['hostname'])

        return inventory


if len(sys.argv) == 2 and sys.argv[1] == '--list':
    inv_json = get_guests()
    print(json.dumps(inv_json, sort_keys=True))
elif len(sys.argv) == 3 and sys.argv[1] == '--host':
    print(json.dumps({}))
else:
    print("Need an argument, either --list or --host <host>")
