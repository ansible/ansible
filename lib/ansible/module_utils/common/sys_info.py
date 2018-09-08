import os
import platform


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
    additional_linux = ('alpine', 'arch', 'devuan')
    supported_dists = platform._supported_dists + additional_linux

    if platform.system() == 'Linux':
        try:
            distribution = platform.linux_distribution(supported_dists=supported_dists)[0].capitalize()
            if not distribution and os.path.isfile('/etc/system-release'):
                distribution = platform.linux_distribution(supported_dists=['system'])[0].capitalize()
                if 'Amazon' in distribution:
                    distribution = 'Amazon'
                else:
                    distribution = 'OtherLinux'
        except Exception:
            # FIXME: MethodMissing, I assume?
            distribution = platform.dist()[0].capitalize()
    return distribution


def get_distribution_version():
    '''
    :rtype: NativeString or None
    :returns: A string representation of the version of the distribution
    '''
    distribution_version = None
    if platform.system() == 'Linux':
        try:
            distribution_version = platform.linux_distribution()[1]
            if not distribution_version and os.path.isfile('/etc/system-release'):
                distribution_version = platform.linux_distribution(supported_dists=['system'])[1]
        except Exception:
            # FIXME: MethodMissing, I assume?
            distribution_version = platform.dist()[1]
    return distribution_version


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
