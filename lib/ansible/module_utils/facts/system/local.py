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
            # Decide if it is runnable or readable
            fact_base = os.path.basename(fn).replace('.fact', '')
            userown = None
            userrun = None
            userread = None
            groupown = None
            # Check only if anybody can run the fact file
            if stat.S_IXOTH & os.stat(fn)[stat.ST_MODE]:
                userrun = True
            # If it is not run all, check if user|group has rights
            else:
                if os.getuid() == os.stat(fn)[stat.ST_UID]:
                    userown = True
                if os.stat(fn)[stat.ST_GID] in os.getgroups():
                    groupown = True
                if userown and stat.S_IXUSR & os.stat(fn)[stat.ST_MODE]:
                    userrun = True
                elif groupown and stat.S_IXGRP & os.stat(fn)[stat.ST_MODE]:
                    userrun = True
                else:
                    if stat.S_IROTH & os.stat(fn)[stat.ST_MODE]:
                        userread = True
                    elif userown and stat.S_IRUSR & os.stat(fn)[stat.ST_MODE]:
                        userread = True
                    elif groupown and stat.S_IRGRP & os.stat(fn)[stat.ST_MODE]:
                        userread = True
            # If user, group or other can run, run
            if userrun:
                # run it
                # try to read it as json first
                # if that fails read it with ConfigParser
                # if that fails, skip it
                try:
                    rc, out, err = module.run_command(fn)
                # If there is error, call warn module
                except UnicodeError:
                    fact = 'error loading fact - output of running %s was not utf-8' % fn
                    local[fact_base] = fact
                    local_facts['local'] = local
                    module.warn(fact)
                    return local_facts
            # If it is eradable, get_file to parse
            elif userread:
                out = get_file_content(fn, default='')
            # If not return run_error and warn
            else:
                out = '{"run_error": "some local facts are not readable by running user"}'
                module.warn(out)
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
                    # Warn parse error
                    module.warn(fact)
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
