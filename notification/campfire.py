#!/usr/bin/python
# -*- coding: utf-8 -*-
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
module: campfire
version_added: "1.2"
short_description: Send a message to Campfire
description:
   - Send a message to Campfire.
   - Messages with newlines will result in a "Paste" message being sent.
options:
  subscription:
    description:
      - The subscription name to use.
    required: true
  token:
    description:
      - API token.
    required: true
  room:
    description:
      - Room number to which the message should be sent.
    required: true
  msg:
    description:
      - The message body.
    required: true
  notify:
    description:
      - Send a notification sound before the message.
    required: false
    choices: ["56k", "bell", "bezos", "bueller", "clowntown",
              "cottoneyejoe", "crickets", "dadgummit", "dangerzone",
              "danielsan", "deeper", "drama", "greatjob", "greyjoy",
              "guarantee", "heygirl", "horn", "horror",
              "inconceivable", "live", "loggins", "makeitso", "noooo",
              "nyan", "ohmy", "ohyeah", "pushit", "rimshot",
              "rollout", "rumble", "sax", "secret", "sexyback",
              "story", "tada", "tmyk", "trololo", "trombone", "unix",
              "vuvuzela", "what", "whoomp", "yeah", "yodel"]

# informational: requirements for nodes
requirements: [ ]
author: "Adam Garside (@fabulops)"
'''

EXAMPLES = '''
- campfire: subscription=foo token=12345 room=123 msg="Task completed."

- campfire: subscription=foo token=12345 room=123 notify=loggins
        msg="Task completed ... with feeling."
'''

import cgi

def main():

    module = AnsibleModule(
        argument_spec=dict(
            subscription=dict(required=True),
            token=dict(required=True),
            room=dict(required=True),
            msg=dict(required=True),
            notify=dict(required=False,
                        choices=["56k", "bell", "bezos", "bueller",
                                 "clowntown", "cottoneyejoe",
                                 "crickets", "dadgummit", "dangerzone",
                                 "danielsan", "deeper", "drama",
                                 "greatjob", "greyjoy", "guarantee",
                                 "heygirl", "horn", "horror",
                                 "inconceivable", "live", "loggins",
                                 "makeitso", "noooo", "nyan", "ohmy",
                                 "ohyeah", "pushit", "rimshot",
                                 "rollout", "rumble", "sax", "secret",
                                 "sexyback", "story", "tada", "tmyk",
                                 "trololo", "trombone", "unix",
                                 "vuvuzela", "what", "whoomp", "yeah",
                                 "yodel"]),
        ),
        supports_check_mode=False
    )

    subscription = module.params["subscription"]
    token = module.params["token"]
    room = module.params["room"]
    msg = module.params["msg"]
    notify = module.params["notify"]

    URI = "https://%s.campfirenow.com" % subscription
    NSTR = "<message><type>SoundMessage</type><body>%s</body></message>"
    MSTR = "<message><body>%s</body></message>"
    AGENT = "Ansible/1.2"

    # Hack to add basic auth username and password the way fetch_url expects
    module.params['url_username'] = token
    module.params['url_password'] = 'X'

    target_url = '%s/room/%s/speak.xml' % (URI, room)
    headers = {'Content-Type': 'application/xml',
            'User-agent': AGENT}

    # Send some audible notification if requested
    if notify:
        response, info = fetch_url(module, target_url, data=NSTR % cgi.escape(notify), headers=headers)
    if info['status'] != 200:
        module.fail_json(msg="unable to send msg: '%s', campfire api"
                            " returned error code: '%s'" %
                             (notify, info['status']))

    # Send the message
    response, info = fetch_url(module, target_url, data=MSTR %cgi.escape(msg), headers=headers)
    if info['status'] != 200:
        module.fail_json(msg="unable to send msg: '%s', campfire api"
                            " returned error code: '%s'" %
                             (msg, info['status']))

    module.exit_json(changed=True, room=room, msg=msg, notify=notify)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
