# (c) 2015, Brian Coca <bcoca@ansible.com>
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

import urllib2

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError
from ansible.utils.unicode import to_unicode

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        validate_certs = kwargs.get('validate_certs', True)

        ret = []
        for term in terms:
            display.vvvv("url lookup connecting to %s" % term)
            try:
                response = open_url(term, validate_certs=validate_certs)
            except urllib2.HTTPError as e:
                raise AnsibleError("Received HTTP error for %s : %s" % (term, str(e)))
            except urllib2.URLError as e:
                raise AnsibleError("Failed lookup url for %s : %s" % (term, str(e)))
            except SSLValidationError as e:
                raise AnsibleError("Error validating the server's certificate for %s: %s" % (term, str(e)))
            except ConnectionError as e:
                raise AnsibleError("Error connecting to %s: %s" % (term, str(e)))

            for line in response.read().splitlines():
                ret.append(to_unicode(line))
        return ret
