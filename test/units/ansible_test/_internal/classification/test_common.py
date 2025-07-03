"""Unit test for resolve_csharp_ps_util function in classification/common.py"""
import unittest
from unittest.mock import Mock, patch

from ansible_test._internal.classification.common import resolve_csharp_ps_util


class TestResolveCSharpPsUtil(unittest.TestCase):
    
    @patch('ansible_test._internal.classification.common.data_context')
    def test_relative_import_converts_to_ansible_collection_path(self, mock_data_context):
        # Setup mock
        mock_content = Mock()
        mock_content.is_ansible = False  
        mock_content.prefix = 'community.windows.'  
        mock_data_context.return_value.content = mock_content
        
        # Test: relative import '.util' from a module in 'plugins/modules/'
        import_name = '.util'
        path = 'plugins/modules/win_feature.py'
        
        # Call the function
        result = resolve_csharp_ps_util(import_name, path)
        
        expected = 'ansible_collections.community.windows.plugins.modules.util'
        
        self.assertEqual(result, expected)
        
        # Verify data_context was called 
        self.assertEqual(mock_data_context.call_count, 2)


if __name__ == '__main__':
    unittest.main()