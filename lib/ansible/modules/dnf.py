# -*- coding: utf-8 -*-

# Copyright 2015 Cristian van Ee <cristian at cvee.org>
# Copyright 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com>
# Copyright 2018 Adam Miller <admiller@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: dnf
version_added: 1.9
short_description: Manages packages with the I(dnf) package manager
description:
     - Installs, upgrade, removes, and lists packages and groups with the I(dnf) package manager.
options:
  use_backend:
    description:
      - Backend module to use.
    default: "auto"
    choices:
        auto: Automatically select the backend based on the C(ansible_facts.pkg_mgr) fact.
        yum: Alias for V(auto) (see Notes)
        dnf: M(ansible.builtin.dnf)
        yum4: Alias for V(dnf)
        dnf4: Alias for V(dnf)
        dnf5: M(ansible.builtin.dnf5)
    type: str
    version_added: 2.15
  name:
    description:
      - "A package name or package specifier with version, like C(name-1.0).
        When using state=latest, this can be '*' which means run: dnf -y update.
        You can also pass a url or a local path to an rpm file.
        To operate on several packages this can accept a comma separated string of packages or a list of packages."
      - Comparison operators for package version are valid here C(>), C(<), C(>=), C(<=). Example - C(name >= 1.0).
        Spaces around the operator are required.
      - You can also pass an absolute path for a binary which is provided by the package to install.
        See examples for more information.
    aliases:
        - pkg
    type: list
    elements: str
    default: []

  list:
    description:
      - Various (non-idempotent) commands for usage with C(/usr/bin/ansible) and I(not) playbooks.
        Use M(ansible.builtin.package_facts) instead of the O(list) argument as a best practice.
    type: str

  state:
    description:
      - Whether to install (V(present), V(latest)), or remove (V(absent)) a package.
      - Default is V(None), however in effect the default action is V(present) unless the O(autoremove=true),
        then V(absent) is inferred.
    choices: ['absent', 'present', 'installed', 'removed', 'latest']
    type: str

  enablerepo:
    description:
      - C(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    type: list
    elements: str
    default: []

  disablerepo:
    description:
      - C(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a C(,).
    type: list
    elements: str
    default: []

  conf_file:
    description:
      - The remote dnf configuration file to use for the transaction.
    type: str

  disable_gpg_check:
    description:
      - Whether to disable the GPG checking of signatures of packages being
        installed. Has an effect only if O(state=present) or O(state=latest).
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
      - If V(true), removes all "leaf" packages from the system that were originally
        installed as dependencies of user-installed packages but which are no longer
        required by any such package. Should be used alone or when O(state=absent).
    type: bool
    default: "no"
    version_added: "2.4"
  exclude:
    description:
      - Package name(s) to exclude when O(state=present), or latest. This can be a
        list or a comma separated string.
    version_added: "2.7"
    type: list
    elements: str
    default: []
  skip_broken:
    description:
      - Skip all unavailable packages or packages with broken dependencies
        without raising an error. Equivalent to passing the C(--skip-broken) option.
    type: bool
    default: "no"
    version_added: "2.7"
  update_cache:
    description:
      - Force dnf to check if cache is out of date and redownload if needed.
        Has an effect only if O(state=present) or O(state=latest).
    type: bool
    default: "no"
    aliases: [ expire-cache ]
    version_added: "2.7"
  update_only:
    description:
      - When using latest, only update installed packages. Do not install packages.
      - Has an effect only if O(state=present) or O(state=latest).
    default: "no"
    type: bool
    version_added: "2.7"
  security:
    description:
      - If set to V(true), and O(state=latest) then only installs updates that have been marked security related.
      - Note that, similar to C(dnf upgrade-minimal), this filter applies to dependencies as well.
    type: bool
    default: "no"
    version_added: "2.7"
  bugfix:
    description:
      - If set to V(true), and O(state=latest) then only installs updates that have been marked bugfix related.
      - Note that, similar to C(dnf upgrade-minimal), this filter applies to dependencies as well.
    default: "no"
    type: bool
    version_added: "2.7"
  enable_plugin:
    description:
      - C(Plugin) name to enable for the install/update operation.
        The enabled plugin will not persist beyond the transaction.
    version_added: "2.7"
    type: list
    elements: str
    default: []
  disable_plugin:
    description:
      - C(Plugin) name to disable for the install/update operation.
        The disabled plugins will not persist beyond the transaction.
    version_added: "2.7"
    type: list
    default: []
    elements: str
  disable_excludes:
    description:
      - Disable the excludes defined in DNF config files.
      - If set to V(all), disables all excludes.
      - If set to V(main), disable excludes defined in C([main]) in C(dnf.conf).
      - If set to V(repoid), disable excludes defined for given repo id.
    version_added: "2.7"
    type: str
  validate_certs:
    description:
      - This only applies if using a https url as the source of the rpm. For example, for localinstall.
        If set to V(false), the SSL certificates will not be validated.
      - This should only set to V(false) used on personally controlled sites using self-signed certificates as it avoids verifying the source site.
    type: bool
    default: "yes"
    version_added: "2.7"
  sslverify:
    description:
      - Disables SSL validation of the repository server for this transaction.
      - This should be set to V(false) if one of the configured repositories is using an untrusted or self-signed certificate.
    type: bool
    default: "yes"
    version_added: "2.13"
  allow_downgrade:
    description:
      - Specify if the named package and version is allowed to downgrade
        a maybe already installed higher version of that package.
        Note that setting O(allow_downgrade=true) can make this module
        behave in a non-idempotent way. The task could end up with a set
        of packages that does not match the complete list of specified
        packages to install (because dependencies between the downgraded
        package and others can cause changes to the packages which were
        in the earlier transaction).
      - Since this feature is not provided by C(dnf) itself but by M(ansible.builtin.dnf) module,
        using this in combination with wildcard characters in O(name) may result in an unexpected results.
    type: bool
    default: "no"
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
      - Has an effect only if O(download_only) is specified.
    type: str
    version_added: "2.8"
  allowerasing:
    description:
      - If V(true) it allows erasing of installed packages to resolve dependencies.
    required: false
    type: bool
    default: "no"
    version_added: "2.10"
  nobest:
    description:
      - This is the opposite of the O(best) option kept for backwards compatibility.
      - Since ansible-core 2.17 the default value is set by the operating system distribution.
    required: false
    type: bool
    version_added: "2.11"
  best:
    description:
      - When set to V(true), either use a package with the highest version available or fail.
      - When set to V(false), if the latest version cannot be installed go with the lower version.
      - Default is set by the operating system distribution.
    required: false
    type: bool
    version_added: "2.17"
  cacheonly:
    description:
      - Tells dnf to run entirely from system cache; does not download or update metadata.
    type: bool
    default: "no"
    version_added: "2.12"
extends_documentation_fragment:
- action_common_attributes
- action_common_attributes.flow
attributes:
    action:
        details: dnf has 2 action plugins that use it under the hood, M(ansible.builtin.dnf) and M(ansible.builtin.package).
        support: partial
    async:
        support: none
    bypass_host_loop:
        support: none
    check_mode:
        support: full
    diff_mode:
        support: full
    platform:
        platforms: rhel
notes:
  - When used with a C(loop:) each package will be processed individually, it is much more efficient to pass the list directly to the O(name) option.
  - Group removal doesn't work if the group was installed with Ansible because
    upstream dnf's API doesn't properly mark groups as installed, therefore upon
    removal the module is unable to detect that the group is installed
    U(https://bugzilla.redhat.com/show_bug.cgi?id=1620324).
  - While O(use_backend=yum) and the ability to call the action plugin as
    M(ansible.builtin.yum) are provided for syntax compatibility, the YUM
    backend was removed in ansible-core 2.17 because the required libraries are
    not available for any supported version of Python. If you rely on this
    functionality, use an older version of Ansible.
requirements:
  - python3-dnf
author:
  - Igor Gnatenko (@ignatenkobrain) <i.gnatenko.brain@gmail.com>
  - Cristian van Ee (@DJMuggs) <cristian at cvee.org>
  - Berend De Schouwer (@berenddeschouwer)
  - Adam Miller (@maxamillion) <admiller@redhat.com>
"""

EXAMPLES = """
- name: Install the latest version of Apache
  ansible.builtin.dnf:
    name: httpd
    state: latest

- name: Install Apache >= 2.4
  ansible.builtin.dnf:
    name: httpd >= 2.4
    state: present

- name: Install the latest version of Apache and MariaDB
  ansible.builtin.dnf:
    name:
      - httpd
      - mariadb-server
    state: latest

- name: Remove the Apache package
  ansible.builtin.dnf:
    name: httpd
    state: absent

- name: Install the latest version of Apache from the testing repo
  ansible.builtin.dnf:
    name: httpd
    enablerepo: testing
    state: present

- name: Upgrade all packages
  ansible.builtin.dnf:
    name: "*"
    state: latest

- name: Update the webserver, depending on which is installed on the system. Do not install the other one
  ansible.builtin.dnf:
    name:
      - httpd
      - nginx
    state: latest
    update_only: yes

- name: Install the nginx rpm from a remote repo
  ansible.builtin.dnf:
    name: 'http://nginx.org/packages/centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm'
    state: present

- name: Install nginx rpm from a local file
  ansible.builtin.dnf:
    name: /usr/local/src/nginx-release-centos-6-0.el6.ngx.noarch.rpm
    state: present

- name: Install Package based upon the file it provides
  ansible.builtin.dnf:
    name: /usr/bin/cowsay
    state: present

- name: Install the 'Development tools' package group
  ansible.builtin.dnf:
    name: '@Development tools'
    state: present

- name: Autoremove unneeded packages installed as dependencies
  ansible.builtin.dnf:
    autoremove: yes

- name: Uninstall httpd but keep its dependencies
  ansible.builtin.dnf:
    name: httpd
    state: absent
    autoremove: no

- name: Install a modularity appstream with defined stream and profile
  ansible.builtin.dnf:
    name: '@postgresql:9.6/client'
    state: present

- name: Install a modularity appstream with defined stream
  ansible.builtin.dnf:
    name: '@postgresql:9.6'
    state: present

- name: Install a modularity appstream with defined profile
  ansible.builtin.dnf:
    name: '@postgresql/client'
    state: present
"""

import os
import sys

from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.urls import fetch_file

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.locale import get_best_parsable_locale
from ansible.module_utils.common.respawn import has_respawned, probe_interpreters_for_module, respawn_module
from ansible.module_utils.yumdnf import YumDnf, yumdnf_argument_spec


# FIXME: NOTE dnf Python bindings import is postponed, see DnfModule._ensure_dnf(),
#  because we need AnsibleModule object to use get_best_parsable_locale()
#  to set proper locale before importing dnf to be able to scrape
#  the output in some cases.
dnf = None


class DnfModule(YumDnf):
    """
    DNF Ansible module back-end implementation
    """

    def __init__(self, module):
        # This populates instance vars for all argument spec params
        super(DnfModule, self).__init__(module)

        self._ensure_dnf()
        self.pkg_mgr_name = "dnf"
        self.with_modules = dnf.base.WITH_MODULES

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

        # envra format for backwards compat
        result['envra'] = '{epoch}:{name}-{version}-{release}.{arch}'.format(**result)

        # keep nevra key for backwards compat as it was previously
        # defined with a value in envra format
        result['nevra'] = result['envra']

        if package.installtime == 0:
            result['yumstate'] = 'available'
        else:
            result['yumstate'] = 'installed'

        return result

    def _ensure_dnf(self):
        locale = get_best_parsable_locale(self.module)
        os.environ['LC_ALL'] = os.environ['LC_MESSAGES'] = locale
        os.environ['LANGUAGE'] = os.environ['LANG'] = locale

        global dnf
        try:
            import dnf
            import dnf.const
            import dnf.exceptions
            import dnf.package
            import dnf.subject
            import dnf.util
            HAS_DNF = True
        except ImportError:
            HAS_DNF = False

        if HAS_DNF:
            return

        system_interpreters = ['/usr/libexec/platform-python',
                               '/usr/bin/python3',
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
                "Please install `python3-dnf` package or ensure you have specified the "
                "correct ansible_python_interpreter. (attempted {2})"
                .format(sys.executable, sys.version.replace('\n', ''), system_interpreters),
            results=[]
        )

    def _configure_base(self, base, conf_file, disable_gpg_check, installroot='/', sslverify=True):
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

        # Set certificate validation
        conf.sslverify = sslverify

        # Set installroot
        if not os.path.isdir(installroot):
            self.module.fail_json(msg=f"Installroot {installroot} must be a directory")

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

        if conf.substitutions.get('releasever') is None:
            self.module.warn(
                'Unable to detect release version (use "releasever" option to specify release version)'
            )
            # values of conf.substitutions are expected to be strings
            # setting this to an empty string instead of None appears to mimic the DNF CLI behavior
            conf.substitutions['releasever'] = ''

        # Honor installroot for dnf directories
        # This will also perform variable substitutions in the paths
        for opt in ('cachedir', 'logdir', 'persistdir'):
            conf.prepend_installroot(opt)

        # Set skip_broken (in dnf this is strict=0)
        if self.skip_broken:
            conf.strict = 0

        # best and nobest are mutually exclusive
        if self.nobest is not None:
            conf.best = not self.nobest
        elif self.best is not None:
            conf.best = self.best

        if self.download_only:
            conf.downloadonly = True
            if self.download_dir:
                conf.destdir = self.download_dir

        if self.cacheonly:
            conf.cacheonly = True

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

        for repo in base.repos.iter_enabled():
            if self.disable_gpg_check:
                repo.gpgcheck = False
                repo.repo_gpgcheck = False

    def _base(self, conf_file, disable_gpg_check, disablerepo, enablerepo, installroot, sslverify):
        """Return a fully configured dnf Base object."""
        base = dnf.Base()
        self._configure_base(base, conf_file, disable_gpg_check, installroot, sslverify)

        base.setup_loggers()
        base.init_plugins(set(self.disable_plugin), set(self.enable_plugin))
        base.pre_configure_plugins()

        self._specify_repositories(base, disablerepo, enablerepo)

        base.configure_plugins()

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

        add_security_filters = getattr(base, "add_security_filters", None)
        if callable(add_security_filters):
            filters = {}
            if self.bugfix:
                filters.setdefault('types', []).append('bugfix')
            if self.security:
                filters.setdefault('types', []).append('security')
            if filters:
                add_security_filters('eq', **filters)
        else:
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
        return bool(dnf.subject.Subject(pkg).get_best_query(sack=self.base.sack).installed())

    def _is_newer_version_installed(self, pkg_spec):
        # expects a versioned package spec
        try:
            if isinstance(pkg_spec, dnf.package.Package):
                installed = sorted(self.base.sack.query().installed().filter(name=pkg_spec.name, arch=pkg_spec.arch))[-1]
                return installed.evr_gt(pkg_spec)
            else:
                solution = dnf.subject.Subject(pkg_spec).get_best_solution(self.base.sack)
                q = solution["query"]
                if not q or not solution['nevra'] or solution['nevra'].has_just_name():
                    return False
                installed = self.base.sack.query().installed().filter(name=solution['nevra'].name)
                if not installed:
                    return False
                return installed[0].evr_gt(q[0])
        except IndexError:
            return False

    def _mark_package_install(self, pkg_spec, upgrade=False):
        """Mark the package for install."""
        msg = ''
        try:
            if dnf.util.is_glob_pattern(pkg_spec):
                # Special case for package specs that contain glob characters.
                # For these we skip `is_installed` and `is_newer_version_installed` tests that allow for the
                # allow_downgrade feature and pass the package specs to dnf.
                # Since allow_downgrade is not available in dnf and while it is relatively easy to implement it for
                # package specs that evaluate to a single package, trying to mimic what would the dnf machinery do
                # for glob package specs and then filtering those for allow_downgrade appears to always
                # result in naive/inferior solution.
                # NOTE this has historically never worked even before https://github.com/ansible/ansible/pull/82725
                # where our (buggy) custom code ignored wildcards for the installed checks.
                # TODO reasearch how feasible it is to implement the above
                if upgrade:
                    # for upgrade we pass the spec to both upgrade and install, to satisfy both available and installed
                    # packages evaluated from the glob spec
                    try:
                        self.base.upgrade(pkg_spec)
                    except dnf.exceptions.PackagesNotInstalledError:
                        pass
                self.base.install(pkg_spec, strict=self.base.conf.strict)
            elif self._is_newer_version_installed(pkg_spec):
                if self.allow_downgrade:
                    self.base.install(pkg_spec, strict=self.base.conf.strict)
            elif self._is_installed(pkg_spec):
                if upgrade:
                    self.base.upgrade(pkg_spec)
            else:
                self.base.install(pkg_spec, strict=self.base.conf.strict)
        except dnf.exceptions.MarkingError as e:
            msg = "No package {0} available.".format(pkg_spec)
            if self.base.conf.strict:
                return {
                    'failed': True,
                    'msg': msg,
                    'failure': " ".join((pkg_spec, to_native(e))),
                    'rc': 1,
                    "results": []
                }
        except dnf.exceptions.DepsolveError as e:
            return {
                'failed': True,
                'msg': "Depsolve Error occurred for package {0}.".format(pkg_spec),
                'failure': " ".join((pkg_spec, to_native(e))),
                'rc': 1,
                "results": []
            }
        except dnf.exceptions.Error as e:
            return {
                'failed': True,
                'msg': "Unknown Error occurred for package {0}.".format(pkg_spec),
                'failure': " ".join((pkg_spec, to_native(e))),
                'rc': 1,
                "results": []
            }

        return {'failed': False, 'msg': msg, 'failure': '', 'rc': 0}

    def _parse_spec_group_file(self):
        pkg_specs, grp_specs, module_specs, filenames = [], [], [], []
        already_loaded_comps = False  # Only load this if necessary, it's slow

        for name in self.names:
            if '://' in name:
                name = fetch_file(self.module, name)
                filenames.append(name)
            elif name.endswith(".rpm"):
                filenames.append(name)
            elif name.startswith('/'):
                # dnf install /usr/bin/vi
                installed = self.base.sack.query().filter(provides=name, file=name).installed().run()
                if installed:
                    pkg_specs.append(installed[0].name)  # should be only one?
                elif not self.update_only:
                    # not installed, pass the filename for dnf to process
                    pkg_specs.append(name)
            elif name.startswith("@") or ('/' in name):
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
            if self._is_installed(
                    self._package_dict(pkg)["nevra"] if isinstance(pkg, dnf.package.Package) else pkg
            ):
                try:
                    if isinstance(pkg, dnf.package.Package):
                        self.base.package_upgrade(pkg)
                    else:
                        self.base.upgrade(pkg)
                except Exception as e:
                    self.module.fail_json(
                        msg="Error occurred attempting update_only operation: {0}".format(to_native(e)),
                        results=[],
                        rc=1,
                    )
            else:
                not_installed.append(pkg)

        return not_installed

    def _install_remote_rpms(self, filenames):
        try:
            pkgs = self.base.add_remote_rpms(filenames)
            if self.update_only:
                self._update_only(pkgs)
            else:
                for pkg in pkgs:
                    if not (self._is_newer_version_installed(pkg) and not self.allow_downgrade):
                        self.base.package_install(pkg, strict=self.base.conf.strict)
        except Exception as e:
            self.module.fail_json(
                msg="Error occurred attempting remote rpm operation: {0}".format(to_native(e)),
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

        return False  # seems like a logical default

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
                failure_response['msg'] = "Depsolve Error occurred attempting to upgrade all packages"
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
                        failure_response['msg'] = "Depsolve Error occurred attempting to install group: {0}".format(group)
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
                        failure_response['msg'] = "Depsolve Error occurred attempting to install environment: {0}".format(environment)
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
                        failure_response['msg'] = "Depsolve Error occurred attempting to install environment: {0}".format(environment)
                    except dnf.exceptions.Error as e:
                        failure_response['failures'].append(" ".join((environment, to_native(e))))

                if self.update_only:
                    not_installed = self._update_only(pkg_specs)
                    for spec in not_installed:
                        response['results'].append("Packages providing %s not installed due to update_only specified" % spec)
                else:
                    for pkg_spec in pkg_specs:
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

                for environment in environments:
                    try:
                        self.base.environment_remove(environment)
                    except dnf.exceptions.CompsError:
                        # Environment is already uninstalled.
                        pass

                for pkg_spec in pkg_specs:
                    try:
                        self.base.remove(pkg_spec)
                    except dnf.exceptions.MarkingError as e:
                        response['results'].append(f"{e.value}: {pkg_spec}")

                # Like the dnf CLI we want to allow recursive removal of dependent
                # packages
                self.allowerasing = True

                if self.autoremove:
                    self.base.autoremove()

        try:
            # NOTE for people who go down the rabbit hole of figuring out why
            # resolve() throws DepsolveError here on dep conflict, but not when
            # called from the CLI: It's controlled by conf.best. When best is
            # set, Hawkey will fail the goal, and resolve() in dnf.base.Base
            # will throw. Otherwise if it's not set, the update (install) will
            # be (almost silently) removed from the goal, and Hawkey will report
            # success. Note that in this case, similar to the CLI, skip_broken
            # does nothing to help here, so we don't take it into account at
            # all.
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
                    failure_response['msg'] = "Failed to download packages: {0}".format(to_native(e))
                    self.module.fail_json(**failure_response)

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
                            msg = 'Failed to validate GPG signature for {0}: {1}'.format(package, gpgerr)
                            self.module.fail_json(msg)

                if self.download_only:
                    # No further work left to do, and the results were already updated above.
                    # Just return them.
                    self.module.exit_json(**response)
                else:
                    tid = self.base.do_transaction()
                    if tid is not None:
                        transaction = self.base.history.old([tid])[0]
                        if transaction.return_code:
                            failure_response['failures'].append(transaction.output())

                if failure_response['failures']:
                    failure_response['msg'] = 'Failed to install some of the specified packages'
                    self.module.fail_json(**failure_response)
                self.module.exit_json(**response)
        except dnf.exceptions.DepsolveError as e:
            failure_response['msg'] = "Depsolve Error occurred: {0}".format(to_native(e))
            self.module.fail_json(**failure_response)
        except dnf.exceptions.Error as e:
            failure_response['msg'] = "Unknown Error occurred: {0}".format(to_native(e))
            self.module.fail_json(**failure_response)

    def run(self):
        if self.update_cache and not self.names and not self.list:
            self.base = self._base(
                self.conf_file, self.disable_gpg_check, self.disablerepo,
                self.enablerepo, self.installroot, self.sslverify
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
                self.enablerepo, self.installroot, self.sslverify
            )
            self.list_items(self.list)
        else:
            # Note: base takes a long time to run so we want to check for failure
            # before running it.
            if not self.download_only and not dnf.util.am_i_root():
                self.module.fail_json(
                    msg="This command has to be run under the root user.",
                    results=[],
                )
            self.base = self._base(
                self.conf_file, self.disable_gpg_check, self.disablerepo,
                self.enablerepo, self.installroot, self.sslverify
            )

            if self.with_modules:
                self.module_base = dnf.module.module_base.ModuleBase(self.base)
            try:
                self.ensure()
            finally:
                self.base.close()


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

    yumdnf_argument_spec['argument_spec']['use_backend'] = dict(default='auto', choices=['auto', 'dnf', 'yum', 'yum4', 'dnf4', 'dnf5'])

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
