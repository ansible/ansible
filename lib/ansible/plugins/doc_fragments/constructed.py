# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


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
'''
