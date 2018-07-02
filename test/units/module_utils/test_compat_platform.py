
# -*- coding: utf-8 -*-
# Copyright: (c) 2017 Ansible Project
# License: GNU General Public License v3 or later (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt )

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import platform

import pytest

from ansible.module_utils.six import string_types
from ansible.module_utils import compat_platform


def assert_dist_tuple(dist_tuple, method_name=None):
    method_name = method_name or "method"
    assert isinstance(dist_tuple, tuple), \
        "return of %s is expected to be a tuple but was a %s" % (method_name, type(dist_tuple))
    assert len(dist_tuple) == 3, \
        "return of %s is expected to have len() of 3 but was %s" % (method_name, len(dist_tuple))
    assert isinstance(dist_tuple[0], string_types)
    assert isinstance(dist_tuple[1], string_types)
    assert isinstance(dist_tuple[2], string_types)


# to test fully need to mock:
# open('/etc/lsb-release')
# os.listdir('/etc')
# open('/etc/$VARIOUS_RELEASE_FILES') /etc/
# open other random locations /var/adm/inst-log/info /etc/.installed /usr/lib/setup
class TestDist:
    def test_dist(self):
        dist = compat_platform.dist()
        assert_dist_tuple(dist, "dist()")


# TODO: test that we dont show deprecation warnings
class TestLinuxDistribution:
    def test_linux_distribution(self):
        linux_dist = compat_platform.linux_distribution()
        # This will be empty unknown for non linux
        assert_dist_tuple(linux_dist, "linux_distribution()")


@pytest.mark.skipif(not hasattr(platform, 'dist'),
                    reason="Skipping platform.dist compat test because there is no platform.dist")
class TestDistCompare:
    def test_dist(self):
        dist = compat_platform.dist()
        py_dist = platform.dist()
        assert dist == py_dist, 'compat_platform.dist() did not match platform.dist() %s != %s' % (dist, py_dist)


@pytest.mark.skipif(not hasattr(platform, 'linux_distribution'),
                    reason="Skipping platform.linux_distribution compat test because there is no platform.linux_distribution")
class TestLinuxDistributionCompare:
    def test_linux_distribution(self):
        linux_dist = compat_platform.linux_distribution()
        py_linux_dist = platform.linux_distribution()
        assert linux_dist == py_linux_dist, \
            'compat_platform.linux_distribution() did not match platform.linux_distribution() %s != %s' % (linux_dist, py_linux_dist)
