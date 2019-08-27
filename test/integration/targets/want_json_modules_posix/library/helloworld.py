#!/usr/bin/python
# This file is part of Ansible
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

# WANT_JSON

import json
import sys

try:
    with open(sys.argv[1], 'r') as f:
        data = json.load(f)
except (IOError, OSError, IndexError):
    print(json.dumps(dict(msg="No argument file provided", failed=True)))
    sys.exit(1)

salutation = data.get('salutation', 'Hello')
name = data.get('name', 'World')
print(json.dumps(dict(msg='%s, %s!' % (salutation, name))))
