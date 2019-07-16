# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Matthew Burtless <mburtless@ns1.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # NS1 doc fragment
    DOCUMENTATION = r'''
options:
  apiKey:
    description:
      - Unique client api key that can be created via the NS1 portal.
    type: str
    required: true

requirements:
  - python >= 2.7
  - ns1-python >= 0.9.19

seealso:
  - name: Documentation for NS1 API
    description: Complete reference for the NS1 API.
    link: https://ns1.com/api/
'''
