# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com> 2016
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import errno
import platform

from ansible.module_utils import distro
from ansible.module_utils.common._utils import get_all_subclasses
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.process import get_bin_path


__all__ = ('get_distribution', 'get_distribution_version', 'get_platform_subclass')

HAVE_SELINUX = False
try:
    import selinux
    HAVE_SELINUX = True
except ImportError:
    pass


def get_distribution():
    '''
    Return the name of the distribution the module is running on

    :rtype: NativeString or None
    :returns: Name of the distribution the module is running on

    This function attempts to determine what Linux distribution the code is running on and return
    a string representing that value.  If the distribution cannot be determined, it returns
    ``OtherLinux``.  If not run on Linux it returns None.
    '''
    distribution = None

    if platform.system() == 'Linux':
        distribution = distro.id().capitalize()

        if distribution == 'Amzn':
            distribution = 'Amazon'
        elif distribution == 'Rhel':
            distribution = 'Redhat'
        elif not distribution:
            distribution = 'OtherLinux'

    return distribution


def get_distribution_version():
    '''
    Get the version of the Linux distribution the code is running on

    :rtype: NativeString or None
    :returns: A string representation of the version of the distribution. If it cannot determine
        the version, it returns empty string. If this is not run on a Linux machine it returns None
    '''
    version = None

    needs_best_version = frozenset((
        u'centos',
        u'debian',
    ))

    if platform.system() == 'Linux':
        version = distro.version()
        distro_id = distro.id()

        if version is not None:
            if distro_id in needs_best_version:
                version_best = distro.version(best=True)

                # CentoOS maintainers believe only the major version is appropriate
                # but Ansible users desire minor version information, e.g., 7.5.
                # https://github.com/ansible/ansible/issues/50141#issuecomment-449452781
                if distro_id == u'centos':
                    version = u'.'.join(version_best.split(u'.')[:2])

                # Debian does not include minor version in /etc/os-release.
                # Bug report filed upstream requesting this be added to /etc/os-release
                # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=931197
                if distro_id == u'debian':
                    version = version_best

        else:
            version = u''

    return version


def get_distribution_codename():
    '''
    Return the code name for this Linux Distribution

    :rtype: NativeString or None
    :returns: A string representation of the distribution's codename or None if not a Linux distro
    '''
    codename = None
    if platform.system() == 'Linux':
        # Until this gets merged and we update our bundled copy of distro:
        # https://github.com/nir0s/distro/pull/230
        # Fixes Fedora 28+ not having a code name and Ubuntu Xenial Xerus needing to be "xenial"
        os_release_info = distro.os_release_info()
        codename = os_release_info.get('version_codename')

        if codename is None:
            codename = os_release_info.get('ubuntu_codename')

        if codename is None and distro.id() == 'ubuntu':
            lsb_release_info = distro.lsb_release_info()
            codename = lsb_release_info.get('codename')

        if codename is None:
            codename = distro.codename()
            if codename == u'':
                codename = None

    return codename


def get_platform_subclass(cls):
    '''
    Finds a subclass implementing desired functionality on the platform the code is running on

    :arg cls: Class to find an appropriate subclass for
    :returns: A class that implements the functionality on this platform

    Some Ansible modules have different implementations depending on the platform they run on.  This
    function is used to select between the various implementations and choose one.  You can look at
    the implementation of the Ansible :ref:`User module<user_module>` module for an example of how to use this.

    This function replaces ``basic.load_platform_subclass()``.  When you port code, you need to
    change the callers to be explicit about instantiating the class.  For instance, code in the
    Ansible User module changed from::

    .. code-block:: python

        # Old
        class User:
            def __new__(cls, args, kwargs):
                return load_platform_subclass(User, args, kwargs)

        # New
        class User:
            def __new__(cls, *args, **kwargs):
                new_cls = get_platform_subclass(User)
                return super(cls, new_cls).__new__(new_cls)
    '''

    this_platform = platform.system()
    distribution = get_distribution()
    subclass = None

    # get the most specific superclass for this platform
    if distribution is not None:
        for sc in get_all_subclasses(cls):
            if sc.distribution is not None and sc.distribution == distribution and sc.platform == this_platform:
                subclass = sc
    if subclass is None:
        for sc in get_all_subclasses(cls):
            if sc.platform == this_platform and sc.distribution is None:
                subclass = sc
    if subclass is None:
        subclass = cls

    return subclass


def selinux_mls_enabled():
    """
    Detect whether using selinux that is MLS-aware. While this means you can
    set the level/range with selinux.lsetfilecon(), it may or may not mean that
    you will get the selevel as part of the context returned by
    selinux.lgetfilecon().
    """

    if not HAVE_SELINUX:
        return False
    if selinux.is_selinux_mls_enabled() == 1:
        return True
    else:
        return False


def selinux_initial_context():
    context = [None, None, None]
    if selinux_mls_enabled():
        context.append(None)
    return context


def selinux_enabled(self):
    if not HAVE_SELINUX:
        try:
            seenabled = get_bin_path('selinuxenabled')
        except ValueError:
            seenabled = None

        if seenabled is not None:
            # FIXME: Need to move run_command
            (rc, out, err) = self.run_command(seenabled)
            if rc == 0:
                raise OSError(rc, "Aborting, target uses selinux but python bindings (libselinux-python) aren't installed!")
        return False
    if selinux.is_selinux_enabled() == 1:
        return True
    else:
        return False


def selinux_context(path):
    context = selinux_initial_context()
    if not HAVE_SELINUX or not selinux_enabled():
        return context
    try:
        ret = selinux.lgetfilecon_raw(to_native(path, errors='surrogate_or_strict'))
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise OSError(to_native('path %s does not exist' % path))
        else:
            raise OSError(to_native('failed to retrieve selinux context'))
    if ret[0] == -1:
        return context
    # Limit split to 4 because the selevel, the last in the list,
    # may contain ':' characters
    context = ret[1].split(':', 3)
    return context


def selinux_default_context(path, mode=0):
    """If selinux fails to find a default, return an array of None"""

    context = selinux_initial_context()
    if not HAVE_SELINUX or not selinux_enabled():
        return context
    try:
        ret = selinux.matchpathcon(to_native(path, errors='surrogate_or_strict'), mode)
    except OSError:
        return context
    if ret[0] == -1:
        return context
    # Limit split to 4 because the selevel, the last in the list,
    # may contain ':' characters
    context = ret[1].split(':', 3)
    return context
