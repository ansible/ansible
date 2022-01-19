#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Cristian van Ee <cristian at cvee.org>
# Copyright 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com>
# Copyright 2018 Adam Miller <admiller@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: dnf
version_added: 1.9
short_description: Manages packages with the I(dnf) package manager
description:
     - Installs, upgrade, removes, and lists packages and groups with the I(dnf) package manager.
options:
  name:
    description:
      - "A package name or package specifier with version, like C(name-1.0).
        When using state=latest, this can be '*' which means run: dnf -y update.
        You can also pass a url or a local path to a rpm file.
        To operate on several packages this can accept a comma separated string of packages or a list of packages."
      - Comparison operators for package version are valid here C(>), C(<), C(>=), C(<=). Example - C(name>=1.0)
    required: true
    aliases:
        - pkg
    type: list
    elements: str

  list:
    description:
      - Various (non-idempotent) commands for usage with C(/usr/bin/ansible) and I(not) playbooks. See examples.
    type: str

  state:
    description:
      - Whether to install (C(present), C(latest)), or remove (C(absent)) a package.
      - Default is C(None), however in effect the default action is C(present) unless the C(autoremove) option is
        enabled for this module, then C(absent) is inferred.
    choices: ['absent', 'present', 'installed', 'removed', 'latest']
    type: str

  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    type: list
    elements: str

  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    type: list
    elements: str

  conf_file:
    description:
      - The remote dnf configuration file to use for the transaction.
    type: str

  disable_gpg_check:
    description:
      - Whether to disable the GPG checking of signatures of packages being
        installed. Has an effect only if state is I(present) or I(latest).
      - This setting affects packages installed from a repository as well as
        "local" packages installed from the filesystem or a URL.
    type: bool
    default: 'no'

  installroot:
    description:
      - Specifies an alternative installroot, relative to which all packages
        will be installed.
    version_added: "2.3"
    default: "/"
    type: str

  releasever:
    description:
      - Specifies an alternative release from which all packages will be
        installed.
    version_added: "2.6"
    type: str

  autoremove:
    description:
      - If C(yes), removes all "leaf" packages from the system that were originally
        installed as dependencies of user-installed packages but which are no longer
        required by any such package. Should be used alone or when state is I(absent)
    type: bool
    default: "no"
    version_added: "2.4"
  exclude:
    description:
      - Package name(s) to exclude when state=present, or latest. This can be a
        list or a comma separated string.
    version_added: "2.7"
    type: list
    elements: str
  skip_broken:
    description:
      - Skip packages with broken dependencies(devsolve) and are causing problems.
    type: bool
    default: "no"
    version_added: "2.7"
  update_cache:
    description:
      - Force dnf to check if cache is out of date and redownload if needed.
        Has an effect only if state is I(present) or I(latest).
    type: bool
    default: "no"
    aliases: [ expire-cache ]
    version_added: "2.7"
  update_only:
    description:
      - When using latest, only update installed packages. Do not install packages.
      - Has an effect only if state is I(latest)
    default: "no"
    type: bool
    version_added: "2.7"
  security:
    description:
      - If set to C(yes), and C(state=latest) then only installs updates that have been marked security related.
      - Note that, similar to C(dnf upgrade-minimal), this filter applies to dependencies as well.
    type: bool
    default: "no"
    version_added: "2.7"
  bugfix:
    description:
      - If set to C(yes), and C(state=latest) then only installs updates that have been marked bugfix related.
      - Note that, similar to C(dnf upgrade-minimal), this filter applies to dependencies as well.
    default: "no"
    type: bool
    version_added: "2.7"
  enable_plugin:
    description:
      - I(Plugin) name to enable for the install/update operation.
        The enabled plugin will not persist beyond the transaction.
    version_added: "2.7"
    type: list
    elements: str
  disable_plugin:
    description:
      - I(Plugin) name to disable for the install/update operation.
        The disabled plugins will not persist beyond the transaction.
    version_added: "2.7"
    type: list
    elements: str
  disable_excludes:
    description:
      - Disable the excludes defined in DNF config files.
      - If set to C(all), disables all excludes.
      - If set to C(main), disable excludes defined in [main] in dnf.conf.
      - If set to C(repoid), disable excludes defined for given repo id.
    version_added: "2.7"
    type: str
  validate_certs:
    description:
      - This only applies if using a https url as the source of the rpm. e.g. for localinstall. If set to C(no), the SSL certificates will not be validated.
      - This should only set to C(no) used on personally controlled sites using self-signed certificates as it avoids verifying the source site.
    type: bool
    default: "yes"
    version_added: "2.7"
  allow_downgrade:
    description:
      - Specify if the named package and version is allowed to downgrade
        a maybe already installed higher version of that package.
        Note that setting allow_downgrade=True can make this module
        behave in a non-idempotent way. The task could end up with a set
        of packages that does not match the complete list of specified
        packages to install (because dependencies between the downgraded
        package and others can cause changes to the packages which were
        in the earlier transaction).
    type: bool
    default: "no"
    version_added: "2.7"
  install_repoquery:
    description:
      - This is effectively a no-op in DNF as it is not needed with DNF, but is an accepted parameter for feature
        parity/compatibility with the I(yum) module.
    type: bool
    default: "yes"
    version_added: "2.7"
  download_only:
    description:
      - Only download the packages, do not install them.
    default: "no"
    type: bool
    version_added: "2.7"
  lock_timeout:
    description:
      - Amount of time to wait for the dnf lockfile to be freed.
    required: false
    default: 30
    type: int
    version_added: "2.8"
  install_weak_deps:
    description:
      - Will also install all packages linked by a weak dependency relation.
    type: bool
    default: "yes"
    version_added: "2.8"
  download_dir:
    description:
      - Specifies an alternate directory to store packages.
      - Has an effect only if I(download_only) is specified.
    type: str
    version_added: "2.8"
  allowerasing:
    description:
      - If C(yes) it allows  erasing  of  installed  packages to resolve dependencies.
    required: false
    type: bool
    default: "no"
    version_added: "2.10"
  nobest:
    description:
      - Set best option to False, so that transactions are not limited to best candidates only.
    required: false
    type: bool
    default: "no"
    version_added: "2.11"
notes:
  - When used with a C(loop:) each package will be processed individually, it is much more efficient to pass the list directly to the I(name) option.
  - Group removal doesn't work if the group was installed with Ansible because
    upstream dnf's API doesn't properly mark groups as installed, therefore upon
    removal the module is unable to detect that the group is installed
    (https://bugzilla.redhat.com/show_bug.cgi?id=1620324)
requirements:
  - "python >= 2.6"
  - python-dnf
  - for the autoremove option you need dnf >= 2.0.1"
author:
  - Igor Gnatenko (@ignatenkobrain) <i.gnatenko.brain@gmail.com>
  - Cristian van Ee (@DJMuggs) <cristian at cvee.org>
  - Berend De Schouwer (@berenddeschouwer)
  - Adam Miller (@maxamillion) <admiller@redhat.com>
'''

EXAMPLES = '''
- name: Install the latest version of Apache
  dnf:
    name: httpd
    state: latest

- name: Install Apache >= 2.4
  dnf:
    name: httpd>=2.4
    state: present

- name: Install the latest version of Apache and MariaDB
  dnf:
    name:
      - httpd
      - mariadb-server
    state: latest

- name: Remove the Apache package
  dnf:
    name: httpd
    state: absent

- name: Install the latest version of Apache from the testing repo
  dnf:
    name: httpd
    enablerepo: testing
    state: present

- name: Upgrade all packages
  dnf:
    name: "*"
    state: latest

- name: Install the nginx rpm from a remote repo
  dnf:
    name: 'http://nginx.org/packages/centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm'
    state: present

- name: Install nginx rpm from a local file
  dnf:
    name: /usr/local/src/nginx-release-centos-6-0.el6.ngx.noarch.rpm
    state: present

- name: Install the 'Development tools' package group
  dnf:
    name: '@Development tools'
    state: present

- name: Autoremove unneeded packages installed as dependencies
  dnf:
    autoremove: yes

- name: Uninstall httpd but keep its dependencies
  dnf:
    name: httpd
    state: absent
    autoremove: no

- name: Install a modularity appstream with defined stream and profile
  dnf:
    name: '@postgresql:9.6/client'
    state: present

- name: Install a modularity appstream with defined stream
  dnf:
    name: '@postgresql:9.6'
    state: present

- name: Install a modularity appstream with defined profile
  dnf:
    name: '@postgresql/client'
    state: present
'''

import os
import re
import sys

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.urls import fetch_file
from ansible.module_utils.six import PY2, text_type
from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.respawn import has_respawned, probe_interpreters_for_module, respawn_module
from ansible.module_utils.yumdnf import YumDnf, yumdnf_argument_spec

try:
    import dnf
    import dnf.cli
    import dnf.const
    import dnf.exceptions
    import dnf.subject
    import dnf.util
    HAS_DNF = True
except ImportError:
    HAS_DNF = False


class DnfModule(YumDnf):
    """
    DNF Ansible module back-end implementation
    """

    def __init__(self, module):
        # This populates instance vars for all argument spec params
        super(DnfModule, self).__init__(module)

        self._ensure_dnf()
        self.lockfile = "/var/cache/dnf/*_lock.pid"
        self.pkg_mgr_name = "dnf"

        try:
            self.with_modules = dnf.base.WITH_MODULES
        except AttributeError:
            self.with_modules = False

        # DNF specific args that are not part of YumDnf
        self.allowerasing = self.module.params['allowerasing']
        self.nobest = self.module.params['nobest']

    def is_lockfile_pid_valid(self):
        # FIXME? it looks like DNF takes care of invalid lock files itself?
        # https://github.com/ansible/ansible/issues/57189
        return True

    def _sanitize_dnf_error_msg_install(self, spec, error):
        """
        For unhandled dnf.exceptions.Error scenarios, there are certain error
        messages we want to filter in an install scenario. Do that here.
        """
        if (
            to_text("no package matched") in to_text(error) or
            to_text("No match for argument:") in to_text(error)
        ):
            return "No package {0} available.".format(spec)

        return error

    def _sanitize_dnf_error_msg_remove(self, spec, error):
        """
        For unhandled dnf.exceptions.Error scenarios, there are certain error
        messages we want to ignore in a removal scenario as known benign
        failures. Do that here.
        """
        if (
            'no package matched' in to_native(error) or
            'No match for argument:' in to_native(error)
        ):
            return (False, "{0} is not installed".format(spec))

        # Return value is tuple of:
        #   ("Is this actually a failure?", "Error Message")
        return (True, error)

    def _package_dict(self, package):
        """Return a dictionary of information for the package."""
        # NOTE: This no longer contains the 'dnfstate' field because it is
        # already known based on the query type.
        result = {
            'name': package.name,
            'arch': package.arch,
            'epoch': str(package.epoch),
            'release': package.release,
            'version': package.version,
            'repo': package.repoid}
        result['nevra'] = '{epoch}:{name}-{version}-{release}.{arch}'.format(
            **result)

        if package.installtime == 0:
            result['yumstate'] = 'available'
        else:
            result['yumstate'] = 'installed'

        return result

    def _split_package_arch(self, packagename):
        # This list was auto generated on a Fedora 28 system with the following one-liner
        #   printf '[ '; for arch in $(ls /usr/lib/rpm/platform); do  printf '"%s", ' ${arch%-linux}; done; printf ']\n'
        redhat_rpm_arches = [
            "aarch64", "alphaev56", "alphaev5", "alphaev67", "alphaev6", "alpha",
            "alphapca56", "amd64", "armv3l", "armv4b", "armv4l", "armv5tejl", "armv5tel",
            "armv5tl", "armv6hl", "armv6l", "armv7hl", "armv7hnl", "armv7l", "athlon",
            "geode", "i386", "i486", "i586", "i686", "ia32e", "ia64", "m68k", "mips64el",
            "mips64", "mips64r6el", "mips64r6", "mipsel", "mips", "mipsr6el", "mipsr6",
            "noarch", "pentium3", "pentium4", "ppc32dy4", "ppc64iseries", "ppc64le", "ppc64",
            "ppc64p7", "ppc64pseries", "ppc8260", "ppc8560", "ppciseries", "ppc", "ppcpseries",
            "riscv64", "s390", "s390x", "sh3", "sh4a", "sh4", "sh", "sparc64", "sparc64v",
            "sparc", "sparcv8", "sparcv9", "sparcv9v", "x86_64"
        ]

        name, delimiter, arch = packagename.rpartition('.')
        if name and arch and arch in redhat_rpm_arches:
            return name, arch
        return packagename, None

    def _packagename_dict(self, packagename):
        """
        Return a dictionary of information for a package name string or None
        if the package name doesn't contain at least all NVR elements
        """

        if packagename[-4:] == '.rpm':
            packagename = packagename[:-4]

        rpm_nevr_re = re.compile(r'(\S+)-(?:(\d*):)?(.*)-(~?\w+[\w.+]*)')
        try:
            arch = None
            nevr, arch = self._split_package_arch(packagename)
            if arch:
                packagename = nevr
            rpm_nevr_match = rpm_nevr_re.match(packagename)
            if rpm_nevr_match:
                name, epoch, version, release = rpm_nevr_re.match(packagename).groups()
                if not version or not version.split('.')[0].isdigit():
                    return None
            else:
                return None
        except AttributeError as e:
            self.module.fail_json(
                msg='Error attempting to parse package: %s, %s' % (packagename, to_native(e)),
                rc=1,
                results=[]
            )

        if not epoch:
            epoch = "0"

        if ':' in name:
            epoch_name = name.split(":")

            epoch = epoch_name[0]
            name = ''.join(epoch_name[1:])

        result = {
            'name': name,
            'epoch': epoch,
            'release': release,
            'version': version,
        }

        return result

    # Original implementation from yum.rpmUtils.miscutils (GPLv2+)
    #   http://yum.baseurl.org/gitweb?p=yum.git;a=blob;f=rpmUtils/miscutils.py
    def _compare_evr(self, e1, v1, r1, e2, v2, r2):
        # return 1: a is newer than b
        # 0: a and b are the same version
        # -1: b is newer than a
        if e1 is None:
            e1 = '0'
        else:
            e1 = str(e1)
        v1 = str(v1)
        r1 = str(r1)
        if e2 is None:
            e2 = '0'
        else:
            e2 = str(e2)
        v2 = str(v2)
        r2 = str(r2)
        # print '%s, %s, %s vs %s, %s, %s' % (e1, v1, r1, e2, v2, r2)
        rc = dnf.rpm.rpm.labelCompare((e1, v1, r1), (e2, v2, r2))
        # print '%s, %s, %s vs %s, %s, %s = %s' % (e1, v1, r1, e2, v2, r2, rc)
        return rc

    def _ensure_dnf(self):
        if HAS_DNF:
            return

        system_interpreters = ['/usr/libexec/platform-python',
                               '/usr/bin/python3',
                               '/usr/bin/python2',
                               '/usr/bin/python']

        if not has_respawned():
            # probe well-known system Python locations for accessible bindings, favoring py3
            interpreter = probe_interpreters_for_module(system_interpreters, 'dnf')

            if interpreter:
                # respawn under the interpreter where the bindings should be found
                respawn_module(interpreter)
                # end of the line for this module, the process will exit here once the respawned module completes

        # done all we can do, something is just broken (auto-install isn't useful anymore with respawn, so it was removed)
        self.module.fail_json(
            msg="Could not import the dnf python module using {0} ({1}). "
                "Please install `python3-dnf` or `python2-dnf` package or ensure you have specified the "
                "correct ansible_python_interpreter. (attempted {2})"
                .format(sys.executable, sys.version.replace('\n', ''), system_interpreters),
            results=[]
        )

    def _configure_base(self, base, conf_file, disable_gpg_check, installroot='/'):
        """Configure the dnf Base object."""

        conf = base.conf

        # Change the configuration file path if provided, this must be done before conf.read() is called
        if conf_file:
            # Fail if we can't read the configuration file.
            if not os.access(conf_file, os.R_OK):
                self.module.fail_json(
                    msg="cannot read configuration file", conf_file=conf_file,
                    results=[],
                )
            else:
                conf.config_file_path = conf_file

        # Read the configuration file
        conf.read()

        # Turn off debug messages in the output
        conf.debuglevel = 0

        # Set whether to check gpg signatures
        conf.gpgcheck = not disable_gpg_check
        conf.localpkg_gpgcheck = not disable_gpg_check

        # Don't prompt for user confirmations
        conf.assumeyes = True

        # Set installroot
        conf.installroot = installroot

        # Load substitutions from the filesystem
        conf.substitutions.update_from_etc(installroot)

        # Handle different DNF versions immutable mutable datatypes and
        # dnf v1/v2/v3
        #
        # In DNF < 3.0 are lists, and modifying them works
        # In DNF >= 3.0 < 3.6 are lists, but modifying them doesn't work
        # In DNF >= 3.6 have been turned into tuples, to communicate that modifying them doesn't work
        #
        # https://www.happyassassin.net/2018/06/27/adams-debugging-adventures-the-immutable-mutable-object/
        #
        # Set excludes
        if self.exclude:
            _excludes = list(conf.exclude)
            _excludes.extend(self.exclude)
            conf.exclude = _excludes
        # Set disable_excludes
        if self.disable_excludes:
            _disable_excludes = list(conf.disable_excludes)
            if self.disable_excludes not in _disable_excludes:
                _disable_excludes.append(self.disable_excludes)
                conf.disable_excludes = _disable_excludes

        # Set releasever
        if self.releasever is not None:
            conf.substitutions['releasever'] = self.releasever

        # Set skip_broken (in dnf this is strict=0)
        if self.skip_broken:
            conf.strict = 0

        # Set best
        if self.nobest:
            conf.best = 0

        if self.download_only:
            conf.downloadonly = True
            if self.download_dir:
                conf.destdir = self.download_dir

        # Default in dnf upstream is true
        conf.clean_requirements_on_remove = self.autoremove

        # Default in dnf (and module default) is True
        conf.install_weak_deps = self.install_weak_deps

    def _specify_repositories(self, base, disablerepo, enablerepo):
        """Enable and disable repositories matching the provided patterns."""
        base.read_all_repos()
        repos = base.repos

        # Disable repositories
        for repo_pattern in disablerepo:
            if repo_pattern:
                for repo in repos.get_matching(repo_pattern):
                    repo.disable()

        # Enable repositories
        for repo_pattern in enablerepo:
            if repo_pattern:
                for repo in repos.get_matching(repo_pattern):
                    repo.enable()

    def _base(self, conf_file, disable_gpg_check, disablerepo, enablerepo, installroot):
        """Return a fully configured dnf Base object."""
        base = dnf.Base()
        self._configure_base(base, conf_file, disable_gpg_check, installroot)
        try:
            # this method has been supported in dnf-4.2.17-6 or later
            # https://bugzilla.redhat.com/show_bug.cgi?id=1788212
            base.setup_loggers()
        except AttributeError:
            pass
        try:
            base.init_plugins(set(self.disable_plugin), set(self.enable_plugin))
            base.pre_configure_plugins()
        except AttributeError:
            pass  # older versions of dnf didn't require this and don't have these methods
        self._specify_repositories(base, disablerepo, enablerepo)
        try:
            base.configure_plugins()
        except AttributeError:
            pass  # older versions of dnf didn't require this and don't have these methods

        try:
            if self.update_cache:
                try:
                    base.update_cache()
                except dnf.exceptions.RepoError as e:
                    self.module.fail_json(
                        msg="{0}".format(to_text(e)),
                        results=[],
                        rc=1
                    )
            base.fill_sack(load_system_repo='auto')
        except dnf.exceptions.RepoError as e:
            self.module.fail_json(
                msg="{0}".format(to_text(e)),
                results=[],
                rc=1
            )

        filters = []
        if self.bugfix:
            key = {'advisory_type__eq': 'bugfix'}
            filters.append(base.sack.query().upgrades().filter(**key))
        if self.security:
            key = {'advisory_type__eq': 'security'}
            filters.append(base.sack.query().upgrades().filter(**key))
        if filters:
            base._update_security_filters = filters

        return base

    def list_items(self, command):
        """List package info based on the command."""
        # Rename updates to upgrades
        if command == 'updates':
            command = 'upgrades'

        # Return the corresponding packages
        if command in ['installed', 'upgrades', 'available']:
            results = [
                self._package_dict(package)
                for package in getattr(self.base.sack.query(), command)()]
        # Return the enabled repository ids
        elif command in ['repos', 'repositories']:
            results = [
                {'repoid': repo.id, 'state': 'enabled'}
                for repo in self.base.repos.iter_enabled()]
        # Return any matching packages
        else:
            packages = dnf.subject.Subject(command).get_best_query(self.base.sack)
            results = [self._package_dict(package) for package in packages]

        self.module.exit_json(msg="", results=results)

    def _is_installed(self, pkg):
        installed = self.base.sack.query().installed()

        package_spec = {}
        name, arch = self._split_package_arch(pkg)
        if arch:
            package_spec['arch'] = arch

        package_details = self._packagename_dict(pkg)
        if package_details:
            package_details['epoch'] = int(package_details['epoch'])
            package_spec.update(package_details)
        else:
            package_spec['name'] = name

        if installed.filter(**package_spec):
            return True
        else:
            return False

    def _is_newer_version_installed(self, pkg_name):
        candidate_pkg = self._packagename_dict(pkg_name)
        if not candidate_pkg:
            # The user didn't provide a versioned rpm, so version checking is
            # not required
            return False

        installed = self.base.sack.query().installed()
        installed_pkg = installed.filter(name=candidate_pkg['name']).run()
        if installed_pkg:
            installed_pkg = installed_pkg[0]

            # this looks weird but one is a dict and the other is a dnf.Package
            evr_cmp = self._compare_evr(
                installed_pkg.epoch, installed_pkg.version, installed_pkg.release,
                candidate_pkg['epoch'], candidate_pkg['version'], candidate_pkg['release'],
            )

            if evr_cmp == 1:
                return True
            else:
                return False

        else:

            return False

    def _mark_package_install(self, pkg_spec, upgrade=False):
        """Mark the package for install."""
        is_newer_version_installed = self._is_newer_version_installed(pkg_spec)
        is_installed = self._is_installed(pkg_spec)
        try:
            if is_newer_version_installed:
                if self.allow_downgrade:
                    # dnf only does allow_downgrade, we have to handle this ourselves
                    # because it allows a possibility for non-idempotent transactions
                    # on a system's package set (pending the yum repo has many old
                    # NVRs indexed)
                    if upgrade:
                        if is_installed:
                            self.base.upgrade(pkg_spec)
                        else:
                            self.base.install(pkg_spec)
                    else:
                        self.base.install(pkg_spec)
                else:  # Nothing to do, report back
                    pass
            elif is_installed:  # An potentially older (or same) version is installed
                if upgrade:
                    self.base.upgrade(pkg_spec)
                else:  # Nothing to do, report back
                    pass
            else:  # The package is not installed, simply install it
                self.base.install(pkg_spec)

            return {'failed': False, 'msg': '', 'failure': '', 'rc': 0}

        except dnf.exceptions.MarkingError as e:
            return {
                'failed': True,
                'msg': "No package {0} available.".format(pkg_spec),
                'failure': " ".join((pkg_spec, to_native(e))),
                'rc': 1,
                "results": []
            }

        except dnf.exceptions.DepsolveError as e:
            return {
                'failed': True,
                'msg': "Depsolve Error occured for package {0}.".format(pkg_spec),
                'failure': " ".join((pkg_spec, to_native(e))),
                'rc': 1,
                "results": []
            }

        except dnf.exceptions.Error as e:
            if to_text("already installed") in to_text(e):
                return {'failed': False, 'msg': '', 'failure': ''}
            else:
                return {
                    'failed': True,
                    'msg': "Unknown Error occured for package {0}.".format(pkg_spec),
                    'failure': " ".join((pkg_spec, to_native(e))),
                    'rc': 1,
                    "results": []
                }

    def _whatprovides(self, filepath):
        available = self.base.sack.query().available()
        pkg_spec = available.filter(provides=filepath).run()

        if pkg_spec:
            return pkg_spec[0].name

    def _parse_spec_group_file(self):
        pkg_specs, grp_specs, module_specs, filenames = [], [], [], []
        already_loaded_comps = False  # Only load this if necessary, it's slow

        for name in self.names:
            if '://' in name:
                name = fetch_file(self.module, name)
                filenames.append(name)
            elif name.endswith(".rpm"):
                filenames.append(name)
            elif name.startswith("@") or ('/' in name):
                # like "dnf install /usr/bin/vi"
                if '/' in name:
                    pkg_spec = self._whatprovides(name)
                    if pkg_spec:
                        pkg_specs.append(pkg_spec)
                        continue

                if not already_loaded_comps:
                    self.base.read_comps()
                    already_loaded_comps = True

                grp_env_mdl_candidate = name[1:].strip()

                if self.with_modules:
                    mdl = self.module_base._get_modules(grp_env_mdl_candidate)
                    if mdl[0]:
                        module_specs.append(grp_env_mdl_candidate)
                    else:
                        grp_specs.append(grp_env_mdl_candidate)
                else:
                    grp_specs.append(grp_env_mdl_candidate)
            else:
                pkg_specs.append(name)
        return pkg_specs, grp_specs, module_specs, filenames

    def _update_only(self, pkgs):
        not_installed = []
        for pkg in pkgs:
            if self._is_installed(pkg):
                try:
                    if isinstance(to_text(pkg), text_type):
                        self.base.upgrade(pkg)
                    else:
                        self.base.package_upgrade(pkg)
                except Exception as e:
                    self.module.fail_json(
                        msg="Error occured attempting update_only operation: {0}".format(to_native(e)),
                        results=[],
                        rc=1,
                    )
            else:
                not_installed.append(pkg)

        return not_installed

    def _install_remote_rpms(self, filenames):
        if int(dnf.__version__.split(".")[0]) >= 2:
            pkgs = list(sorted(self.base.add_remote_rpms(list(filenames)), reverse=True))
        else:
            pkgs = []
            try:
                for filename in filenames:
                    pkgs.append(self.base.add_remote_rpm(filename))
            except IOError as e:
                if to_text("Can not load RPM file") in to_text(e):
                    self.module.fail_json(
                        msg="Error occured attempting remote rpm install of package: {0}. {1}".format(filename, to_native(e)),
                        results=[],
                        rc=1,
                    )
        if self.update_only:
            self._update_only(pkgs)
        else:
            for pkg in pkgs:
                try:
                    if self._is_newer_version_installed(self._package_dict(pkg)['nevra']):
                        if self.allow_downgrade:
                            self.base.package_install(pkg)
                    else:
                        self.base.package_install(pkg)
                except Exception as e:
                    self.module.fail_json(
                        msg="Error occured attempting remote rpm operation: {0}".format(to_native(e)),
                        results=[],
                        rc=1,
                    )

    def _is_module_installed(self, module_spec):
        if self.with_modules:
            module_spec = module_spec.strip()
            module_list, nsv = self.module_base._get_modules(module_spec)
            enabled_streams = self.base._moduleContainer.getEnabledStream(nsv.name)

            if enabled_streams:
                if nsv.stream:
                    if nsv.stream in enabled_streams:
                        return True     # The provided stream was found
                    else:
                        return False    # The provided stream was not found
                else:
                    return True         # No stream provided, but module found

        return False  # seems like a sane default

    def ensure(self):

        response = {
            'msg': "",
            'changed': False,
            'results': [],
            'rc': 0
        }

        # Accumulate failures.  Package management modules install what they can
        # and fail with a message about what they can't.
        failure_response = {
            'msg': "",
            'failures': [],
            'results': [],
            'rc': 1
        }

        # Autoremove is called alone
        # Jump to remove path where base.autoremove() is run
        if not self.names and self.autoremove:
            self.names = []
            self.state = 'absent'

        if self.names == ['*'] and self.state == 'latest':
            try:
                self.base.upgrade_all()
            except dnf.exceptions.DepsolveError as e:
                failure_response['msg'] = "Depsolve Error occured attempting to upgrade all packages"
                self.module.fail_json(**failure_response)
        else:
            pkg_specs, group_specs, module_specs, filenames = self._parse_spec_group_file()

            pkg_specs = [p.strip() for p in pkg_specs]
            filenames = [f.strip() for f in filenames]
            groups = []
            environments = []
            for group_spec in (g.strip() for g in group_specs):
                group = self.base.comps.group_by_pattern(group_spec)
                if group:
                    groups.append(group.id)
                else:
                    environment = self.base.comps.environment_by_pattern(group_spec)
                    if environment:
                        environments.append(environment.id)
                    else:
                        self.module.fail_json(
                            msg="No group {0} available.".format(group_spec),
                            results=[],
                        )

            if self.state in ['installed', 'present']:
                # Install files.
                self._install_remote_rpms(filenames)
                for filename in filenames:
                    response['results'].append("Installed {0}".format(filename))

                # Install modules
                if module_specs and self.with_modules:
                    for module in module_specs:
                        try:
                            if not self._is_module_installed(module):
                                response['results'].append("Module {0} installed.".format(module))
                            self.module_base.install([module])
                            self.module_base.enable([module])
                        except dnf.exceptions.MarkingErrors as e:
                            failure_response['failures'].append(' '.join((module, to_native(e))))

                # Install groups.
                for group in groups:
                    try:
                        group_pkg_count_installed = self.base.group_install(group, dnf.const.GROUP_PACKAGE_TYPES)
                        if group_pkg_count_installed == 0:
                            response['results'].append("Group {0} already installed.".format(group))
                        else:
                            response['results'].append("Group {0} installed.".format(group))
                    except dnf.exceptions.DepsolveError as e:
                        failure_response['msg'] = "Depsolve Error occured attempting to install group: {0}".format(group)
                        self.module.fail_json(**failure_response)
                    except dnf.exceptions.Error as e:
                        # In dnf 2.0 if all the mandatory packages in a group do
                        # not install, an error is raised.  We want to capture
                        # this but still install as much as possible.
                        failure_response['failures'].append(" ".join((group, to_native(e))))

                for environment in environments:
                    try:
                        self.base.environment_install(environment, dnf.const.GROUP_PACKAGE_TYPES)
                    except dnf.exceptions.DepsolveError as e:
                        failure_response['msg'] = "Depsolve Error occured attempting to install environment: {0}".format(environment)
                        self.module.fail_json(**failure_response)
                    except dnf.exceptions.Error as e:
                        failure_response['failures'].append(" ".join((environment, to_native(e))))

                if module_specs and not self.with_modules:
                    # This means that the group or env wasn't found in comps
                    self.module.fail_json(
                        msg="No group {0} available.".format(module_specs[0]),
                        results=[],
                    )

                # Install packages.
                if self.update_only:
                    not_installed = self._update_only(pkg_specs)
                    for spec in not_installed:
                        response['results'].append("Packages providing %s not installed due to update_only specified" % spec)
                else:
                    for pkg_spec in pkg_specs:
                        install_result = self._mark_package_install(pkg_spec)
                        if install_result['failed']:
                            if install_result['msg']:
                                failure_response['msg'] += install_result['msg']
                            failure_response['failures'].append(self._sanitize_dnf_error_msg_install(pkg_spec, install_result['failure']))
                        else:
                            if install_result['msg']:
                                response['results'].append(install_result['msg'])

            elif self.state == 'latest':
                # "latest" is same as "installed" for filenames.
                self._install_remote_rpms(filenames)
                for filename in filenames:
                    response['results'].append("Installed {0}".format(filename))

                # Upgrade modules
                if module_specs and self.with_modules:
                    for module in module_specs:
                        try:
                            if self._is_module_installed(module):
                                response['results'].append("Module {0} upgraded.".format(module))
                            self.module_base.upgrade([module])
                        except dnf.exceptions.MarkingErrors as e:
                            failure_response['failures'].append(' '.join((module, to_native(e))))

                for group in groups:
                    try:
                        try:
                            self.base.group_upgrade(group)
                            response['results'].append("Group {0} upgraded.".format(group))
                        except dnf.exceptions.CompsError:
                            if not self.update_only:
                                # If not already installed, try to install.
                                group_pkg_count_installed = self.base.group_install(group, dnf.const.GROUP_PACKAGE_TYPES)
                                if group_pkg_count_installed == 0:
                                    response['results'].append("Group {0} already installed.".format(group))
                                else:
                                    response['results'].append("Group {0} installed.".format(group))
                    except dnf.exceptions.Error as e:
                        failure_response['failures'].append(" ".join((group, to_native(e))))

                for environment in environments:
                    try:
                        try:
                            self.base.environment_upgrade(environment)
                        except dnf.exceptions.CompsError:
                            # If not already installed, try to install.
                            self.base.environment_install(environment, dnf.const.GROUP_PACKAGE_TYPES)
                    except dnf.exceptions.DepsolveError as e:
                        failure_response['msg'] = "Depsolve Error occured attempting to install environment: {0}".format(environment)
                    except dnf.exceptions.Error as e:
                        failure_response['failures'].append(" ".join((environment, to_native(e))))

                if self.update_only:
                    not_installed = self._update_only(pkg_specs)
                    for spec in not_installed:
                        response['results'].append("Packages providing %s not installed due to update_only specified" % spec)
                else:
                    for pkg_spec in pkg_specs:
                        # best effort causes to install the latest package
                        # even if not previously installed
                        self.base.conf.best = True
                        install_result = self._mark_package_install(pkg_spec, upgrade=True)
                        if install_result['failed']:
                            if install_result['msg']:
                                failure_response['msg'] += install_result['msg']
                            failure_response['failures'].append(self._sanitize_dnf_error_msg_install(pkg_spec, install_result['failure']))
                        else:
                            if install_result['msg']:
                                response['results'].append(install_result['msg'])

            else:
                # state == absent
                if filenames:
                    self.module.fail_json(
                        msg="Cannot remove paths -- please specify package name.",
                        results=[],
                    )

                # Remove modules
                if module_specs and self.with_modules:
                    for module in module_specs:
                        try:
                            if self._is_module_installed(module):
                                response['results'].append("Module {0} removed.".format(module))
                            self.module_base.remove([module])
                            self.module_base.disable([module])
                            self.module_base.reset([module])
                        except dnf.exceptions.MarkingErrors as e:
                            failure_response['failures'].append(' '.join((module, to_native(e))))

                for group in groups:
                    try:
                        self.base.group_remove(group)
                    except dnf.exceptions.CompsError:
                        # Group is already uninstalled.
                        pass
                    except AttributeError:
                        # Group either isn't installed or wasn't marked installed at install time
                        # because of DNF bug
                        #
                        # This is necessary until the upstream dnf API bug is fixed where installing
                        # a group via the dnf API doesn't actually mark the group as installed
                        #   https://bugzilla.redhat.com/show_bug.cgi?id=1620324
                        pass

                for environment in environments:
                    try:
                        self.base.environment_remove(environment)
                    except dnf.exceptions.CompsError:
                        # Environment is already uninstalled.
                        pass

                installed = self.base.sack.query().installed()
                for pkg_spec in pkg_specs:
                    # short-circuit installed check for wildcard matching
                    if '*' in pkg_spec:
                        try:
                            self.base.remove(pkg_spec)
                        except dnf.exceptions.MarkingError as e:
                            is_failure, handled_remove_error = self._sanitize_dnf_error_msg_remove(pkg_spec, to_native(e))
                            if is_failure:
                                failure_response['failures'].append('{0} - {1}'.format(pkg_spec, to_native(e)))
                            else:
                                response['results'].append(handled_remove_error)
                        continue

                    installed_pkg = dnf.subject.Subject(pkg_spec).get_best_query(
                        sack=self.base.sack).installed().run()

                    for pkg in installed_pkg:
                        self.base.remove(str(pkg))

                # Like the dnf CLI we want to allow recursive removal of dependent
                # packages
                self.allowerasing = True

                if self.autoremove:
                    self.base.autoremove()

        try:
            if not self.base.resolve(allow_erasing=self.allowerasing):
                if failure_response['failures']:
                    failure_response['msg'] = 'Failed to install some of the specified packages'
                    self.module.fail_json(**failure_response)

                response['msg'] = "Nothing to do"
                self.module.exit_json(**response)
            else:
                response['changed'] = True

                # If packages got installed/removed, add them to the results.
                # We do this early so we can use it for both check_mode and not.
                if self.download_only:
                    install_action = 'Downloaded'
                else:
                    install_action = 'Installed'
                for package in self.base.transaction.install_set:
                    response['results'].append("{0}: {1}".format(install_action, package))
                for package in self.base.transaction.remove_set:
                    response['results'].append("Removed: {0}".format(package))

                if failure_response['failures']:
                    failure_response['msg'] = 'Failed to install some of the specified packages'
                    self.module.fail_json(**failure_response)
                if self.module.check_mode:
                    response['msg'] = "Check mode: No changes made, but would have if not in check mode"
                    self.module.exit_json(**response)

                try:
                    if self.download_only and self.download_dir and self.base.conf.destdir:
                        dnf.util.ensure_dir(self.base.conf.destdir)
                        self.base.repos.all().pkgdir = self.base.conf.destdir

                    self.base.download_packages(self.base.transaction.install_set)
                except dnf.exceptions.DownloadError as e:
                    self.module.fail_json(
                        msg="Failed to download packages: {0}".format(to_text(e)),
                        results=[],
                    )

                # Validate GPG. This is NOT done in dnf.Base (it's done in the
                # upstream CLI subclass of dnf.Base)
                if not self.disable_gpg_check:
                    for package in self.base.transaction.install_set:
                        fail = False
                        gpgres, gpgerr = self.base._sig_check_pkg(package)
                        if gpgres == 0:  # validated successfully
                            continue
                        elif gpgres == 1:  # validation failed, install cert?
                            try:
                                self.base._get_key_for_package(package)
                            except dnf.exceptions.Error as e:
                                fail = True
                        else:  # fatal error
                            fail = True

                        if fail:
                            msg = 'Failed to validate GPG signature for {0}'.format(package)
                            self.module.fail_json(msg)

                if self.download_only:
                    # No further work left to do, and the results were already updated above.
                    # Just return them.
                    self.module.exit_json(**response)
                else:
                    self.base.do_transaction()

                if failure_response['failures']:
                    failure_response['msg'] = 'Failed to install some of the specified packages'
                    self.module.exit_json(**response)
                self.module.exit_json(**response)
        except dnf.exceptions.DepsolveError as e:
            failure_response['msg'] = "Depsolve Error occured: {0}".format(to_native(e))
            self.module.fail_json(**failure_response)
        except dnf.exceptions.Error as e:
            if to_text("already installed") in to_text(e):
                response['changed'] = False
                response['results'].append("Package already installed: {0}".format(to_native(e)))
                self.module.exit_json(**response)
            else:
                failure_response['msg'] = "Unknown Error occured: {0}".format(to_native(e))
                self.module.fail_json(**failure_response)

    @staticmethod
    def has_dnf():
        return HAS_DNF

    def run(self):
        """The main function."""

        # Check if autoremove is called correctly
        if self.autoremove:
            if LooseVersion(dnf.__version__) < LooseVersion('2.0.1'):
                self.module.fail_json(
                    msg="Autoremove requires dnf>=2.0.1. Current dnf version is %s" % dnf.__version__,
                    results=[],
                )

        # Check if download_dir is called correctly
        if self.download_dir:
            if LooseVersion(dnf.__version__) < LooseVersion('2.6.2'):
                self.module.fail_json(
                    msg="download_dir requires dnf>=2.6.2. Current dnf version is %s" % dnf.__version__,
                    results=[],
                )

        if self.update_cache and not self.names and not self.list:
            self.base = self._base(
                self.conf_file, self.disable_gpg_check, self.disablerepo,
                self.enablerepo, self.installroot
            )
            self.module.exit_json(
                msg="Cache updated",
                changed=False,
                results=[],
                rc=0
            )

        # Set state as installed by default
        # This is not set in AnsibleModule() because the following shouldn't happen
        # - dnf: autoremove=yes state=installed
        if self.state is None:
            self.state = 'installed'

        if self.list:
            self.base = self._base(
                self.conf_file, self.disable_gpg_check, self.disablerepo,
                self.enablerepo, self.installroot
            )
            self.list_items(self.list)
        else:
            # Note: base takes a long time to run so we want to check for failure
            # before running it.
            if not dnf.util.am_i_root():
                self.module.fail_json(
                    msg="This command has to be run under the root user.",
                    results=[],
                )
            self.base = self._base(
                self.conf_file, self.disable_gpg_check, self.disablerepo,
                self.enablerepo, self.installroot
            )

            if self.with_modules:
                self.module_base = dnf.module.module_base.ModuleBase(self.base)

            self.ensure()


def main():
    # state=installed name=pkgspec
    # state=removed name=pkgspec
    # state=latest name=pkgspec
    #
    # informational commands:
    #   list=installed
    #   list=updates
    #   list=available
    #   list=repos
    #   list=pkgspec

    # Extend yumdnf_argument_spec with dnf-specific features that will never be
    # backported to yum because yum is now in "maintenance mode" upstream
    yumdnf_argument_spec['argument_spec']['allowerasing'] = dict(default=False, type='bool')
    yumdnf_argument_spec['argument_spec']['nobest'] = dict(default=False, type='bool')

    module = AnsibleModule(
        **yumdnf_argument_spec
    )

    module_implementation = DnfModule(module)
    try:
        module_implementation.run()
    except dnf.exceptions.RepoError as de:
        module.fail_json(
            msg="Failed to synchronize repodata: {0}".format(to_native(de)),
            rc=1,
            results=[],
            changed=False
        )


if __name__ == '__main__':
    main()
