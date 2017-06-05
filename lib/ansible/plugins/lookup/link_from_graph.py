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

import json
import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.unicode import to_unicode

from pydot import graph_from_dot_file

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        basedir = self.get_basedir(variables)
        for term in terms:
            params = term.split()
            paramvals = {
                'hostname' : 's-switch-1',
                'graph'    : 'graph.dot',
                'link'     : 'Ethernet1/1',
            }
           
            try:
                for param in params:
                    name, value = param.split('=')
                    assert(name in paramvals)
                    paramvals[name] = value
            except (ValueError, AssertionError) as e:
                display.v(e)
                raise AnsibleError(e)
            path = self._loader.path_dwim_relative(basedir, 'files', paramvals['graph'])
            display.v("Loading dot file: " + path)
            
            g = graph_from_dot_file(path)
            edges = g.get_edges()
            addr = None
            display.v("Looking for :%s %s" % (paramvals['hostname'], paramvals['link']))
            for edge in edges:
                edge_attrib = json.loads(edge.get('label').strip('"').replace("'", "\""))
                src_link = edge_attrib['srcLink']
                # Local links don't have dst, ignore
                try:
                    dst_link = edge_attrib['dstLink']
                except:
                    dst_link = ""
                    pass
                display.vvvv("source: " + str(edge.get_source()).lower().strip('"'))
                display.vvvv("destination: " + str(edge.get_destination()).lower().strip('"'))
                display.vvvv(paramvals['hostname'])
                display.vvvv("sl: " + src_link)
                display.vvvv("dl: " + dst_link)
                display.vvvv("link: " + paramvals['link'])
                # Boilerplate :(
                if paramvals['hostname'].lower() == str(edge.get_source()).lower().strip('"'):
                    if paramvals['link'].lower().strip() == src_link.lower().strip():
                        display.vvv("found: " + paramvals['hostname'])
                        display.vvv("link: " + paramvals['link'])
                        display.vvv("edge_id: " + edge.get('id'))
                        addr = edge.get('id').strip('"')
                        break
                if paramvals['hostname'].lower() == str(edge.get_destination()).lower().strip('"'):
                    if paramvals['link'].lower().strip() == dst_link.lower().strip():
                        display.vvv("found: " + paramvals['hostname'])
                        display.vvv("link: " + paramvals['link'])
                        display.vvv("edge_id: " + edge.get('id'))
                        addr = edge.get('id').strip('"')
                        break
            if addr is None:
                raise AnsibleError("Could not find address for link %s" % paramvals['link'])

        return [{"name": paramvals['link'], "subnet": addr}]
