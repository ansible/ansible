#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Steve Pletcher <steve@steve-pletcher.com>
# (c) 2016, René Moser <mail@renemoser.net>
# (c) 2015, Stefan Berggren <nsg@nsg.cc>
# (c) 2014, Ramon de la Fuente <ramon@delafuente.nl>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: slack
short_description: Send Slack notifications
description:
    - The C(slack) module sends notifications to U(http://slack.com) via the Incoming WebHook integration
version_added: "1.6"
author: "Ramon de la Fuente (@ramondelafuente)"
options:
  domain:
    description:
      - Slack (sub)domain for your environment without protocol. (i.e.
        C(example.slack.com)) In 1.8 and beyond, this is deprecated and may
        be ignored.  See token documentation for information.
  token:
    description:
      - Slack integration token.  This authenticates you to the slack service.
        Prior to 1.8, a token looked like C(3Ffe373sfhRE6y42Fg3rvf4GlK).  In
        1.8 and above, ansible adapts to the new slack API where tokens look
        like C(G922VJP24/D921DW937/3Ffe373sfhRE6y42Fg3rvf4GlK).  If tokens
        are in the new format then slack will ignore any value of domain.  If
        the token is in the old format the domain is required.  Ansible has no
        control of when slack will get rid of the old API.  When slack does
        that the old format will stop working.  ** Please keep in mind the tokens
        are not the API tokens but are the webhook tokens.  In slack these are
        found in the webhook URL which are obtained under the apps and integrations.
        The incoming webhooks can be added in that area.  In some cases this may
        be locked by your Slack admin and you must request access.  It is there
        that the incoming webhooks can be added.  The key is on the end of the
        URL given to you in that section.
    required: true
  msg:
    description:
      - Message to send. Note that the module does not handle escaping characters.
        Plain-text angle brackets and ampersands should be converted to HTML entities (e.g. & to &amp;) before sending.
        See Slack's documentation (U(https://api.slack.com/docs/message-formatting)) for more.
  channel:
    description:
      - Channel to send the message to. If absent, the message goes to the channel selected for the I(token).
  thread_id:
    version_added: 2.8
    description:
      - Optional. Timestamp of message to thread this message to as a float. https://api.slack.com/docs/message-threading
  username:
    description:
      - This is the sender of the message.
    default: "Ansible"
  icon_url:
    description:
      - Url for the message sender's icon (default C(https://www.ansible.com/favicon.ico))
  icon_emoji:
    description:
      - Emoji for the message sender. See Slack documentation for options.
        (if I(icon_emoji) is set, I(icon_url) will not be used)
  link_names:
    description:
      - Automatically create links for channels and usernames in I(msg).
    default: 1
    choices:
      - 1
      - 0
  parse:
    description:
      - Setting for the message parser at Slack
    choices:
      - 'full'
      - 'none'
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
  color:
    version_added: "2.0"
    description:
      - Allow text to use default colors - use the default of 'normal' to not send a custom color bar at the start of the message.
      - Allowed values for color can be one of 'normal', 'good', 'warning', 'danger', any valid 3 digit or 6 digit hex color value.
      - Specifying value in hex is supported from version 2.8.
    default: 'normal'
  attachments:
    description:
      - Define a list of attachments. This list mirrors the Slack JSON API.
      - For more information, see also in the (U(https://api.slack.com/docs/attachments)).
"""

EXAMPLES = """
- name: Send notification message via Slack
  slack:
    token: thetoken/generatedby/slack
    msg: '{{ inventory_hostname }} completed'
  delegate_to: localhost

- name: Send notification message via Slack all options
  slack:
    token: thetoken/generatedby/slack
    msg: '{{ inventory_hostname }} completed'
    channel: '#ansible'
    thread_id: 1539917263.000100
    username: 'Ansible on {{ inventory_hostname }}'
    icon_url: http://www.example.com/some-image-file.png
    link_names: 0
    parse: 'none'
  delegate_to: localhost

- name: insert a color bar in front of the message for visibility purposes and use the default webhook icon and name configured in Slack
  slack:
    token: thetoken/generatedby/slack
    msg: '{{ inventory_hostname }} is alive!'
    color: good
    username: ''
    icon_url: ''

- name: insert a color bar in front of the message with valid hex color value
  slack:
    token: thetoken/generatedby/slack
    msg: 'This message uses color in hex value'
    color: '#00aacc'
    username: ''
    icon_url: ''

- name: Use the attachments API
  slack:
    token: thetoken/generatedby/slack
    attachments:
      - text: Display my system load on host A and B
        color: '#ff00dd'
        title: System load
        fields:
          - title: System A
            value: "load average: 0,74, 0,66, 0,63"
            short: True
          - title: System B
            value: 'load average: 5,16, 4,64, 2,43'
            short: True

- name: Send a message with a link using Slack markup
  slack:
    token: thetoken/generatedby/slack
    msg: We sent this message using <https://www.ansible.com|Ansible>!

- name: Send a message with angle brackets and ampersands
  slack:
    token: thetoken/generatedby/slack
    msg: This message has &lt;brackets&gt; &amp; ampersands in plain text.
"""

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


OLD_SLACK_INCOMING_WEBHOOK = 'https://%s/services/hooks/incoming-webhook?token=%s'
SLACK_INCOMING_WEBHOOK = 'https://hooks.slack.com/services/%s'

# Escaping quotes and apostrophes to avoid ending string prematurely in ansible call.
# We do not escape other characters used as Slack metacharacters (e.g. &, <, >).
escape_table = {
    '"': "\"",
    "'": "\'",
}


def is_valid_hex_color(color_choice):
    if re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color_choice):
        return True
    return False


def escape_quotes(text):
    '''Backslash any quotes within text.'''
    return "".join(escape_table.get(c, c) for c in text)


def build_payload_for_slack(module, text, channel, thread_id, username, icon_url, icon_emoji, link_names,
                            parse, color, attachments):
    payload = {}
    if color == "normal" and text is not None:
        payload = dict(text=escape_quotes(text))
    elif text is not None:
        # With a custom color we have to set the message as attachment, and explicitly turn markdown parsing on for it.
        payload = dict(attachments=[dict(text=escape_quotes(text), color=color, mrkdwn_in=["text"])])
    if channel is not None:
        if (channel[0] == '#') or (channel[0] == '@'):
            payload['channel'] = channel
        else:
            payload['channel'] = '#' + channel
    if thread_id is not None:
        payload['thread_ts'] = thread_id
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
        keys_to_escape = [
            'title',
            'text',
            'author_name',
            'pretext',
            'fallback',
        ]
        for attachment in attachments:
            for key in keys_to_escape:
                if key in attachment:
                    attachment[key] = escape_quotes(attachment[key])

            if 'fallback' not in attachment:
                attachment['fallback'] = attachment['text']

            payload['attachments'].append(attachment)

    payload = module.jsonify(payload)
    return payload


def do_notify_slack(module, domain, token, payload):
    if token.count('/') >= 2:
        # New style token
        slack_incoming_webhook = SLACK_INCOMING_WEBHOOK % (token)
    else:
        if not domain:
            module.fail_json(msg="Slack has updated its webhook API.  You need to specify a token of the form "
                                 "XXXX/YYYY/ZZZZ in your playbook")
        slack_incoming_webhook = OLD_SLACK_INCOMING_WEBHOOK % (domain, token)

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    response, info = fetch_url(module=module, url=slack_incoming_webhook, headers=headers, method='POST', data=payload)

    if info['status'] != 200:
        obscured_incoming_webhook = SLACK_INCOMING_WEBHOOK % ('[obscured]')
        module.fail_json(msg=" failed to send %s to %s: %s" % (payload, obscured_incoming_webhook, info['msg']))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain=dict(type='str', required=False, default=None),
            token=dict(type='str', required=True, no_log=True),
            msg=dict(type='str', required=False, default=None),
            channel=dict(type='str', default=None),
            thread_id=dict(type='float', default=None),
            username=dict(type='str', default='Ansible'),
            icon_url=dict(type='str', default='https://www.ansible.com/favicon.ico'),
            icon_emoji=dict(type='str', default=None),
            link_names=dict(type='int', default=1, choices=[0, 1]),
            parse=dict(type='str', default=None, choices=['none', 'full']),
            validate_certs=dict(default='yes', type='bool'),
            color=dict(type='str', default='normal'),
            attachments=dict(type='list', required=False, default=None)
        )
    )

    domain = module.params['domain']
    token = module.params['token']
    text = module.params['msg']
    channel = module.params['channel']
    thread_id = module.params['thread_id']
    username = module.params['username']
    icon_url = module.params['icon_url']
    icon_emoji = module.params['icon_emoji']
    link_names = module.params['link_names']
    parse = module.params['parse']
    color = module.params['color']
    attachments = module.params['attachments']

    color_choices = ['normal', 'good', 'warning', 'danger']
    if color not in color_choices and not is_valid_hex_color(color):
        module.fail_json(msg="Color value specified should be either one of %r "
                             "or any valid hex value with length 3 or 6." % color_choices)

    payload = build_payload_for_slack(module, text, channel, thread_id, username, icon_url, icon_emoji, link_names,
                                      parse, color, attachments)
    do_notify_slack(module, domain, token, payload)

    module.exit_json(msg="OK")


if __name__ == '__main__':
    main()
