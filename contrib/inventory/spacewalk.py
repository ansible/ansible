#!/bin/env python

"""
Spacewalk external inventory script
=================================

Ansible has a feature where instead of reading from /etc/ansible/hosts
as a text file, it can query external programs to obtain the list
of hosts, groups the hosts are in, and even variables to assign to each host.

To use this, copy this file over /etc/ansible/hosts and chmod +x the file.
This, more or less, allows you to keep one central database containing
info about all of your managed instances.

This script is dependent upon the spacealk-reports package being installed
on the same machine. It is basically a CSV-to-JSON converter from the
output of "spacewalk-report system-groups-systems|inventory".

Tested with Ansible 1.1
"""
# 
# Author:: Jon Miller <jonEbird@gmail.com>
# Copyright:: Copyright (c) 2013, Jon Miller
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

import sys
import os
import time
from optparse import OptionParser
import subprocess

try:
    import json
except:
    import simplejson as json

base_dir  = os.path.dirname(os.path.realpath(__file__))
SW_REPORT = '/usr/bin/spacewalk-report'
CACHE_DIR = os.path.join(base_dir, ".spacewalk_reports")
CACHE_AGE = 300 # 5min

# Sanity check
if not os.path.exists(SW_REPORT):
    print >> sys.stderr, 'Error: %s is required for operation.' % (SW_REPORT)
    sys.exit(1)

# Pre-startup work
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
    os.chmod(CACHE_DIR, 2775)

# Helper functions
#------------------------------

def spacewalk_report(name):
    """Yield a dictionary form of each CSV output produced by the specified
    spacewalk-report
    """
    cache_filename = os.path.join(CACHE_DIR, name)
    if not os.path.exists(cache_filename) or \
            (time.time() - os.stat(cache_filename).st_mtime) > CACHE_AGE:
        # Update the cache
        fh = open(cache_filename, 'w')
        p = subprocess.Popen([SW_REPORT, name], stdout=fh)
        p.wait()
        fh.close()

    lines = open(cache_filename, 'r').readlines()
    keys = lines[0].strip().split(',')
    for line in lines[1:]:
        values = line.strip().split(',')
        if len(keys) == len(values):
            yield dict(zip(keys, values))


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


# List out the known server from Spacewalk
#------------------------------
if options.list:

    groups = {}
    try:
        for system in spacewalk_report('system-groups-systems'):
            if system['group_name'] not in groups:
                groups[system['group_name']] = set()

            groups[system['group_name']].add(system['server_name'])

    except (OSError), e:
        print >> sys.stderr, 'Problem executing the command "%s system-groups-systems": %s' % \
            (SW_REPORT, str(e))
        sys.exit(2)

    if options.human:
        for group, systems in groups.iteritems():
            print '[%s]\n%s\n' % (group, '\n'.join(systems))
    else:
        print json.dumps(dict([ (k, list(s)) for k, s in groups.iteritems() ]))

    sys.exit(0)


# Return a details information concerning the spacewalk server
#------------------------------
elif options.host:

    host_details = {}
    try:
        for system in spacewalk_report('inventory'):
            if system['hostname'] == options.host:
                host_details = system
                break

    except (OSError), e:
        print >> sys.stderr, 'Problem executing the command "%s inventory": %s' % \
            (SW_REPORT, str(e))
        sys.exit(2)
    
    if options.human:
        print 'Host: %s' % options.host
        for k, v in host_details.iteritems():
            print '  %s: %s' % (k, '\n    '.join(v.split(';')))
    else:
        print json.dumps(host_details)

    sys.exit(0)

else:

    parser.print_help()
    sys.exit(1)
