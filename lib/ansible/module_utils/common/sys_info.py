# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com> 2016
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import platform

from ansible.module_utils import distro
from ansible.module_utils.common._utils import get_all_subclasses


__all__ = ('get_distribution', 'get_distribution_version', 'get_platform_subclass')


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
    if platform.system() == 'Linux':
        version = distro.version()
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
            def __new__(cls, args, kwargs):
                new_cls = get_platform_subclass(User)
                return super(cls, new_cls).__new__(new_cls, args, kwargs)
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
