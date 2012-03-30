#!/usr/bin/python

"""
Cobbler external inventory script
=================================

Ansible has a feature where instead of reading from /etc/ansible/hosts
as a text file, it can query external programs to obtain the list
of hosts, groups the hosts are in, and even variables to assign to each host.  

To use this, copy this file over /etc/ansible/hosts and chmod +x the file.
This, more or less, allows you to keep one central database containing
info about all of your managed instances.

This script is an example of sourcing that data from Cobbler
(http://cobbler.github.com).  With cobbler each --mgmt-class in cobbler 
will correspond to a group in Ansible, and --ks-meta variables will be 
passed down for use in templates or even in argument lines.

NOTE: The cobbler system names will not be used.  Make sure a
cobbler --dns-name is set for each cobbler system.   If a system
appears with two DNS names we do not add it twice because we don't want
ansible talking to it twice.  The first one found will be used. If no
--dns-name is set the system will NOT be visible to ansible.  We do
not add cobbler system names because there is no requirement in cobbler
that those correspond to addresses.  

See http://ansible.github.com/api.html for more info

Tested with Cobbler 2.0.11. 
"""

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible,
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

######################################################################


import sys
import xmlrpclib
import shlex

try:
    import json
except:
    import simplejson as json

# NOTE -- this file assumes Ansible is being accessed FROM the cobbler
# server, so it does not attempt to login with a username and password.
# this will be addressed in a future version of this script.

conn = xmlrpclib.Server("http://127.0.0.1/cobbler_api", allow_none=True)

###################################################
# executed with no parameters, return the list of
# all groups and hosts

if len(sys.argv) == 1:

    systems = conn.get_item_names('system')
    groups = { 'ungrouped' : [] }

    for system in systems:

        data = conn.get_blended_data(None, system)

        dns_name = None
        interfaces = data['interfaces']
        for (iname, ivalue) in interfaces.iteritems():
            this_dns_name = ivalue.get('dns_name', None)
            if this_dns_name is not None:
                dns_name = this_dns_name       
 
        if dns_name is None:
            continue

        classes  = data['mgmt_classes']
        for cls in classes:
            if cls not in groups:
                groups[cls] = []
            # hostname is not really what we want to insert, really insert the
            # first DNS name but no further DNS names
            groups[cls].append(dns_name)
 
    print json.dumps(groups)
    sys.exit(0)

#####################################################
# executed with a hostname as a parameter, return the
# variables for that host

if len(sys.argv) == 2:

    # look up the system record for the given DNS name
    result = conn.find_system_by_dns_name(sys.argv[1])
    system = result.get('name', None)
    data = {}
    if system is None:
        print json.dumps({})
        sys.exit(1)
    data = conn.get_system_for_koan(system)

    # return the ksmeta data for that system
    metadata = data['ks_meta']
    tokens = shlex.split(metadata)
    results = {}
    for t in tokens:
        if t.find("=") != -1:
           (k,v) = t.split("=",1)
           results[k]=v
    print json.dumps(results)
    sys.exit(0)

