# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Flowroute LLC
# Written by Matthew Williams <matthew@flowroute.com>
# Based on yum module written by Seth Vidal <skvidal at fedoraproject.org>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


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
      - A list of package names, like V(foo), or package specifier with version, like V(foo=1.0) or V(foo>=1.0).
        Name wildcards (fnmatch) like V(apt*) and version wildcards like V(foo=1.0*) are also supported.
      - Do not use single or double quotes around the version when referring to the package name with a specific version, such as V(foo=1.0) or V(foo>=1.0).
    aliases: [ package, pkg ]
    type: list
    elements: str
  state:
    description:
      - Indicates the desired package state. V(latest) ensures that the latest version is installed. V(build-dep) ensures the package build dependencies
        are installed. V(fixed) attempt to correct a system with broken dependencies in place.
    type: str
    default: present
    choices: [ absent, build-dep, latest, present, fixed ]
  update_cache:
    description:
      - Run the equivalent of C(apt-get update) before the operation. Can be run as part of the package installation or as a separate step.
      - Default is not to update the cache.
    aliases: [ update-cache ]
    type: bool
  update_cache_retries:
    description:
      - Amount of retries if the cache update fails. Also see O(update_cache_retry_max_delay).
    type: int
    default: 5
    version_added: '2.10'
  update_cache_retry_max_delay:
    description:
      - Use an exponential backoff delay for each retry (see O(update_cache_retries)) up to this max delay in seconds.
    type: int
    default: 12
    version_added: '2.10'
  cache_valid_time:
    description:
      - Update the apt cache if it is older than the O(cache_valid_time). This option is set in seconds.
      - As of Ansible 2.4, if explicitly set, this sets O(update_cache=yes).
    type: int
    default: 0
  purge:
    description:
     - Will force purging of configuration files if O(state=absent) or O(autoremove=yes).
    type: bool
    default: 'no'
  default_release:
    description:
      - Corresponds to the C(-t) option for I(apt) and sets pin priorities.
    aliases: [ default-release ]
    type: str
  install_recommends:
    description:
      - Corresponds to the C(--no-install-recommends) option for C(apt). V(true) installs recommended packages. V(false) does not install
        recommended packages. By default, Ansible will use the same defaults as the operating system. Suggested packages are never installed.
    aliases: [ install-recommends ]
    type: bool
  force:
    description:
      - 'Corresponds to the C(--force-yes) to C(apt-get) and implies O(allow_unauthenticated=yes) and O(allow_downgrade=yes).'
      - "This option will disable checking both the packages' signatures and the certificates of the web servers they are downloaded from."
      - 'This option *is not* the equivalent of passing the C(-f) flag to C(apt-get) on the command line.'
      - '**This is a destructive operation with the potential to destroy your system, and it should almost never be used.**
         Please also see C(man apt-get) for more information.'
    type: bool
    default: 'no'
  clean:
    description:
      - Run the equivalent of C(apt-get clean) to clear out the local repository of retrieved package files. It removes everything but
        the lock file from C(/var/cache/apt/archives/) and C(/var/cache/apt/archives/partial/).
      - Can be run as part of the package installation (clean runs before install) or as a separate step.
    type: bool
    default: 'no'
    version_added: "2.13"
  allow_unauthenticated:
    description:
      - Ignore if packages cannot be authenticated. This is useful for bootstrapping environments that manage their own apt-key setup.
      - 'O(allow_unauthenticated) is only supported with O(state): V(install)/V(present).'
    aliases: [ allow-unauthenticated ]
    type: bool
    default: 'no'
    version_added: "2.1"
  allow_downgrade:
    description:
      - Corresponds to the C(--allow-downgrades) option for I(apt).
      - This option enables the named package and version to replace an already installed higher version of that package.
      - Note that setting O(allow_downgrade=true) can make this module behave in a non-idempotent way.
      - (The task could end up with a set of packages that does not match the complete list of specified packages to install).
      - 'O(allow_downgrade) is only supported by C(apt) and will be ignored if C(aptitude) is detected or specified.'
    aliases: [ allow-downgrade, allow_downgrades, allow-downgrades ]
    type: bool
    default: 'no'
    version_added: "2.12"
  allow_change_held_packages:
    description:
      - Allows changing the version of a package which is on the apt hold list.
    type: bool
    default: 'no'
    version_added: '2.13'
  upgrade:
    description:
      - If yes or safe, performs an aptitude safe-upgrade.
      - If full, performs an aptitude full-upgrade.
      - If dist, performs an apt-get dist-upgrade.
      - 'Note: This does not upgrade a specific package, use state=latest for that.'
      - 'Note: Since 2.4, apt-get is used as a fall-back if aptitude is not present.'
    version_added: "1.1"
    choices: [ dist, full, 'no', safe, 'yes' ]
    default: 'no'
    type: str
  dpkg_options:
    description:
      - Add C(dpkg) options to C(apt) command. Defaults to C(-o "Dpkg::Options::=--force-confdef" -o "Dpkg::Options::=--force-confold").
      - Options should be supplied as comma separated list.
    default: force-confdef,force-confold
    type: str
  deb:
     description:
       - Path to a .deb package on the remote machine.
       - If C(://) in the path, ansible will attempt to download deb before installing. (Version added 2.1)
       - Requires the C(xz-utils) package to extract the control file of the deb package to install.
     type: path
     required: false
     version_added: "1.6"
  autoremove:
    description:
      - If V(true), remove unused dependency packages for all module states except V(build-dep). It can also be used as the only option.
      - Previous to version 2.4, O(autoclean) was also an alias for O(autoremove), now it is its own separate command.
        See documentation for further information.
    type: bool
    default: 'no'
    version_added: "2.1"
  autoclean:
    description:
      - If V(true), cleans the local repository of retrieved package files that can no longer be downloaded.
    type: bool
    default: 'no'
    version_added: "2.4"
  policy_rc_d:
    description:
      - Force the exit code of C(/usr/sbin/policy-rc.d).
      - For example, if O(policy_rc_d=101) the installed package will not trigger a service start.
      - If C(/usr/sbin/policy-rc.d) already exists, it is backed up and restored after the package installation.
      - If V(null), the C(/usr/sbin/policy-rc.d) is not created/changed.
    type: int
    default: null
    version_added: "2.8"
  only_upgrade:
    description:
      - Only upgrade a package if it is already installed.
    type: bool
    default: 'no'
    version_added: "2.1"
  fail_on_autoremove:
    description:
      - 'Corresponds to the C(--no-remove) option for C(apt).'
      - 'If V(true), it is ensured that no packages will be removed or the task will fail.'
      - 'O(fail_on_autoremove) is only supported with O(state) except V(absent).'
      - 'O(fail_on_autoremove) is only supported by C(apt) and will be ignored if C(aptitude) is detected or specified.'
    type: bool
    default: 'no'
    version_added: "2.11"
  force_apt_get:
    description:
      - Force usage of apt-get instead of aptitude.
    type: bool
    default: 'no'
    version_added: "2.4"
  lock_timeout:
    description:
      - How many seconds will this action wait to acquire a lock on the apt db.
      - Sometimes there is a transitory lock and this will retry at least until timeout is hit.
    type: int
    default: 60
    version_added: "2.12"
requirements:
   - python-apt (python 2)
   - python3-apt (python 3)
   - aptitude (before 2.4)
author: "Matthew Williams (@mgwilliams)"
extends_documentation_fragment: action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
    platform:
        platforms: debian
notes:
   - Three of the upgrade modes (V(full), V(safe) and its alias V(true)) required C(aptitude) up to 2.3, since 2.4 C(apt-get) is used as a fall-back.
   - In most cases, packages installed with I(apt) will start newly installed services by default. Most distributions have mechanisms to avoid this.
     For example when installing Postgresql-9.5 in Debian 9, creating an executable shell script (/usr/sbin/policy-rc.d) that throws
     a return code of 101 will stop Postgresql 9.5 starting up after install. Remove the file or its execute permission afterward.
   - The C(apt-get) commandline supports implicit regex matches here but we do not because it can let typos through easier
     (If you typo C(foo) as C(fo) apt-get would install packages that have "fo" in their name with a warning and a prompt for the user.
     Since there are no warnings and prompts before installing, we disallow this. Use an explicit fnmatch pattern if you want wildcarding).
   - When used with a C(loop:) each package will be processed individually, it is much more efficient to pass the list directly to the O(name) option.
   - When O(default_release) is used, an implicit priority of 990 is used. This is the same behavior as C(apt-get -t).
   - When an exact version is specified, an implicit priority of 1001 is used.
   - If the interpreter can't import C(python-apt)/C(python3-apt) the module will check for it in system-owned interpreters as well.
     If the dependency can't be found, the module will attempt to install it.
     If the dependency is found or installed, the module will be respawned under the correct interpreter.
'''

EXAMPLES = '''
- name: Install apache httpd (state=present is optional)
  ansible.builtin.apt:
    name: apache2
    state: present

- name: Update repositories cache and install "foo" package
  ansible.builtin.apt:
    name: foo
    update_cache: yes

- name: Remove "foo" package
  ansible.builtin.apt:
    name: foo
    state: absent

- name: Install the package "foo"
  ansible.builtin.apt:
    name: foo

- name: Install a list of packages
  ansible.builtin.apt:
    pkg:
    - foo
    - foo-tools

- name: Install the version '1.00' of package "foo"
  ansible.builtin.apt:
    name: foo=1.00

- name: Update the repository cache and update package "nginx" to latest version using default release squeeze-backport
  ansible.builtin.apt:
    name: nginx
    state: latest
    default_release: squeeze-backports
    update_cache: yes

- name: Install the version '1.18.0' of package "nginx" and allow potential downgrades
  ansible.builtin.apt:
    name: nginx=1.18.0
    state: present
    allow_downgrade: yes

- name: Install zfsutils-linux with ensuring conflicted packages (e.g. zfs-fuse) will not be removed.
  ansible.builtin.apt:
    name: zfsutils-linux
    state: latest
    fail_on_autoremove: yes

- name: Install latest version of "openjdk-6-jdk" ignoring "install-recommends"
  ansible.builtin.apt:
    name: openjdk-6-jdk
    state: latest
    install_recommends: no

- name: Update all packages to their latest version
  ansible.builtin.apt:
    name: "*"
    state: latest

- name: Upgrade the OS (apt-get dist-upgrade)
  ansible.builtin.apt:
    upgrade: dist

- name: Run the equivalent of "apt-get update" as a separate step
  ansible.builtin.apt:
    update_cache: yes

- name: Only run "update_cache=yes" if the last one is more than 3600 seconds ago
  ansible.builtin.apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Pass options to dpkg on run
  ansible.builtin.apt:
    upgrade: dist
    update_cache: yes
    dpkg_options: 'force-confold,force-confdef'

- name: Install a .deb package
  ansible.builtin.apt:
    deb: /tmp/mypackage.deb

- name: Install the build dependencies for package "foo"
  ansible.builtin.apt:
    pkg: foo
    state: build-dep

- name: Install a .deb package from the internet
  ansible.builtin.apt:
    deb: https://example.com/python-ppq_0.1-1_all.deb

- name: Remove useless packages from the cache
  ansible.builtin.apt:
    autoclean: yes

- name: Remove dependencies that are no longer required
  ansible.builtin.apt:
    autoremove: yes

- name: Remove dependencies that are no longer required and purge their configuration files
  ansible.builtin.apt:
    autoremove: yes
    purge: true

- name: Run the equivalent of "apt-get clean" as a separate step
  ansible.builtin.apt:
    clean: yes
'''

RETURN = '''
cache_updated:
    description: if the cache was updated or not
    returned: success, in some cases
    type: bool
    sample: True
cache_update_time:
    description: time of the last cache update (0 if unknown)
    returned: success, in some cases
    type: int
    sample: 1425828348000
stdout:
    description: output from apt
    returned: success, when needed
    type: str
    sample: |-
        Reading package lists...
        Building dependency tree...
        Reading state information...
        The following extra packages will be installed:
          apache2-bin ...
stderr:
    description: error output from apt
    returned: success, when needed
    type: str
    sample: "AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 127.0.1.1. Set the 'ServerName' directive globally to ..."
'''  # NOQA

# added to stave off future warnings about apt api
import warnings
warnings.filterwarnings('ignore', "apt API not stable yet", FutureWarning)

import datetime
import fnmatch
import locale as locale_module
import os
import re
import secrets
import shutil
import sys
import tempfile
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.file import S_IRWXU_RXG_RXO
from ansible.module_utils.common.locale import get_best_parsable_locale
from ansible.module_utils.common.respawn import has_respawned, probe_interpreters_for_module, respawn_module
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.six import string_types
from ansible.module_utils.urls import fetch_file

DPKG_OPTIONS = 'force-confdef,force-confold'
APT_GET_ZERO = "\n0 upgraded, 0 newly installed, 0 to remove"
APTITUDE_ZERO = "\n0 packages upgraded, 0 newly installed, 0 to remove"
APT_LISTS_PATH = "/var/lib/apt/lists"
APT_UPDATE_SUCCESS_STAMP_PATH = "/var/lib/apt/periodic/update-success-stamp"
APT_MARK_INVALID_OP = 'Invalid operation'
APT_MARK_INVALID_OP_DEB6 = 'Usage: apt-mark [options] {markauto|unmarkauto} packages'

CLEAN_OP_CHANGED_STR = dict(
    autoremove='The following packages will be REMOVED',
    # "Del python3-q 2.4-1 [24 kB]"
    autoclean='Del ',
)


HAS_PYTHON_APT = False
try:
    import apt
    import apt.debfile
    import apt_pkg
    HAS_PYTHON_APT = True
except ImportError:
    apt = apt_pkg = None


class PolicyRcD(object):
    """
    This class is a context manager for the /usr/sbin/policy-rc.d file.
    It allow the user to prevent dpkg to start the corresponding service when installing
    a package.
    https://people.debian.org/~hmh/invokerc.d-policyrc.d-specification.txt
    """

    def __init__(self, module):
        # we need the module for later use (eg. fail_json)
        self.m = module

        # if policy_rc_d is null then we don't need to modify policy-rc.d
        if self.m.params['policy_rc_d'] is None:
            return

        # if the /usr/sbin/policy-rc.d already exists
        # we will back it up during package installation
        # then restore it
        if os.path.exists('/usr/sbin/policy-rc.d'):
            self.backup_dir = tempfile.mkdtemp(prefix="ansible")
        else:
            self.backup_dir = None

    def __enter__(self):
        """
        This method will be called when we enter the context, before we call `apt-get …`
        """

        # if policy_rc_d is null then we don't need to modify policy-rc.d
        if self.m.params['policy_rc_d'] is None:
            return

        # if the /usr/sbin/policy-rc.d already exists we back it up
        if self.backup_dir:
            try:
                shutil.move('/usr/sbin/policy-rc.d', self.backup_dir)
            except Exception:
                self.m.fail_json(msg="Fail to move /usr/sbin/policy-rc.d to %s" % self.backup_dir)

        # we write /usr/sbin/policy-rc.d so it always exits with code policy_rc_d
        try:
            with open('/usr/sbin/policy-rc.d', 'w') as policy_rc_d:
                policy_rc_d.write('#!/bin/sh\nexit %d\n' % self.m.params['policy_rc_d'])

            os.chmod('/usr/sbin/policy-rc.d', S_IRWXU_RXG_RXO)
        except Exception:
            self.m.fail_json(msg="Failed to create or chmod /usr/sbin/policy-rc.d")

    def __exit__(self, type, value, traceback):
        """
        This method will be called when we exit the context, after `apt-get …` is done
        """

        # if policy_rc_d is null then we don't need to modify policy-rc.d
        if self.m.params['policy_rc_d'] is None:
            return

        if self.backup_dir:
            # if /usr/sbin/policy-rc.d already exists before the call to __enter__
            # we restore it (from the backup done in __enter__)
            try:
                shutil.move(os.path.join(self.backup_dir, 'policy-rc.d'),
                            '/usr/sbin/policy-rc.d')
                os.rmdir(self.backup_dir)
            except Exception:
                self.m.fail_json(msg="Fail to move back %s to /usr/sbin/policy-rc.d"
                                     % os.path.join(self.backup_dir, 'policy-rc.d'))
        else:
            # if there wasn't a /usr/sbin/policy-rc.d file before the call to __enter__
            # we just remove the file
            try:
                os.remove('/usr/sbin/policy-rc.d')
            except Exception:
                self.m.fail_json(msg="Fail to remove /usr/sbin/policy-rc.d (after package manipulation)")


def package_split(pkgspec):
    parts = re.split(r'(>?=)', pkgspec, 1)
    if len(parts) > 1:
        return parts
    return parts[0], None, None


def package_version_compare(version, other_version):
    try:
        return apt_pkg.version_compare(version, other_version)
    except AttributeError:
        return apt_pkg.VersionCompare(version, other_version)


def package_best_match(pkgname, version_cmp, version, release, cache):
    policy = apt_pkg.Policy(cache)

    policy.read_pinfile(apt_pkg.config.find_file("Dir::Etc::preferences"))
    policy.read_pindir(apt_pkg.config.find_file("Dir::Etc::preferencesparts"))

    if release:
        # 990 is the priority used in `apt-get -t`
        policy.create_pin('Release', pkgname, release, 990)
    if version_cmp == "=":
        # Installing a specific version from command line overrides all pinning
        # We don't mimic this exactly, but instead set a priority which is higher than all APT built-in pin priorities.
        policy.create_pin('Version', pkgname, version, 1001)
    pkg = cache[pkgname]
    pkgver = policy.get_candidate_ver(pkg)
    if not pkgver:
        return None
    if version_cmp == "=" and not fnmatch.fnmatch(pkgver.ver_str, version):
        # Even though we put in a pin policy, it can be ignored if there is no
        # possible candidate.
        return None
    return pkgver.ver_str


def package_status(m, pkgname, version_cmp, version, default_release, cache, state):
    """
    :return: A tuple of (installed, installed_version, version_installable, has_files). *installed* indicates whether
    the package (regardless of version) is installed. *installed_version* indicates whether the installed package
    matches the provided version criteria. *version_installable* provides the latest matching version that can be
    installed. In the case of virtual packages where we can't determine an applicable match, True is returned.
    *has_files* indicates whether the package has files on the filesystem (even if not installed, meaning a purge is
    required).
    """
    try:
        # get the package from the cache, as well as the
        # low-level apt_pkg.Package object which contains
        # state fields not directly accessible from the
        # higher-level apt.package.Package object.
        pkg = cache[pkgname]
        ll_pkg = cache._cache[pkgname]  # the low-level package object
    except KeyError:
        if state == 'install':
            try:
                provided_packages = cache.get_providing_packages(pkgname)
                if provided_packages:
                    # When this is a virtual package satisfied by only
                    # one installed package, return the status of the target
                    # package to avoid requesting re-install
                    if cache.is_virtual_package(pkgname) and len(provided_packages) == 1:
                        package = provided_packages[0]
                        installed, installed_version, version_installable, has_files = \
                            package_status(m, package.name, version_cmp, version, default_release, cache, state='install')
                        if installed:
                            return installed, installed_version, version_installable, has_files

                    # Otherwise return nothing so apt will sort out
                    # what package to satisfy this with
                    return False, False, True, False

                m.fail_json(msg="No package matching '%s' is available" % pkgname)
            except AttributeError:
                # python-apt version too old to detect virtual packages
                # mark as not installed and let apt-get install deal with it
                return False, False, True, False
        else:
            return False, False, None, False
    try:
        has_files = len(pkg.installed_files) > 0
    except UnicodeDecodeError:
        has_files = True
    except AttributeError:
        has_files = False  # older python-apt cannot be used to determine non-purged

    try:
        package_is_installed = ll_pkg.current_state == apt_pkg.CURSTATE_INSTALLED
    except AttributeError:  # python-apt 0.7.X has very weak low-level object
        try:
            # might not be necessary as python-apt post-0.7.X should have current_state property
            package_is_installed = pkg.is_installed
        except AttributeError:
            # assume older version of python-apt is installed
            package_is_installed = pkg.isInstalled

    version_best = package_best_match(pkgname, version_cmp, version, default_release, cache._cache)
    version_is_installed = False
    version_installable = None
    if package_is_installed:
        try:
            installed_version = pkg.installed.version
        except AttributeError:
            installed_version = pkg.installedVersion

        if version_cmp == "=":
            # check if the version is matched as well
            version_is_installed = fnmatch.fnmatch(installed_version, version)
            if version_best and installed_version != version_best and fnmatch.fnmatch(version_best, version):
                version_installable = version_best
        elif version_cmp == ">=":
            version_is_installed = apt_pkg.version_compare(installed_version, version) >= 0
            if version_best and installed_version != version_best and apt_pkg.version_compare(version_best, version) >= 0:
                version_installable = version_best
        else:
            version_is_installed = True
            if version_best and installed_version != version_best:
                version_installable = version_best
    else:
        version_installable = version_best

    return package_is_installed, version_is_installed, version_installable, has_files


def expand_dpkg_options(dpkg_options_compressed):
    options_list = dpkg_options_compressed.split(',')
    dpkg_options = ""
    for dpkg_option in options_list:
        dpkg_options = '%s -o "Dpkg::Options::=--%s"' \
                       % (dpkg_options, dpkg_option)
    return dpkg_options.strip()


def expand_pkgspec_from_fnmatches(m, pkgspec, cache):
    # Note: apt-get does implicit regex matching when an exact package name
    # match is not found.  Something like this:
    # matches = [pkg.name for pkg in cache if re.match(pkgspec, pkg.name)]
    # (Should also deal with the ':' for multiarch like the fnmatch code below)
    #
    # We have decided not to do similar implicit regex matching but might take
    # a PR to add some sort of explicit regex matching:
    # https://github.com/ansible/ansible-modules-core/issues/1258
    new_pkgspec = []
    if pkgspec:
        for pkgspec_pattern in pkgspec:

            if not isinstance(pkgspec_pattern, string_types):
                m.fail_json(msg="Invalid type for package name, expected string but got %s" % type(pkgspec_pattern))

            pkgname_pattern, version_cmp, version = package_split(pkgspec_pattern)

            # note that none of these chars is allowed in a (debian) pkgname
            if frozenset('*?[]!').intersection(pkgname_pattern):
                # handle multiarch pkgnames, the idea is that "apt*" should
                # only select native packages. But "apt*:i386" should still work
                if ":" not in pkgname_pattern:
                    # Filter the multiarch packages from the cache only once
                    try:
                        pkg_name_cache = _non_multiarch  # pylint: disable=used-before-assignment
                    except NameError:
                        pkg_name_cache = _non_multiarch = [pkg.name for pkg in cache if ':' not in pkg.name]  # noqa: F841
                else:
                    # Create a cache of pkg_names including multiarch only once
                    try:
                        pkg_name_cache = _all_pkg_names  # pylint: disable=used-before-assignment
                    except NameError:
                        pkg_name_cache = _all_pkg_names = [pkg.name for pkg in cache]  # noqa: F841

                matches = fnmatch.filter(pkg_name_cache, pkgname_pattern)

                if not matches:
                    m.fail_json(msg="No package(s) matching '%s' available" % to_text(pkgname_pattern))
                else:
                    new_pkgspec.extend(matches)
            else:
                # No wildcards in name
                new_pkgspec.append(pkgspec_pattern)
    return new_pkgspec


def parse_diff(output):
    diff = to_native(output).splitlines()
    try:
        # check for start marker from aptitude
        diff_start = diff.index('Resolving dependencies...')
    except ValueError:
        try:
            # check for start marker from apt-get
            diff_start = diff.index('Reading state information...')
        except ValueError:
            # show everything
            diff_start = -1
    try:
        # check for end marker line from both apt-get and aptitude
        diff_end = next(i for i, item in enumerate(diff) if re.match('[0-9]+ (packages )?upgraded', item))
    except StopIteration:
        diff_end = len(diff)
    diff_start += 1
    diff_end += 1
    return {'prepared': '\n'.join(diff[diff_start:diff_end])}


def mark_installed_manually(m, packages):
    if not packages:
        return

    apt_mark_cmd_path = m.get_bin_path("apt-mark")

    # https://github.com/ansible/ansible/issues/40531
    if apt_mark_cmd_path is None:
        m.warn("Could not find apt-mark binary, not marking package(s) as manually installed.")
        return

    cmd = "%s manual %s" % (apt_mark_cmd_path, ' '.join(packages))
    rc, out, err = m.run_command(cmd)

    if APT_MARK_INVALID_OP in err or APT_MARK_INVALID_OP_DEB6 in err:
        cmd = "%s unmarkauto %s" % (apt_mark_cmd_path, ' '.join(packages))
        rc, out, err = m.run_command(cmd)

    if rc != 0:
        m.fail_json(msg="'%s' failed: %s" % (cmd, err), stdout=out, stderr=err, rc=rc)


def install(m, pkgspec, cache, upgrade=False, default_release=None,
            install_recommends=None, force=False,
            dpkg_options=expand_dpkg_options(DPKG_OPTIONS),
            build_dep=False, fixed=False, autoremove=False, fail_on_autoremove=False, only_upgrade=False,
            allow_unauthenticated=False, allow_downgrade=False, allow_change_held_packages=False):
    pkg_list = []
    packages = ""
    pkgspec = expand_pkgspec_from_fnmatches(m, pkgspec, cache)
    package_names = []
    for package in pkgspec:
        if build_dep:
            # Let apt decide what to install
            pkg_list.append("'%s'" % package)
            continue

        name, version_cmp, version = package_split(package)
        package_names.append(name)
        installed, installed_version, version_installable, has_files = package_status(m, name, version_cmp, version, default_release, cache, state='install')

        if not installed and only_upgrade:
            # only_upgrade upgrades packages that are already installed
            # since this package is not installed, skip it
            continue

        if not installed_version and not version_installable:
            status = False
            data = dict(msg="no available installation candidate for %s" % package)
            return (status, data)

        if version_installable and ((not installed and not only_upgrade) or upgrade or not installed_version):
            if version_installable is not True:
                pkg_list.append("'%s=%s'" % (name, version_installable))
            elif version:
                pkg_list.append("'%s=%s'" % (name, version))
            else:
                pkg_list.append("'%s'" % name)
        elif installed_version and version_installable and version_cmp == "=":
            # This happens when the package is installed, a newer version is
            # available, and the version is a wildcard that matches both
            #
            # This is legacy behavior, and isn't documented (in fact it does
            # things documentations says it shouldn't). It should not be relied
            # upon.
            pkg_list.append("'%s=%s'" % (name, version))
    packages = ' '.join(pkg_list)

    if packages:
        if force:
            force_yes = '--force-yes'
        else:
            force_yes = ''

        if m.check_mode:
            check_arg = '--simulate'
        else:
            check_arg = ''

        if autoremove:
            autoremove = '--auto-remove'
        else:
            autoremove = ''

        if fail_on_autoremove:
            fail_on_autoremove = '--no-remove'
        else:
            fail_on_autoremove = ''

        if only_upgrade:
            only_upgrade = '--only-upgrade'
        else:
            only_upgrade = ''

        if fixed:
            fixed = '--fix-broken'
        else:
            fixed = ''

        if build_dep:
            cmd = "%s -y %s %s %s %s %s %s build-dep %s" % (APT_GET_CMD, dpkg_options, only_upgrade, fixed, force_yes, fail_on_autoremove, check_arg, packages)
        else:
            cmd = "%s -y %s %s %s %s %s %s %s install %s" % \
                  (APT_GET_CMD, dpkg_options, only_upgrade, fixed, force_yes, autoremove, fail_on_autoremove, check_arg, packages)

        if default_release:
            cmd += " -t '%s'" % (default_release,)

        if install_recommends is False:
            cmd += " -o APT::Install-Recommends=no"
        elif install_recommends is True:
            cmd += " -o APT::Install-Recommends=yes"
        # install_recommends is None uses the OS default

        if allow_unauthenticated:
            cmd += " --allow-unauthenticated"

        if allow_downgrade:
            cmd += " --allow-downgrades"

        if allow_change_held_packages:
            cmd += " --allow-change-held-packages"

        with PolicyRcD(m):
            rc, out, err = m.run_command(cmd)

        if m._diff:
            diff = parse_diff(out)
        else:
            diff = {}
        status = True

        changed = True
        if build_dep:
            changed = APT_GET_ZERO not in out

        data = dict(changed=changed, stdout=out, stderr=err, diff=diff)
        if rc:
            status = False
            data = dict(msg="'%s' failed: %s" % (cmd, err), stdout=out, stderr=err, rc=rc)
    else:
        status = True
        data = dict(changed=False)

    if not build_dep and not m.check_mode:
        mark_installed_manually(m, package_names)

    return (status, data)


def get_field_of_deb(m, deb_file, field="Version"):
    cmd_dpkg = m.get_bin_path("dpkg", True)
    cmd = cmd_dpkg + " --field %s %s" % (deb_file, field)
    rc, stdout, stderr = m.run_command(cmd)
    if rc != 0:
        m.fail_json(msg="%s failed" % cmd, stdout=stdout, stderr=stderr)
    return to_native(stdout).strip('\n')


def install_deb(
        m, debs, cache, force, fail_on_autoremove, install_recommends,
        allow_unauthenticated,
        allow_downgrade,
        allow_change_held_packages,
        dpkg_options,
):
    changed = False
    deps_to_install = []
    pkgs_to_install = []
    for deb_file in debs.split(','):
        try:
            pkg = apt.debfile.DebPackage(deb_file, cache=apt.Cache())
            pkg_name = get_field_of_deb(m, deb_file, "Package")
            pkg_version = get_field_of_deb(m, deb_file, "Version")
            if hasattr(apt_pkg, 'get_architectures') and len(apt_pkg.get_architectures()) > 1:
                pkg_arch = get_field_of_deb(m, deb_file, "Architecture")
                pkg_key = "%s:%s" % (pkg_name, pkg_arch)
            else:
                pkg_key = pkg_name
            try:
                installed_pkg = apt.Cache()[pkg_key]
                installed_version = installed_pkg.installed.version
                if package_version_compare(pkg_version, installed_version) == 0:
                    # Does not need to down-/upgrade, move on to next package
                    continue
            except Exception:
                # Must not be installed, continue with installation
                pass
            # Check if package is installable
            if not pkg.check():
                if force or ("later version" in pkg._failure_string and allow_downgrade):
                    pass
                else:
                    m.fail_json(msg=pkg._failure_string)

            # add any missing deps to the list of deps we need
            # to install so they're all done in one shot
            deps_to_install.extend(pkg.missing_deps)

        except Exception as e:
            m.fail_json(msg="Unable to install package: %s" % to_native(e))

        # Install 'Recommends' of this deb file
        if install_recommends:
            pkg_recommends = get_field_of_deb(m, deb_file, "Recommends")
            deps_to_install.extend([pkg_name.strip() for pkg_name in pkg_recommends.split()])

        # and add this deb to the list of packages to install
        pkgs_to_install.append(deb_file)

    # install the deps through apt
    retvals = {}
    if deps_to_install:
        (success, retvals) = install(m=m, pkgspec=deps_to_install, cache=cache,
                                     install_recommends=install_recommends,
                                     fail_on_autoremove=fail_on_autoremove,
                                     allow_unauthenticated=allow_unauthenticated,
                                     allow_downgrade=allow_downgrade,
                                     allow_change_held_packages=allow_change_held_packages,
                                     dpkg_options=expand_dpkg_options(dpkg_options))
        if not success:
            m.fail_json(**retvals)
        changed = retvals.get('changed', False)

    if pkgs_to_install:
        options = ' '.join(["--%s" % x for x in dpkg_options.split(",")])
        if m.check_mode:
            options += " --simulate"
        if force:
            options += " --force-all"

        cmd = "dpkg %s -i %s" % (options, " ".join(pkgs_to_install))

        with PolicyRcD(m):
            rc, out, err = m.run_command(cmd)

        if "stdout" in retvals:
            stdout = retvals["stdout"] + out
        else:
            stdout = out
        if "diff" in retvals:
            diff = retvals["diff"]
            if 'prepared' in diff:
                diff['prepared'] += '\n\n' + out
        else:
            diff = parse_diff(out)
        if "stderr" in retvals:
            stderr = retvals["stderr"] + err
        else:
            stderr = err

        if rc == 0:
            m.exit_json(changed=True, stdout=stdout, stderr=stderr, diff=diff)
        else:
            m.fail_json(msg="%s failed" % cmd, stdout=stdout, stderr=stderr)
    else:
        m.exit_json(changed=changed, stdout=retvals.get('stdout', ''), stderr=retvals.get('stderr', ''), diff=retvals.get('diff', ''))


def remove(m, pkgspec, cache, purge=False, force=False,
           dpkg_options=expand_dpkg_options(DPKG_OPTIONS), autoremove=False,
           allow_change_held_packages=False):
    pkg_list = []
    pkgspec = expand_pkgspec_from_fnmatches(m, pkgspec, cache)
    for package in pkgspec:
        name, version_cmp, version = package_split(package)
        installed, installed_version, upgradable, has_files = package_status(m, name, version_cmp, version, None, cache, state='remove')
        if installed_version or (has_files and purge):
            pkg_list.append("'%s'" % package)
    packages = ' '.join(pkg_list)

    if not packages:
        m.exit_json(changed=False)
    else:
        if force:
            force_yes = '--force-yes'
        else:
            force_yes = ''

        if purge:
            purge = '--purge'
        else:
            purge = ''

        if autoremove:
            autoremove = '--auto-remove'
        else:
            autoremove = ''

        if m.check_mode:
            check_arg = '--simulate'
        else:
            check_arg = ''

        if allow_change_held_packages:
            allow_change_held_packages = '--allow-change-held-packages'
        else:
            allow_change_held_packages = ''

        cmd = "%s -q -y %s %s %s %s %s %s remove %s" % (
            APT_GET_CMD,
            dpkg_options,
            purge,
            force_yes,
            autoremove,
            check_arg,
            allow_change_held_packages,
            packages
        )

        with PolicyRcD(m):
            rc, out, err = m.run_command(cmd)

        if m._diff:
            diff = parse_diff(out)
        else:
            diff = {}
        if rc:
            m.fail_json(msg="'apt-get remove %s' failed: %s" % (packages, err), stdout=out, stderr=err, rc=rc)
        m.exit_json(changed=True, stdout=out, stderr=err, diff=diff)


def cleanup(m, purge=False, force=False, operation=None,
            dpkg_options=expand_dpkg_options(DPKG_OPTIONS)):

    if operation not in frozenset(['autoremove', 'autoclean']):
        raise AssertionError('Expected "autoremove" or "autoclean" cleanup operation, got %s' % operation)

    if force:
        force_yes = '--force-yes'
    else:
        force_yes = ''

    if purge:
        purge = '--purge'
    else:
        purge = ''

    if m.check_mode:
        check_arg = '--simulate'
    else:
        check_arg = ''

    cmd = "%s -y %s %s %s %s %s" % (APT_GET_CMD, dpkg_options, purge, force_yes, operation, check_arg)

    with PolicyRcD(m):
        rc, out, err = m.run_command(cmd)

    if m._diff:
        diff = parse_diff(out)
    else:
        diff = {}
    if rc:
        m.fail_json(msg="'apt-get %s' failed: %s" % (operation, err), stdout=out, stderr=err, rc=rc)

    changed = CLEAN_OP_CHANGED_STR[operation] in out

    m.exit_json(changed=changed, stdout=out, stderr=err, diff=diff)


def aptclean(m):
    clean_rc, clean_out, clean_err = m.run_command(['apt-get', 'clean'])
    clean_diff = parse_diff(clean_out) if m._diff else {}

    if clean_rc:
        m.fail_json(msg="apt-get clean failed", stdout=clean_out, rc=clean_rc)
    if clean_err:
        m.fail_json(msg="apt-get clean failed: %s" % clean_err, stdout=clean_out, rc=clean_rc)
    return (clean_out, clean_err, clean_diff)


def upgrade(m, mode="yes", force=False, default_release=None,
            use_apt_get=False,
            dpkg_options=expand_dpkg_options(DPKG_OPTIONS), autoremove=False, fail_on_autoremove=False,
            allow_unauthenticated=False,
            allow_downgrade=False,
            ):

    if autoremove:
        autoremove = '--auto-remove'
    else:
        autoremove = ''

    if m.check_mode:
        check_arg = '--simulate'
    else:
        check_arg = ''

    apt_cmd = None
    prompt_regex = None
    if mode == "dist" or (mode == "full" and use_apt_get):
        # apt-get dist-upgrade
        apt_cmd = APT_GET_CMD
        upgrade_command = "dist-upgrade %s" % (autoremove)
    elif mode == "full" and not use_apt_get:
        # aptitude full-upgrade
        apt_cmd = APTITUDE_CMD
        upgrade_command = "full-upgrade"
    else:
        if use_apt_get:
            apt_cmd = APT_GET_CMD
            upgrade_command = "upgrade --with-new-pkgs %s" % (autoremove)
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

    if fail_on_autoremove:
        if apt_cmd == APT_GET_CMD:
            fail_on_autoremove = '--no-remove'
        else:
            m.warn("APTITUDE does not support '--no-remove', ignoring the 'fail_on_autoremove' parameter.")
            fail_on_autoremove = ''
    else:
        fail_on_autoremove = ''

    allow_unauthenticated = '--allow-unauthenticated' if allow_unauthenticated else ''

    if allow_downgrade:
        if apt_cmd == APT_GET_CMD:
            allow_downgrade = '--allow-downgrades'
        else:
            m.warn("APTITUDE does not support '--allow-downgrades', ignoring the 'allow_downgrade' parameter.")
            allow_downgrade = ''
    else:
        allow_downgrade = ''

    if apt_cmd is None:
        if use_apt_get:
            apt_cmd = APT_GET_CMD
        else:
            m.fail_json(msg="Unable to find APTITUDE in path. Please make sure "
                            "to have APTITUDE in path or use 'force_apt_get=True'")
    apt_cmd_path = m.get_bin_path(apt_cmd, required=True)

    cmd = '%s -y %s %s %s %s %s %s %s' % (
        apt_cmd_path,
        dpkg_options,
        force_yes,
        fail_on_autoremove,
        allow_unauthenticated,
        allow_downgrade,
        check_arg,
        upgrade_command,
    )

    if default_release:
        cmd += " -t '%s'" % (default_release,)

    with PolicyRcD(m):
        rc, out, err = m.run_command(cmd, prompt_regex=prompt_regex)

    if m._diff:
        diff = parse_diff(out)
    else:
        diff = {}
    if rc:
        m.fail_json(msg="'%s %s' failed: %s" % (apt_cmd, upgrade_command, err), stdout=out, rc=rc)
    if (apt_cmd == APT_GET_CMD and APT_GET_ZERO in out) or (apt_cmd == APTITUDE_CMD and APTITUDE_ZERO in out):
        m.exit_json(changed=False, msg=out, stdout=out, stderr=err)
    m.exit_json(changed=True, msg=out, stdout=out, stderr=err, diff=diff)


def get_cache_mtime():
    """Return mtime of a valid apt cache file.
    Stat the apt cache file and if no cache file is found return 0
    :returns: ``int``
    """
    cache_time = 0
    if os.path.exists(APT_UPDATE_SUCCESS_STAMP_PATH):
        cache_time = os.stat(APT_UPDATE_SUCCESS_STAMP_PATH).st_mtime
    elif os.path.exists(APT_LISTS_PATH):
        cache_time = os.stat(APT_LISTS_PATH).st_mtime
    return cache_time


def get_updated_cache_time():
    """Return the mtime time stamp and the updated cache time.
    Always retrieve the mtime of the apt cache or set the `cache_mtime`
    variable to 0
    :returns: ``tuple``
    """
    cache_mtime = get_cache_mtime()
    mtimestamp = datetime.datetime.fromtimestamp(cache_mtime)
    updated_cache_time = int(time.mktime(mtimestamp.timetuple()))
    return mtimestamp, updated_cache_time


# https://github.com/ansible/ansible-modules-core/issues/2951
def get_cache(module):
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
                module.fail_json(msg='Updating the cache to correct corrupt package lists failed:\n%s\n%s' % (to_native(e), so + se), rc=rc)
            # try again
            cache = apt.Cache()
        else:
            module.fail_json(msg=to_native(e))
    return cache


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'build-dep', 'fixed', 'latest', 'present']),
            update_cache=dict(type='bool', aliases=['update-cache']),
            update_cache_retries=dict(type='int', default=5),
            update_cache_retry_max_delay=dict(type='int', default=12),
            cache_valid_time=dict(type='int', default=0),
            purge=dict(type='bool', default=False),
            package=dict(type='list', elements='str', aliases=['pkg', 'name']),
            deb=dict(type='path'),
            default_release=dict(type='str', aliases=['default-release']),
            install_recommends=dict(type='bool', aliases=['install-recommends']),
            force=dict(type='bool', default=False),
            upgrade=dict(type='str', choices=['dist', 'full', 'no', 'safe', 'yes'], default='no'),
            dpkg_options=dict(type='str', default=DPKG_OPTIONS),
            autoremove=dict(type='bool', default=False),
            autoclean=dict(type='bool', default=False),
            fail_on_autoremove=dict(type='bool', default=False),
            policy_rc_d=dict(type='int', default=None),
            only_upgrade=dict(type='bool', default=False),
            force_apt_get=dict(type='bool', default=False),
            clean=dict(type='bool', default=False),
            allow_unauthenticated=dict(type='bool', default=False, aliases=['allow-unauthenticated']),
            allow_downgrade=dict(type='bool', default=False, aliases=['allow-downgrade', 'allow_downgrades', 'allow-downgrades']),
            allow_change_held_packages=dict(type='bool', default=False),
            lock_timeout=dict(type='int', default=60),
        ),
        mutually_exclusive=[['deb', 'package', 'upgrade']],
        required_one_of=[['autoremove', 'deb', 'package', 'update_cache', 'upgrade']],
        supports_check_mode=True,
    )

    # We screenscrape apt-get and aptitude output for information so we need
    # to make sure we use the best parsable locale when running commands
    # also set apt specific vars for desired behaviour
    locale = get_best_parsable_locale(module)
    locale_module.setlocale(locale_module.LC_ALL, locale)
    # APT related constants
    APT_ENV_VARS = dict(
        DEBIAN_FRONTEND='noninteractive',
        DEBIAN_PRIORITY='critical',
        LANG=locale,
        LC_ALL=locale,
        LC_MESSAGES=locale,
        LC_CTYPE=locale,
        LANGUAGE=locale,
    )
    module.run_command_environ_update = APT_ENV_VARS

    global APTITUDE_CMD
    APTITUDE_CMD = module.get_bin_path("aptitude", False)
    global APT_GET_CMD
    APT_GET_CMD = module.get_bin_path("apt-get")

    p = module.params
    install_recommends = p['install_recommends']
    dpkg_options = expand_dpkg_options(p['dpkg_options'])

    if not HAS_PYTHON_APT:
        # This interpreter can't see the apt Python library- we'll do the following to try and fix that:
        # 1) look in common locations for system-owned interpreters that can see it; if we find one, respawn under it
        # 2) finding none, try to install a matching python-apt package for the current interpreter version;
        #    we limit to the current interpreter version to try and avoid installing a whole other Python just
        #    for apt support
        # 3) if we installed a support package, try to respawn under what we think is the right interpreter (could be
        #    the current interpreter again, but we'll let it respawn anyway for simplicity)
        # 4) if still not working, return an error and give up (some corner cases not covered, but this shouldn't be
        #    made any more complex than it already is to try and cover more, eg, custom interpreters taking over
        #    system locations)

        apt_pkg_name = 'python3-apt'

        if has_respawned():
            # this shouldn't be possible; short-circuit early if it happens...
            module.fail_json(msg="{0} must be installed and visible from {1}.".format(apt_pkg_name, sys.executable))

        interpreters = ['/usr/bin/python3', '/usr/bin/python']

        interpreter = probe_interpreters_for_module(interpreters, 'apt')

        if interpreter:
            # found the Python bindings; respawn this module under the interpreter where we found them
            respawn_module(interpreter)
            # this is the end of the line for this process, it will exit here once the respawned module has completed

        # don't make changes if we're in check_mode
        if module.check_mode:
            module.fail_json(msg="%s must be installed to use check mode. "
                                 "If run normally this module can auto-install it." % apt_pkg_name)

        # We skip cache update in auto install the dependency if the
        # user explicitly declared it with update_cache=no.
        if module.params.get('update_cache') is False:
            module.warn("Auto-installing missing dependency without updating cache: %s" % apt_pkg_name)
        else:
            module.warn("Updating cache and auto-installing missing dependency: %s" % apt_pkg_name)
            module.run_command([APT_GET_CMD, 'update'], check_rc=True)

        # try to install the apt Python binding
        apt_pkg_cmd = [APT_GET_CMD, 'install', apt_pkg_name, '-y', '-q', dpkg_options]

        if install_recommends is False:
            apt_pkg_cmd.extend(["-o", "APT::Install-Recommends=no"])
        elif install_recommends is True:
            apt_pkg_cmd.extend(["-o", "APT::Install-Recommends=yes"])
        # install_recommends is None uses the OS default

        module.run_command(apt_pkg_cmd, check_rc=True)

        # try again to find the bindings in common places
        interpreter = probe_interpreters_for_module(interpreters, 'apt')

        if interpreter:
            # found the Python bindings; respawn this module under the interpreter where we found them
            # NB: respawn is somewhat wasteful if it's this interpreter, but simplifies the code
            respawn_module(interpreter)
            # this is the end of the line for this process, it will exit here once the respawned module has completed
        else:
            # we've done all we can do; just tell the user it's busted and get out
            module.fail_json(msg="{0} must be installed and visible from {1}.".format(apt_pkg_name, sys.executable))

    if p['clean'] is True:
        aptclean_stdout, aptclean_stderr, aptclean_diff = aptclean(module)
        # If there is nothing else to do exit. This will set state as
        #  changed based on if the cache was updated.
        if not p['package'] and p['upgrade'] == 'no' and not p['deb']:
            module.exit_json(
                changed=True,
                msg=aptclean_stdout,
                stdout=aptclean_stdout,
                stderr=aptclean_stderr,
                diff=aptclean_diff
            )

    if p['upgrade'] == 'no':
        p['upgrade'] = None

    use_apt_get = p['force_apt_get']

    if not use_apt_get and not APTITUDE_CMD:
        use_apt_get = True

    updated_cache = False
    updated_cache_time = 0
    allow_unauthenticated = p['allow_unauthenticated']
    allow_downgrade = p['allow_downgrade']
    allow_change_held_packages = p['allow_change_held_packages']
    autoremove = p['autoremove']
    fail_on_autoremove = p['fail_on_autoremove']
    autoclean = p['autoclean']

    # max times we'll retry
    deadline = time.time() + p['lock_timeout']

    # keep running on lock issues unless timeout or resolution is hit.
    while True:

        # Get the cache object, this has 3 retries built in
        cache = get_cache(module)

        try:
            if p['default_release']:
                try:
                    apt_pkg.config['APT::Default-Release'] = p['default_release']
                except AttributeError:
                    apt_pkg.Config['APT::Default-Release'] = p['default_release']
                # reopen cache w/ modified config
                cache.open(progress=None)

            mtimestamp, updated_cache_time = get_updated_cache_time()
            # Cache valid time is default 0, which will update the cache if
            #  needed and `update_cache` was set to true
            updated_cache = False
            if p['update_cache'] or p['cache_valid_time']:
                now = datetime.datetime.now()
                tdelta = datetime.timedelta(seconds=p['cache_valid_time'])
                if not mtimestamp + tdelta >= now:
                    # Retry to update the cache with exponential backoff
                    err = ''
                    update_cache_retries = module.params.get('update_cache_retries')
                    update_cache_retry_max_delay = module.params.get('update_cache_retry_max_delay')
                    randomize = secrets.randbelow(1000) / 1000.0

                    for retry in range(update_cache_retries):
                        try:
                            if not module.check_mode:
                                cache.update()
                            break
                        except apt.cache.FetchFailedException as fetch_failed_exc:
                            err = fetch_failed_exc
                            module.warn(
                                f"Failed to update cache after {retry + 1} retries due "
                                f"to {to_native(fetch_failed_exc)}, retrying"
                            )

                        # Use exponential backoff plus a little bit of randomness
                        delay = 2 ** retry + randomize
                        if delay > update_cache_retry_max_delay:
                            delay = update_cache_retry_max_delay + randomize
                        time.sleep(delay)
                        module.warn(f"Sleeping for {int(round(delay))} seconds, before attempting to refresh the cache again")
                    else:
                        msg = (
                            f"Failed to update apt cache after {update_cache_retries} retries: "
                            f"{err if err else 'unknown reason'}"
                        )
                        module.fail_json(msg=msg)

                    cache.open(progress=None)
                    mtimestamp, post_cache_update_time = get_updated_cache_time()
                    if module.check_mode or updated_cache_time != post_cache_update_time:
                        updated_cache = True
                    updated_cache_time = post_cache_update_time

                # If there is nothing else to do exit. This will set state as
                #  changed based on if the cache was updated.
                if not p['package'] and not p['upgrade'] and not p['deb']:
                    module.exit_json(
                        changed=updated_cache,
                        cache_updated=updated_cache,
                        cache_update_time=updated_cache_time
                    )

            force_yes = p['force']

            if p['upgrade']:
                upgrade(
                    module,
                    p['upgrade'],
                    force_yes,
                    p['default_release'],
                    use_apt_get,
                    dpkg_options,
                    autoremove,
                    fail_on_autoremove,
                    allow_unauthenticated,
                    allow_downgrade
                )

            if p['deb']:
                if p['state'] != 'present':
                    module.fail_json(msg="deb only supports state=present")
                if '://' in p['deb']:
                    p['deb'] = fetch_file(module, p['deb'])
                install_deb(module, p['deb'], cache,
                            install_recommends=install_recommends,
                            allow_unauthenticated=allow_unauthenticated,
                            allow_change_held_packages=allow_change_held_packages,
                            allow_downgrade=allow_downgrade,
                            force=force_yes, fail_on_autoremove=fail_on_autoremove, dpkg_options=p['dpkg_options'])

            unfiltered_packages = p['package'] or ()
            packages = [package.strip() for package in unfiltered_packages if package != '*']
            all_installed = '*' in unfiltered_packages
            latest = p['state'] == 'latest'

            if latest and all_installed:
                if packages:
                    module.fail_json(msg='unable to install additional packages when upgrading all installed packages')
                upgrade(
                    module,
                    'yes',
                    force_yes,
                    p['default_release'],
                    use_apt_get,
                    dpkg_options,
                    autoremove,
                    fail_on_autoremove,
                    allow_unauthenticated,
                    allow_downgrade
                )

            if packages:
                for package in packages:
                    if package.count('=') > 1:
                        module.fail_json(msg="invalid package spec: %s" % package)

            if not packages:
                if autoclean:
                    cleanup(module, p['purge'], force=force_yes, operation='autoclean', dpkg_options=dpkg_options)
                if autoremove:
                    cleanup(module, p['purge'], force=force_yes, operation='autoremove', dpkg_options=dpkg_options)

            if p['state'] in ('latest', 'present', 'build-dep', 'fixed'):
                state_upgrade = False
                state_builddep = False
                state_fixed = False
                if p['state'] == 'latest':
                    state_upgrade = True
                if p['state'] == 'build-dep':
                    state_builddep = True
                if p['state'] == 'fixed':
                    state_fixed = True

                success, retvals = install(
                    module,
                    packages,
                    cache,
                    upgrade=state_upgrade,
                    default_release=p['default_release'],
                    install_recommends=install_recommends,
                    force=force_yes,
                    dpkg_options=dpkg_options,
                    build_dep=state_builddep,
                    fixed=state_fixed,
                    autoremove=autoremove,
                    fail_on_autoremove=fail_on_autoremove,
                    only_upgrade=p['only_upgrade'],
                    allow_unauthenticated=allow_unauthenticated,
                    allow_downgrade=allow_downgrade,
                    allow_change_held_packages=allow_change_held_packages,
                )

                # Store if the cache has been updated
                retvals['cache_updated'] = updated_cache
                # Store when the update time was last
                retvals['cache_update_time'] = updated_cache_time

                if success:
                    module.exit_json(**retvals)
                else:
                    module.fail_json(**retvals)
            elif p['state'] == 'absent':
                remove(
                    module,
                    packages,
                    cache,
                    p['purge'],
                    force=force_yes,
                    dpkg_options=dpkg_options,
                    autoremove=autoremove,
                    allow_change_held_packages=allow_change_held_packages
                )

        except apt.cache.LockFailedException as lockFailedException:
            if time.time() < deadline:
                continue
            module.fail_json(msg="Failed to lock apt for exclusive operation: %s" % lockFailedException)
        except apt.cache.FetchFailedException as fetchFailedException:
            module.fail_json(msg="Could not fetch updated apt files: %s" % fetchFailedException)

        # got here w/o exception and/or exit???
        module.fail_json(msg='Unexpected code path taken, we really should have exited before, this is a bug')


if __name__ == "__main__":
    main()
