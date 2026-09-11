# Copyright © 2024, 2025 mirabilos <tglaser@b1-systems.de>
# Testsuite for dversion.py in Ansible, cribbed from:
#
# libdpkg - Debian packaging suite library routines
# t-version.c - test version handling
#
# Copyright © 2009-2014 Guillem Jover <guillem@debian.org>
#
# GNU General Public License v2 or later (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import annotations

from ansible.utils.dversion import Version


def p(v):
    if not v:
        raise Exception('v: ' + repr(v))


def f(v):
    if v:
        raise Exception('v: ' + repr(v))


def chkdebver(v, towhat):
    # pycodestyle is wrong here, False need not be a singleton
    # (even if it is in current cpython) so "is false" is wrong,
    # and we do need the explicit comparison to False because
    # the other values can be falsy
    if towhat:
        # pylint: disable-next=singleton-comparison
        p(v.isDebianVersion() != False)  # noqa: E712 (see above)
    else:
        # pylint: disable-next=singleton-comparison
        p(v.isDebianVersion() == False)  # noqa: E712 (see above)


def doesaccept(v, should):
    does = True
    try:
        a = Version(v)
    except ValueError:
        does = False
    p(does == should)


class Dummy:
    def __str__(self):
        return "dummy"


def test_dversion():
    a = Version(b"1:0")
    b = Version(b"1:0")
    p(a == b)
    b = Version(b"2:0")
    f(a == b)

    a = Version((0, b"1", b"1"), True)
    b = Version((0, b"2", b"1"), True)
    f(a == b)

    a = Version((0, b"1", b"1"), True)
    b = Version((0, b"1", b"2"), True)
    f(a == b)

    # Test for version equality
    a = b = Version((0, b"0", b"0"), True)
    p(a == b)

    a = Version((0, b"0", b"00"), True)
    b = Version((0, b"00", b"0"), True)
    p(a == b)

    a = b = Version((1, b"2", b"3"), True)
    p(a == b)

    # Test for epoch difference
    a = Version((0, b"0", b"0"), True)
    b = Version((1, b"0", b"0"), True)
    p(a < b)
    p(b > a)

    # Test for version component difference
    a = Version((0, b"a", b"0"), True)
    b = Version((0, b"b", b"0"), True)
    p(a < b)
    p(b > a)

    # Test for revision component difference
    a = Version((0, b"0", b"a"), True)
    b = Version((0, b"0", b"b"), True)
    p(a < b)
    p(b > a)

    a = Version((0, b"1", b"1"), True)
    b = Version((0, b"1", b"1"), True)
    p(a == b)
    f(a < b)
    p(a <= b)
    f(a > b)
    p(a >= b)

    a = Version((0, b"1", b"1"), True)
    b = Version((0, b"2", b"1"), True)
    f(a == b)
    p(a < b)
    p(a <= b)
    f(a > b)
    f(a >= b)

    a = Version((0, b"2", b"1"), True)
    b = Version((0, b"1", b"1"), True)
    f(a == b)
    f(a < b)
    f(a <= b)
    p(a > b)
    p(a >= b)

    b = Version((0, b"0", None), True)
    a = Version(b"0:0")
    chkdebver(a, True)
    p(a == b)

    b = Version((0, b"0", b"0"), True)
    a = Version(b"0:0-0")
    chkdebver(a, True)
    p(a == b)

    b = Version((0, b"0.0", b"0.0"), True)
    a = Version(b"0:0.0-0.0")
    chkdebver(a, True)
    p(a == b)

    # Test epoched versions
    b = Version((1, b"0", None), True)
    a = Version(b"1:0")
    chkdebver(a, True)
    p(a == b)

    b = Version((5, b"1", None), True)
    a = Version(b"5:1")
    chkdebver(a, True)
    p(a == b)

    # Test multiple hyphens
    b = Version((0, b"0-0", b"0"), True)
    a = Version(b"0:0-0-0")
    chkdebver(a, True)
    p(a == b)

    b = Version((0, b"0-0-0", b"0"), True)
    a = Version(b"0:0-0-0-0")
    chkdebver(a, True)
    p(a == b)

    # Test multiple colons
    b = Version((0, b"0:0", b"0"), True)
    a = Version(b"0:0:0-0")
    chkdebver(a, False)

    b = Version((0, b"0:0:0", b"0"), True)
    a = Version(b"0:0:0:0-0")
    chkdebver(a, False)

    # Test multiple hyphens and colons
    b = Version((0, b"0:0-0", b"0"), True)
    a = Version(b"0:0:0-0-0")
    chkdebver(a, False)

    b = Version((0, b"0-0:0", b"0"), True)
    a = Version(b"0:0-0:0-0")
    chkdebver(a, False)

    # Test valid characters in upstream version
    a = Version(b"0:09azAZ.-+~:-0")
    chkdebver(a, False)
    b = Version((0, b"09azAZ.-+~", b"0"), True)
    a = Version(b"0:09azAZ.-+~-0")
    chkdebver(a, True)
    p(a == b)

    # Test valid characters in revision
    b = Version((0, b"0", b"azAZ09.+~"), True)
    a = Version(b"0:0-azAZ09.+~")
    chkdebver(a, True)
    p(a == b)

    # Test empty version
    doesaccept(b"", False)
    doesaccept(b"  ", True)
    dummy = Dummy()
    doesaccept(dummy, False)
    doesaccept(None, False)
    doesaccept(True, False)
    doesaccept(False, False)
    doesaccept(str, False)
    doesaccept(bytes, False)
    doesaccept(1, False)
    # we accept basically any string and bytes but nothing else

    # Test empty upstream version after epoch
    a = Version(b"0:")
    chkdebver(a, False)

    # Test empty epoch in version
    a = Version(b":1.0")
    chkdebver(a, False)

    # Test empty revision in version
    a = Version(b"1.0-")
    chkdebver(a, False)

    # Test version with embedded spaces
    a = Version(b"0:0 0-1")
    chkdebver(a, False)

    # Test version with negative epoch
    a = Version(b"-1:0-1")
    chkdebver(a, False)

    # Test version with huge epoch
    a = Version(b"999999999999999999999999:0-1")
    chkdebver(a, False)

    # Test invalid characters in epoch
    a = Version(b"a:0-0")
    chkdebver(a, False)
    a = Version(b"A:0-0")
    chkdebver(a, False)

    # Test invalid empty upstream version
    a = Version(b"-0")
    chkdebver(a, False)
    a = Version(b"0:-0")
    chkdebver(a, False)

    # Test upstream version not starting with a digit
    a = Version(b"0:abc3-0")
    chkdebver(a, True)

    # Test invalid characters in upstream version
    a = Version(b"0:0%s-0" % b"a")
    chkdebver(a, True)
    a = Version(b"0:0%s-0" % b"!")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"#")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"@")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"$")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"%")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"&")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"/")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"|")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"\\")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"<")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b">")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"(")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b")")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"[")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"]")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"{")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"}")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b";")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b",")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"_")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"=")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"*")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"^")
    chkdebver(a, False)
    a = Version(b"0:0%s-0" % b"'")
    chkdebver(a, False)

    # Test invalid characters in revision
    a = Version(b"0:0-0%s0" % b":")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"a")
    chkdebver(a, True)
    a = Version(b"0:0-0%s0" % b"!")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"#")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"@")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"$")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"%")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"&")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"/")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"|")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"\\")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"<")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b">")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"(")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b")")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"[")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"]")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"{")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"}")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b";")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b",")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"_")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"=")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"*")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"^")
    chkdebver(a, False)
    a = Version(b"0:0-0%s0" % b"'")
    chkdebver(a, False)

    # and from me
    a = Version(b'1.23.')
    b = Version(b'1.23.0')
    chkdebver(a, True)
    chkdebver(b, True)
    p(a == b)

    a = Version(b"0-1")
    chkdebver(a, True)
    a = Version(b"2:0-1")
    chkdebver(a, True)
    a = Version(b'0:1.23.')
    b = Version(b'1.23.0')
    chkdebver(a, True)
    chkdebver(b, True)
    p(a == b)
    a = Version(b"2147483647:0-1")
    chkdebver(a, True)
    a = Version(b"2147483648:0-1")
    chkdebver(a, False)
