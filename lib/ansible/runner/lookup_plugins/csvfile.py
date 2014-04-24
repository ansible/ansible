# (c) 2013, Jan-Piet Mens <jpmens(at)gmail.com>
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

from ansible import utils, errors
import os
import codecs
import csv

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def read_csv(self, filename, key, delimiter, dflt=None, col=1):

        try:
            f = codecs.open(filename, 'r', encoding='utf-8')
            creader = csv.reader(f, delimiter=delimiter)

            for row in creader:
                if row[0] == key:
                    return row[int(col)]
        except Exception, e:
            raise errors.AnsibleError("csvfile: %s" % str(e))

        return dflt

    def run(self, terms, inject=None, **kwargs):

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        if isinstance(terms, basestring):
            terms = [ terms ]

        ret = []
        for term in terms:
            params = term.split()
            key = params[0]

            paramvals = {
                'file' : 'ansible.csv',
                'default' : None,
                'delimiter' : "TAB",
                'col' : "1",          # column to return
            }

            # parameters specified?
            try:
                for param in params[1:]:
                    name, value = param.split('=')
                    assert(name in paramvals)
                    paramvals[name] = value
            except (ValueError, AssertionError), e:
                raise errors.AnsibleError(e)

            if paramvals['delimiter'] == 'TAB':
                paramvals['delimiter'] = "\t"

            path = utils.path_dwim(self.basedir, paramvals['file'])

            var = self.read_csv(path, key, paramvals['delimiter'], paramvals['default'], paramvals['col'])
            if var is not None:
                if type(var) is list:
                    for v in var:
                        ret.append(v)
                else:
                    ret.append(var)
        return ret
