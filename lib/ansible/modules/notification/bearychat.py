#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Jiangge Zhang <tonyseek@gmail.com>
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: bearychat
short_description: Send BearyChat notifications
description:
    - The M(bearychat) module sends notifications to U(https://bearychat.com)
      via the Incoming Robot integration.
version_added: "2.4"
author: "Jiangge Zhang (@tonyseek)"
options:
  url:
    description:
      - BearyChat WebHook URL. This authenticates you to the bearychat
        service. It looks like
        C(https://hook.bearychat.com/=ae2CF/incoming/e61bd5c57b164e04b11ac02e66f47f60).
    required: true
  text:
    description:
      - Message to send.
  markdown:
    description:
      - If C(yes), text will be parsed as markdown.
    default: 'yes'
    type: bool
  channel:
    description:
      - Channel to send the message to. If absent, the message goes to the
        default channel selected by the I(url).
  attachments:
    description:
      - Define a list of attachments. For more information, see
        https://github.com/bearyinnovative/bearychat-tutorial/blob/master/robots/incoming.md#attachments
"""

EXAMPLES = """
- name: Send notification message via BearyChat
  local_action:
    module: bearychat
    url: |
      https://hook.bearychat.com/=ae2CF/incoming/e61bd5c57b164e04b11ac02e66f47f60
    text: "{{ inventory_hostname }} completed"

- name: Send notification message via BearyChat all options
  local_action:
    module: bearychat
    url: |
      https://hook.bearychat.com/=ae2CF/incoming/e61bd5c57b164e04b11ac02e66f47f60
    text: "{{ inventory_hostname }} completed"
    markdown: no
    channel: "#ansible"
    attachments:
      - title: "Ansible on {{ inventory_hostname }}"
        text: "May the Force be with you."
        color: "#ffffff"
        images:
          - http://example.com/index.png
"""

RETURN = """
msg:
    description: execution result
    returned: success
    type: string
    sample: "OK"
"""

try:
    from ansible.module_utils.six.moves.urllib.parse import urlparse, urlunparse
    HAS_URLPARSE = True
except:
    HAS_URLPARSE = False
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def build_payload_for_bearychat(module, text, markdown, channel, attachments):
    payload = {}
    if text is not None:
        payload['text'] = text
    if markdown is not None:
        payload['markdown'] = markdown
    if channel is not None:
        payload['channel'] = channel
    if attachments is not None:
        payload.setdefault('attachments', []).extend(
            build_payload_for_bearychat_attachment(
                module, item.get('title'), item.get('text'), item.get('color'),
                item.get('images'))
            for item in attachments)
    payload = 'payload=%s' % module.jsonify(payload)
    return payload


def build_payload_for_bearychat_attachment(module, title, text, color, images):
    attachment = {}
    if title is not None:
        attachment['title'] = title
    if text is not None:
        attachment['text'] = text
    if color is not None:
        attachment['color'] = color
    if images is not None:
        target_images = attachment.setdefault('images', [])
        if not isinstance(images, (list, tuple)):
            images = [images]
        for image in images:
            if isinstance(image, dict) and 'url' in image:
                image = {'url': image['url']}
            elif hasattr(image, 'startswith') and image.startswith('http'):
                image = {'url': image}
            else:
                module.fail_json(
                    msg="BearyChat doesn't have support for this kind of "
                        "attachment image")
            target_images.append(image)
    return attachment


def do_notify_bearychat(module, url, payload):
    response, info = fetch_url(module, url, data=payload)
    if info['status'] != 200:
        url_info = urlparse(url)
        obscured_incoming_webhook = urlunparse(
            (url_info.scheme, url_info.netloc, '[obscured]', '', '', ''))
        module.fail_json(
            msg=" failed to send %s to %s: %s" % (
                payload, obscured_incoming_webhook, info['msg']))


def main():
    module = AnsibleModule(argument_spec={
        'url': dict(type='str', required=True, no_log=True),
        'text': dict(type='str'),
        'markdown': dict(default='yes', type='bool'),
        'channel': dict(type='str'),
        'attachments': dict(type='list'),
    })

    if not HAS_URLPARSE:
        module.fail_json(msg='urlparse is not installed')

    url = module.params['url']
    text = module.params['text']
    markdown = module.params['markdown']
    channel = module.params['channel']
    attachments = module.params['attachments']

    payload = build_payload_for_bearychat(
        module, text, markdown, channel, attachments)
    do_notify_bearychat(module, url, payload)

    module.exit_json(msg="OK")


if __name__ == '__main__':
    main()
