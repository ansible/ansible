""" This module tries to retrieve as much platform-identifying data as
    possible. It makes this information available via function APIs.

    If called from the command line, it prints the platform
    information concatenated as single string to stdout. The output
    format is useable as part of a filename.

"""
#    This module is maintained by Marc-Andre Lemburg <mal@egenix.com>.
#    If you find problems, please submit bug reports/patches via the
#    Python bug tracker (http://bugs.python.org) and assign them to "lemburg".
#
#    Still needed:
#    * support for MS-DOS (PythonDX ?)
#    * support for Amiga and other still unsupported platforms running Python
#    * support for additional Linux distributions
#
#    Many thanks to all those who helped adding platform-specific
#    checks (in no particular order):
#
#      Charles G Waldman, David Arnold, Gordon McMillan, Ben Darnell,
#      Jeff Bauer, Cliff Crawford, Ivan Van Laningham, Josef
#      Betancourt, Randall Hopper, Karl Putland, John Farrell, Greg
#      Andruk, Just van Rossum, Thomas Heller, Mark R. Levinson, Mark
#      Hammond, Bill Tutt, Hans Nowak, Uwe Zessin (OpenVMS support),
#      Colin Kong, Trent Mick, Guido van Rossum, Anthony Baxter, Steve
#      Dower
#
#    History:
#
#    <see CVS and SVN checkin messages for history>
#
#    1.0.8 - changed Windows support to read version from kernel32.dll
#    1.0.7 - added DEV_NULL
#    1.0.6 - added linux_distribution()
#    1.0.5 - fixed Java support to allow running the module on Jython
#    1.0.4 - added IronPython support
#    1.0.3 - added normalization of Windows system name
#    1.0.2 - added more Windows support
#    1.0.1 - reformatted to make doc.py happy
#    1.0.0 - reformatted a bit and checked into Python CVS
#    0.8.0 - added sys.version parser and various new access
#            APIs (python_version(), python_compiler(), etc.)
#    0.7.2 - fixed architecture() to use sizeof(pointer) where available
#    0.7.1 - added support for Caldera OpenLinux
#    0.7.0 - some fixes for WinCE; untabified the source file
#    0.6.2 - support for OpenVMS - requires version 1.5.2-V006 or higher and
#            vms_lib.getsyi() configured
#    0.6.1 - added code to prevent 'uname -p' on platforms which are
#            known not to support it
#    0.6.0 - fixed win32_ver() to hopefully work on Win95,98,NT and Win2k;
#            did some cleanup of the interfaces - some APIs have changed
#    0.5.5 - fixed another type in the MacOS code... should have
#            used more coffee today ;-)
#    0.5.4 - fixed a few typos in the MacOS code
#    0.5.3 - added experimental MacOS support; added better popen()
#            workarounds in _syscmd_ver() -- still not 100% elegant
#            though
#    0.5.2 - fixed uname() to return '' instead of 'unknown' in all
#            return values (the system uname command tends to return
#            'unknown' instead of just leaving the field empty)
#    0.5.1 - included code for slackware dist; added exception handlers
#            to cover up situations where platforms don't have os.popen
#            (e.g. Mac) or fail on socket.gethostname(); fixed libc
#            detection RE
#    0.5.0 - changed the API names referring to system commands to *syscmd*;
#            added java_ver(); made syscmd_ver() a private
#            API (was system_ver() in previous versions) -- use uname()
#            instead; extended the win32_ver() to also return processor
#            type information
#    0.4.0 - added win32_ver() and modified the platform() output for WinXX
#    0.3.4 - fixed a bug in _follow_symlinks()
#    0.3.3 - fixed popen() and "file" command invokation bugs
#    0.3.2 - added architecture() API and support for it in platform()
#    0.3.1 - fixed syscmd_ver() RE to support Windows NT
#    0.3.0 - added system alias support
#    0.2.3 - removed 'wince' again... oh well.
#    0.2.2 - added 'wince' to syscmd_ver() supported platforms
#    0.2.1 - added cache logic and changed the platform string format
#    0.2.0 - changed the API to use functions instead of module globals
#            since some action take too long to be run on module import
#    0.1.0 - first release
#
#    You can always get the latest version of this module at:
#
#             http://www.egenix.com/files/python/platform.py
#
#    If that URL should fail, try contacting the author.

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

import os
import re
import sys

import warnings


# Directory to search for configuration information on Unix.
# Constant used by test_platform to test linux_distribution().
_UNIXCONFDIR = '/etc'


def _dist_try_harder(distname, version, id):

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
                id = values[2]
        return distname, version, id

    if os.path.exists('/etc/.installed'):
        # Caldera OpenLinux has some infos in that file (thanks to Colin Kong)
        for line in open('/etc/.installed'):
            pkg = line.split('-')
            if len(pkg) >= 2 and pkg[0] == 'OpenLinux':
                # XXX does Caldera support non Intel platforms ? If yes,
                #     where can we find the needed id ?
                return 'OpenLinux', pkg[1], id

    if os.path.isdir('/usr/lib/setup'):
        # Check for slackware version tag file (thanks to Greg Andruk)
        verfiles = os.listdir('/usr/lib/setup')
        for n in range(len(verfiles)-1, -1, -1):
            if verfiles[n][:14] != 'slack-version-':
                del verfiles[n]
        if verfiles:
            verfiles.sort()
            distname = 'slackware'
            version = verfiles[-1][14:]
            return distname, version, id

    return distname, version, id


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

# from http://bazaar.launchpad.net/~doko/python/pkg2.7-debian/view/head:/patches/platform-lsbrelease.diff
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
    id = ''

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
            id = l[1]
    return '', version, id


# TODO: remove, we dont want to warn
def linux_distribution(distname='', version='', id='',

                       supported_dists=_supported_dists,
                       full_distribution_name=1):
    import warnings
    warnings.warn("dist() and linux_distribution() functions are deprecated "
                  "in Python 3.5", PendingDeprecationWarning, stacklevel=2)
    return _linux_distribution(distname, version, id, supported_dists,
                               full_distribution_name)


def _linux_distribution(distname, version, id, supported_dists,
                        full_distribution_name):

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
        return distname, version, id
    etc.sort()
    for file in etc:
        m = _release_filename.match(file)
        if m is not None:
            _distname, dummy = m.groups()
            if _distname in supported_dists:
                distname = _distname
                break
    else:
        return _dist_try_harder(distname, version, id)

    # Read the first line

    # FIXME: wrap with py2/py3 compat encoding stuff
    with open(os.path.join(_UNIXCONFDIR, file), 'r',) as f:
        # encoding='utf-8', errors='surrogateescape') as f:
        firstline = f.readline()
    _distname, _version, _id = _parse_release_file(firstline)

    if _distname and full_distribution_name:
        distname = _distname
    if _version:
        version = _version
    if _id:
        id = _id
    return distname, version, id


def dist(distname='', version='', id='',

         supported_dists=_supported_dists):

    """ Tries to determine the name of the Linux OS distribution name.

        The function first looks for a distribution release file in
        /etc and then reverts to _dist_try_harder() in case no
        suitable files are found.

        Returns a tuple (distname, version, id) which default to the
        args given as parameters.

    """
    import warnings
    warnings.warn("dist() and linux_distribution() functions are deprecated "
                  "in Python 3.5", PendingDeprecationWarning, stacklevel=2)
    return _linux_distribution(distname, version, id,
                               supported_dists=supported_dists,
                               full_distribution_name=0)


if __name__ == '__main__':
    print(linux_distribution())
    sys.exit(0)
