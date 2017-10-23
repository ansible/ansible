# Copyright: (c) 2017, Christian Giese (@GIC-de)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError

try:
    from lxml import etree
    parser = etree.XMLParser(remove_blank_text=True)
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


def xml_findtext(data, expr):
    if not HAS_LXML:
        raise AnsibleError('The lxml module is required but does not appear to be installed.')
    else:
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
