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

from ansible import utils
import urllib2

from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError
from ansible.utils.unicode import to_unicode

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        if isinstance(terms, basestring):
            terms = [ terms ]

        validate_certs = kwargs.get('validate_certs', True)

        ret = []
        for term in terms:
            try:
                response = open_url(term, validate_certs=validate_certs)
            except urllib2.URLError as e:
                utils.warning("Failed lookup url for %s : %s" % (term, str(e)))
                continue
            except urllib2.HTTPError as e:
                utils.warning("Received HTTP error for %s : %s" % (term, str(e)))
                continue
            except SSLValidationError as e:
                utils.warning("Error validating the server's certificate for %s: %s" % (term, str(e)))
                continue
            except ConnectionError as e:
                utils.warning("Error connecting to %s: %s" % (term, str(e)))
                continue

            for line in response.read().splitlines():
                ret.append(to_unicode(line))
        return ret
