#!/usr/bin/env python

# (c) 2015, Dagobert Michelsen <dam@baltic-online.de>
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

pipe = Popen(['zoneadm', 'list', '-ip'], stdout=PIPE, universal_newlines=True)
result['all']['hosts'] = []
for l in pipe.stdout.readlines():
    # 1:work:running:/zones/work:3126dc59-9a07-4829-cde9-a816e4c5040e:native:shared
    s = l.split(':')
    if s[1] != 'global':
        result['all']['hosts'].append(s[1])

result['all']['vars'] = {}
result['all']['vars']['ansible_connection'] = 'zone'

if len(sys.argv) == 2 and sys.argv[1] == '--list':
    print(json.dumps(result))
elif len(sys.argv) == 3 and sys.argv[1] == '--host':
    print(json.dumps({'ansible_connection': 'zone'}))
else:
    sys.stderr.write("Need an argument, either --list or --host <host>\n")
