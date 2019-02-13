#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_product_facts
short_description: Provides Windows product and license information
description:
- Provides Windows product and license information.
version_added: '2.5'
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Get product id and product key
  win_product_facts:
'''

RETURN = r'''
ansible_facts:
  description: Dictionary containing all the detailed information about the Windows product and license.
  returned: always
  type: complex
  contains:
    ansible_os_license_channel:
      description: The Windows license channel.
      returned: always
      type: str
      sample: Volume:MAK
      version_added: '2.8'
    ansible_os_license_edition:
      description: The Windows license edition.
      returned: always
      type: str
      sample: Windows(R) ServerStandard edition
      version_added: '2.8'
    ansible_os_license_status:
      description: The Windows license status.
      returned: always
      type: str
      sample: Licensed
      version_added: '2.8'
    ansible_os_product_id:
      description: The Windows product ID.
      returned: always
      type: str
      sample: 00326-10000-00000-AA698
    ansible_os_product_key:
      description: The Windows product key.
      returned: always
      type: str
      sample: T49TD-6VFBW-VV7HY-B2PXY-MY47H
'''
