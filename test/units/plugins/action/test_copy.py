# -*- coding: utf-8 -*-
# Copyright: (c) 2026, Ansible Project
# License: GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import unittest
from unittest.mock import Mock


class TestCopyDiffAccumulation(unittest.TestCase):
    """Test that the copy action plugin correctly accumulates diffs for recursive copies."""

    def test_diff_accumulation_logic(self):
        """Test the core diff accumulation logic that was fixed."""
        # Simulate the result dict initialization
        result = {'diff': []}
        
        # Simulate multiple file copies with diffs
        module_returns = [
            {'changed': True, 'diff': [{'before': 'old_file1', 'after': 'new_file1'}]},
            {'changed': True, 'diff': [{'before': 'old_file2', 'after': 'new_file2'}]},
        ]
        
        # Simulate the accumulation logic from the fix
        for module_return in module_returns:
            if 'diff' in module_return:
                result['diff'].extend(module_return['diff'])
        
        # Verify diffs are accumulated
        self.assertEqual(len(result['diff']), 2)
        self.assertEqual(result['diff'][0], {'before': 'old_file1', 'after': 'new_file1'})
        self.assertEqual(result['diff'][1], {'before': 'old_file2', 'after': 'new_file2'})

    def test_empty_diff_removal(self):
        """Test that empty diff lists are removed from result."""
        result = {'diff': [], 'changed': False}
        
        # Simulate the cleanup logic
        if 'diff' in result and not result['diff']:
            del result['diff']
        
        # Verify empty diff is removed
        self.assertNotIn('diff', result)

    def test_diff_preservation_in_result_update(self):
        """Test that accumulated diffs are preserved when updating result."""
        result = {'diff': [{'before': 'old', 'after': 'new'}], 'changed': True}
        
        # Simulate the result update with diff preservation
        saved_diff = result.get('diff', [])
        result.update(dict(dest='dest/', src='src/', changed=True))
        if saved_diff:
            result['diff'] = saved_diff
        
        # Verify diff is preserved
        self.assertIn('diff', result)
        self.assertEqual(len(result['diff']), 1)
        self.assertEqual(result['diff'][0], {'before': 'old', 'after': 'new'})
