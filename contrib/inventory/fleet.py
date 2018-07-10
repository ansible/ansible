#!/usr/bin/env python
"""
fleetctl base external inventory script. Automatically finds the IPs of the booted coreos instances and
returns it under the host group 'coreos'
"""

# Copyright (C) 2014  Andrew Rothstein <andrew.rothstein at gmail.com>
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
# Thanks to the vagrant.py inventory script for giving me the basic structure
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
# ------------------------------

parser = OptionParser(usage="%prog [options] --list | --host <machine>")
parser.add_option('--list', default=False, dest="list", action="store_true",
                  help="Produce a JSON consumable grouping of servers in your fleet")
parser.add_option('--host', default=None, dest="host",
                  help="Generate additional host specific details for given host for Ansible")
(options, args) = parser.parse_args()

#
# helper functions
#


def get_ssh_config():
    configs = []
    for box in list_running_boxes():
        config = get_a_ssh_config(box)
        configs.append(config)
    return configs


# list all the running instances in the fleet
def list_running_boxes():
    boxes = []
    for line in subprocess.check_output(["fleetctl", "list-machines"]).split('\n'):
        matcher = re.search(r"[^\s]+[\s]+([^\s]+).+", line)
        if matcher and matcher.group(1) != "IP":
            boxes.append(matcher.group(1))

    return boxes


def get_a_ssh_config(box_name):
    config = {}
    config['Host'] = box_name
    config['ansible_ssh_user'] = 'core'
    config['ansible_python_interpreter'] = '/opt/bin/python'
    return config


# List out servers that vagrant has running
# ------------------------------
if options.list:
    ssh_config = get_ssh_config()
    hosts = {'coreos': []}

    for data in ssh_config:
        hosts['coreos'].append(data['Host'])

    print(json.dumps(hosts))
    sys.exit(1)

# Get out the host details
# ------------------------------
elif options.host:
    result = {}
    ssh_config = get_ssh_config()

    details = filter(lambda x: (x['Host'] == options.host), ssh_config)
    if len(details) > 0:
        # pass through the port, in case it's non standard.
        result = details[0]

    print(json.dumps(result))
    sys.exit(1)


# Print out help
# ------------------------------
else:
    parser.print_help()
    sys.exit(1)
