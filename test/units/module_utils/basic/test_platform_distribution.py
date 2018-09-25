# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from units.mock.procenv import ModuleTestCase

from ansible.compat.tests.mock import patch
from ansible.module_utils.six.moves import builtins

realimport = builtins.__import__


class TestPlatform(ModuleTestCase):
    def test_module_utils_basic_get_platform(self):
        with patch('platform.system', return_value='foo'):
            from ansible.module_utils.basic import get_platform
            self.assertEqual(get_platform(), 'foo')

    def test_module_utils_basic_get_distribution(self):
        from ansible.module_utils.basic import get_distribution

        with patch('platform.system', return_value='Foo'):
            self.assertEqual(get_distribution(), None)

        with patch('platform.system', return_value='Linux'):
            with patch('platform.linux_distribution', return_value=["foo"]):
                self.assertEqual(get_distribution(), "Foo")

            with patch('os.path.isfile', return_value=True):
                with patch('platform.linux_distribution', side_effect=[("AmazonFooBar", )]):
                    self.assertEqual(get_distribution(), "Amazonfoobar")

                with patch('platform.linux_distribution', side_effect=(("", ), ("AmazonFooBam",))):
                    self.assertEqual(get_distribution(), "Amazon")

                with patch('platform.linux_distribution', side_effect=[("", ), ("", )]):
                    self.assertEqual(get_distribution(), "OtherLinux")

                def _dist(distname='', version='', id='', supported_dists=(), full_distribution_name=1):
                    if supported_dists != ():
                        return ("Bar", "2", "Two")
                    else:
                        return ("", "", "")

                with patch('platform.linux_distribution', side_effect=_dist):
                    self.assertEqual(get_distribution(), "Bar")

            with patch('platform.linux_distribution', side_effect=Exception("boo")):
                with patch('platform.dist', return_value=("bar", "2", "Two")):
                    self.assertEqual(get_distribution(), "Bar")

    def test_module_utils_basic_get_distribution_version(self):
        from ansible.module_utils.basic import get_distribution_version

        with patch('platform.system', return_value='Foo'):
            self.assertEqual(get_distribution_version(), None)

        with patch('platform.system', return_value='Linux'):
            with patch('platform.linux_distribution', return_value=("foo", "1", "One")):
                self.assertEqual(get_distribution_version(), "1")

            with patch('os.path.isfile', return_value=True):
                def _dist(distname='', version='', id='', supported_dists=(), full_distribution_name=1):
                    if supported_dists != ():
                        return ("AmazonFooBar", "2", "")
                    else:
                        return ("", "", "")

                with patch('platform.linux_distribution', side_effect=_dist):
                    self.assertEqual(get_distribution_version(), "2")

            with patch('platform.linux_distribution', side_effect=Exception("boo")):
                with patch('platform.dist', return_value=("bar", "3", "Three")):
                    self.assertEqual(get_distribution_version(), "3")

    def test_module_utils_basic_load_platform_subclass(self):
        class LinuxTest:
            pass

        class Foo(LinuxTest):
            platform = "Linux"
            distribution = None

        class Bar(LinuxTest):
            platform = "Linux"
            distribution = "Bar"

        from ansible.module_utils.basic import load_platform_subclass

        # match just the platform class, not a specific distribution
        with patch('ansible.module_utils.basic.get_platform', return_value="Linux"):
            with patch('ansible.module_utils.basic.get_distribution', return_value=None):
                self.assertIs(type(load_platform_subclass(LinuxTest)), Foo)

        # match both the distribution and platform class
        with patch('ansible.module_utils.basic.get_platform', return_value="Linux"):
            with patch('ansible.module_utils.basic.get_distribution', return_value="Bar"):
                self.assertIs(type(load_platform_subclass(LinuxTest)), Bar)

        # if neither match, the fallback should be the top-level class
        with patch('ansible.module_utils.basic.get_platform', return_value="Foo"):
            with patch('ansible.module_utils.basic.get_distribution', return_value=None):
                self.assertIs(type(load_platform_subclass(LinuxTest)), LinuxTest)
