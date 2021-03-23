# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r'''
options:
    testcol2option:
        description:
            - A plugin option taken from testcol2
        type: str
        version_added: 1.0.0
        ini:
            - key: foo
              section: bar
              version_added: 1.1.0
              deprecated:
                alternative: none
                why: Test deprecation
                version: '3.0.0'
        env:
            - name: FOO_BAR
              version_added: 1.2.0
              deprecated:
                alternative: none
                why: Test deprecation
                removed_at_date: 2020-01-31
        vars:
            - name: foobar
              version_added: 1.3.0
              deprecated:
                alternative: none
                why: Test deprecation
                removed_at_date: 2040-12-31
    testcol2depr:
        description:
            - A plugin option taken from testcol2 that is deprecated
        type: str
        deprecated:
            alternative: none
            why: Test option deprecation
            version: '2.0.0'
'''
