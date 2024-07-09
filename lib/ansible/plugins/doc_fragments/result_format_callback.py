# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
    options:
      result_format:
        name: Format of the task result
        description:
          - Define the task result format used in the callback output.
          - These formats do not cause the callback to emit valid JSON or YAML formats.
          - The output contains these formats interspersed with other non-machine parsable data.
        type: str
        default: json
        env:
          - name: ANSIBLE_CALLBACK_RESULT_FORMAT
        ini:
          - key: callback_result_format
            section: defaults
        choices:
            - json
            - yaml
        version_added: '2.13'
      pretty_results:
        name: Configure output for readability
        description:
          - Configure the result format to be more readable.
          - When O(result_format) is set to V(yaml) this option defaults to V(true), and defaults
            to V(false) when configured to V(json).
          - Setting this option to V(true) will force V(json) and V(yaml) results to always be pretty
            printed regardless of verbosity.
          - When set to V(true) and used with the V(yaml) result format, this option will
            modify module responses in an attempt to produce a more human friendly output at the expense
            of correctness, and should not be relied upon to aid in writing variable manipulations
            or conditionals. For correctness, set this option to V(false) or set O(result_format) to V(json).
        type: bool
        default: null
        env:
          - name: ANSIBLE_CALLBACK_FORMAT_PRETTY
        ini:
          - key: callback_format_pretty
            section: defaults
        version_added: '2.13'
'''
