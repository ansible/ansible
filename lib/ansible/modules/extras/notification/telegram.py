#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Artem Feofanov <artem.feofanov@gmail.com>
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
#


DOCUMENTATION = """

module: telegram
version_added: "2.2"
author: "Artem Feofanov (@tyouxa)"

short_description: module for sending notifications via telegram

description:
    - Send notifications via telegram bot, to a verified group or user
notes:
    - You will require a telegram account and create telegram bot to use this module.
options:
  msg:
    description:
      - What message you wish to send.
    required: true
  token:
    description:
      - Token identifying your telegram bot.
    required: true
  chat_id:
    description:
      - Telegram group or user chat_id
    required: true

"""

EXAMPLES = """

send a message to chat in playbook
- telegram:  token=bot9999999:XXXXXXXXXXXXXXXXXXXXXXX
    chat_id=000000
    msg="Ansible task finished"

"""

RETURN = """

msg:
  description: The message you attempted to send
  returned: success
  type: string
  sample: "Ansible task finished"


"""

import urllib

def main():

    module = AnsibleModule(
        argument_spec = dict(
            token = dict(type='str',required=True,no_log=True),
            chat_id = dict(type='str',required=True,no_log=True),
            msg = dict(type='str',required=True)),
        supports_check_mode=True
    )

    token = urllib.quote(module.params.get('token'))
    chat_id = urllib.quote(module.params.get('chat_id'))
    msg = urllib.quote(module.params.get('msg'))

    url = 'https://api.telegram.org/' + token + '/sendMessage?text=' + msg + '&chat_id=' + chat_id

    if module.check_mode:
        module.exit_json(changed=False)

    response, info = fetch_url(module, url)
    if info['status'] == 200:
        module.exit_json(changed=True)
    else:
        module.fail_json(msg="failed to send message, return status=%s" % str(info['status']))


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
