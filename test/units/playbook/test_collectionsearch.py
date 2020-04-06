# (c) 2020 Ansible Project
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat import unittest
from ansible.playbook.collectionsearch import CollectionSearch
from units.compat.mock import patch


class TestCollectionSearch(unittest.TestCase):

    @patch('ansible.utils.display.Display.display')
    def test_collection_static_warning(self, mock_display):
        '''
        Test that collection name is not templated and a warning message is
        generated for the referenced name.
        '''
        cs = CollectionSearch()
        self.assertIn(
            'foo.{{bar}}',
            cs._load_collections(None, ['foo.{{bar}}'])
        )
        self.assertEqual(mock_display.call_count, 1)
        self.assertIn(
            '[WARNING]: "collections" is not templatable, but we found: foo.{{bar}}',
            mock_display.call_args[0][0])
