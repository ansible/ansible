#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_rabbitmq_plugin
short_description: Adds or removes plugins to RabbitMQ.
description:
  - Enables or disables RabbitMQ plugins.
version_added: "2.4"
author: '"Artem Zinenko (@ar7z1)"'
options:
  names:
    description:
      - Comma-separated list of plugin names.
    required: true
    default: null
    aliases: [name]
  new_only:
    description:
      - Only enable missing plugins.
      - Does not disable plugins that are not in the names list.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  state:
    description:
      - Specify if plugins are to be enabled or disabled.
    required: false
    default: enabled
    choices: [enabled, disabled]
  prefix:
    description:
      - Specify a custom install prefix to a Rabbit.
    required: false
    default: null
'''

EXAMPLES = r'''
# Enables the rabbitmq_management plugin
- win_rabbitmq_plugin:
    names: rabbitmq_management
    state: enabled
'''

RETURN = r'''
# Default return values
'''
