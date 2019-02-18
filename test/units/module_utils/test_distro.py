
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

import platform
import pytest
import sys

from ansible.module_utils import distro
from ansible.module_utils.common.sys_info import (get_distribution, get_distribution_version,
                                                  get_distribution_codename)


# Generic test case with minimal assertions about specific returned values.
class TestDistro():
    # should run on any platform without errors, even if non-linux without any
    # useful info to return
    def test_info(self):
        info = distro.info()
        assert isinstance(info, dict), \
            'distro.info() returned %s (%s) which is not a dist' % (info, type(info))

    def test_linux_distribution(self):
        linux_dist = distro.linux_distribution()
        assert isinstance(linux_dist, tuple), \
            'linux_distrution() returned %s (%s) which is not a tuple' % (linux_dist, type(linux_dist))


# compare distro.py results with platform.linux_distribution() if we have it
# Depending on the platform, it is okay if these don't match exactly as long as the
# distro result is what we expect and special cased.
class TestDistroCompat():
    '''Verify that distro.linux_distribution matches plain platform.linux_distribution'''
    @pytest.mark.skipif(sys.version_info >= (3, 8), reason="Python 3.8 and later do not have platform.linux_distribution().")
    def test_linux_distribution(self):
        distro_linux_dist = (get_distribution(), get_distribution_version(), get_distribution_codename())

        platform_linux_dist = platform.linux_distribution()

        assert isinstance(distro_linux_dist, type(platform_linux_dist)), \
            'linux_distribution() returned type (%s) which is different from platform.linux_distribution type (%s)' % \
            (type(distro_linux_dist), type(platform_linux_dist))

        # TODO: add the cases where we expect them to differ

        # The third item in the tuple is different.
        assert distro_linux_dist[0] == platform_linux_dist[0]
        assert distro_linux_dist[1] == platform_linux_dist[1]

        if platform_linux_dist[0] == 'Fedora' and 20 < int(platform_linux_dist[1]) < 28:
            pytest.skip("Fedora versions between 20 and 28 return the variant instead of the code name making this test unreliable")
            # Fedora considers the platform_linux behaviour to have been a bug as it's finding the
            # variant, not the code name.  Fedora wants this to be the empty string.
            platform_linux_dist = platform_linux_dist[:2] + ('',)
        assert distro_linux_dist[2] == platform_linux_dist[2]
