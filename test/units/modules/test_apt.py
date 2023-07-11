from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import collections

from units.compat.mock import Mock
from units.compat import unittest

from ansible.modules.apt import (
    expand_pkgspec_from_fnmatches,
)


class AptExpandPkgspecTestCase(unittest.TestCase):

    def setUp(self):
        FakePackage = collections.namedtuple("Package", ("name",))
        self.fake_cache = [
            FakePackage("apt"),
            FakePackage("apt-utils"),
            FakePackage("not-selected"),
        ]

    def test_trivial(self):
        pkg = ["apt"]
        self.assertEqual(
            expand_pkgspec_from_fnmatches(None, pkg, self.fake_cache), pkg)

    def test_version_wildcard(self):
        pkg = ["apt=1.0*"]
        self.assertEqual(
            expand_pkgspec_from_fnmatches(None, pkg, self.fake_cache), pkg)

    def test_pkgname_wildcard_version_wildcard(self):
        pkg = ["apt*=1.0*"]
        m_mock = Mock()
        self.assertEqual(
            expand_pkgspec_from_fnmatches(m_mock, pkg, self.fake_cache),
            ['apt', 'apt-utils'])

    def test_pkgname_expands(self):
        pkg = ["apt*"]
        m_mock = Mock()
        self.assertEqual(
            expand_pkgspec_from_fnmatches(m_mock, pkg, self.fake_cache),
            ["apt", "apt-utils"])
