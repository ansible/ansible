#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers (dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: win_product_facts
short_description: Provides Windows product information (product id, product key)
description:
- Provides Windows product information.
version_added: '2.5'
author:
- Dag Wieers (@dagwieers)
options: {}
'''

EXAMPLES = r'''
- name: Get product id and product key
  win_product_facts:
'''

RETURN = '''
ansible_facts:
  description: returned facts by this module
  returned: always
  type: dictionary
  sample:
    ansible_os_product_id: 00326-10000-00000-AA698
    ansible_os_product_key: T49TD-6VFBW-VV7HY-B2PXY-MY47H
'''
