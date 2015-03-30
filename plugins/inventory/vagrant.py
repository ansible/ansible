#!/usr/bin/env python
"""
Vagrant external inventory script. Automatically finds the IP of the booted vagrant vm(s), and
returns it under the host group 'vagrant'

Example Vagrant configuration using this script:

    config.vm.provision :ansible do |ansible|
      ansible.playbook = "./provision/your_playbook.yml"
      ansible.inventory_file = "./provision/inventory/vagrant.py"
      ansible.verbose = true
    end
"""

# Copyright (C) 2013  Mark Mandel <mark@compoundtheory.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# Thanks to the spacewalk.py inventory script for giving me the basic structure
# of this.
#

import sys
import subprocess
import re
import string
from optparse import OptionParser
try:
    import json
except:
    import simplejson as json

# Options
#------------------------------

parser = OptionParser(usage="%prog [options] --list | --host <machine>")
parser.add_option('--list', default=False, dest="list", action="store_true",
                  help="Produce a JSON consumable grouping of Vagrant servers for Ansible")
parser.add_option('--host', default=None, dest="host",
                  help="Generate additional host specific details for given host for Ansible")
(options, args) = parser.parse_args()

#
# helper functions
#

# get all the ssh configs for all boxes in an array of dictionaries.
def get_ssh_config():
    configs = []

    boxes = list_running_boxes()

    for box in boxes:
        config = get_a_ssh_config(box)
        configs.append(config)

    return configs

#list all the running boxes
def list_running_boxes():
    output = subprocess.check_output(["vagrant", "status"]).split('\n')

    boxes = []

    for line in output:
        matcher = re.search("([^\s]+)[\s]+running \(.+", line)
        if matcher:
            boxes.append(matcher.group(1))


    return boxes

#get the ssh config for a single box
def get_a_ssh_config(box_name):
    """Gives back a map of all the machine's ssh configurations"""

    output = subprocess.check_output(["vagrant", "ssh-config", box_name]).split('\n')

    config = {}
    for line in output:
        if line.strip() != '':
            matcher = re.search("(  )?([a-zA-Z]+) (.*)", line)
            config[matcher.group(2)] = matcher.group(3)

    return config


# List out servers that vagrant has running
#------------------------------
if options.list:
    ssh_config = get_ssh_config()
    hosts = { 'vagrant': []}

    for data in ssh_config:
        hosts['vagrant'].append(data['HostName'])

    print json.dumps(hosts)
    sys.exit(0)

# Get out the host details
#------------------------------
elif options.host:
    result = {}
    ssh_config = get_ssh_config()

    details = filter(lambda x: (x['HostName'] == options.host), ssh_config)
    if len(details) > 0:
        #pass through the port, in case it's non standard.
        result = details[0]
        result['ansible_ssh_port'] = result['Port']

    print json.dumps(result)
    sys.exit(0)


# Print out help
#------------------------------
else:
    parser.print_help()
    sys.exit(0)
