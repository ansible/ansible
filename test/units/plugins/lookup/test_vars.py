#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.plugins.lookup.vars import LookupModule
from ansible._internal._templating._engine import TemplateEngine
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible.errors import AnsibleUndefinedVariable


class TestVarsLookupPlugin:
    """Test the vars lookup plugin, particularly the fix for select('defined') issue"""

    def test_vars_lookup_with_select_defined(self):
        """
        Test that vars lookup doesn't re-template select('defined') results.
        
        This addresses the bug where:
        1. A variable uses select('defined') to filter out undefined variables
        2. The vars lookup plugin retrieves this variable
        3. The plugin re-templates the result, causing undefined variable errors
        
        See: https://github.com/ansible/ansible/issues/XXXXX
        """
        # Set up the scenario from the bug report
        variables = {
            'var1': 'foo',
            # var2 is intentionally undefined
        }

        # Create templar with variables (use available_variables API)
        templar = TemplateEngine(variables=variables)

        # First, template the select('defined') expression
        # This should work and filter out undefined var2
        template_expr = "{{ [var1, var2] | select('defined') }}"
        defined_vals_result = templar.template(TrustedAsTemplate().tag(template_expr))

        # The result should be ['foo'] (var2 filtered out)
        assert defined_vals_result == ['foo']

        # Add the result to variables (simulating what happens in a playbook)
        variables['defined_vals'] = defined_vals_result
        templar.available_variables = variables

        # Now test the vars lookup - this should NOT re-template the result
        lookup = LookupModule()
        lookup._templar = templar

        # This should work without throwing AnsibleUndefinedVariable
        result = lookup.run(['defined_vals'], variables)

        # Verify the result is correct
        assert result == [['foo']]
        assert len(result) == 1
        assert result[0] == ['foo']
    
    def test_vars_lookup_still_templates_strings(self):
        """Test that the vars lookup still templates string values that need templating"""
        variables = {
            'var1': 'world',
            'template_string': 'Hello {{ var1 }}!',
        }

        templar = TemplateEngine(variables=variables)

        lookup = LookupModule()
        lookup._templar = templar

        result = lookup.run(['template_string'], variables)

        # The template string should be templated
        assert result == ['Hello world!']
    
    def test_vars_lookup_with_non_string_values(self):
        """Test that non-string values are returned as-is"""
        variables = {
            'list_val': ['item1', 'item2'],
            'dict_val': {'key': 'value'},
            'int_val': 42,
            'bool_val': True,
            'none_val': None,
        }

        templar = TemplateEngine(variables=variables)

        lookup = LookupModule()
        lookup._templar = templar

        for var_name, expected in variables.items():
            result = lookup.run([var_name], variables)
            assert result == [expected], f"Failed for {var_name}: got {result}, expected {[expected]}"
    
    def test_vars_lookup_with_plain_strings(self):
        """Test that plain strings without template syntax are not re-templated"""
        variables = {
            'plain_string': 'just a plain string',
            'string_with_braces': 'not a {template} at all',
        }

        templar = TemplateEngine(variables=variables)

        lookup = LookupModule()
        lookup._templar = templar

        for var_name, expected in variables.items():
            result = lookup.run([var_name], variables)
            assert result == [expected], f"Failed for {var_name}: got {result}, expected {[expected]}"


if __name__ == '__main__':
    # Simple test runner for standalone execution
    test_class = TestVarsLookupPlugin()
    
    try:
        print("Running vars lookup plugin tests...")
        
        print("1. Testing select('defined') scenario...")
        test_class.test_vars_lookup_with_select_defined()
        print("   ✓ PASSED")
        
        print("2. Testing template strings...")
        test_class.test_vars_lookup_still_templates_strings()
        print("   ✓ PASSED")
        
        print("3. Testing non-string values...")
        test_class.test_vars_lookup_with_non_string_values()
        print("   ✓ PASSED")
        
        print("4. Testing plain strings...")
        test_class.test_vars_lookup_with_plain_strings()
        print("   ✓ PASSED")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
