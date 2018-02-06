
# -*- coding: utf-8 -*-
# Copyright: (c) 2017 Ansible Project
# License: GNU General Public License v3 or later (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt )

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

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

    def test_dist_all_none(self):
        with pytest.raises(TypeError):
            compat_platform.dist(distname=None, version=None, id=None, supported_dists=None)

    def test_dist_empty_supported_dists(self):
        dist = compat_platform.dist(supported_dists=tuple())
        assert dist == ('', '', ''), \
            "no supported dists were provided so dist() should have returned ('', '', '')"


# TODO: test that we dont show deprecation warnings
class TestLinuxDistribution:
    def test_linux_distribution(self):
        linux_dist = compat_platform.linux_distribution()
        # This will be empty unknown for non linux
        assert isinstance(linux_dist, tuple), \
            "return of linux_distribution() is expected to be a tuple but was a %s" % type(linux_dist)

    def test_linux_distribution_all_none(self):
        with pytest.raises(TypeError):
            compat_platform.linux_distribution(distname=None, version=None,
                                               id=None, supported_dists=None,
                                               full_distribution_name=None)

    def test_linux_distribution_empty_supported_dists(self):
        linux_dist = compat_platform.linux_distribution(supported_dists=tuple())
        assert linux_dist[0] == ''
        assert linux_dist[1] == ''
        assert linux_dist[2] == ''
        assert linux_dist[0] == linux_dist[1] == linux_dist[2] == '', \
            "linux_distribtion was expected to return ('', '', '') with no supported_dists"
