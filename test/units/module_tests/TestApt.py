import collections
import mock
import os
import unittest

from ansible.modules.core.packaging.os.apt import (
    expand_pkgspec_from_fnmatches,
)


class AptExpandPkgspecTestCase(unittest.TestCase):

    def setUp(self):
        FakePackage = collections.namedtuple("Package", ("name",))
        self.fake_cache = [ FakePackage("apt"),
                            FakePackage("apt-utils"),
                            FakePackage("not-selected"),
        ]

    def test_trivial(self):
        foo = ["apt"]
        self.assertEqual(
            expand_pkgspec_from_fnmatches(None, foo, self.fake_cache), foo)

    def test_version_wildcard(self):
        foo = ["apt=1.0*"]
        self.assertEqual(
            expand_pkgspec_from_fnmatches(None, foo, self.fake_cache), foo)

    def test_pkgname_wildcard_version_wildcard(self):
        foo = ["apt*=1.0*"]
        m_mock = mock.Mock()
        self.assertEqual(
            expand_pkgspec_from_fnmatches(m_mock, foo, self.fake_cache),
            ['apt', 'apt-utils'])

    def test_pkgname_expands(self):
        foo = ["apt*"]
        m_mock = mock.Mock()
        self.assertEqual(
            expand_pkgspec_from_fnmatches(m_mock, foo, self.fake_cache),
            ["apt", "apt-utils"])
