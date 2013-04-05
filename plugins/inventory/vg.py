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

import os.path
import sys
import shlex

try:
    import lockfile
except ImportError:
    pass

try:
    import vagrant
except ImportError:
    print "python-vagrant required for this inventory"
    sys.exit(1)

try:
    import json
except:
    import simplejson as json

VAGRANT_LOCKFILE = './.vagrant-lock'

class VagrantWrapper(object):

    def __init__(self):
        '''
        Wrapper around the python-vagrant module for use with ansible.
        Note that Vagrant itself is non-thread safe, as is the python-vagrant lib, so we need to lock on basically all operations ...
        '''
        # Get a lock
        self.lock = None

        try:
            self.lock = lockfile.FileLock(VAGRANT_LOCKFILE)
            self.lock.acquire()
        except:
            # fall back to using flock instead ...
            try:
                import fcntl
                self.lock = open(VAGRANT_LOCKFILE, 'w')
                fcntl.flock(self.lock, fcntl.LOCK_EX)
            except:
                print "Could not get a lock for using vagrant. Install python module \"lockfile\" to use vagrant on non-POSIX filesytems."
                sys.exit(1)
            
        # Initialize vagrant and state files
        self.vg = vagrant.Vagrant()
        
    def __del__(self):
        '''Clean up file locks'''
        try:
            self.lock.release()
        except:
            self.lock.close()
            # Can someone tell me how to unlink that file ?? 
            # os.unlink(self.lock)

    def list(self):
        # Vagrant currently doesn't support grouping - we end up with a flat list. Yeah!
        result = dict(
            hosts = []
        )
        for host in self.vg.status():
            result['hosts'].append(host)
        return result

    def host(self, vm_name):
        # The only valuable info from vagrant are:
        #  - ip
        #  - ssh user
        #  - ssh port
        #  - ssh key -- damned how to use it ??
        result = dict(
            ansible_ssh_host = '',
            ansible_ssh_port = '',
            ansible_ssh_user = '',
            ansible_ssh_private_key = ''
        )
        config = self.vg.conf(None, vm_name)
        result['ansible_ssh_host'] = config['HostName']
        result['ansible_ssh_user'] = config['User']
        result['ansible_ssh_port'] = config['Port']
        result['ansible_ssh_private_key'] = config['IdentityFile']

        return result


# NOTE -- this file assumes Ansible is being accessed FROM the vagrant
# server, so it does not attempt to remote connect to any remote host

###################################################
# executed with no parameters, return the list of
# all groups and hosts

if len(sys.argv) == 2 and (sys.argv[1] == '--list'):

    vgw = VagrantWrapper()
    print vgw.list()

    sys.exit(0)

#####################################################
# executed with a hostname as a parameter, return the
# variables for that host

elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):

    vgw = VagrantWrapper()
    print vgw.host(sys.argv[2])

    sys.exit(0)

else:

    print "usage: --list  ..OR.. --host <hostname>"
    sys.exit(1)
