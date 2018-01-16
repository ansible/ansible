# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    DOCUMENTATION = """
options:
  strict:
    description:
        - If true make invalid entries a fatal error, otherwise skip and continue
        - Since it is possible to use facts in the expressions they might not always be available
          and we ignore those errors by default.
    type: boolean
    default: False
  compose:
    description: create vars from jinja2 expressions
    type: dictionary
    default: {}
  groups:
    description: add hosts to group based on Jinja2 conditionals
    type: dictionary
    default: {}
  keyed_groups:
    description: add hosts to group based on the values of a variable
    type: list
    default: []
"""
