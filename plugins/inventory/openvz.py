#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# openvz.py
#
# Copyright 2014 jordonr <jordon@beamsyn.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.
#
#
# Inspired by libvirt_lxc.py inventory script
# https://github.com/ansible/ansible/blob/e5ef0eca03cbb6c8950c06dc50d0ca22aa8902f4/plugins/inventory/libvirt_lxc.py
#
# Groups are determined by the description field of openvz guests
# multiple groups can be seperated by commas: webserver,dbserver

from subprocess import Popen,PIPE
import sys
import json


#List openvz hosts
vzhosts = ['192.168.1.3','192.168.1.2','192.168.1.1']
#Add openvzhosts to the inventory
inventory = {'vzhosts': {'hosts': vzhosts}}
#default group, when description not defined
default_group = ['vzguest']

def getGuests():
        #Loop through vzhosts
        for h in vzhosts:
                #SSH to vzhost and get the list of guests in json
                pipe = Popen(['ssh', h,'vzlist','-j'], stdout=PIPE, universal_newlines=True)

                #Load Json info of guests
                json_data = json.loads(pipe.stdout.read())

                #loop through guests
                for j in json_data:
                        #determine group from guest description
                        if j['description'] is not None:
                                groups = j['description'].split(",")
                        else:
                                groups = default_group

                        #add guest to inventory
                        for g in groups:
                                if g not in inventory:
                                        inventory[g] = {'hosts': []}

                                for ip in j['ip']:
                                        inventory[g]['hosts'].append(ip)

        print json.dumps(inventory)

if len(sys.argv) == 2 and sys.argv[1] == '--list':
        getGuests()
elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        print json.dumps({});
else:
        print "Need an argument, either --list or --host <host>"
