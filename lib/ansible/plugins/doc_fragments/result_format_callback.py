# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
    options:
      result_format:
        name: Format of the task result
        description:
          - Define the task result format used in the callback output.
          - These formats do not cause the callback to emit valid JSON or YAML formats.
          - The output contains these formats interspersed with other non-machine parsable data.
          - C(yaml_lossy) will modify module responses in an attempt to produce a more human friendly output
            at the expense of correctness, and should not be relied upon to aid in writing variable manipulations
            or conditionals
        type: str
        default: json
        env:
          - name: ANSIBLE_CALLBACK_RESULT_FORMAT
        choices:
            - json
            - yaml
            - yaml_lossy
        version_added: '2.13'
'''
