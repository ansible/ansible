# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Flowroute LLC
# Copyright: (c) 2018, Salvatore Mesoraca <s.mesoraca16@gmail.com>
# Based on apt module written by Matthew Williams <matthew@flowroute.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys

from ansible.module_utils._text import to_native

if sys.version_info[0] < 3:
    PYTHON_APT = 'python-apt'
else:
    PYTHON_APT = 'python3-apt'


def _install_python_apt(module):
    if not module.check_mode:
        apt_get_path = module.get_bin_path('apt-get')
        if apt_get_path:
            rc, so, se = module.run_command([apt_get_path, 'update'])
            if rc != 0:
                module.fail_json(msg="Failed to auto-install %s. Error was: '%s'" %
                                 (PYTHON_APT, se.strip()), rc=rc)
            rc, so, se = module.run_command([apt_get_path,
                                             'install',
                                             '--no-install-recommends',
                                             PYTHON_APT, '-y', '-q'])
            if rc != 0:
                module.fail_json(msg="Failed to auto-install %s. Error was: '%s'" %
                                 (PYTHON_APT, se.strip()), rc=rc)
    else:
        module.fail_json(msg="%s must be installed to use check mode. "
                             "If run normally this module can auto-install it." %
                             PYTHON_APT)


def import_apt(module, install_python_apt=True):
    has_python_apt = True
    try:
        import apt
        import apt.debfile
        import apt_pkg
        import aptsources.distro
    except ImportError:
        has_python_apt = False

    if not has_python_apt:
        if install_python_apt:
            _install_python_apt(module)
        else:
            module.fail_json(msg='%s is not installed, and install_python_apt is False' %
                             PYTHON_APT)
        try:
            import apt
            import apt.debfile
            import apt_pkg
            import aptsources.distro
        except ImportError:
            module.fail_json(msg="Could not import python modules: apt, apt_pkg. "
                                 "Please install %s package." % PYTHON_APT)

    return apt, apt_pkg, aptsources.distro


# https://github.com/ansible/ansible-modules-core/issues/2951
def get_cache(apt, module):
    '''Attempt to get the cache object and update till it works'''
    cache = None
    try:
        cache = apt.Cache()
    except SystemError as e:
        if '/var/lib/apt/lists/' in to_native(e).lower():
            # update cache until files are fixed or retries exceeded
            retries = 0
            while retries < 2:
                (rc, so, se) = module.run_command(['apt-get', 'update', '-q'])
                retries += 1
                if rc == 0:
                    break
            if rc != 0:
                module.fail_json(msg='Updating the cache to correct corrupt package lists failed:\n%s\n%s' %
                                 (to_native(e), so + se), rc=rc)
            # try again
            cache = apt.Cache()
        else:
            module.fail_json(msg=to_native(e))
    return cache
