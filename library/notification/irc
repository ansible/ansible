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
version_added: "1.2"
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
      - Nickname. May be shortened, depending on server's NICKLEN setting.
    required: false
    default: ansible
  msg:
    description:
      - The message body.
    required: true
    default: null
  color:
    description:
      - Text color for the message. ("none" is a valid option in 1.6 or later, in 1.6 and prior, the default color is black, not "none"). 
    required: false
    default: "none"
    choices: [ "none", "yellow", "red", "green", "blue", "black" ]
  channel:
    description:
      - Channel name
    required: true
  key:
    description:
      - Channel key
    required: false
    version_added: 1.7
  passwd:
    description:
      - Server password
    required: false
  timeout:
    description:
      - Timeout to use while waiting for successful registration and join
        messages, this is to prevent an endless loop
    default: 30
    version_added: 1.5
  use_ssl:
    description:
      - Designates whether TLS/SSL should be used when connecting to the IRC server
    default: False
    version_added: 1.8

# informational: requirements for nodes
requirements: [ socket ]
author: Jan-Piet Mens, Matt Martz
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

import re
import socket
import ssl

from time import sleep


def send_msg(channel, msg, server='localhost', port='6667', key=None,
             nick="ansible", color='none', passwd=False, timeout=30, use_ssl=False):
    '''send message to IRC'''

    colornumbers = {
        'black': "01",
        'red': "04",
        'green': "09",
        'yellow': "08",
        'blue': "12",
    }

    try:
        colornumber = colornumbers[color]
        colortext = "\x03" + colornumber
    except:
        colortext = ""

    message = colortext + msg

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if use_ssl:
        irc = ssl.wrap_socket(irc)
    irc.connect((server, int(port)))
    if passwd:
        irc.send('PASS %s\r\n' % passwd)
    irc.send('NICK %s\r\n' % nick)
    irc.send('USER %s %s %s :ansible IRC\r\n' % (nick, nick, nick))
    motd = ''
    start = time.time()
    while 1:
        motd += irc.recv(1024)
        # The server might send back a shorter nick than we specified (due to NICKLEN),
        #  so grab that and use it from now on (assuming we find the 00[1-4] response).
        match = re.search('^:\S+ 00[1-4] (?P<nick>\S+) :', motd, flags=re.M)
        if match:
            nick = match.group('nick')
            break
        elif time.time() - start > timeout:
            raise Exception('Timeout waiting for IRC server welcome response')
        sleep(0.5)

    if key:
        irc.send('JOIN %s %s\r\n' % (channel, key))
    else:
        irc.send('JOIN %s\r\n' % channel)

    join = ''
    start = time.time()
    while 1:
        join += irc.recv(1024)
        if re.search('^:\S+ 366 %s %s :' % (nick, channel), join, flags=re.M):
            break
        elif time.time() - start > timeout:
            raise Exception('Timeout waiting for IRC JOIN response')
        sleep(0.5)

    irc.send('PRIVMSG %s :%s\r\n' % (channel, message))
    sleep(1)
    irc.send('PART %s\r\n' % channel)
    irc.send('QUIT\r\n')
    sleep(1)
    irc.close()

# ===========================================
# Main
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='localhost'),
            port=dict(default=6667),
            nick=dict(default='ansible'),
            msg=dict(required=True),
            color=dict(default="none", choices=["yellow", "red", "green",
                                                 "blue", "black", "none"]),
            channel=dict(required=True),
            key=dict(),
            passwd=dict(),
            timeout=dict(type='int', default=30),
            use_ssl=dict(type='bool', default=False)
        ),
        supports_check_mode=True
    )

    server = module.params["server"]
    port = module.params["port"]
    nick = module.params["nick"]
    msg = module.params["msg"]
    color = module.params["color"]
    channel = module.params["channel"]
    key = module.params["key"]
    passwd = module.params["passwd"]
    timeout = module.params["timeout"]
    use_ssl = module.params["use_ssl"]

    try:
        send_msg(channel, msg, server, port, key, nick, color, passwd, timeout, use_ssl)
    except Exception, e:
        module.fail_json(msg="unable to send to IRC: %s" % e)

    module.exit_json(changed=False, channel=channel, nick=nick,
                     msg=msg)

# import module snippets
from ansible.module_utils.basic import *
main()
