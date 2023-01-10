# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Ansible, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):
    # Standard documentation fragment
    DOCUMENTATION = r'''
options:
  validate:
    description:
    - The validation command to run before copying the updated file into the final destination.
    - A temporary file path is used to validate, passed in through '%s' which must be present as in the examples below.
    - Also, the command is passed securely so shell features such as expansion and pipes will not work.
    - For an example on how to handle more complex validation than what this
      option provides, see R(handling complex validation,complex_configuration_validation).
    type: str
'''
