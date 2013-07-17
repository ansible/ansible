#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jan-Piet Mens <jpmens () gmail.com>
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

DOCUMENTATION = '''
---
module: irc
short_description: Send a message to an IRC channel
description:
   - Send a message to an IRC channel. This is a very simplistic implementation.
options:
  server:
    description:
      - IRC server name/address
    required: false
    default: localhost
  port:
    description:
      - IRC server port number
    required: false
    default: 6667
  nick:
    description:
      - Nickname
    required: false
    default: ansible
  msg:
    description:
      - The message body.
    required: true
    default: null
  color:
    description:
      - Text color for the message. Default is black.
    required: false
    default: black
    choices: [ "yellow", "red", "green", "blue", "black" ]
  channel:
    description:
      - Channel name
    required: true
  passwd:
    description:
      - Server password
    required: false

# informational: requirements for nodes
requirements: [ socket ]
author: Jan-Piet Mens
'''

EXAMPLES = '''
- irc: server=irc.example.net channel="#t1" msg="Hello world"

- local_action: irc port=6669
                channel="#t1"
                msg="All finished at {{ ansible_date_time.iso8601 }}"
                color=red
                nick=ansibleIRC
'''

# ===========================================
# IRC module support methods.
#

from time import sleep
import socket

def send_msg(channel, msg, server='localhost', port='6667',
        nick="ansible", color='black', passwd=False):
    '''send message to IRC'''

    colornumbers = {
        'black'  : "01",
        'red'    : "04",
        'green'  : "09",
        'yellow' : "08",
        'blue'   : "12",
    }

    try:
        colornumber = colornumbers[color]
    except:
        colornumber = "01"  # black

    message = "\x03" + colornumber + msg

    irc = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    irc.connect( ( server, int(port) ) )
    if passwd:
        irc.send( 'PASS %s\r\n' % passwd )
    irc.send( 'NICK %s\r\n' % nick )
    irc.send( 'USER %s %s %s :ansible IRC\r\n' % (nick, nick, nick))
    time.sleep(1)
    irc.send( 'JOIN %s\r\n' % channel )
    irc.send( 'PRIVMSG %s :%s\r\n' % (channel, message))
    time.sleep(1)
    irc.send( 'PART %s\r\n' % channel)
    irc.send( 'QUIT\r\n' )
    time.sleep(1)
    irc.close()

# ===========================================
# Main
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            server = dict(default='localhost'),
            port = dict(default = 6667),
            nick = dict(default = 'ansible'),
            msg = dict(required = True),
            color = dict(default="black", choices=["yellow", "red", "green",
                                                  "blue", "black"]),
            channel = dict(required = True),
            passwd = dict()
        ),
        supports_check_mode=True
    )

    server  = module.params["server"]
    port    = module.params["port"]
    nick    = module.params["nick"]
    msg     = module.params["msg"]
    color   = module.params["color"]
    channel = module.params["channel"]
    passwd  = module.params["passwd"]

    try:
        send_msg(channel, msg, server, port, nick, color, passwd)
    except Exception, e:
        module.fail_json(msg="unable to send to IRC: %s" % e)

    module.exit_json(changed=False, channel=channel, nick=nick,
                     msg=msg)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()
