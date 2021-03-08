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

from ansible.module_utils._text import to_text
from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.facts.collector import BaseFactCollector
from ansible.module_utils.six.moves import configparser, StringIO


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
        # go over .fact files, run executables, read rest, skip bad with warning and note
        for fn in sorted(glob.glob(fact_path + '/*.fact')):
            # use filename for key where it will sit under local facts
            fact_base = os.path.basename(fn).replace('.fact', '')
            if stat.S_IXUSR & os.stat(fn)[stat.ST_MODE]:
                failed = None
                try:
                    # run it
                    rc, out, err = module.run_command(fn)
                    if rc != 0:
                        failed = 'Failure executing fact script (%s), rc: %s, err: %s' % (fn, rc, err)
                except (IOError, OSError) as e:
                    failed = 'Could not execute fact script (%s): %s' % (fn, to_text(e))

                if failed is not None:
                    local[fact_base] = failed
                    module.warn(failed)
                    continue
            else:
                # ignores exceptions and returns empty
                out = get_file_content(fn, default='')

            try:
                # ensure we have unicode
                out = to_text(out, errors='surrogate_or_strict')
            except UnicodeError:
                fact = 'error loading fact - output of running "%s" was not utf-8' % fn
                local[fact_base] = fact
                module.warn(fact)
                continue

            # try to read it as json first
            try:
                fact = json.loads(out)
            except ValueError:
                # if that fails read it with ConfigParser
                cp = configparser.ConfigParser()
                try:
                    cp.readfp(StringIO(out))
                except configparser.Error:
                    fact = "error loading facts as JSON or ini - please check content: %s" % fn
                    module.warn(fact)
                else:
                    fact = {}
                    for sect in cp.sections():
                        if sect not in fact:
                            fact[sect] = {}
                        for opt in cp.options(sect):
                            val = cp.get(sect, opt)
                            fact[sect][opt] = val
            except Exception as e:
                fact = "Failed to convert (%s) to JSON: %s" % (fn, to_text(e))
                module.warn(fact)

            local[fact_base] = fact

        local_facts['local'] = local
        return local_facts
