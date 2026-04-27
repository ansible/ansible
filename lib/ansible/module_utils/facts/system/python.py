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

from __future__ import annotations

import sys
import typing as t

from ansible.module_utils.facts.collector import BaseFactCollector

try:
    # Check if we have SSLContext support
    from ssl import create_default_context, SSLContext
    del create_default_context
    del SSLContext
    HAS_SSLCONTEXT = True
except ImportError:
    HAS_SSLCONTEXT = False


class PythonFactCollector(BaseFactCollector):
    name = 'python'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        python_facts = {}
        python_facts['python'] = {
            'version': {
                'major': sys.version_info[0],
                'minor': sys.version_info[1],
                'micro': sys.version_info[2],
                'releaselevel': sys.version_info[3],
                'serial': sys.version_info[4]
            },
            'version_info': list(sys.version_info),
            'executable': sys.executable,
            'has_sslcontext': HAS_SSLCONTEXT
        }

        try:
            python_facts['python']['type'] = sys.subversion[0]
        except AttributeError:
            try:
                python_facts['python']['type'] = sys.implementation.name
            except AttributeError:
                python_facts['python']['type'] = None

        return python_facts
