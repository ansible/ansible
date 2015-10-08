#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Stefan Berggren <nsg@nsg.cc>
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
version_added: "1.6"
author: "Ramon de la Fuente (@ramondelafuente)"
options:
  domain:
    description:
      - Slack (sub)domain for your environment without protocol. (i.e.
        C(future500.slack.com)) In 1.8 and beyond, this is deprecated and may
        be ignored.  See token documentation for information.
    required: false
    default: None
  token:
    description:
      - Slack integration token.  This authenticates you to the slack service.
        Prior to 1.8, a token looked like C(3Ffe373sfhRE6y42Fg3rvf4GlK).  In
        1.8 and above, ansible adapts to the new slack API where tokens look
        like C(G922VJP24/D921DW937/3Ffe373sfhRE6y42Fg3rvf4GlK).  If tokens
        are in the new format then slack will ignore any value of domain.  If
        the token is in the old format the domain is required.  Ansible has no
        control of when slack will get rid of the old API.  When slack does
        that the old format will stop working.
    required: true
  msg:
    description:
      - Message to send.
    required: false
    default: None
  channel:
    description:
      - Channel to send the message to. If absent, the message goes to the channel selected for the I(token).
    required: false
    default: None
  username:
    description:
      - This is the sender of the message.
    required: false
    default: "Ansible"
  icon_url:
    description:
      - Url for the message sender's icon (default C(http://www.ansible.com/favicon.ico))
    required: false
  icon_emoji:
    description:
      - Emoji for the message sender. See Slack documentation for options.
        (if I(icon_emoji) is set, I(icon_url) will not be used)
    required: false
    default: None
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
    default: None
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
  color:
    version_added: "2.0"
    description:
      - Allow text to use default colors - use the default of 'normal' to not send a custom color bar at the start of the message
    required: false
    default: 'normal'
    choices:
      - 'normal'
      - 'good'
      - 'warning'
      - 'danger'
  attachments:
    description:
      - Define a list of attachments. This list mirrors the Slack JSON API. For more information, see https://api.slack.com/docs/attachments
    required: false
    default: None
"""

EXAMPLES = """
- name: Send notification message via Slack
  local_action:
    module: slack
    token: thetoken/generatedby/slack
    msg: "{{ inventory_hostname }} completed"

- name: Send notification message via Slack all options
  local_action:
    module: slack
    token: thetoken/generatedby/slack
    msg: "{{ inventory_hostname }} completed"
    channel: "#ansible"
    username: "Ansible on {{ inventory_hostname }}"
    icon_url: "http://www.example.com/some-image-file.png"
    link_names: 0
    parse: 'none'

- name: insert a color bar in front of the message for visibility purposes and use the default webhook icon and name configured in Slack
  slack:
    token: thetoken/generatedby/slack
    msg: "{{ inventory_hostname }} is alive!"
    color: good
    username: ""
    icon_url: ""

- name: Use the attachments API
  slack:
    token: thetoken/generatedby/slack
    attachments:
      - text: "Display my system load on host A and B"
        color: "#ff00dd"
        title: "System load"
        fields:
          - title: "System A"
            value: "load average: 0,74, 0,66, 0,63"
            short: "true"
          - title: "System B"
            value: "load average: 5,16, 4,64, 2,43"
            short: "true"

- name: Send notification message via Slack (deprecated API using domian)
  local_action:
    module: slack
    domain: future500.slack.com
    token: thetokengeneratedbyslack
    msg: "{{ inventory_hostname }} completed"

"""

OLD_SLACK_INCOMING_WEBHOOK = 'https://%s/services/hooks/incoming-webhook?token=%s'
SLACK_INCOMING_WEBHOOK = 'https://hooks.slack.com/services/%s'

def build_payload_for_slack(module, text, channel, username, icon_url, icon_emoji, link_names, parse, color, attachments):
    payload = {}
    if color == "normal" and text is not None:
        payload = dict(text=text)
    elif text is not None:
        payload = dict(attachments=[dict(text=text, color=color)])
    if channel is not None:
        if (channel[0] == '#') or (channel[0] == '@'):
            payload['channel'] = channel
        else:
            payload['channel'] = '#'+channel
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

    if attachments is not None:
        if 'attachments' not in payload:
            payload['attachments'] = []

    if attachments is not None:
        for attachment in attachments:
            if 'fallback' not in attachment:
                attachment['fallback'] = attachment['text']
            payload['attachments'].append(attachment)

    payload="payload=" + module.jsonify(payload)
    return payload

def do_notify_slack(module, domain, token, payload):
    if token.count('/') >= 2:
        # New style token
        slack_incoming_webhook = SLACK_INCOMING_WEBHOOK % (token)
    else:
        if not domain:
            module.fail_json(msg="Slack has updated its webhook API.  You need to specify a token of the form XXXX/YYYY/ZZZZ in your playbook")
        slack_incoming_webhook = OLD_SLACK_INCOMING_WEBHOOK % (domain, token)

    response, info = fetch_url(module, slack_incoming_webhook, data=payload)
    if info['status'] != 200:
        obscured_incoming_webhook = SLACK_INCOMING_WEBHOOK % ('[obscured]')
        module.fail_json(msg=" failed to send %s to %s: %s" % (payload, obscured_incoming_webhook, info['msg']))

def main():
    module = AnsibleModule(
        argument_spec = dict(
            domain      = dict(type='str', required=False, default=None),
            token       = dict(type='str', required=True, no_log=True),
            msg         = dict(type='str', required=False, default=None),
            channel     = dict(type='str', default=None),
            username    = dict(type='str', default='Ansible'),
            icon_url    = dict(type='str', default='http://www.ansible.com/favicon.ico'),
            icon_emoji  = dict(type='str', default=None),
            link_names  = dict(type='int', default=1, choices=[0,1]),
            parse       = dict(type='str', default=None, choices=['none', 'full']),
            validate_certs = dict(default='yes', type='bool'),
            color       = dict(type='str', default='normal', choices=['normal', 'good', 'warning', 'danger']),
            attachments = dict(type='list', required=False, default=None)
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
    color = module.params['color']
    attachments = module.params['attachments']

    payload = build_payload_for_slack(module, text, channel, username, icon_url, icon_emoji, link_names, parse, color, attachments)
    do_notify_slack(module, domain, token, payload)

    module.exit_json(msg="OK")

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
