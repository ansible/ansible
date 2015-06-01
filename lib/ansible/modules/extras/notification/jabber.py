#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Brian Coca <bcoca@ansible.com>
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>


DOCUMENTATION = '''
---
version_added: "1.2"
module: jabber
short_description: Send a message to jabber user or chat room
description:
   - Send a message to jabber
options:
  user:
    description:
      User as which to connect
    required: true
  password:
    description:
      password for user to connect
    required: true
  to:
    description:
      user ID or name of the room, when using room use a slash to indicate your nick.
    required: true
  msg:
    description:
      - The message body.
    required: true
    default: null
  host:
    description:
      host to connect, overrides user info
    required: false
  port:
    description:
      port to connect to, overrides default
    required: false
    default: 5222
  encoding:
    description:
      message encoding
    required: false

# informational: requirements for nodes
requirements: [ xmpp ]
author: Brian Coca
'''

EXAMPLES = '''
# send a message to a user
- jabber: user=mybot@example.net
          password=secret
          to=friend@example.net
          msg="Ansible task finished"

# send a message to a room
- jabber: user=mybot@example.net
          password=secret
          to=mychaps@conference.example.net/ansiblebot
          msg="Ansible task finished"

# send a message, specifying the host and port
- jabber user=mybot@example.net
         host=talk.example.net
         port=5223
         password=secret
         to=mychaps@example.net
         msg="Ansible task finished"
'''

import os
import re
import time

HAS_XMPP = True
try:
    import xmpp
except ImportError:
    HAS_XMPP = False

def main():

    module = AnsibleModule(
        argument_spec=dict(
            user=dict(required=True),
            password=dict(required=True),
            to=dict(required=True),
            msg=dict(required=True),
            host=dict(required=False),
            port=dict(required=False,default=5222),
            encoding=dict(required=False),
        ),
        supports_check_mode=True
    )

    if not HAS_XMPP:
        module.fail_json(msg="xmpp is not installed")

    jid = xmpp.JID(module.params['user'])
    user = jid.getNode()
    server = jid.getDomain()
    port = module.params['port']
    password = module.params['password']
    try:
        to, nick = module.params['to'].split('/', 1)
    except ValueError:
        to, nick = module.params['to'], None

    if module.params['host']:
        host = module.params['host']
    else:
        host = server
    if module.params['encoding']:
        xmpp.simplexml.ENCODING = params['encoding']

    msg = xmpp.protocol.Message(body=module.params['msg'])

    try:
        conn=xmpp.Client(server)
        if not conn.connect(server=(host,port)):
            module.fail_json(rc=1, msg='Failed to connect to server: %s' % (server))
        if not conn.auth(user,password,'Ansible'):
            module.fail_json(rc=1, msg='Failed to authorize %s on: %s' % (user,server))
        # some old servers require this, also the sleep following send
        conn.sendInitPresence(requestRoster=0)

        if nick: # sending to room instead of user, need to join
            msg.setType('groupchat')
            msg.setTag('x', namespace='http://jabber.org/protocol/muc#user')
            conn.send(xmpp.Presence(to=module.params['to']))
            time.sleep(1)
        else:
            msg.setType('chat')

        msg.setTo(to)
        if not module.check_mode:
            conn.send(msg)
        time.sleep(1)
        conn.disconnect()
    except Exception, e:
        module.fail_json(msg="unable to send msg: %s" % e)

    module.exit_json(changed=False, to=to, user=user, msg=msg.getBody())

# import module snippets
from ansible.module_utils.basic import *
main()
