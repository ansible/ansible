#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
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

DOCUMENTATION = '''
---
module: slurp
version_added: historical
short_description: Slurps a file from remote nodes
description:
     - This module works like M(fetch). It is used for fetching a base64-
       encoded blob containing the data in a remote file.
options:
  src:
    description:
      - The file on the remote system to fetch. This I(must) be a file, not a
        directory.
    required: true
    default: null
    aliases: []
notes:
   - "See also: M(fetch)"
requirements: []
author: Michael DeHaan
'''

EXAMPLES = '''
ansible host -m slurp -a 'src=/tmp/xx'
   host | success >> {
      "content": "aGVsbG8gQW5zaWJsZSB3b3JsZAo=", 
      "encoding": "base64"
   }
'''

import base64

def main():
    module = AnsibleModule(
        argument_spec = dict(
            src = dict(required=True, aliases=['path']),
        ),
        supports_check_mode=True
    )
    source = os.path.expanduser(module.params['src'])

    if not os.path.exists(source):
        module.fail_json(msg="file not found: %s" % source)
    if not os.access(source, os.R_OK):
        module.fail_json(msg="file is not readable: %s" % source)

    data = base64.b64encode(file(source).read())

    module.exit_json(content=data, source=source, encoding='base64')

# import module snippets
from ansible.module_utils.basic import *

main()

