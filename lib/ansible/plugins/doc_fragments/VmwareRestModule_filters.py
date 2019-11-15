# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Paul Knight <paul.knight@delaware.gov>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    # Parameters for VMware ReST HTTPAPI modules includes filters
    DOCUMENTATION = r'''
options:
    allow_multiples:
      description:
      - Indicates whether get_id() can return multiple IDs for a given name.
      - Typically, this should be false when updating or deleting; otherwise, all named objects could be affected.
      required: true
      version_added: "2.10"
      type: bool
    filters:
      description:
      - The key/value pairs describing filters to be applied to the request(s) made by this instance.
      required: false
      version_added: "2.10"
      type: dict
    log_level:
      description:
      - If ANSIBLE_DEBUG is set, this will be forced to 'debug', but can be user-defined otherwise.
      required: True
      choices: ['debug', 'info', 'normal']
      version_added: "2.10"
      type: str
      default: 'normal'
    status_code:
      description:
      - A list of integer status codes considered to be successful for the this module.
      required: true
      version_added: "2.10"
      type: list
      default: [200]
'''
