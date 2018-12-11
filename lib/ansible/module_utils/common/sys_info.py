# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# Copyright (c), Toshio Kuratomi <tkuratomi@ansible.com> 2016
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import platform

from ansible.module_utils import distro


# Backwards compat.  New code should just use platform.system()
def get_platform():
    '''
    :rtype: NativeString
    :returns: Name of the platform the module is running on
    '''
    return platform.system()


def get_distribution():
    '''
    :rtype: NativeString or None
    :returns: Name of the distribution the module is running on
    '''
    distribution = None

    if platform.system() == 'Linux':
        distribution = distro.name().capitalize()

        # FIXME: Would we need to normalize these if we used: id() instead of name()?
        distribution_words = distribution.split()
        if 'Amazon' in distribution_words:
            distribution = 'Amazon'
        elif not distribution:
            distribution = 'OtherLinux'

    return distribution


def get_distribution_version():
    '''
    :rtype: NativeString or None
    :returns: A string representation of the version of the distribution.  None if this is not run
        on a Linux machine
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


def get_all_subclasses(cls):
    '''
    used by modules like Hardware or Network fact classes to recursively retrieve all
    subclasses of a given class not only the direct sub classes.
    '''
    # Retrieve direct subclasses
    subclasses = cls.__subclasses__()
    to_visit = list(subclasses)
    # Then visit all subclasses
    while to_visit:
        for sc in to_visit:
            # The current class is now visited, so remove it from list
            to_visit.remove(sc)
            # Appending all subclasses to visit and keep a reference of available class
            for ssc in sc.__subclasses__():
                subclasses.append(ssc)
                to_visit.append(ssc)
    return subclasses


def load_platform_subclass(cls, *args, **kwargs):
    '''
    used by modules like User to have different implementations based on detected platform.  See User
    module for an example.
    '''

    this_platform = get_platform()
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

    return super(cls, subclass).__new__(subclass)
