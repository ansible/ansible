#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Aymeric Bringard <diadzine@gmail.com>
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = """
module: teams
short_description: Send Microsoft Teams notifications
description:
    - The C(teams) module sends notifications to
      U(https://teams.microsoft.com/start) through Office 365 Connectors via
      the Incoming WebHook integration.
version_added: "2.3"
author: "Aymeric Bringard (@diadzine)"
options:
  title:
    description:
      - A message can also contain a title.
  text:
    description:
      - The contents of text will be displayed in a card format, along with a
        sender image and display name. This image and display name are set
        when the webhook is configured.
        The simplest message just contains a text variable.
        To add links to text, developers **must** include Markdown syntax for
        hyperlinks.
    required: true
  color:
    description:
      - You can also control a color bar by setting color to a color hex code.
        This bar appears to the left of the cards content, and is primarily
        used to indicate status to the user.
  url:
    description:
      - The webhook URL is given to you when you create a new Connector in
        Microsoft Teams. This URL is used to communicate with the target
        Office 365 Group.
        All the GUIDs within the URL define the reference to the context of the
        current webhook.
    required: true
"""

EXAMPLES = """
- name: Send notification message via Microsoft Teams
  teams:
    url: https://outlook.office.com/webhook/GUID/IncomingWebhook/GUID/GUID
    text: 'Deployment completed on {{ inventory_hostname }}'
  delegate_to: localhost

- name: Send notification message via Microsoft Teams
  teams:
    url: https://outlook.office.com/webhook/GUID/IncomingWebhook/GUID/GUID
    title: 'Ansible status'
    text: '{{ inventory_hostname }} is up and running'
    color: '00CC00'
  delegate_to: localhost
"""

RETURN = """

"""

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def build_payload_for_teams(module, text, title, color):
    payload = dict(text=text)

    if title is not None:
        payload['title'] = title

    if color is not None:
        payload['themeColor'] = color

    payload=module.jsonify(payload)
    return payload


def do_notify_teams(module, teams_incoming_webhook, payload):
    headers = {
        'Content-Type': 'application/json',
    }
    response, info = fetch_url(
        module=module,
        url=teams_incoming_webhook,
        headers=headers,
        method='POST',
        data=payload
    )

    if info['status'] == 200:
        module.exit_json(changed=True)
    else:
        module.fail_json(
            msg=" failed to send %s to Teams incoming webhook: %s" % (
                payload,
                info['msg']
            )
        )

def main():

    module = AnsibleModule(
        argument_spec = dict(
            url = dict(type='str', required=True, no_log=True),
            text = dict(type='str', required=True),
            title = dict(type='str'),
            color = dict(type='str')
        ),
        supports_check_mode=True
    )

    url = module.params['url']
    text = module.params['text']
    title = module.params['title']
    color = module.params['color']

    if module.check_mode:
        module.exit_json(changed=False)

    payload = build_payload_for_teams(module, text, title, color)
    do_notify_teams(module, url, payload)


if __name__ == '__main__':
    main()
