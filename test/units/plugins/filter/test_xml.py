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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import pytest

from ansible.plugins.filter.xml import xml_findall, xml_findtext
from ansible.errors import AnsibleFilterError

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'network')

invalid_xml = "<root><c1><c2></c2></root>"

with open(os.path.join(fixture_path, 'show_vlans_xml_output.txt')) as f:
    output_xml = f.read()


def test_xml_filter_find():
    expected = [
        '<vlan><name>test-1</name><vlan-id>100</vlan-id></vlan>',
        '<vlan><name>test-2</name></vlan>',
        '<vlan><name>test-3</name><vlan-id>300</vlan-id><description>test vlan-3</description>'
        '<interface><name>em3.0</name></interface></vlan>',
        '<vlan inactive="inactive"><name>test-4</name><description>test vlan-4</description>'
        '<vlan-id>400</vlan-id></vlan>',
        '<vlan inactive="inactive"><name>test-5</name><description>test vlan-5</description>'
        '<vlan-id>500</vlan-id><interface><name>em5.0</name></interface></vlan>'
    ]
    parsed = xml_findall(output_xml, ".//vlan")
    assert parsed == expected


def test_xml_filter_findall_not_found():
    parsed = xml_findall(output_xml, ".//foobar")
    assert parsed == []


def test_xml_filter_findall_invalid():
    with pytest.raises(AnsibleFilterError):
        xml_findall(invalid_xml, ".//vlan")


def test_xml_filter_findtext():
    parsed = xml_findtext(output_xml, ".//vlan[name='test-1']/vlan-id")
    assert parsed == "100"


def test_xml_filter_findtext_not_found():
    parsed = xml_findtext(output_xml, ".//vlan[name='test-99']/vlan-id")
    assert parsed == ""


def test_xml_filter_findtext_invalid():
    with pytest.raises(AnsibleFilterError):
        xml_findtext(invalid_xml, ".//vlan[name='test-1']/vlan-id")
