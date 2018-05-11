#!/usr/bin/env python

# (c) 2013, Michael Scherer <misc@zarb.org>
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

from subprocess import Popen, PIPE
import sys
import json

result = {}
result['all'] = {}

pipe = Popen(['virsh', '-q', '-c', 'lxc:///', 'list', '--name', '--all'], stdout=PIPE, universal_newlines=True)
result['all']['hosts'] = [x[:-1] for x in pipe.stdout.readlines()]
result['all']['vars'] = {}
result['all']['vars']['ansible_connection'] = 'libvirt_lxc'

if len(sys.argv) == 2 and sys.argv[1] == '--list':
    print(json.dumps(result))
elif len(sys.argv) == 3 and sys.argv[1] == '--host':
    print(json.dumps({'ansible_connection': 'libvirt_lxc'}))
else:
    sys.stderr.write("Need an argument, either --list or --host <host>\n")
