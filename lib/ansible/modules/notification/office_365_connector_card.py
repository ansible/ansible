#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Marc Sensenich <hello@marc-sensenich.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: office_365_connector_card
short_description: Use webhooks to create Connector Card messages within an Office 365 group
description:
  - Creates Connector Card messages through
  - Office 365 Connectors U(https://dev.outlook.com/Connectors)
version_added: "2.4"
author: "Marc Sensenich (@marc-sensenich)"
notes:
  - This module is not idempotent, therefore if the same task is run twice
    there will be two Connector Cards created
options:
  webhook:
    description:
      - The webhook URL is given to you when you create a new Connector.
    required: true
  summary:
    description:
      - A string used for summarizing card content.
      - This will be shown as the message subject.
      - This is required if the text parameter isn't populated.
  color:
    description:
      - Accent color used for branding or indicating status in the card.
  title:
    description:
      - A title for the Connector message. Shown at the top of the message.
  text:
    description:
      - The main text of the card.
      - This will be rendered below the sender information and optional title,
      - and above any sections or actions present.
  actions:
    description:
      - This array of objects will power the action links
      - found at the bottom of the card.
  sections:
    description:
      - Contains a list of sections to display in the card.
      - For more information see https://dev.outlook.com/Connectors/reference.
"""

EXAMPLES = """
- name: Create a simple Connector Card
  office_365_connector_card:
    webhook: https://outlook.office.com/webhook/GUID/IncomingWebhook/GUID/GUID
    text: 'Hello, World!'

- name: Create a Connector Card with the full format
  office_365_connector_card:
    webhook: https://outlook.office.com/webhook/GUID/IncomingWebhook/GUID/GUID
    summary: This is the summary property
    title: This is the **card's title** property
    text: This is the **card's text** property. Lorem ipsum dolor sit amet, consectetur
      adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
    color: E81123
    sections:
    - title: This is the **section's title** property
      activity_image: http://connectorsdemo.azurewebsites.net/images/MSC12_Oscar_002.jpg
      activity_title: This is the section's **activityTitle** property
      activity_subtitle: This is the section's **activitySubtitle** property
      activity_text: This is the section's **activityText** property.
      hero_image:
        image: http://connectorsdemo.azurewebsites.net/images/WIN12_Scene_01.jpg
        title: This is the image's alternate text
      text: This is the section's text property. Lorem ipsum dolor sit amet, consectetur
        adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
      facts:
      - name: This is a fact name
        value: This is a fact value
      - name: This is a fact name
        value: This is a fact value
      - name: This is a fact name
        value: This is a fact value
      images:
      - image: http://connectorsdemo.azurewebsites.net/images/MicrosoftSurface_024_Cafe_OH-06315_VS_R1c.jpg
        title: This is the image's alternate text
      - image: http://connectorsdemo.azurewebsites.net/images/WIN12_Scene_01.jpg
        title: This is the image's alternate text
      - image: http://connectorsdemo.azurewebsites.net/images/WIN12_Anthony_02.jpg
        title: This is the image's alternate text
      actions:
      - "@type": ActionCard
        name: Comment
        inputs:
        - "@type": TextInput
          id: comment
          is_multiline: true
          title: Input's title property
        actions:
        - "@type": HttpPOST
          name: Save
          target: http://...
      - "@type": ActionCard
        name: Due Date
        inputs:
        - "@type": DateInput
          id: dueDate
          title: Input's title property
        actions:
        - "@type": HttpPOST
          name: Save
          target: http://...
      - "@type": HttpPOST
        name: Action's name prop.
        target: http://...
      - "@type": OpenUri
        name: Action's name prop
        targets:
        - os: default
          uri: http://...
    - start_group: true
      title: This is the title of a **second section**
      text: This second section is visually separated from the first one by setting its
        **startGroup** property to true.
"""

RETURN = """
"""

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.ec2 import snake_dict_to_camel_dict

OFFICE_365_CARD_CONTEXT = "http://schema.org/extensions"
OFFICE_365_CARD_TYPE = "MessageCard"
OFFICE_365_CARD_EMPTY_PAYLOAD_MSG = "Summary or Text is required."
OFFICE_365_INVALID_WEBHOOK_MSG = "The Incoming Webhook was not reachable."


def build_actions(actions):
    action_items = []

    for action in actions:
        action_item = snake_dict_to_camel_dict(action)
        action_items.append(action_item)

    return action_items


def build_sections(sections):
    sections_created = []

    for section in sections:
        sections_created.append(build_section(section))

    return sections_created


def build_section(section):
    section_payload = dict()

    if 'title' in section:
        section_payload['title'] = section['title']

    if 'start_group' in section:
        section_payload['startGroup'] = section['start_group']

    if 'activity_image' in section:
        section_payload['activityImage'] = section['activity_image']

    if 'activity_title' in section:
        section_payload['activityTitle'] = section['activity_title']

    if 'activity_subtitle' in section:
        section_payload['activitySubtitle'] = section['activity_subtitle']

    if 'activity_text' in section:
        section_payload['activityText'] = section['activity_text']

    if 'hero_image' in section:
        section_payload['heroImage'] = section['hero_image']

    if 'text' in section:
        section_payload['text'] = section['text']

    if 'facts' in section:
        section_payload['facts'] = section['facts']

    if 'images' in section:
        section_payload['images'] = section['images']

    if 'actions' in section:
        section_payload['potentialAction'] = build_actions(section['actions'])

    return section_payload


def build_payload_for_connector_card(module, summary=None, color=None, title=None, text=None, actions=None, sections=None):
    payload = dict()
    payload['@context'] = OFFICE_365_CARD_CONTEXT
    payload['@type'] = OFFICE_365_CARD_TYPE

    if summary is not None:
        payload['summary'] = summary

    if color is not None:
        payload['themeColor'] = color

    if title is not None:
        payload['title'] = title

    if text is not None:
        payload['text'] = text

    if actions:
        payload['potentialAction'] = build_actions(actions)

    if sections:
        payload['sections'] = build_sections(sections)

    payload = module.jsonify(payload)
    return payload


def do_notify_connector_card_webhook(module, webhook, payload):
    headers = {
        'Content-Type': 'application/json'
    }

    response, info = fetch_url(
        module=module,
        url=webhook,
        headers=headers,
        method='POST',
        data=payload
    )

    if info['status'] == 200:
        module.exit_json(changed=True)
    elif info['status'] == 400 and module.check_mode:
        if info['body'] == OFFICE_365_CARD_EMPTY_PAYLOAD_MSG:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg=OFFICE_365_INVALID_WEBHOOK_MSG)
    else:
        module.fail_json(
            msg="failed to send %s as a connector card to Incoming Webhook: %s"
                % (payload, info['msg'])
        )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            webhook=dict(required=True, no_log=True),
            summary=dict(type='str'),
            color=dict(type='str'),
            title=dict(type='str'),
            text=dict(type='str'),
            actions=dict(type='list'),
            sections=dict(type='list')
        ),
        supports_check_mode=True
    )

    webhook = module.params['webhook']
    summary = module.params['summary']
    color = module.params['color']
    title = module.params['title']
    text = module.params['text']
    actions = module.params['actions']
    sections = module.params['sections']

    payload = build_payload_for_connector_card(
        module,
        summary,
        color,
        title,
        text,
        actions,
        sections)

    if module.check_mode:
        # In check mode, send an empty payload to validate connection
        check_mode_payload = build_payload_for_connector_card(module)
        do_notify_connector_card_webhook(module, webhook, check_mode_payload)

    do_notify_connector_card_webhook(module, webhook, payload)


if __name__ == '__main__':
    main()
