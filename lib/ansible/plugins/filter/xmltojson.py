# (c) 2019, Nicholas Long <long.nicholas.480@gmail.com>
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

from ansible.errors import AnsibleError, AnsibleFilterError
from ansible.module_utils._text import to_native
import json

try:
    import xmltodict
except ImportError:
    raise AnsibleError(
        'You need to install "xmltodict" prior to running '
        'xmltojson filter.'
    )

def xmltojson(data):
    """ Converts an XML string to a JSON string. """

    try:
        return json.dumps(xmltodict.parse(data))
    except Exception as e:
        raise AnsibleFilterError(
            'Error in xmltojson filter plugin:%s' % to_native(e)
        )


class FilterModule(object):
    """ XML to JSON filter. """

    def filters(self):
        return {'xmltojson': xmltojson}
