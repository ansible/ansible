# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Ansible, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard documentation fragment
    DOCUMENTATION = r'''
options:
  validate:
    description:
    - The validation command to run before copying into place.
    - The path to the file to validate is passed in via '%s' which must be present as in the examples below.
    - The command is passed securely so shell features like expansion and pipes will not work.
    type: str
'''
