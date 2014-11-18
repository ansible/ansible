#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Ramon de la Fuente <ramon@delafuente.nl>
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

DOCUMENTATION = """
module: slack
short_description: Send Slack notifications
description:
    - The M(slack) module sends notifications to U(http://slack.com) via the Incoming WebHook integration
version_added: 1.6
author: Ramon de la Fuente <ramon@delafuente.nl>
options:
  domain:
    description:
      - Slack (sub)domain for your environment without protocol.
        (i.e. C(future500.slack.com))
    required: true
  token:
    description:
      - Slack integration token
    required: true
  msg:
    description:
      - Message to send.
    required: true
  channel:
    description:
      - Channel to send the message to. If absent, the message goes to the channel selected for the I(token).
    required: false
  username:
    description:
      - This is the sender of the message.
    required: false
    default: ansible
  icon_url:
    description:
      - Url for the message sender's icon (default C(http://www.ansible.com/favicon.ico))
    required: false
  icon_emoji:
    description:
      - Emoji for the message sender. See Slack documentation for options.
        (if I(icon_emoji) is set, I(icon_url) will not be used)
    required: false
  link_names:
    description:
      - Automatically create links for channels and usernames in I(msg).
    required: false
    default: 1
    choices:
      - 1
      - 0
  parse:
    description:
      - Setting for the message parser at Slack
    required: false
    choices:
      - 'full'
      - 'none'
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices:
      - 'yes'
      - 'no'
"""

EXAMPLES = """
- name: Send notification message via Slack
  local_action:
    module: slack
    domain: future500.slack.com
    token: thetokengeneratedbyslack
    msg: "{{ inventory_hostname }} completed"

- name: Send notification message via Slack all options
  local_action:
    module: slack
    domain: future500.slack.com
    token: thetokengeneratedbyslack
    msg: "{{ inventory_hostname }} completed"
    channel: "#ansible"
    username: "Ansible on {{ inventory_hostname }}"
    icon_url: "http://www.example.com/some-image-file.png"
    link_names: 0
    parse: 'none'

"""

SLACK_INCOMING_WEBHOOK = 'https://hooks.slack.com/services/%s'

def build_payload_for_slack(module, text, channel, username, icon_url, icon_emoji, link_names, parse):
    payload = dict(text=text)

    if channel is not None:
        payload['channel'] = channel if (channel[0] == '#') else '#'+channel
    if username is not None:
        payload['username'] = username
    if icon_emoji is not None:
        payload['icon_emoji'] = icon_emoji
    else:
        payload['icon_url'] = icon_url
    if link_names is not None:
        payload['link_names'] = link_names
    if parse is not None:
        payload['parse'] = parse

    payload="payload=" + module.jsonify(payload)
    return payload

def do_notify_slack(module, domain, token, payload):
    slack_incoming_webhook = SLACK_INCOMING_WEBHOOK % (token)

    response, info = fetch_url(module, slack_incoming_webhook, data=payload)
    if info['status'] != 200:
        obscured_incoming_webhook = SLACK_INCOMING_WEBHOOK % ('[obscured]')
        module.fail_json(msg=" failed to send %s to %s: %s" % (payload, obscured_incoming_webhook, info['msg']))

def main():
    module = AnsibleModule(
        argument_spec = dict(
            domain      = dict(type='str', required=True),
            token       = dict(type='str', required=True),
            msg         = dict(type='str', required=True),
            channel     = dict(type='str', default=None),
            username    = dict(type='str', default='Ansible'),
            icon_url    = dict(type='str', default='http://www.ansible.com/favicon.ico'),
            icon_emoji  = dict(type='str', default=None),
            link_names  = dict(type='int', default=1, choices=[0,1]),
            parse       = dict(type='str', default=None, choices=['none', 'full']),

            validate_certs = dict(default='yes', type='bool'),
        )
    )

    domain = module.params['domain']
    token = module.params['token']
    text = module.params['msg']
    channel = module.params['channel']
    username = module.params['username']
    icon_url = module.params['icon_url']
    icon_emoji = module.params['icon_emoji']
    link_names = module.params['link_names']
    parse = module.params['parse']

    payload = build_payload_for_slack(module, text, channel, username, icon_url, icon_emoji, link_names, parse)
    do_notify_slack(module, domain, token, payload)

    module.exit_json(msg="OK")

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()
