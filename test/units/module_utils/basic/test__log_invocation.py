# -*- coding: utf-8 -*-
# (c) 2016, James Cammarata <jimi@sngx.net>
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
from __future__ import (absolute_import, division)
__metaclass__ = type

import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import MagicMock

class TestModuleUtilsBasic(unittest.TestCase):

    def test_module_utils_basic__log_invocation(self):
        from ansible.module_utils import basic

        # test basic log invocation
        basic.MODULE_COMPLEX_ARGS = json.dumps(dict(foo=False, bar=[1,2,3], bam="bam", baz=u'baz'))
        am = basic.AnsibleModule(
            argument_spec=dict(
                foo = dict(default=True, type='bool'),
                bar = dict(default=[], type='list'),
                bam = dict(default="bam"),
                baz = dict(default=u"baz"),
                password = dict(default=True),
                no_log = dict(default="you shouldn't see me", no_log=True),
            ),
        )

        am.log = MagicMock()
        am._log_invocation()
        am.log.assert_called_with(
            'Invoked with bam=bam bar=[1, 2, 3] foo=False baz=baz no_log=NOT_LOGGING_PARAMETER password=NOT_LOGGING_PASSWORD ',
            log_args={
                'foo': 'False',
                'bar': '[1, 2, 3]',
                'bam': 'bam',
                'baz': 'baz',
                'password': 'NOT_LOGGING_PASSWORD',
                'no_log': 'NOT_LOGGING_PARAMETER',
            },
        )
