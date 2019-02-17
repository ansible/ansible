#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jan-Piet Mens <jpmens () gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


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
    default: localhost
  port:
    description:
      - IRC server port number
    default: 6667
  nick:
    description:
      - Nickname to send the message from. May be shortened, depending on server's NICKLEN setting.
    default: ansible
  msg:
    description:
      - The message body.
    required: true
  topic:
    description:
      - Set the channel topic
    version_added: "2.0"
  color:
    description:
      - Text color for the message. ("none" is a valid option in 1.6 or later, in 1.6 and prior, the default color is black, not "none").
        Added 11 more colors in version 2.0.
    default: "none"
    choices: [ "none", "white", "black", "blue", "green", "red", "brown", "purple", "orange", "yellow", "light_green", "teal", "light_cyan",
               "light_blue", "pink", "gray", "light_gray"]
  channel:
    description:
      - Channel name.  One of nick_to or channel needs to be set.  When both are set, the message will be sent to both of them.
    required: true
  nick_to:
    description:
      - A list of nicknames to send the message to. One of nick_to or channel needs to be set.  When both are defined, the message will be sent to both of them.
    version_added: "2.0"
  key:
    description:
      - Channel key
    version_added: "1.7"
  passwd:
    description:
      - Server password
  timeout:
    description:
      - Timeout to use while waiting for successful registration and join
        messages, this is to prevent an endless loop
    default: 30
    version_added: "1.5"
  use_ssl:
    description:
      - Designates whether TLS/SSL should be used when connecting to the IRC server
    type: bool
    default: 'no'
    version_added: "1.8"
  part:
    description:
      - Designates whether user should part from channel after sending message or not.
        Useful for when using a faux bot and not wanting join/parts between messages.
    type: bool
    default: 'yes'
    version_added: "2.0"
  style:
    description:
      - Text style for the message. Note italic does not work on some clients
    choices: [ "bold", "underline", "reverse", "italic" ]
    version_added: "2.0"

# informational: requirements for nodes
requirements: [ socket ]
author:
    - "Jan-Piet Mens (@jpmens)"
    - "Matt Martz (@sivel)"
'''

EXAMPLES = '''
- irc:
    server: irc.example.net
    channel: #t1
    msg: Hello world

- local_action:
    module: irc
    port: 6669
    server: irc.example.net
    channel: #t1
    msg: 'All finished at {{ ansible_date_time.iso8601 }}'
    color: red
    nick: ansibleIRC

- local_action:
    module: irc
    port: 6669
    server: irc.example.net
    channel: #t1
    nick_to:
      - nick1
      - nick2
    msg: 'All finished at {{ ansible_date_time.iso8601 }}'
    color: red
    nick: ansibleIRC
'''

# ===========================================
# IRC module support methods.
#

import re
import socket
import ssl
import time
import traceback

from ansible.module_utils._text import to_native, to_bytes
from ansible.module_utils.basic import AnsibleModule


def send_msg(msg, server='localhost', port='6667', channel=None, nick_to=None, key=None, topic=None,
             nick="ansible", color='none', passwd=False, timeout=30, use_ssl=False, part=True, style=None):
    '''send message to IRC'''
    nick_to = [] if nick_to is None else nick_to

    colornumbers = {
        'white': "00",
        'black': "01",
        'blue': "02",
        'green': "03",
        'red': "04",
        'brown': "05",
        'purple': "06",
        'orange': "07",
        'yellow': "08",
        'light_green': "09",
        'teal': "10",
        'light_cyan': "11",
        'light_blue': "12",
        'pink': "13",
        'gray': "14",
        'light_gray': "15",
    }

    stylechoices = {
        'bold': "\x02",
        'underline': "\x1F",
        'reverse': "\x16",
        'italic': "\x1D",
    }

    try:
        styletext = stylechoices[style]
    except Exception:
        styletext = ""

    try:
        colornumber = colornumbers[color]
        colortext = "\x03" + colornumber
    except Exception:
        colortext = ""

    message = styletext + colortext + msg

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if use_ssl:
        irc = ssl.wrap_socket(irc)
    irc.connect((server, int(port)))

    if passwd:
        irc.send(to_bytes('PASS %s\r\n' % passwd))
    irc.send(to_bytes('NICK %s\r\n' % nick))
    irc.send(to_bytes('USER %s %s %s :ansible IRC\r\n' % (nick, nick, nick)))
    motd = ''
    start = time.time()
    while 1:
        motd += to_native(irc.recv(1024))
        # The server might send back a shorter nick than we specified (due to NICKLEN),
        #  so grab that and use it from now on (assuming we find the 00[1-4] response).
        match = re.search(r'^:\S+ 00[1-4] (?P<nick>\S+) :', motd, flags=re.M)
        if match:
            nick = match.group('nick')
            break
        elif time.time() - start > timeout:
            raise Exception('Timeout waiting for IRC server welcome response')
        time.sleep(0.5)

    if key:
        irc.send(to_bytes('JOIN %s %s\r\n' % (channel, key)))
    else:
        irc.send(to_bytes('JOIN %s\r\n' % channel))

    join = ''
    start = time.time()
    while 1:
        join += to_native(irc.recv(1024))
        if re.search(r'^:\S+ 366 %s %s :' % (nick, channel), join, flags=re.M):
            break
        elif time.time() - start > timeout:
            raise Exception('Timeout waiting for IRC JOIN response')
        time.sleep(0.5)

    if topic is not None:
        irc.send(to_bytes('TOPIC %s :%s\r\n' % (channel, topic)))
        time.sleep(1)

    if nick_to:
        for nick in nick_to:
            irc.send(to_bytes('PRIVMSG %s :%s\r\n' % (nick, message)))
    if channel:
        irc.send(to_bytes('PRIVMSG %s :%s\r\n' % (channel, message)))
    time.sleep(1)
    if part:
        irc.send(to_bytes('PART %s\r\n' % channel))
        irc.send(to_bytes('QUIT\r\n'))
        time.sleep(1)
    irc.close()

# ===========================================
# Main
#


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='localhost'),
            port=dict(type='int', default=6667),
            nick=dict(default='ansible'),
            nick_to=dict(required=False, type='list'),
            msg=dict(required=True),
            color=dict(default="none", aliases=['colour'], choices=["white", "black", "blue",
                                                                    "green", "red", "brown",
                                                                    "purple", "orange", "yellow",
                                                                    "light_green", "teal", "light_cyan",
                                                                    "light_blue", "pink", "gray",
                                                                    "light_gray", "none"]),
            style=dict(default="none", choices=["underline", "reverse", "bold", "italic", "none"]),
            channel=dict(required=False),
            key=dict(no_log=True),
            topic=dict(),
            passwd=dict(no_log=True),
            timeout=dict(type='int', default=30),
            part=dict(type='bool', default=True),
            use_ssl=dict(type='bool', default=False)
        ),
        supports_check_mode=True,
        required_one_of=[['channel', 'nick_to']]
    )

    server = module.params["server"]
    port = module.params["port"]
    nick = module.params["nick"]
    nick_to = module.params["nick_to"]
    msg = module.params["msg"]
    color = module.params["color"]
    channel = module.params["channel"]
    topic = module.params["topic"]
    if topic and not channel:
        module.fail_json(msg="When topic is specified, a channel is required.")
    key = module.params["key"]
    passwd = module.params["passwd"]
    timeout = module.params["timeout"]
    use_ssl = module.params["use_ssl"]
    part = module.params["part"]
    style = module.params["style"]

    try:
        send_msg(msg, server, port, channel, nick_to, key, topic, nick, color, passwd, timeout, use_ssl, part, style)
    except Exception as e:
        module.fail_json(msg="unable to send to IRC: %s" % to_native(e), exception=traceback.format_exc())

    module.exit_json(changed=False, channel=channel, nick=nick,
                     msg=msg)


if __name__ == '__main__':
    main()
