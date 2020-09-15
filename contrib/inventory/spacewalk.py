#!/usr/bin/env python

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

Tested with Ansible 1.9.2 and spacewalk 2.3
"""
#
# Author:: Jon Miller <jonEbird@gmail.com>
# Copyright:: Copyright (c) 2013, Jon Miller
#
# Extended for support of multiple organizations and
# adding the "_meta" dictionary to --list output by
# Bernhard Lichtinger <bernhard.lichtinger@lrz.de> 2015
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

from __future__ import print_function

import sys
import os
import time
from optparse import OptionParser
import subprocess
import json

from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import configparser as ConfigParser


base_dir = os.path.dirname(os.path.realpath(__file__))
default_ini_file = os.path.join(base_dir, "spacewalk.ini")

SW_REPORT = '/usr/bin/spacewalk-report'
CACHE_DIR = os.path.join(base_dir, ".spacewalk_reports")
CACHE_AGE = 300  # 5min
INI_FILE = os.path.expanduser(os.path.expandvars(os.environ.get("SPACEWALK_INI_PATH", default_ini_file)))


# Sanity check
if not os.path.exists(SW_REPORT):
    print('Error: %s is required for operation.' % (SW_REPORT), file=sys.stderr)
    sys.exit(1)

# Pre-startup work
if not os.path.exists(CACHE_DIR):
    os.mkdir(CACHE_DIR)
    os.chmod(CACHE_DIR, 0o2775)

# Helper functions
# ------------------------------


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
    # add 'spacewalk_' prefix to the keys
    keys = ['spacewalk_' + key for key in keys]
    for line in lines[1:]:
        values = line.strip().split(',')
        if len(keys) == len(values):
            yield dict(zip(keys, values))


# Options
# ------------------------------

parser = OptionParser(usage="%prog [options] --list | --host <machine>")
parser.add_option('--list', default=False, dest="list", action="store_true",
                  help="Produce a JSON consumable grouping of servers for Ansible")
parser.add_option('--host', default=None, dest="host",
                  help="Generate additional host specific details for given host for Ansible")
parser.add_option('-H', '--human', dest="human",
                  default=False, action="store_true",
                  help="Produce a friendlier version of either server list or host detail")
parser.add_option('-o', '--org', default=None, dest="org_number",
                  help="Limit to spacewalk organization number")
parser.add_option('-p', default=False, dest="prefix_org_name", action="store_true",
                  help="Prefix the group name with the organization number")
(options, args) = parser.parse_args()


# read spacewalk.ini if present
# ------------------------------
if os.path.exists(INI_FILE):
    config = ConfigParser.SafeConfigParser()
    config.read(INI_FILE)
    if config.has_option('spacewalk', 'cache_age'):
        CACHE_AGE = config.get('spacewalk', 'cache_age')
    if not options.org_number and config.has_option('spacewalk', 'org_number'):
        options.org_number = config.get('spacewalk', 'org_number')
    if not options.prefix_org_name and config.has_option('spacewalk', 'prefix_org_name'):
        options.prefix_org_name = config.getboolean('spacewalk', 'prefix_org_name')


# Generate dictionary for mapping group_id to org_id
# ------------------------------
org_groups = {}
try:
    for group in spacewalk_report('system-groups'):
        org_groups[group['spacewalk_group_id']] = group['spacewalk_org_id']

except (OSError) as e:
    print('Problem executing the command "%s system-groups": %s' %
          (SW_REPORT, str(e)), file=sys.stderr)
    sys.exit(2)


# List out the known server from Spacewalk
# ------------------------------
if options.list:

    # to build the "_meta"-Group with hostvars first create dictionary for later use
    host_vars = {}
    try:
        for item in spacewalk_report('inventory'):
            host_vars[item['spacewalk_profile_name']] = dict((key, (value.split(';') if ';' in value else value)) for key, value in item.items())

    except (OSError) as e:
        print('Problem executing the command "%s inventory": %s' %
              (SW_REPORT, str(e)), file=sys.stderr)
        sys.exit(2)

    groups = {}
    meta = {"hostvars": {}}
    try:
        for system in spacewalk_report('system-groups-systems'):
            # first get org_id of system
            org_id = org_groups[system['spacewalk_group_id']]

            # shall we add the org_id as prefix to the group name:
            if options.prefix_org_name:
                prefix = org_id + "-"
                group_name = prefix + system['spacewalk_group_name']
            else:
                group_name = system['spacewalk_group_name']

            # if we are limited to one organization:
            if options.org_number:
                if org_id == options.org_number:
                    if group_name not in groups:
                        groups[group_name] = set()

                    groups[group_name].add(system['spacewalk_server_name'])
                    if system['spacewalk_server_name'] in host_vars and not system['spacewalk_server_name'] in meta["hostvars"]:
                        meta["hostvars"][system['spacewalk_server_name']] = host_vars[system['spacewalk_server_name']]
            # or we list all groups and systems:
            else:
                if group_name not in groups:
                    groups[group_name] = set()

                groups[group_name].add(system['spacewalk_server_name'])
                if system['spacewalk_server_name'] in host_vars and not system['spacewalk_server_name'] in meta["hostvars"]:
                    meta["hostvars"][system['spacewalk_server_name']] = host_vars[system['spacewalk_server_name']]

    except (OSError) as e:
        print('Problem executing the command "%s system-groups-systems": %s' %
              (SW_REPORT, str(e)), file=sys.stderr)
        sys.exit(2)

    if options.human:
        for group, systems in iteritems(groups):
            print('[%s]\n%s\n' % (group, '\n'.join(systems)))
    else:
        final = dict([(k, list(s)) for k, s in iteritems(groups)])
        final["_meta"] = meta
        print(json.dumps(final))
        # print(json.dumps(groups))
    sys.exit(0)


# Return a details information concerning the spacewalk server
# ------------------------------
elif options.host:

    host_details = {}
    try:
        for system in spacewalk_report('inventory'):
            if system['spacewalk_hostname'] == options.host:
                host_details = system
                break

    except (OSError) as e:
        print('Problem executing the command "%s inventory": %s' %
              (SW_REPORT, str(e)), file=sys.stderr)
        sys.exit(2)

    if options.human:
        print('Host: %s' % options.host)
        for k, v in iteritems(host_details):
            print('  %s: %s' % (k, '\n    '.join(v.split(';'))))
    else:
        print(json.dumps(dict((key, (value.split(';') if ';' in value else value)) for key, value in host_details.items())))
    sys.exit(0)

else:

    parser.print_help()
    sys.exit(1)
