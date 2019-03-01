# make a lookup that queries the process table and gets the pid for a
# process based on an input string

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
lookup: foo
description: lookup some stuff from the proc table
options:
  _proc_name:
    description: procs to be looked up
    required: true
"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
import psutil


class LookupModule(LookupBase):

    def run(self, lookup_procs, **kwargs):
        # lookups in general are expected to both take a list as input
        # and output a list
        # this is done so they work with the looping construct 'with_'.
        ret = []
        for proc_name in lookup_procs:
            psitems = [i.as_dict(attrs=['pid', 'name']) for i in psutil.process_iter()]
            for proc in psitems:
                try:
                    if proc['name'] == proc_name:
                        ret.append(proc['pid'])
                except AnsibleParserError:
                    raise AnsibleParserError()
        return ret
