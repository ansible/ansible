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

import glob
import json
import os
import stat

from ansible.module_utils.six.moves import configparser
from ansible.module_utils.six.moves import StringIO

from ansible.module_utils.facts.utils import get_file_content

from ansible.module_utils.facts.collector import BaseFactCollector


class LocalFactCollector(BaseFactCollector):
    name = 'local'
    _fact_ids = set()

    def collect(self, module=None, collected_facts=None):
        local_facts = {}
        local_facts['local'] = {}

        if not module:
            return local_facts

        fact_path = module.params.get('fact_path', None)

        if not fact_path or not os.path.exists(fact_path):
            return local_facts

        local = {}
        for fn in sorted(glob.glob(fact_path + '/*.fact')):
            # where it will sit under local facts
            fact_base = os.path.basename(fn).replace('.fact', '')
            if stat.S_IXUSR & os.stat(fn)[stat.ST_MODE]:
                # run it
                # try to read it as json first
                # if that fails read it with ConfigParser
                # if that fails, skip it
                try:
                    rc, out, err = module.run_command(fn)
                except UnicodeError:
                    fact = 'error loading fact - output of running %s was not utf-8' % fn
                    local[fact_base] = fact
                    local_facts['local'] = local
                    return local_facts
            else:
                out = get_file_content(fn, default='')

            # load raw json
            fact = 'loading %s' % fact_base
            try:
                fact = json.loads(out)
            except ValueError:
                # load raw ini
                cp = configparser.ConfigParser()
                try:
                    cp.readfp(StringIO(out))
                except configparser.Error:
                    fact = "error loading fact - please check content"
                else:
                    fact = {}
                    for sect in cp.sections():
                        if sect not in fact:
                            fact[sect] = {}
                        for opt in cp.options(sect):
                            val = cp.get(sect, opt)
                            fact[sect][opt] = val

            local[fact_base] = fact

        local_facts['local'] = local
        return local_facts
