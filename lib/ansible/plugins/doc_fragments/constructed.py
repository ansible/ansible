# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  strict:
    description:
        - If C(yes) make invalid entries a fatal error, otherwise skip and continue.
        - Since it is possible to use facts in the expressions they might not always be available
          and we ignore those errors by default.
    type: bool
    default: no
  compose:
    description: Create vars from jinja2 expressions.
    type: dict
    default: {}
  groups:
    description: Add hosts to group based on Jinja2 conditionals.
    type: dict
    default: {}
  keyed_groups:
    description: Add hosts to group based on the values of a variable.
    type: list
    default: []
    elements: dict
    suboptions:
      parent_group:
        type: str
        description: parent group for keyed group
      prefix:
        type: str
        description: A keyed group name will start with this prefix
        default: ''
      separator:
        type: str
        description: separator used to build the keyed group name
        default: "_"
      key:
        type: str
        description:
        - The key from input dictionary used to generate groups
      default_value:
        description:
        - The default value when the host variable's value is an empty string.
        - This option is mutually exclusive with C(trailing_separator).
        type: str
        version_added: '2.12'
      trailing_separator:
        description:
        - Set this option to I(False) to omit the C(separator) after the host variable when the value is an empty string.
        - This option is mutually exclusive with C(default_value).
        type: bool
        default: True
        version_added: '2.12'
  use_extra_vars:
    version_added: '2.11'
    description: Merge extra vars into the available variables for composition (highest precedence).
    type: bool
    default: False
    ini:
      - section: inventory_plugins
        key: use_extra_vars
    env:
      - name: ANSIBLE_INVENTORY_USE_EXTRA_VARS
  leading_separator:
    description:
      - Use in conjunction with keyed_groups.
      - By default, a keyed group that does not have a prefix or a separator provided will have a name that starts with an underscore.
      - This is because the default prefix is "" and the default separator is "_".
      - Set this option to False to omit the leading underscore (or other separator) if no prefix is given.
      - If the group name is derived from a mapping the separator is still used to concatenate the items.
      - To not use a separator in the group name at all, set the separator for the keyed group to an empty string instead.
    type: boolean
    default: True
    version_added: '2.11'
'''
