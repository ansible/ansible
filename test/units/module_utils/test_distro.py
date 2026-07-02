
# (c) 2018 Adrian Likins <alikins@redhat.com>
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#  or
# Apache License v2.0 (see http://www.apache.org/licenses/LICENSE-2.0)
#
# Dual licensed so any test cases could potentially be included by the upstream project
# that module_utils/distro.py is from (https://github.com/nir0s/distro)


# Note that nir0s/distro has many more tests in it's test suite. The tests here are
# primarily for testing the vendoring.

from __future__ import annotations

from ansible.module_utils import distro


# Generic test case with minimal assertions about specific returned values.
class TestDistro():
    # should run on any platform without errors, even if non-linux without any
    # useful info to return
    def test_info(self):
        info = distro.info()
        assert isinstance(info, dict), \
            'distro.info() returned %s (%s) which is not a dist' % (info, type(info))

    def test_id(self):
        id = distro.id()
        assert isinstance(id, str), 'distro.id() returned %s (%s) which is not a string' % (id, type(id))
