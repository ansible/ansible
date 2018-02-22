
# -*- coding: utf-8 -*-
# Copyright: (c) 2017 Ansible Project
# License: GNU General Public License v3 or later (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt )

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import platform

import pytest

from ansible.module_utils import compat_platform


# to test fully need to mock:
# open('/etc/lsb-release')
# os.listdir('/etc')
# open('/etc/$VARIOUS_RELEASE_FILES') /etc/
# open other random locations /var/adm/inst-log/info /etc/.installed /usr/lib/setup
class TestDist:
    def test_dist(self):
        dist = compat_platform.dist()
        assert isinstance(dist, tuple), \
            "return of dist() is expected to be a tuple but was a %s" % type(dist)

    def test_dist_empty_supported_dists(self):
        dist = compat_platform.dist(supported_dists=tuple())
        assert dist == ('', '', ''), \
            "no supported dists were provided so dist() should have returned ('', '', '')"


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


# TODO: test that we dont show deprecation warnings
class TestLinuxDistribution:
    def test_linux_distribution(self):
        linux_dist = compat_platform.linux_distribution()
        # This will be empty unknown for non linux
        assert isinstance(linux_dist, tuple), \
            "return of linux_distribution() is expected to be a tuple but was a %s" % type(linux_dist)

    def test_linux_distribution_empty_supported_dists(self):
        linux_dist = compat_platform.linux_distribution(supported_dists=tuple())
        assert linux_dist[0] == ''
        assert linux_dist[1] == ''
        assert linux_dist[2] == ''
        assert linux_dist[0] == linux_dist[1] == linux_dist[2] == '', \
            "linux_distribtion was expected to return ('', '', '') with no supported_dists"
