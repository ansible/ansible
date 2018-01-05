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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

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
    version_added: "2.1"
  api:
    description:
      - API endpoint
    default: data.logentries.com
    version_added: "2.1"
  port:
    description:
      - API endpoint port
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


# import module snippets
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.basic import AnsibleModule
import socket


def send_msg(module, token, msg, api, port):

    message = "{} {}\n".format(token, msg)

    api_ip = socket.gethostbyname(api)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((api_ip, port))
    try:
        if not module.check_mode:
            s.send(message)
    except:
        e = get_exception()
        module.fail_json(msg="failed to send message, msg=%s" % e)
    s.close()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            token=dict(type='str', required=True),
            msg=dict(type='str', required=True),
            api=dict(type='str', default="data.logentries.com"),
            port=dict(type='int', default=80)),
        supports_check_mode=True
    )

    token = module.params["token"]
    msg = module.params["msg"]
    api = module.params["api"]
    port = module.params["port"]

    changed = False
    try:
        send_msg(module, token, msg, api, port)
        changed = True
    except Exception:
        e = get_exception()
        module.fail_json(msg="unable to send msg: %s" % e)

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
