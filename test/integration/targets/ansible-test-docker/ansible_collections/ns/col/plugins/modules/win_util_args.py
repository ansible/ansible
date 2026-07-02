#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r"""
---
module: win_util_args
short_description: Short description
description:
- Some test description for the module
options:
  my_opt:
    description:
    - Test description
    required: yes
    type: str
extends_documentation_fragment:
- ns.col.ps_util

author:
- Ansible Test (@ansible)
"""

EXAMPLES = r"""
- win_util_args:
    option1: test
    my_opt: test
"""

RETURN = r"""
#
"""
