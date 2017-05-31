#!/usr/bin/env python

'''
Juju + Ansible = Awesome
========================
A simple Ansible plug-in for Juju environments. juju-ansible allows you to
easily run Ansible modules and playbooks on service units deployed with Juju.

Why?
----
Ansible is a simple yet powerful tool for distributing ad-hoc, low-level
system administration tasks to a large number of machines over ubiquitous
SSH. But you already knew that! :)

Juju can orchestrate complex service deployments with ease. Learn more at
https://juju.ubuntu.com.

With their powers combined, you can quickly deploy services with best
practices already set up for you -- and then easily customize and
administer them in production.

Prereqs
-------
Juju (https://juju.ubuntu.com/install) and of course Ansible must be
installed.

Installation
------------
There are two ways this plugin can be used:

Drive Juju with Ansible
~~~~~~~~~~~~~~~~~~~~~~~
This script can be used to drive Juju from Ansible as an inventory plugin
script.

Drive Ansible with Juju
~~~~~~~~~~~~~~~~~~~~~~~
Copy or symbolically-link this script to function as Juju plugins:

    $ ln -s /path/to/juju.py /path/to/bin/juju-ansible
    $ ln -s /path/to/juju.py /path/to/bin/juju-ansible-playbook

This will add juju subcommands 'ansible' and 'ansible-playbook', which
invoke ansible with itself as the inventory plugin.

Usage
-----
This plugin defines an inventory group for each service and OS distribution.

Example
-------
Let's say we have Wordpress and MySQL deployed with Juju:

    $ juju deploy mysql
    $ juju deploy wordpress
    $ juju add-relation mysql wordpress

Run modules and playbooks with Ansible:

    $ ansible mysql -i /path/to/juju.py -m ping

    $ ansible-playbook -i /path/to/juju.py sched_maint.yml -vvv

Or from Juju, if you set up the Juju plugin symbolic links:

    $ juju ansible -m ping

    $ juju ansible-playbook sched_maint.yml -vvv

Contact
-------
Casey Marshall <casey.marshall@canonical.com>.
I'm usually in #ansible and #juju on FreeNode.
'''

# Copyright (c) 2013, Canonical Ltd.
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

import json
import os
import re
import subprocess
import sys


def is_exe(fpath):
    """Test if fpath is an executable file."""
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def which(program):
    """Get the absolute path to the executable by name,
    if it exists in the $PATH."""
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


class JujuCmdError(Exception):
    """Juju command failure exception."""
    def __init__(self, message, stderr=None, rc=-1):
        self.stderr = stderr
        self.rc = rc
        Exception.__init__(self, message)


def juju_status():
    """Deserialize the current Juju status."""
    p = subprocess.Popen(["juju", "status", "--format", "json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode:
        raise JujuCmdError("Error executing 'juju status'. Please check your Juju environment and try again.",
            stderr=stderr, rc=p.returncode)
    return json.loads(stdout)


def to_inventory_object(status):
    """Restructure juju status into an Ansible dynamic inventory.
    Groups are currently created for each service and series."""
    result = {}

    # Create the 'all' group, and a group for each distribution series
    for machine_num, machine in status.get('machines', {}).iteritems():
        if not machine.get('dns-name'):
            continue
        result.setdefault('all', []).append(machine['dns-name'])
        if machine.get('series'):
            result.setdefault(machine['series'], []).append(machine['dns-name'])

    # Create groups for each service
    for service_name, service in status.get('services', {}).iteritems():
        for unit_name, unit in service.get('units', []).iteritems():
            if status.get('machines', {}).get(unit.get('machine'), {}).get('dns-name'):
                result.setdefault(service_name, []).append(
                        status['machines'][unit['machine']]['dns-name'])

    # Unique all the hosts, in case there are duplicates. Could happen,
    # if multiple units are targeted to a machine.
    for k in result.keys():
        result[k] = list(set(result[k]))

    return result


if __name__ == '__main__':
    try:
        # Check that juju is installed
        juju_cmd_path = which("juju")
        if not juju_cmd_path:
            raise Exception("""'juju' was not found in your path, check your Juju installation.
See https://juju.ubuntu.com/install/ for installation instructions.""")

        # For no arguments, or just --list, just output the inventory.
        # This allows juju-ansible to be used as a dynamic inventory plugin.
        if not sys.argv[1:] or sys.argv[1] == '--list':
            # Build an Ansible inventory file from Juju environment status
            status = juju_status()
            inv = to_inventory_object(status)
            sys.stdout.write(json.dumps(inv, indent=4))
            sys.stdout.flush()
            os._exit(0)
        if sys.argv[1] == '--host':
            # hostvars not supported yet, exit quickly to minimize the lookup cost
            sys.stdout.write(json.dumps({}))
            sys.stdout.flush()
            os._exit(0)

        # Derive ansible command, check that it is actually installed
        ansible_cmd = re.sub('juju-', '', os.path.basename(sys.argv[0]))
        ansible_cmd_path = which(ansible_cmd)
        if not ansible_cmd_path:
            raise Exception("""'%s' was not found in your path, check your Ansible installation.
See http://www.ansibleworks.com/docs/intro_installation.html for installation instructions.""" % (
                ansible_cmd))

        # Run ansible with command line arguments passed to this script,
        # passing ourselves as the dynamic inventory script.
        cmdline = [ansible_cmd, "-i", sys.argv[0]]
        cmdline.extend(sys.argv[1:])
        p = subprocess.Popen(cmdline)
        p.wait()
        os._exit(p.returncode)
    except Exception, e:
        print >>sys.stderr, "Error: %s" % (e.message)
        os._exit(1)
    except:
        print >>sys.stderr, "An unknown error occurred."
        os._exit(1)
