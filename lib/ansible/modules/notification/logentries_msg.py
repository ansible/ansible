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

from ansible.module_utils.pycompat24 import get_exception

DOCUMENTATION = '''
---
module: logentries_msg
version_added: "2.2"
short_description: Send a message to logentries.
description:
   - Send a message to logentries
requirements:
  - "python >= 2.6"
options:
  token:
    description:
      - Log token.
    required: true
    version_added: "2.1"
  msg:
    description:
      - The message body.
    required: true
    default: null
    version_added: "2.1"
  api:
    description:
      - API endpoint
    required: false
    default: data.logentries.com
    version_added: "2.1"
  port:
    description:
      - API endpoint port
    required: false
    default: 80
    version_added: "2.1"
author: "Jimmy Tang <jimmy_tang@rapid7.com>"
'''

# TODO: Disabled the RETURN as it was breaking docs building. Someone needs to
# fix this
RETURN = '''# '''

EXAMPLES = '''
- logentries_msg:
    token=00000000-0000-0000-0000-000000000000
    msg="{{ ansible_hostname }}"
'''


def send_msg(module, token, msg, api, port):
    import socket

    message = "{} {}\n".format(token, msg)

    api_ip = socket.gethostbyname(api)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((api_ip, port))
    try:
        s.send(message)
    except:
        module.fail_json(msg="failed to send message, msg=%s" % str(message))
    s.close()

def main():
    module = AnsibleModule(
            argument_spec=dict(
                token=dict(required=True),
                msg=dict(required=True),
                api=dict(default="data.logentries.com"),
                port=dict(default=80)
                ),
            supports_check_mode=False
            )

    token = module.params["token"]
    msg = module.params["msg"]
    api = module.params["api"]
    port = module.params["port"]

    try:
        send_msg(module, token, msg, api, port)
    except Exception:
        e = get_exception()
        module.fail_json(msg="unable to send msg: %s" % e)

    changed = True
    module.exit_json(changed=changed, msg=msg)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
