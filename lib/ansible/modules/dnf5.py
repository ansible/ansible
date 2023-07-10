# -*- coding: utf-8 -*-
# Copyright 2023 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
module: dnf5
author: Ansible Core Team
description:
  - Installs, upgrade, removes, and lists packages and groups with the I(dnf5) package manager.
  - "WARNING: The I(dnf5) package manager is still under development and not all features that the existing I(dnf) module
    provides are implemented in I(dnf5), please consult specific options for more information."
short_description: Manages packages with the I(dnf5) package manager
options:
  name:
    description:
      - "A package name or package specifier with version, like C(name-1.0).
        When using state=latest, this can be '*' which means run: dnf -y update.
        You can also pass a url or a local path to a rpm file.
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
        Use M(ansible.builtin.package_facts) instead of the C(list) argument as a best practice.
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
    default: []
  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
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
        installed. Has an effect only if state is I(present) or I(latest).
      - This setting affects packages installed from a repository as well as
        "local" packages installed from the filesystem or a URL.
    type: bool
    default: 'no'
  installroot:
    description:
      - Specifies an alternative installroot, relative to which all packages
        will be installed.
    default: "/"
    type: str
  releasever:
    description:
      - Specifies an alternative release from which all packages will be
        installed.
    type: str
  autoremove:
    description:
      - If C(true), removes all "leaf" packages from the system that were originally
        installed as dependencies of user-installed packages but which are no longer
        required by any such package. Should be used alone or when state is I(absent)
    type: bool
    default: "no"
  exclude:
    description:
      - Package name(s) to exclude when state=present, or latest. This can be a
        list or a comma separated string.
    type: list
    elements: str
    default: []
  skip_broken:
    description:
      - Skip all unavailable packages or packages with broken dependencies
        without raising an error. Equivalent to passing the --skip-broken option.
    type: bool
    default: "no"
  update_cache:
    description:
      - Force dnf to check if cache is out of date and redownload if needed.
        Has an effect only if state is I(present) or I(latest).
    type: bool
    default: "no"
    aliases: [ expire-cache ]
  update_only:
    description:
      - When using latest, only update installed packages. Do not install packages.
      - Has an effect only if state is I(latest)
    default: "no"
    type: bool
  security:
    description:
      - If set to C(true), and C(state=latest) then only installs updates that have been marked security related.
      - Note that, similar to C(dnf upgrade-minimal), this filter applies to dependencies as well.
    type: bool
    default: "no"
  bugfix:
    description:
      - If set to C(true), and C(state=latest) then only installs updates that have been marked bugfix related.
      - Note that, similar to C(dnf upgrade-minimal), this filter applies to dependencies as well.
    default: "no"
    type: bool
  enable_plugin:
    description:
      - This is currently a no-op as dnf5 itself does not implement this feature.
      - I(Plugin) name to enable for the install/update operation.
        The enabled plugin will not persist beyond the transaction.
    type: list
    elements: str
    default: []
  disable_plugin:
    description:
      - This is currently a no-op as dnf5 itself does not implement this feature.
      - I(Plugin) name to disable for the install/update operation.
        The disabled plugins will not persist beyond the transaction.
    type: list
    default: []
    elements: str
  disable_excludes:
    description:
      - Disable the excludes defined in DNF config files.
      - If set to C(all), disables all excludes.
      - If set to C(main), disable excludes defined in [main] in dnf.conf.
      - If set to C(repoid), disable excludes defined for given repo id.
    type: str
  validate_certs:
    description:
      - This is effectively a no-op in the dnf5 module as dnf5 itself handles downloading a https url as the source of the rpm,
        but is an accepted parameter for feature parity/compatibility with the I(yum) module.
    type: bool
    default: "yes"
  sslverify:
    description:
      - Disables SSL validation of the repository server for this transaction.
      - This should be set to C(false) if one of the configured repositories is using an untrusted or self-signed certificate.
    type: bool
    default: "yes"
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
  install_repoquery:
    description:
      - This is effectively a no-op in DNF as it is not needed with DNF, but is an accepted parameter for feature
        parity/compatibility with the I(yum) module.
    type: bool
    default: "yes"
  download_only:
    description:
      - Only download the packages, do not install them.
    default: "no"
    type: bool
  lock_timeout:
    description:
      - This is currently a no-op as dnf5 does not provide an option to configure it.
      - Amount of time to wait for the dnf lockfile to be freed.
    required: false
    default: 30
    type: int
  install_weak_deps:
    description:
      - Will also install all packages linked by a weak dependency relation.
    type: bool
    default: "yes"
  download_dir:
    description:
      - Specifies an alternate directory to store packages.
      - Has an effect only if I(download_only) is specified.
    type: str
  allowerasing:
    description:
      - If C(true) it allows  erasing  of  installed  packages to resolve dependencies.
    required: false
    type: bool
    default: "no"
  nobest:
    description:
      - Set best option to False, so that transactions are not limited to best candidates only.
    required: false
    type: bool
    default: "no"
  cacheonly:
    description:
      - Tells dnf to run entirely from system cache; does not download or update metadata.
    type: bool
    default: "no"
extends_documentation_fragment:
- action_common_attributes
- action_common_attributes.flow
attributes:
    action:
        details: In the case of dnf, it has 2 action plugins that use it under the hood, M(ansible.builtin.yum) and M(ansible.builtin.package).
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
requirements:
  - "python3"
  - "python3-libdnf5"
version_added: 2.15
"""

EXAMPLES = """
- name: Install the latest version of Apache
  ansible.builtin.dnf5:
    name: httpd
    state: latest

- name: Install Apache >= 2.4
  ansible.builtin.dnf5:
    name: httpd >= 2.4
    state: present

- name: Install the latest version of Apache and MariaDB
  ansible.builtin.dnf5:
    name:
      - httpd
      - mariadb-server
    state: latest

- name: Remove the Apache package
  ansible.builtin.dnf5:
    name: httpd
    state: absent

- name: Install the latest version of Apache from the testing repo
  ansible.builtin.dnf5:
    name: httpd
    enablerepo: testing
    state: present

- name: Upgrade all packages
  ansible.builtin.dnf5:
    name: "*"
    state: latest

- name: Update the webserver, depending on which is installed on the system. Do not install the other one
  ansible.builtin.dnf5:
    name:
      - httpd
      - nginx
    state: latest
    update_only: yes

- name: Install the nginx rpm from a remote repo
  ansible.builtin.dnf5:
    name: 'http://nginx.org/packages/centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm'
    state: present

- name: Install nginx rpm from a local file
  ansible.builtin.dnf5:
    name: /usr/local/src/nginx-release-centos-6-0.el6.ngx.noarch.rpm
    state: present

- name: Install Package based upon the file it provides
  ansible.builtin.dnf5:
    name: /usr/bin/cowsay
    state: present

- name: Install the 'Development tools' package group
  ansible.builtin.dnf5:
    name: '@Development tools'
    state: present

- name: Autoremove unneeded packages installed as dependencies
  ansible.builtin.dnf5:
    autoremove: yes

- name: Uninstall httpd but keep its dependencies
  ansible.builtin.dnf5:
    name: httpd
    state: absent
    autoremove: no
"""

RETURN = """
msg:
  description: Additional information about the result
  returned: always
  type: str
  sample: "Nothing to do"
results:
  description: A list of the dnf transaction results
  returned: success
  type: list
  sample: ["Installed: lsof-4.94.0-4.fc37.x86_64"]
failures:
  description: A list of the dnf transaction failures
  returned: failure
  type: list
  sample: ["Argument 'lsof' matches only excluded packages."]
rc:
  description: For compatibility, 0 for success, 1 for failure
  returned: always
  type: int
  sample: 0
"""

import os
import sys

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.locale import get_best_parsable_locale
from ansible.module_utils.common.respawn import has_respawned, probe_interpreters_for_module, respawn_module
from ansible.module_utils.yumdnf import YumDnf, yumdnf_argument_spec

libdnf5 = None


def is_installed(base, spec):
    settings = libdnf5.base.ResolveSpecSettings()
    query = libdnf5.rpm.PackageQuery(base)
    query.filter_installed()
    match, nevra = query.resolve_pkg_spec(spec, settings, True)
    return match


def is_newer_version_installed(base, spec):
    try:
        spec_nevra = next(iter(libdnf5.rpm.Nevra.parse(spec)))
    except RuntimeError:
        return False
    spec_name = spec_nevra.get_name()
    v = spec_nevra.get_version()
    r = spec_nevra.get_release()
    if not v or not r:
        return False
    spec_evr = "{}:{}-{}".format(spec_nevra.get_epoch() or "0", v, r)

    query = libdnf5.rpm.PackageQuery(base)
    query.filter_installed()
    query.filter_name([spec_name])
    query.filter_evr([spec_evr], libdnf5.common.QueryCmp_GT)

    return query.size() > 0


def package_to_dict(package):
    return {
        "nevra": package.get_nevra(),
        "envra": package.get_nevra(),  # dnf module compat
        "name": package.get_name(),
        "arch": package.get_arch(),
        "epoch": str(package.get_epoch()),
        "release": package.get_release(),
        "version": package.get_version(),
        "repo": package.get_repo_id(),
        "yumstate": "installed" if package.is_installed() else "available",
    }


def get_unneeded_pkgs(base):
    query = libdnf5.rpm.PackageQuery(base)
    query.filter_installed()
    query.filter_unneeded()
    for pkg in query:
        yield pkg


class Dnf5Module(YumDnf):
    def __init__(self, module):
        super(Dnf5Module, self).__init__(module)
        self._ensure_dnf()

        # FIXME https://github.com/rpm-software-management/dnf5/issues/402
        self.lockfile = ""
        self.pkg_mgr_name = "dnf5"

        # DNF specific args that are not part of YumDnf
        self.allowerasing = self.module.params["allowerasing"]
        self.nobest = self.module.params["nobest"]

    def _ensure_dnf(self):
        locale = get_best_parsable_locale(self.module)
        os.environ["LC_ALL"] = os.environ["LC_MESSAGES"] = locale
        os.environ["LANGUAGE"] = os.environ["LANG"] = locale

        global libdnf5
        has_dnf = True
        try:
            import libdnf5  # type: ignore[import]
        except ImportError:
            has_dnf = False

        if has_dnf:
            return

        system_interpreters = [
            "/usr/libexec/platform-python",
            "/usr/bin/python3",
            "/usr/bin/python2",
            "/usr/bin/python",
        ]

        if not has_respawned():
            # probe well-known system Python locations for accessible bindings, favoring py3
            interpreter = probe_interpreters_for_module(system_interpreters, "libdnf5")

            if interpreter:
                # respawn under the interpreter where the bindings should be found
                respawn_module(interpreter)
                # end of the line for this module, the process will exit here once the respawned module completes

        # done all we can do, something is just broken (auto-install isn't useful anymore with respawn, so it was removed)
        self.module.fail_json(
            msg="Could not import the libdnf5 python module using {0} ({1}). "
            "Please install python3-libdnf5 package or ensure you have specified the "
            "correct ansible_python_interpreter. (attempted {2})".format(
                sys.executable, sys.version.replace("\n", ""), system_interpreters
            ),
            failures=[],
        )

    def is_lockfile_pid_valid(self):
        # FIXME https://github.com/rpm-software-management/dnf5/issues/402
        return True

    def run(self):
        if sys.version_info.major < 3:
            self.module.fail_json(
                msg="The dnf5 module requires Python 3.",
                failures=[],
                rc=1,
            )
        if not self.list and not self.download_only and os.geteuid() != 0:
            self.module.fail_json(
                msg="This command has to be run under the root user.",
                failures=[],
                rc=1,
            )

        if self.enable_plugin or self.disable_plugin:
            self.module.fail_json(
                msg="enable_plugin and disable_plugin options are not yet implemented in DNF5",
                failures=[],
                rc=1,
            )

        base = libdnf5.base.Base()
        conf = base.get_config()

        if self.conf_file:
            conf.config_file_path = self.conf_file

        try:
            base.load_config_from_file()
        except RuntimeError as e:
            self.module.fail_json(
                msg=str(e),
                conf_file=self.conf_file,
                failures=[],
                rc=1,
            )

        if self.releasever is not None:
            variables = base.get_vars()
            variables.set("releasever", self.releasever)
        if self.exclude:
            conf.excludepkgs = self.exclude
        if self.disable_excludes:
            if self.disable_excludes == "all":
                self.disable_excludes = "*"
            conf.disable_excludes = self.disable_excludes
        conf.skip_broken = self.skip_broken
        conf.best = not self.nobest
        conf.install_weak_deps = self.install_weak_deps
        conf.gpgcheck = not self.disable_gpg_check
        conf.localpkg_gpgcheck = not self.disable_gpg_check
        conf.sslverify = self.sslverify
        conf.clean_requirements_on_remove = self.autoremove
        conf.installroot = self.installroot
        conf.use_host_config = True  # needed for installroot
        conf.cacheonly = "all" if self.cacheonly else "none"
        if self.download_dir:
            conf.destdir = self.download_dir

        base.setup()

        log_router = base.get_logger()
        global_logger = libdnf5.logger.GlobalLogger()
        global_logger.set(log_router.get(), libdnf5.logger.Logger.Level_DEBUG)
        logger = libdnf5.logger.create_file_logger(base)
        log_router.add_logger(logger)

        if self.update_cache:
            repo_query = libdnf5.repo.RepoQuery(base)
            repo_query.filter_type(libdnf5.repo.Repo.Type_AVAILABLE)
            for repo in repo_query:
                repo_dir = repo.get_cachedir()
                if os.path.exists(repo_dir):
                    repo_cache = libdnf5.repo.RepoCache(base, repo_dir)
                    repo_cache.write_attribute(libdnf5.repo.RepoCache.ATTRIBUTE_EXPIRED)

        sack = base.get_repo_sack()
        sack.create_repos_from_system_configuration()

        repo_query = libdnf5.repo.RepoQuery(base)
        if self.disablerepo:
            repo_query.filter_id(self.disablerepo, libdnf5.common.QueryCmp_IGLOB)
            for repo in repo_query:
                repo.disable()
        if self.enablerepo:
            repo_query.filter_id(self.enablerepo, libdnf5.common.QueryCmp_IGLOB)
            for repo in repo_query:
                repo.enable()

        sack.update_and_load_enabled_repos(True)

        if self.update_cache and not self.names and not self.list:
            self.module.exit_json(
                msg="Cache updated",
                changed=False,
                results=[],
                rc=0
            )

        if self.list:
            command = self.list
            if command == "updates":
                command = "upgrades"

            if command in {"installed", "upgrades", "available"}:
                query = libdnf5.rpm.PackageQuery(base)
                getattr(query, "filter_{}".format(command))()
                results = [package_to_dict(package) for package in query]
            elif command in {"repos", "repositories"}:
                query = libdnf5.repo.RepoQuery(base)
                query.filter_enabled(True)
                results = [{"repoid": repo.get_id(), "state": "enabled"} for repo in query]
            else:
                resolve_spec_settings = libdnf5.base.ResolveSpecSettings()
                query = libdnf5.rpm.PackageQuery(base)
                query.resolve_pkg_spec(command, resolve_spec_settings, True)
                results = [package_to_dict(package) for package in query]

            self.module.exit_json(msg="", results=results, rc=0)

        settings = libdnf5.base.GoalJobSettings()
        settings.group_with_name = True
        if self.bugfix or self.security:
            advisory_query = libdnf5.advisory.AdvisoryQuery(base)
            types = []
            if self.bugfix:
                types.append("bugfix")
            if self.security:
                types.append("security")
            advisory_query.filter_type(types)
            settings.set_advisory_filter(advisory_query)

        goal = libdnf5.base.Goal(base)
        results = []
        if self.names == ["*"] and self.state == "latest":
            goal.add_rpm_upgrade(settings)
        elif self.state in {"install", "present", "latest"}:
            upgrade = self.state == "latest"
            for spec in self.names:
                if is_newer_version_installed(base, spec):
                    if self.allow_downgrade:
                        if upgrade:
                            if is_installed(base, spec):
                                goal.add_upgrade(spec, settings)
                            else:
                                goal.add_install(spec, settings)
                        else:
                            goal.add_install(spec, settings)
                elif is_installed(base, spec):
                    if upgrade:
                        goal.add_upgrade(spec, settings)
                else:
                    if self.update_only:
                        results.append("Packages providing {} not installed due to update_only specified".format(spec))
                    else:
                        goal.add_install(spec, settings)
        elif self.state in {"absent", "removed"}:
            for spec in self.names:
                try:
                    goal.add_remove(spec, settings)
                except RuntimeError as e:
                    self.module.fail_json(msg=str(e), failures=[], rc=1)
            if self.autoremove:
                for pkg in get_unneeded_pkgs(base):
                    goal.add_rpm_remove(pkg, settings)

        goal.set_allow_erasing(self.allowerasing)
        try:
            transaction = goal.resolve()
        except RuntimeError as e:
            self.module.fail_json(msg=str(e), failures=[], rc=1)

        if transaction.get_problems():
            failures = []
            for log_event in transaction.get_resolve_logs():
                if log_event.get_problem() == libdnf5.base.GoalProblem_NOT_FOUND and self.state in {"install", "present", "latest"}:
                    # NOTE dnf module compat
                    failures.append("No package {} available.".format(log_event.get_spec()))
                else:
                    failures.append(log_event.to_string())

            if transaction.get_problems() & libdnf5.base.GoalProblem_SOLVER_ERROR != 0:
                msg = "Depsolve Error occurred"
            else:
                msg = "Failed to install some of the specified packages"
            self.module.fail_json(
                msg=msg,
                failures=failures,
                rc=1,
            )

        # NOTE dnf module compat
        actions_compat_map = {
            "Install": "Installed",
            "Remove": "Removed",
            "Replace": "Installed",
            "Upgrade": "Installed",
            "Replaced": "Removed",
        }
        changed = bool(transaction.get_transaction_packages())
        for pkg in transaction.get_transaction_packages():
            if self.download_only:
                action = "Downloaded"
            else:
                action = libdnf5.base.transaction.transaction_item_action_to_string(pkg.get_action())
            results.append("{}: {}".format(actions_compat_map.get(action, action), pkg.get_package().get_nevra()))

        msg = ""
        if self.module.check_mode:
            if results:
                msg = "Check mode: No changes made, but would have if not in check mode"
        else:
            transaction.download()
            if not self.download_only:
                transaction.set_description("ansible dnf5 module")
                result = transaction.run()
                if result == libdnf5.base.Transaction.TransactionRunResult_ERROR_GPG_CHECK:
                    self.module.fail_json(
                        msg="Failed to validate GPG signatures: {}".format(",".join(transaction.get_gpg_signature_problems())),
                        failures=[],
                        rc=1,
                    )
                elif result != libdnf5.base.Transaction.TransactionRunResult_SUCCESS:
                    self.module.fail_json(
                        msg="Failed to install some of the specified packages",
                        failures=["{}: {}".format(transaction.transaction_result_to_string(result), log) for log in transaction.get_transaction_problems()],
                        rc=1,
                    )

        if not msg and not results:
            msg = "Nothing to do"

        self.module.exit_json(
            results=results,
            changed=changed,
            msg=msg,
            rc=0,
        )


def main():
    # Extend yumdnf_argument_spec with dnf-specific features that will never be
    # backported to yum because yum is now in "maintenance mode" upstream
    yumdnf_argument_spec["argument_spec"]["allowerasing"] = dict(default=False, type="bool")
    yumdnf_argument_spec["argument_spec"]["nobest"] = dict(default=False, type="bool")
    Dnf5Module(AnsibleModule(**yumdnf_argument_spec)).run()


if __name__ == "__main__":
    main()
