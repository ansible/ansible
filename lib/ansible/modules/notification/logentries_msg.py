#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: logentries_msg
version_added: "2.5"
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
  msg:
    description:
      - The message body.
    required: true
  api:
    description:
      - API endpoint
    default: data.logentries.com
  port:
    description:
      - API endpoint port
    default: 80
author: "Jimmy Tang (@jcftang) <jimmy_tang@rapid7.com>"
'''

RETURN = '''# '''

EXAMPLES = '''
- logentries_msg:
    token=00000000-0000-0000-0000-000000000000
    msg="{{ ansible_hostname }}"
'''

import socket

from ansible.module_utils.basic import AnsibleModule


def send_msg(module, token, msg, api, port):

    message = "{0} {1}\n".format(token, msg)

    api_ip = socket.gethostbyname(api)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((api_ip, port))
    try:
        if not module.check_mode:
            s.send(message)
    except Exception as e:
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
    except Exception as e:
        module.fail_json(msg="unable to send msg: %s" % e)

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
