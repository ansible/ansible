# -*- coding: utf-8 -*-
# Copyright (c) 2025, Felix Fontein <felix@fontein.de>, The Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations


DOCUMENTATION = r"""
name: broken
short_description: Test input precedence
author: Felix Fontein (@felixfontein)
description:
  - Test input precedence.
options:
  _terms:
    description:
      - Ignored.
    type: list
    elements: str
    required: true
  some_option:
    description:
      - The interesting part.
    type: str
    default: default value
    env:
      - name: PLAYGROUND_TEST_1
      - name: PLAYGROUND_TEST_2
    vars:
      - name: playground_test_1
      - name: playground_test_2
    ini:
      - key: playground_test_1
        section: playground
      - key: playground_test_2
        section: playground
"""

EXAMPLES = r"""#"""

RETURN = r"""
_list:
  description:
    - The value of O(some_option).
  type: list
  elements: str
"""

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        """Generate list."""
        self.set_options(var_options=variables, direct=kwargs)

        return [self.get_option("some_option"), *self.get_option_and_origin("some_option")]
