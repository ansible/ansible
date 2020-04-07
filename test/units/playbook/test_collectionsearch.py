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

import pytest


def test_collection_static_warning(capsys):
    """Test that collection name is not templated.

    Also, make sure that users see the warning message for the referenced name.
    """

    collection_name = 'foo.{{bar}}'
    cs = CollectionSearch()
    assert collection_name in cs._load_collections(None, [collection_name])

    std_out, std_err = capsys.readouterr()
    assert '[WARNING]: "collections" is not templatable, but we found: %s' % collection_name in std_err
    assert '' == std_out
