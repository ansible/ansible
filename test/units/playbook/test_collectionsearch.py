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

from ansible.playbook.collectionsearch import CollectionSearch
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils.display import Display
from units.compat.mock import MagicMock


def test_collection_static_warning(monkeypatch):
    mock_display = MagicMock()
    monkeypatch.setattr(Display, 'display', mock_display)

    collection_name = 'foo.{{bar}}'
    cs = CollectionSearch()
    assert collection_name in cs._load_collections(None, [collection_name])

    assert mock_display.call_count == 1
    actual_warn = ' '.join(mock_display.mock_calls[0][1][0].split('\n'))
    expected_warn = '"collections" is not templatable, but we found: %s' \
        % to_text(collection_name)
    assert expected_warn in actual_warn
