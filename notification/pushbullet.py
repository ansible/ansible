#!/usr/bin/python
# -*- coding: utf-8 -*-

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
author: "Willy Barro (@willybarro)"
requirements: [ pushbullet.py ]
module: pushbullet
short_description: Sends notifications to Pushbullet
description:
   - This module sends push notifications via Pushbullet to channels or devices.
version_added: "2.0"
options:
    api_key:
        description:
            - Push bullet API token
        required: true
    channel:
        description:
            - The channel TAG you wish to broadcast a push notification,
              as seen on the "My Channels" > "Edit your channel" at
              Pushbullet page.
        required: false
        default: null
    device:
        description:
            - The device NAME you wish to send a push notification,
              as seen on the Pushbullet main page.
        required: false
        default: null
    push_type:
        description:
          - Thing you wish to push.
        required: false
        default: note
        choices: [ "note", "link" ]
    title:
        description:
          - Title of the notification.
        required: true
    body:
        description:
          - Body of the notification, e.g. Details of the fault you're alerting.
        required: false

notes:
   - Requires pushbullet.py Python package on the remote host.
     You can install it via pip with ($ pip install pushbullet.py).
     See U(https://github.com/randomchars/pushbullet.py)
'''

EXAMPLES = '''
# Sends a push notification to a device
- pushbullet: 
    api_key: "ABC123abc123ABC123abc123ABC123ab"
    device: "Chrome"
    title: "You may see this on Google Chrome"

# Sends a link to a device
- pushbullet: 
    api_key: "ABC123abc123ABC123abc123ABC123ab"
    device: "Chrome"
    push_type: "link"
    title: "Ansible Documentation"
    body: "http://docs.ansible.com/"

# Sends a push notification to a channel
- pushbullet: 
    api_key: "ABC123abc123ABC123abc123ABC123ab"
    channel: "my-awesome-channel"
    title: "Broadcasting a message to the #my-awesome-channel folks"

# Sends a push notification with title and body to a channel
- pushbullet: 
    api_key: "ABC123abc123ABC123abc123ABC123ab"
    channel: "my-awesome-channel"
    title: "ALERT! Signup service is down"
    body: "Error rate on signup service is over 90% for more than 2 minutes"
'''

try:
    from pushbullet import PushBullet
    from pushbullet.errors import InvalidKeyError, PushError
except ImportError:
    pushbullet_found = False
else:
    pushbullet_found = True

# ===========================================
# Main
#

def main():
    module = AnsibleModule(
        argument_spec = dict(
            api_key     = dict(type='str', required=True, no_log=True),
            channel     = dict(type='str', default=None),
            device      = dict(type='str', default=None),
            push_type   = dict(type='str', default="note", choices=['note', 'link']),
            title       = dict(type='str', required=True),
            body        = dict(type='str', default=None),
            url         = dict(type='str', default=None),
        ),
        mutually_exclusive = (
            ['channel', 'device'],
        ),
        supports_check_mode=True
    )

    api_key     = module.params['api_key']
    channel     = module.params['channel']
    device      = module.params['device']
    push_type   = module.params['push_type']
    title       = module.params['title']
    body        = module.params['body']
    url         = module.params['url']

    if not pushbullet_found:
        module.fail_json(msg="Python 'pushbullet.py' module is required. Install via: $ pip install pushbullet.py")

    # Init pushbullet 
    try:
        pb = PushBullet(api_key)
        target = None
    except InvalidKeyError:
        module.fail_json(msg="Invalid api_key")

    # Checks for channel/device
    if device is None and channel is None:
        module.fail_json(msg="You need to provide a channel or a device.")

    # Search for given device
    if device is not None:
        devices_by_nickname = {}
        for d in pb.devices:
            devices_by_nickname[d.nickname] = d

        if device in devices_by_nickname:
            target = devices_by_nickname[device]
        else:
            module.fail_json(msg="Device '%s' not found. Available devices: '%s'" % (device, "', '".join(devices_by_nickname.keys())))

    # Search for given channel
    if channel is not None:
        channels_by_tag = {}
        for c in pb.channels:
            channels_by_tag[c.channel_tag] = c

        if channel in channels_by_tag:
            target = channels_by_tag[channel]
        else:
            module.fail_json(msg="Channel '%s' not found. Available channels: '%s'" % (channel, "', '".join(channels_by_tag.keys())))

    # If in check mode, exit saying that we succeeded
    if module.check_mode:
        module.exit_json(changed=False, msg="OK")

    # Send push notification
    try:
        if push_type == "link":
            target.push_link(title, url, body)
        else:
            target.push_note(title, body)
        module.exit_json(changed=False, msg="OK")
    except PushError as e:
        module.fail_json(msg="An error occurred, Pushbullet's response: %s" % str(e))

    module.fail_json(msg="An unknown error has occurred")

# import module snippets
from ansible.module_utils.basic import *
main()
