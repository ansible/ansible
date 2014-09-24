#!/usr/bin/env python

"""
External inventory script for Chef
===================================

Ansible has a feature where instead of reading from /etc/ansible/hosts
as a text file, it can query external programs to obtain the list
of hosts, groups the hosts are in, and even variables to assign to each host.

To use this, copy this file over /etc/ansible/hosts and chmod +x the file.
This, more or less, allows you to keep one central database containing
info about all of your managed instances.

This script converts the Chef node information and makes it available to
Ansible.
"""
#
# Author:: Michael Stucki <michael@stucki.io>
# Copyright:: Copyright (c) 2014, Michael Stucki
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# Thanks to the spacewalk.py and vagrant.py inventory scripts for giving
# me the basic structure of this.
#

import sys
import os
import time
from optparse import OptionParser
from subprocess import Popen,PIPE

try:
    import json
except:
    import simplejson as json


# Helper functions
#------------------------------

def knife_report(key):
    """Return information from the "knife" utility"""
    try:
        pipe = Popen(['knife', key, 'list'], stdout=PIPE, universal_newlines=True)
        pipe.wait()

    except (OSError), e:
        print >> sys.stderr, 'Problem executing the command "%s": %s' % ("knife " + key + " list", str(e))
        sys.exit(2)

    result = {}

    for line in pipe.stdout.readlines():
        host = line[:-1]
        hostvars = {}

        #if host == "somehost":
        #    hostvars['ansible_ssh_port'] = 2222

        result[host] = hostvars

    return result


# Options
#------------------------------

parser = OptionParser(usage="%prog [options] --list | --host <machine>")
parser.add_option('--list', default=False, dest="list", action="store_true",
                  help="Produce a JSON consumable grouping of servers for Ansible")
parser.add_option('--host', default=None, dest="host",
                  help="Generate additional host specific details for given host for Ansible")
parser.add_option('-H', '--human', dest="human",
                  default=False, action="store_true",
                  help="Produce a friendlier version of either server list or host detail")
(options, args) = parser.parse_args()


# List known servers from knife
#------------------------------
if options.list:
    inventory = {}
    inventory['chef_hosts'] = []
    inventory['_meta'] = {}
    inventory['_meta']['hostvars'] = {}

    for host, hostvars in knife_report('node').items():
        inventory['chef_hosts'].append(host)
        inventory['_meta']['hostvars'][host] = hostvars

    if options.human:
        print "[chef_hosts]"
        for host in inventory['chef_hosts']:
            print host

        print
        print "[_meta][hostvars]"

        for host, hostvars in inventory['_meta']['hostvars'].iteritems():
            if hostvars:
                attributes = []
                for key, value in hostvars.iteritems():
                    attributes.append(key + "=" + str(value))
                print '%s\t%s' % (host, ','.join(attributes))
    else:
        print json.dumps(inventory)

    sys.exit(0)


# Return details for a host
#------------------------------
elif options.host:

    host_details = {}
    for host, hostvars in knife_report('node').items():
        if host == options.host:
            host_details = hostvars
            break

    if options.human:
        attributes = []
        for key, value in hostvars.iteritems():
            attributes.append(key + "=" + str(value))
        print 'Host: %s\n  %s' % (host, '\n  '.join(attributes))

    else:
        print json.dumps(host_details)

    sys.exit(0)

else:

    parser.print_help()
    sys.exit(1)
