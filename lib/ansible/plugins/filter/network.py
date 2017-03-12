#
# {c) 2017 Red Hat, Inc.
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import urllib2
import urlparse

try:
    import textfsm
    HAS_TEXTFSM = True
except ImportError:
    HAS_TEXTFSM = False

from ansible.module_utils.six import StringIO
from ansible.module_utils.netcfg import NetworkConfig, dumps
from ansible.errors import AnsibleError

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

NETWORK_OS = {
    'ios': 1,
    'iosxr': 1,
    'nxos': 2,
    'eos': 4
}

def diff_network_config(value, base, network_os=None, indent=1, match='line', replace='line'):

    assert match in ('line', 'strict', 'exact', 'none')
    assert replace in ('line', 'block')
    assert network_os in NETWORK_OS.keys()

    if network_os:
        indent = NETWORK_OS.get(network_os, indent)

    candidate = NetworkConfig(indent=indent, contents=value)
    base_config = NetworkConfig(indent=indent, contents=base)

    objs = candidate.difference(base_config, match=match, replace=replace)
    commands = dumps(objs, 'commands')

    return commands

def parse_cli(value, template):
    if not HAS_TEXTFSM:
        raise AnsibleError('parse_cli filter requires TextFSM library to be installed')

    url = urlparse.urlparse(template)
    if url.scheme.startswith('http'):
        try:
            handler = {}
            if 'HTTP_PROXY' in os.environ:
                handler['http'] = '127.0.0.1'
            if 'HTTPS_PROXY' in os.environ:
                handler['https'] = '127.0.0.1'
            if handler:
                opener = urllib2.build_opener(urllib2.ProxyHandler(handler))
                urllib2.install_opener(opener)
            resp = urllib2.urlopen(template)
        except urllib2.HTTPError as exc:
            raise AnsibleError(str(exc))
        data = StringIO()
        data.write(resp.read())
        data.seek(0)
        template = data
    else:
        if not os.path.exists(template):
            raise AnsibleError('unable to locate parse_cli template: %s' % template)
        try:
            template = open(template)
        except IOError as exc:
            raise AnsibleError(str(exc))
    re_table = textfsm.TextFSM(template)
    fsm_results = re_table.ParseText(value)
    results = list()
    for item in fsm_results:
        results.append(dict(zip(re_table.header, item)))
    return results

class FilterModule(object):
    """Filters for working with output from network devices"""

    filter_map =  {
        'parse_cli': parse_cli,
        'diff_network_config': diff_network_config
    }

    def filters(self):
        return self.filter_map
