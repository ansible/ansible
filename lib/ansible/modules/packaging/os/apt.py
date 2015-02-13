#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Flowroute LLC
# Written by Matthew Williams <matthew@flowroute.com>
# Based on yum module written by Seth Vidal <skvidal at fedoraproject.org>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = '''
---
module: apt
short_description: Manages apt-packages
description:
  - Manages I(apt) packages (such as for Debian/Ubuntu).
version_added: "0.0.2"
options:
  name:
    description:
      - A package name, like C(foo), or package specifier with version, like C(foo=1.0). Name wildcards (fnmatch) like C(apt*) and version wildcards like C(foo=1.0*) are also supported.
    required: false
    default: null
  state:
    description:
      - Indicates the desired package state. C(latest) ensures that the latest version is installed. C(build-dep) ensures the package build dependencies are installed.
    required: false
    default: present
    choices: [ "latest", "absent", "present", "build-dep" ]
  update_cache:
    description:
      - Run the equivalent of C(apt-get update) before the operation. Can be run as part of the package installation or as a separate step.
    required: false
    default: no
    choices: [ "yes", "no" ]
  cache_valid_time:
    description:
      - If C(update_cache) is specified and the last run is less or equal than I(cache_valid_time) seconds ago, the C(update_cache) gets skipped.
    required: false
    default: no
  purge:
    description:
     - Will force purging of configuration files if the module state is set to I(absent).
    required: false
    default: no
    choices: [ "yes", "no" ]
  default_release:
    description:
      - Corresponds to the C(-t) option for I(apt) and sets pin priorities
    required: false
    default: null
  install_recommends:
    description:
      - Corresponds to the C(--no-install-recommends) option for I(apt). Default behavior (C(yes)) replicates apt's default behavior; C(no) does not install recommended packages. Suggested packages are never installed.
    required: false
    default: yes
    choices: [ "yes", "no" ]
  force:
    description:
      - If C(yes), force installs/removes.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  upgrade:
    description:
      - 'If yes or safe, performs an aptitude safe-upgrade.'
      - 'If full, performs an aptitude full-upgrade.'
      - 'If dist, performs an apt-get dist-upgrade.'
      - 'Note: This does not upgrade a specific package, use state=latest for that.'
    version_added: "1.1"
    required: false
    default: "yes"
    choices: [ "yes", "safe", "full", "dist"]
  dpkg_options:
    description:
      - Add dpkg options to apt command. Defaults to '-o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confold"'
      - Options should be supplied as comma separated list
    required: false
    default: 'force-confdef,force-confold'
  deb:
     description:
       - Path to a .deb package on the remote machine.
     required: false
     version_added: "1.6"
requirements: [ python-apt, aptitude ]
author: Matthew Williams
notes:
   - Three of the upgrade modes (C(full), C(safe) and its alias C(yes)) require C(aptitude), otherwise
     C(apt-get) suffices.
'''

EXAMPLES = '''
# Update repositories cache and install "foo" package
- apt: name=foo update_cache=yes

# Remove "foo" package
- apt: name=foo state=absent

# Install the package "foo"
- apt: name=foo state=present

# Install the version '1.00' of package "foo"
- apt: name=foo=1.00 state=present

# Update the repository cache and update package "nginx" to latest version using default release squeeze-backport
- apt: name=nginx state=latest default_release=squeeze-backports update_cache=yes

# Install latest version of "openjdk-6-jdk" ignoring "install-recommends"
- apt: name=openjdk-6-jdk state=latest install_recommends=no

# Update all packages to the latest version
- apt: upgrade=dist

# Run the equivalent of "apt-get update" as a separate step
- apt: update_cache=yes

# Only run "update_cache=yes" if the last one is more than 3600 seconds ago
- apt: update_cache=yes cache_valid_time=3600

# Pass options to dpkg on run
- apt: upgrade=dist update_cache=yes dpkg_options='force-confold,force-confdef'

# Install a .deb package
- apt: deb=/tmp/mypackage.deb

# Install the build dependencies for package "foo"
- apt: pkg=foo state=build-dep
'''


import traceback
# added to stave off future warnings about apt api
import warnings
warnings.filterwarnings('ignore', "apt API not stable yet", FutureWarning)

import os
import datetime
import fnmatch
import itertools

# APT related constants
APT_ENV_VARS = dict(
  DEBIAN_FRONTEND = 'noninteractive',
  DEBIAN_PRIORITY = 'critical',
  LANG = 'C'
)

DPKG_OPTIONS = 'force-confdef,force-confold'
APT_GET_ZERO = "0 upgraded, 0 newly installed"
APTITUDE_ZERO = "0 packages upgraded, 0 newly installed"
APT_LISTS_PATH = "/var/lib/apt/lists"
APT_UPDATE_SUCCESS_STAMP_PATH = "/var/lib/apt/periodic/update-success-stamp"

HAS_PYTHON_APT = True
try:
    import apt
    import apt.debfile
    import apt_pkg
except ImportError:
    HAS_PYTHON_APT = False

def package_split(pkgspec):
    parts = pkgspec.split('=', 1)
    if len(parts) > 1:
        return parts[0], parts[1]
    else:
        return parts[0], None

def package_versions(pkgname, pkg, pkg_cache):
    try:
        versions = set(p.version for p in pkg.versions)
    except AttributeError:
        # assume older version of python-apt is installed
        # apt.package.Package#versions require python-apt >= 0.7.9.
        pkg_cache_list = (p for p in pkg_cache.Packages if p.Name == pkgname)
        pkg_versions = (p.VersionList for p in pkg_cache_list)
        versions = set(p.VerStr for p in itertools.chain(*pkg_versions))

    return versions

def package_version_compare(version, other_version):
    try:
        return apt_pkg.version_compare(version, other_version)
    except AttributeError:
        return apt_pkg.VersionCompare(version, other_version)

def package_status(m, pkgname, version, cache, state):
    try:
        # get the package from the cache, as well as the
        # the low-level apt_pkg.Package object which contains
        # state fields not directly acccesible from the
        # higher-level apt.package.Package object.
        pkg = cache[pkgname]
        ll_pkg = cache._cache[pkgname] # the low-level package object
    except KeyError:
        if state == 'install':
            try:
                if cache.get_providing_packages(pkgname):
                    return False, True, False
                m.fail_json(msg="No package matching '%s' is available" % pkgname)
            except AttributeError:
                # python-apt version too old to detect virtual packages
                # mark as upgradable and let apt-get install deal with it
                return False, True, False
        else:
            return False, False, False
    try:
        has_files = len(pkg.installed_files) > 0
    except UnicodeDecodeError:
        has_files = True
    except AttributeError:
        has_files = False  # older python-apt cannot be used to determine non-purged

    try:
        package_is_installed = ll_pkg.current_state == apt_pkg.CURSTATE_INSTALLED
    except AttributeError: # python-apt 0.7.X has very weak low-level object
        try:
            # might not be necessary as python-apt post-0.7.X should have current_state property
            package_is_installed = pkg.is_installed
        except AttributeError:
            # assume older version of python-apt is installed
            package_is_installed = pkg.isInstalled

    if version:
        versions = package_versions(pkgname, pkg, cache._cache)
        avail_upgrades = fnmatch.filter(versions, version)

        if package_is_installed:
            try:
                installed_version = pkg.installed.version
            except AttributeError:
                installed_version = pkg.installedVersion

            # Only claim the package is installed if the version is matched as well
            package_is_installed = fnmatch.fnmatch(installed_version, version)

            # Only claim the package is upgradable if a candidate matches the version
            package_is_upgradable = False
            for candidate in avail_upgrades:
                if package_version_compare(candidate, installed_version) > 0:
                    package_is_upgradable = True
                    break
        else:
            package_is_upgradable = bool(avail_upgrades)
    else:
        try:
            package_is_upgradable = pkg.is_upgradable
        except AttributeError:
            # assume older version of python-apt is installed
            package_is_upgradable = pkg.isUpgradable

    return package_is_installed, package_is_upgradable, has_files

def expand_dpkg_options(dpkg_options_compressed):
    options_list = dpkg_options_compressed.split(',')
    dpkg_options = ""
    for dpkg_option in options_list:
        dpkg_options = '%s -o "Dpkg::Options::=--%s"' \
                       % (dpkg_options, dpkg_option)
    return dpkg_options.strip()

def expand_pkgspec_from_fnmatches(m, pkgspec, cache):
    new_pkgspec = []
    for pkgspec_pattern in pkgspec:
        pkgname_pattern, version = package_split(pkgspec_pattern)

        # note that none of these chars is allowed in a (debian) pkgname
        if frozenset('*?[]!').intersection(pkgname_pattern):
            # handle multiarch pkgnames, the idea is that "apt*" should
            # only select native packages. But "apt*:i386" should still work
            if not ":" in pkgname_pattern:
                try:
                    pkg_name_cache = _non_multiarch
                except NameError:
                    pkg_name_cache = _non_multiarch = [pkg.name for pkg in cache if not ':' in pkg.name]
            else:
                try:
                    pkg_name_cache = _all_pkg_names
                except NameError:
                    pkg_name_cache = _all_pkg_names = [pkg.name for pkg in cache]
            matches = fnmatch.filter(pkg_name_cache, pkgname_pattern)

            if len(matches) == 0:
                m.fail_json(msg="No package(s) matching '%s' available" % str(pkgname_pattern))
            else:
                new_pkgspec.extend(matches)
        else:
            # No wildcards in name
            new_pkgspec.append(pkgspec_pattern)
    return new_pkgspec

def install(m, pkgspec, cache, upgrade=False, default_release=None,
            install_recommends=True, force=False,
            dpkg_options=expand_dpkg_options(DPKG_OPTIONS),
            build_dep=False):
    pkg_list = []
    packages = ""
    pkgspec = expand_pkgspec_from_fnmatches(m, pkgspec, cache)
    for package in pkgspec:
        name, version = package_split(package)
        installed, upgradable, has_files = package_status(m, name, version, cache, state='install')
        if build_dep:
            # Let apt decide what to install
            pkg_list.append("'%s'" % package)
            continue
        if not installed or (upgrade and upgradable):
            pkg_list.append("'%s'" % package)
        if installed and upgradable and version:
            # This happens when the package is installed, a newer version is
            # available, and the version is a wildcard that matches both
            #
            # We do not apply the upgrade flag because we cannot specify both
            # a version and state=latest.  (This behaviour mirrors how apt
            # treats a version with wildcard in the package)
            pkg_list.append("'%s'" % package)
    packages = ' '.join(pkg_list)

    if len(packages) != 0:
        if force:
            force_yes = '--force-yes'
        else:
            force_yes = ''

        if m.check_mode:
            check_arg = '--simulate'
        else:
            check_arg = ''

        for (k,v) in APT_ENV_VARS.iteritems():
            os.environ[k] = v

        if build_dep:
            cmd = "%s -y %s %s %s build-dep %s" % (APT_GET_CMD, dpkg_options, force_yes, check_arg, packages)
        else:
            cmd = "%s -y %s %s %s install %s" % (APT_GET_CMD, dpkg_options, force_yes, check_arg, packages)

        if default_release:
            cmd += " -t '%s'" % (default_release,)
        if not install_recommends:
            cmd += " --no-install-recommends"

        rc, out, err = m.run_command(cmd)
        if rc:
            return (False, dict(msg="'%s' failed: %s" % (cmd, err), stdout=out, stderr=err))
        else:
            return (True, dict(changed=True, stdout=out, stderr=err))
    else:
        return (True, dict(changed=False))

def install_deb(m, debs, cache, force, install_recommends, dpkg_options):
    changed=False
    deps_to_install = []
    pkgs_to_install = []
    for deb_file in debs.split(','):
        try:
            pkg = apt.debfile.DebPackage(deb_file)
        except SystemError, e:
            m.fail_json(msg="Error: %s\nSystem Error: %s" % (pkg._failure_string,str(e)))

        # Check if it's already installed
        if pkg.compare_to_version_in_cache() == pkg.VERSION_SAME:
            continue
        # Check if package is installable
        if not pkg.check() and not force:
            m.fail_json(msg=pkg._failure_string)

        # add any missing deps to the list of deps we need
        # to install so they're all done in one shot
        deps_to_install.extend(pkg.missing_deps)

        # and add this deb to the list of packages to install
        pkgs_to_install.append(deb_file)

    # install the deps through apt
    retvals = {}
    if len(deps_to_install) > 0:
        (success, retvals) = install(m=m, pkgspec=deps_to_install, cache=cache,
                                     install_recommends=install_recommends,
                                     dpkg_options=expand_dpkg_options(dpkg_options))
        if not success:
            m.fail_json(**retvals)
        changed = retvals.get('changed', False)

    if len(pkgs_to_install) > 0:
        options = ' '.join(["--%s"% x for x in dpkg_options.split(",")])
        if m.check_mode:
            options += " --simulate"
        if force:
            options += " --force-all"

        cmd = "dpkg %s -i %s" % (options, " ".join(pkgs_to_install))
        rc, out, err = m.run_command(cmd)
        if "stdout" in retvals:
            stdout = retvals["stdout"] + out
        else:
            stdout = out
        if "stderr" in retvals:
            stderr = retvals["stderr"] + err
        else:
            stderr = err

        if rc == 0:
            m.exit_json(changed=True, stdout=stdout, stderr=stderr)
        else:
            m.fail_json(msg="%s failed" % cmd, stdout=stdout, stderr=stderr)
    else:
        m.exit_json(changed=changed, stdout=retvals.get('stdout',''), stderr=retvals.get('stderr',''))

def remove(m, pkgspec, cache, purge=False,
           dpkg_options=expand_dpkg_options(DPKG_OPTIONS)):
    pkg_list = []
    pkgspec = expand_pkgspec_from_fnmatches(m, pkgspec, cache)
    for package in pkgspec:
        name, version = package_split(package)
        installed, upgradable, has_files = package_status(m, name, version, cache, state='remove')
        if installed or (has_files and purge):
            pkg_list.append("'%s'" % package)
    packages = ' '.join(pkg_list)

    if len(packages) == 0:
        m.exit_json(changed=False)
    else:
        if purge:
            purge = '--purge'
        else:
            purge = ''

        for (k,v) in APT_ENV_VARS.iteritems():
            os.environ[k] = v

        cmd = "%s -q -y %s %s remove %s" % (APT_GET_CMD, dpkg_options, purge, packages)

        if m.check_mode:
            m.exit_json(changed=True)

        rc, out, err = m.run_command(cmd)
        if rc:
            m.fail_json(msg="'apt-get remove %s' failed: %s" % (packages, err), stdout=out, stderr=err)
        m.exit_json(changed=True, stdout=out, stderr=err)

def upgrade(m, mode="yes", force=False, default_release=None,
            dpkg_options=expand_dpkg_options(DPKG_OPTIONS)):
    if m.check_mode:
        check_arg = '--simulate'
    else:
        check_arg = ''

    apt_cmd = None
    prompt_regex = None
    if mode == "dist":
        # apt-get dist-upgrade
        apt_cmd = APT_GET_CMD
        upgrade_command = "dist-upgrade"
    elif mode == "full":
        # aptitude full-upgrade
        apt_cmd = APTITUDE_CMD
        upgrade_command = "full-upgrade"
    else:
        # aptitude safe-upgrade # mode=yes # default
        apt_cmd = APTITUDE_CMD
        upgrade_command = "safe-upgrade"
        prompt_regex = r"(^Do you want to ignore this warning and proceed anyway\?|^\*\*\*.*\[default=.*\])"

    if force:
        if apt_cmd == APT_GET_CMD:
            force_yes = '--force-yes'
        else:
            force_yes = '--assume-yes --allow-untrusted'
    else:
        force_yes = ''

    apt_cmd_path = m.get_bin_path(apt_cmd, required=True)

    for (k,v) in APT_ENV_VARS.iteritems():
        os.environ[k] = v

    cmd = '%s -y %s %s %s %s' % (apt_cmd_path, dpkg_options,
                                    force_yes, check_arg, upgrade_command)

    if default_release:
        cmd += " -t '%s'" % (default_release,)

    rc, out, err = m.run_command(cmd, prompt_regex=prompt_regex)
    if rc:
        m.fail_json(msg="'%s %s' failed: %s" % (apt_cmd, upgrade_command, err), stdout=out)
    if (apt_cmd == APT_GET_CMD and APT_GET_ZERO in out) or (apt_cmd == APTITUDE_CMD and APTITUDE_ZERO in out):
        m.exit_json(changed=False, msg=out, stdout=out, stderr=err)
    m.exit_json(changed=True, msg=out, stdout=out, stderr=err)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(default='present', choices=['installed', 'latest', 'removed', 'absent', 'present', 'build-dep']),
            update_cache = dict(default=False, aliases=['update-cache'], type='bool'),
            cache_valid_time = dict(type='int'),
            purge = dict(default=False, type='bool'),
            package = dict(default=None, aliases=['pkg', 'name'], type='list'),
            deb = dict(default=None),
            default_release = dict(default=None, aliases=['default-release']),
            install_recommends = dict(default='yes', aliases=['install-recommends'], type='bool'),
            force = dict(default='no', type='bool'),
            upgrade = dict(choices=['yes', 'safe', 'full', 'dist']),
            dpkg_options = dict(default=DPKG_OPTIONS)
        ),
        mutually_exclusive = [['package', 'upgrade', 'deb']],
        required_one_of = [['package', 'upgrade', 'update_cache', 'deb']],
        supports_check_mode = True
    )

    if not HAS_PYTHON_APT:
        try:
            module.run_command('apt-get update && apt-get install python-apt -y -q', use_unsafe_shell=True, check_rc=True)
            global apt, apt_pkg
            import apt
            import apt_pkg
        except ImportError:
            module.fail_json(msg="Could not import python modules: apt, apt_pkg. Please install python-apt package.")

    global APTITUDE_CMD
    APTITUDE_CMD = module.get_bin_path("aptitude", False)
    global APT_GET_CMD
    APT_GET_CMD = module.get_bin_path("apt-get")

    p = module.params
    if not APTITUDE_CMD and p.get('upgrade', None) in [ 'full', 'safe', 'yes' ]:
        module.fail_json(msg="Could not find aptitude. Please ensure it is installed.")

    install_recommends = p['install_recommends']
    dpkg_options = expand_dpkg_options(p['dpkg_options'])

    # Deal with deprecated aliases
    if p['state'] == 'installed':
        p['state'] = 'present'
    if p['state'] == 'removed':
        p['state'] = 'absent'

    try:
        cache = apt.Cache()
        if p['default_release']:
            try:
                apt_pkg.config['APT::Default-Release'] = p['default_release']
            except AttributeError:
                apt_pkg.Config['APT::Default-Release'] = p['default_release']
            # reopen cache w/ modified config
            cache.open(progress=None)

        if p['update_cache']:
            # Default is: always update the cache
            cache_valid = False
            if p['cache_valid_time']:
                tdelta = datetime.timedelta(seconds=p['cache_valid_time'])
                try:
                    mtime = os.stat(APT_UPDATE_SUCCESS_STAMP_PATH).st_mtime
                except:
                    mtime = False
                if mtime is False:
                    # Looks like the update-success-stamp is not available
                    # Fallback: Checking the mtime of the lists
                    try:
                        mtime = os.stat(APT_LISTS_PATH).st_mtime
                    except:
                        mtime = False
                if mtime is False:
                    # No mtime could be read - looks like lists are not there
                    # We update the cache to be safe
                    cache_valid = False
                else:
                    mtimestamp = datetime.datetime.fromtimestamp(mtime)
                    if mtimestamp + tdelta >= datetime.datetime.now():
                        # dont update the cache
                        # the old cache is less than cache_valid_time seconds old - so still valid
                        cache_valid = True

            if cache_valid is not True:
                cache.update()
                cache.open(progress=None)
            if not p['package'] and not p['upgrade'] and not p['deb']:
                module.exit_json(changed=False)

        force_yes = p['force']

        if p['upgrade']:
            upgrade(module, p['upgrade'], force_yes,
                    p['default_release'], dpkg_options)

        if p['deb']:
            if p['state'] != 'present':
                module.fail_json(msg="deb only supports state=present")
            install_deb(module, p['deb'], cache,
                        install_recommends=install_recommends,
                        force=force_yes, dpkg_options=p['dpkg_options'])

        packages = p['package']
        latest = p['state'] == 'latest'
        for package in packages:
            if package.count('=') > 1:
                module.fail_json(msg="invalid package spec: %s" % package)
            if latest and '=' in package:
                module.fail_json(msg='version number inconsistent with state=latest: %s' % package)

        if p['state'] in ('latest', 'present', 'build-dep'):
            state_upgrade = False
            state_builddep = False
            if p['state'] == 'latest':
                state_upgrade = True
            if p['state'] == 'build-dep':
                state_builddep = True
            result = install(module, packages, cache, upgrade=state_upgrade,
                    default_release=p['default_release'],
                    install_recommends=install_recommends,
                    force=force_yes, dpkg_options=dpkg_options,
                    build_dep=state_builddep)
            (success, retvals) = result
            if success:
                module.exit_json(**retvals)
            else:
                module.fail_json(**retvals)
        elif p['state'] == 'absent':
            remove(module, packages, cache, p['purge'], dpkg_options)

    except apt.cache.LockFailedException:
        module.fail_json(msg="Failed to lock apt for exclusive operation")
    except apt.cache.FetchFailedException:
        module.fail_json(msg="Could not fetch updated apt files")

# import module snippets
from ansible.module_utils.basic import *

if __name__ == "__main__":
    main()
