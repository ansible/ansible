from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pkg_resources

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        return ['ok']
