# -*- coding: utf-8 -*-
# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import unittest

import pytest


@pytest.mark.usefixtures("stdin")
class TestOtherFilesystem(unittest.TestCase):
    def test_human_to_bytes(self):
        from ansible.module_utils import basic

        am = basic.AnsibleModule(
            argument_spec=dict(),
        )

        self.assertEqual(am.human_to_bytes("4KB"), 4096)
        self.assertEqual(am.human_to_bytes("4KB", False), 4096)
        self.assertEqual(am.human_to_bytes("4KB", isbits=False), 4096)
        with pytest.raises(ValueError):
            am.human_to_bytes("4Kb", isbits=False)
        self.assertEqual(am.human_to_bytes("4Kb", True), 4096)
        self.assertEqual(am.human_to_bytes("4Kb", isbits=True), 4096)
        with pytest.raises(ValueError):
            am.human_to_bytes("4KB", isbits=True)
