# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import configparser
import glob
import json
import os
import stat
import typing as t

from io import StringIO

from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.facts.collector import BaseFactCollector


class LocalFactCollector(BaseFactCollector):
    name = 'local'
    _fact_ids = set()  # type: t.Set[str]

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
            failed = None
            try:
                executable_fact = stat.S_IXUSR & os.stat(fn)[stat.ST_MODE]
            except OSError as e:
                failed = 'Could not stat fact (%s): %s' % (fn, to_text(e))
                local[fact_base] = failed
                module.warn(failed)
                continue
            if executable_fact:
                try:
                    # run it
                    rc, out, err = module.run_command(fn)
                    if rc != 0:
                        failed = 'Failure executing fact script (%s), rc: %s, err: %s' % (fn, rc, err)
                except OSError as e:
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
                    cp.read_file(StringIO(out))
                except configparser.Error:
                    fact = f"error loading facts as JSON or ini - please check content: {fn}"
                    module.warn(fact)
                else:
                    fact = {}
                    for sect in cp.sections():
                        if sect not in fact:
                            fact[sect] = {}
                        for opt in cp.options(sect):
                            try:
                                val = cp.get(sect, opt)
                            except configparser.Error as ex:
                                fact = f"error loading facts as ini - please check content: {fn} ({ex})"
                                module.warn(fact)
                                continue
                            else:
                                fact[sect][opt] = val
            except Exception as e:
                fact = "Failed to convert (%s) to JSON: %s" % (fn, to_text(e))
                module.warn(fact)

            local[fact_base] = fact

        local_facts['local'] = local
        return local_facts
