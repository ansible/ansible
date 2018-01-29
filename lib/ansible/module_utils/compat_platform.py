#
# This module is based on the python 3.6.2 'platform.py' but with
# everything except the deprecated 'dist' and 'linux_distribution'
# methods removed
#
# The following comment is from original upstream python platform.py
#
#    This module is maintained by Marc-Andre Lemburg <mal@egenix.com>.
#    If you find problems, please submit bug reports/patches via the
#    Python bug tracker (http://bugs.python.org) and assign them to "lemburg".
#
#    You can always get the latest version of this module at:
#
#             http://www.egenix.com/files/python/platform.py
#
#    If that URL should fail, try contacting the author.

import os
import re
import sys

__copyright__ = """
    Copyright (c) 1999-2000, Marc-Andre Lemburg; mailto:mal@lemburg.com
    Copyright (c) 2000-2010, eGenix.com Software GmbH; mailto:info@egenix.com

    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose and without fee or royalty is hereby granted,
    provided that the above copyright notice appear in all copies and that
    both that copyright notice and this permission notice appear in
    supporting documentation or portions thereof, including modifications,
    that you make.

    EGENIX.COM SOFTWARE GMBH DISCLAIMS ALL WARRANTIES WITH REGARD TO
    THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
    FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
    INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
    FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
    NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
    WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

"""

__version__ = '1.0.8'


# Directory to search for configuration information on Unix.
# Constant used by test_platform to test linux_distribution().
_UNIXCONFDIR = '/etc'


def _dist_try_harder(distname, version, distid):

    """ Tries some special tricks to get the distribution
        information in case the default method fails.

        Currently supports older SuSE Linux, Caldera OpenLinux and
        Slackware Linux distributions.

    """
    if os.path.exists('/var/adm/inst-log/info'):
        # SuSE Linux stores distribution information in that file
        distname = 'SuSE'
        for line in open('/var/adm/inst-log/info'):
            tv = line.split()
            if len(tv) == 2:
                tag, value = tv
            else:
                continue
            if tag == 'MIN_DIST_VERSION':
                version = value.strip()
            elif tag == 'DIST_IDENT':
                values = value.split('-')
                distid = values[2]
        return distname, version, distid

    if os.path.exists('/etc/.installed'):
        # Caldera OpenLinux has some infos in that file (thanks to Colin Kong)
        for line in open('/etc/.installed'):
            pkg = line.split('-')
            if len(pkg) >= 2 and pkg[0] == 'OpenLinux':
                # XXX does Caldera support non Intel platforms ? If yes,
                #     where can we find the needed id ?
                return 'OpenLinux', pkg[1], distid

    if os.path.isdir('/usr/lib/setup'):
        # Check for slackware version tag file (thanks to Greg Andruk)
        verfiles = os.listdir('/usr/lib/setup')
        for n in range(len(verfiles) - 1, -1, -1):
            if verfiles[n][:14] != 'slack-version-':
                del verfiles[n]
        if verfiles:
            verfiles.sort()
            distname = 'slackware'
            version = verfiles[-1][14:]
            return distname, version, distid

    return distname, version, distid


# 3.6 versions specify the re.ASCII flag here. rm for compat
_release_filename = re.compile(r'(\w+)[-_](release|version)')
_lsb_release_version = re.compile(r'(.+)'
                                  r' release '
                                  r'([\d.]+)'
                                  r'[^(]*(?:\((.+)\))?')
_release_version = re.compile(r'([^0-9]+)'
                              r'(?: release )?'
                              r'([\d.]+)'
                              r'[^(]*(?:\((.+)\))?')

# from http://bazaar.launchpad.net/~doko/python/pkg2.7-debian/view/head:/patches/platform-lsbrelease.diff  # noqa
_distributor_id_file_re = re.compile(r"(?:DISTRIB_ID\s*=)\s*(.*)", re.I)
_release_file_re = re.compile(r"(?:DISTRIB_RELEASE\s*=)\s*(.*)", re.I)
_codename_file_re = re.compile(r"(?:DISTRIB_CODENAME\s*=)\s*(.*)", re.I)

# See also http://www.novell.com/coolsolutions/feature/11251.html
# and http://linuxmafia.com/faq/Admin/release-files.html
# and http://data.linux-ntfs.org/rpm/whichrpm
# and http://www.die.net/doc/linux/man/man1/lsb_release.1.html

_supported_dists = (
    'SuSE', 'debian', 'fedora', 'redhat', 'centos',
    'mandrake', 'mandriva', 'rocks', 'slackware', 'yellowdog', 'gentoo',
    'UnitedLinux', 'turbolinux', 'arch', 'mageia', 'Ubuntu')


def _parse_release_file(firstline):

    # Default to empty 'version' and 'id' strings.  Both defaults are used
    # when 'firstline' is empty.  'id' defaults to empty when an id can not
    # be deduced.
    version = ''
    _id = ''

    # Parse the first line
    m = _lsb_release_version.match(firstline)
    if m is not None:
        # LSB format: "distro release x.x (codename)"
        return tuple(m.groups())

    # Pre-LSB format: "distro x.x (codename)"
    m = _release_version.match(firstline)
    if m is not None:
        return tuple(m.groups())

    # Unknown format... take the first two words
    l = firstline.strip().split()
    if l:
        version = l[0]
        if len(l) > 1:
            _id = l[1]
    return '', version, _id


# noqa because id shadows builtin but cant change API
def linux_distribution(distname='', version='', id='', supported_dists=_supported_dists,  # noqa
                       full_distribution_name=1):

    """ Tries to determine the name of the Linux OS distribution name.

        The function first looks for a distribution release file in
        /etc and then reverts to _dist_try_harder() in case no
        suitable files are found.

        supported_dists may be given to define the set of Linux
        distributions to look for. It defaults to a list of currently
        supported Linux distributions identified by their release file
        name.

        If full_distribution_name is true (default), the full
        distribution read from the OS is returned. Otherwise the short
        name taken from supported_dists is used.

        Returns a tuple (distname, version, id) which default to the
        args given as parameters.

    """

    distid = id
    # check for the LSB /etc/lsb-release file first, needed so
    # that the distribution doesn't get identified as Debian.
    try:
        with open("/etc/lsb-release", "rU") as etclsbrel:
            for line in etclsbrel:
                m = _distributor_id_file_re.search(line)
                if m:
                    _u_distname = m.group(1).strip()
                m = _release_file_re.search(line)
                if m:
                    _u_version = m.group(1).strip()
                m = _codename_file_re.search(line)
                if m:
                    _u_id = m.group(1).strip()
            if _u_distname and _u_version:
                return (_u_distname, _u_version, _u_id)
    except (EnvironmentError, UnboundLocalError):
        pass

    try:
        etc = os.listdir(_UNIXCONFDIR)
    except OSError:
        # Probably not a Unix system
        return distname, version, distid

    etc.sort()

    filename = None
    _distname = None
    _version = None
    _distid = None

    for filename in etc:
        m = _release_filename.match(filename)
        if m is not None:
            _distname, dummy = m.groups()
            if _distname in supported_dists:
                distname = _distname
                break
    else:
        return _dist_try_harder(distname, version, distid)

    # Read the first line

    # FIXME: wrap with py2/py3 compat encoding stuff
    if filename:
        with open(os.path.join(_UNIXCONFDIR, filename), 'r',) as f:
            # encoding='utf-8', errors='surrogateescape') as f:
            firstline = f.readline()
        _distname, _version, _distid = _parse_release_file(firstline)

    if _distname and full_distribution_name:
        distname = _distname
    if _version:
        version = _version
    if _distid:
        distid = _distid
    return distname, version, distid


def dist(distname='', version='', id='',
         supported_dists=_supported_dists):

    """ Tries to determine the name of the Linux OS distribution name.

        The function first looks for a distribution release file in
        /etc and then reverts to _dist_try_harder() in case no
        suitable files are found.

        Returns a tuple (distname, version, id) which default to the
        args given as parameters.

    """
    return linux_distribution(distname, version, id,
                              supported_dists=supported_dists,
                              full_distribution_name=0)


if __name__ == '__main__':
    print(linux_distribution())
    sys.exit(0)
