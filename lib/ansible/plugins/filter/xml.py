# (c) 2017, Christian Giese (@GIC-de)
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

from ansible.errors import AnsibleError
from lxml import etree

parser = etree.XMLParser(remove_blank_text=True)


def xml_findtext(data, expr):
    try:
        xml = etree.XML(data, parser=parser)
        result = xml.findtext(expr)
    except Exception as ex:
        raise AnsibleError('xml error: ' + str(ex))
    return result


class FilterModule(object):
    """XPATH Filter"""
    def filters(self):
        return {
            'xml_findtext': xml_findtext
        }
