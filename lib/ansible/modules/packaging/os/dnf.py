#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Cristian van Ee <cristian at cvee.org>
# Copyright 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com>
# Copyright 2018 Adam Miller <admiller@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


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
      - "A list of package names, or package specifier with version, like C(name-1.0)
        When using state=latest, this can be '*' which means run: dnf -y update.
        You can also pass a url or a local path to a rpm file."
    required: true
    aliases:
        - pkg

  list:
    description:
      - Various (non-idempotent) commands for usage with C(/usr/bin/ansible) and I(not) playbooks. See examples.

  state:
    description:
      - Whether to install (C(present), C(latest)), or remove (C(absent)) a package.
    choices: ['absent', 'present', 'installed', 'removed', 'latest']
    default: "present"

  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".

  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".

  conf_file:
    description:
      - The remote dnf configuration file to use for the transaction.

  disable_gpg_check:
    description:
      - Whether to disable the GPG checking of signatures of packages being
        installed. Has an effect only if state is I(present) or I(latest).
    type: bool
    default: 'no'

  installroot:
    description:
      - Specifies an alternative installroot, relative to which all packages
        will be installed.
    version_added: "2.3"
    default: "/"

  releasever:
    description:
      - Specifies an alternative release from which all packages will be
        installed.
    required: false
    version_added: "2.6"
    default: null

  autoremove:
    description:
      - If C(yes), removes all "leaf" packages from the system that were originally
        installed as dependencies of user-installed packages but which are no longer
        required by any such package. Should be used alone or when state is I(absent)
    type: bool
    default: false
    version_added: "2.4"
  exclude:
    description:
      - Package name(s) to exclude when state=present, or latest. This can be a
        list or a comma separated string.
    version_added: "2.7"
  skip_broken:
    description:
      - Skip packages with broken dependencies(devsolve) and are causing problems.
    type: bool
    default: "no"
    version_added: "2.7"
  update_cache:
    description:
      - Force yum to check if cache is out of date and redownload if needed.
        Has an effect only if state is I(present) or I(latest).
    type: bool
    default: "no"
    aliases: [ expire-cache ]
    version_added: "2.7"
  update_only:
    description:
      - When using latest, only update installed packages. Do not install packages.
      - Has an effect only if state is I(latest)
    required: false
    default: "no"
    type: bool
    version_added: "2.7"
  security:
    description:
      - If set to C(yes), and C(state=latest) then only installs updates that have been marked security related.
    type: bool
    default: "no"
    version_added: "2.7"
  bugfix:
    description:
      - If set to C(yes), and C(state=latest) then only installs updates that have been marked bugfix related.
    required: false
    default: "no"
    type: bool
    version_added: "2.7"
  enable_plugin:
    description:
      - I(Plugin) name to enable for the install/update operation.
        The enabled plugin will not persist beyond the transaction.
    required: false
    version_added: "2.7"
  disable_plugin:
    description:
      - I(Plugin) name to disable for the install/update operation.
        The disabled plugins will not persist beyond the transaction.
    required: false
    version_added: "2.7"
  disable_excludes:
    description:
      - Disable the excludes defined in DNF config files.
      - If set to C(all), disables all excludes.
      - If set to C(main), disable excludes defined in [main] in yum.conf.
      - If set to C(repoid), disable excludes defined for given repo id.
    required: false
    choices: [ all, main, repoid ]
    version_added: "2.7"
  validate_certs:
    description:
      - This only applies if using a https url as the source of the rpm. e.g. for localinstall. If set to C(no), the SSL certificates will not be validated.
      - This should only set to C(no) used on personally controlled sites using self-signed certificates as it avoids verifying the source site.
    type: bool
    default: "yes"
    version_added: "2.7"
  allow_downgrade:
    description:
      - This is effectively a no-op in DNF as it is the default behavior of dnf, but is an accepted parameter for feature
        parity/compatibility with the I(yum) module.
    type: bool
    default: False
    version_added: "2.7"
  install_repoquery:
    description:
      - This is effectively a no-op in DNF as it is not needed with DNF, but is an accepted parameter for feature
        parity/compatibility with the I(yum) module.
    type: bool
    default: True
    version_added: "2.7"
  download_only:
    description:
      - Only download the packages, do not install them.
    required: false
    default: "no"
    type: bool
    version_added: "2.7"
notes:
  - When used with a `loop:` each package will be processed individually, it is much more efficient to pass the list directly to the `name` option.
requirements:
  - "python >= 2.6"
  - python-dnf
  - for the autoremove option you need dnf >= 2.0.1"
author:
  - '"Igor Gnatenko (@ignatenkobrain)" <i.gnatenko.brain@gmail.com>'
  - '"Cristian van Ee (@DJMuggs)" <cristian at cvee.org>'
  - "Berend De Schouwer (github.com/berenddeschouwer)"
  - '"Adam Miller (@maxamillion)" <admiller@redhat.com>"'
'''

EXAMPLES = '''
- name: install the latest version of Apache
  dnf:
    name: httpd
    state: latest

- name: remove the Apache package
  dnf:
    name: httpd
    state: absent

- name: install the latest version of Apache from the testing repo
  dnf:
    name: httpd
    enablerepo: testing
    state: present

- name: upgrade all packages
  dnf:
    name: "*"
    state: latest

- name: install the nginx rpm from a remote repo
  dnf:
    name: 'http://nginx.org/packages/centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm'
    state: present

- name: install nginx rpm from a local file
  dnf:
    name: /usr/local/src/nginx-release-centos-6-0.el6.ngx.noarch.rpm
    state: present

- name: install the 'Development tools' package group
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
'''

import os
import tempfile

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

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six import PY2
from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.yumdnf import YumDnf, yumdnf_argument_spec

# 64k.  Number of bytes to read at a time when manually downloading pkgs via a url
BUFSIZE = 65536


class DnfModule(YumDnf):
    """
    DNF Ansible module back-end implementation
    """

    def __init__(self, module):
        # This populates instance vars for all argument spec params
        super(DnfModule, self).__init__(module)

        self._ensure_dnf()

    def fetch_rpm_from_url(self, spec):
        # FIXME: Remove this once this PR is merged:
        #   https://github.com/ansible/ansible/pull/19172

        # download package so that we can query it
        package_name, dummy = os.path.splitext(str(spec.rsplit('/', 1)[1]))
        package_file = tempfile.NamedTemporaryFile(dir=self.module.tmpdir, prefix=package_name, suffix='.rpm', delete=False)
        self.module.add_cleanup_file(package_file.name)
        try:
            rsp, info = fetch_url(self.module, spec)
            if not rsp:
                self.module.fail_json(msg="Failure downloading %s, %s" % (spec, info['msg']))
            data = rsp.read(BUFSIZE)
            while data:
                package_file.write(data)
                data = rsp.read(BUFSIZE)
            package_file.close()
        except Exception as e:
            self.module.fail_json(msg="Failure downloading %s, %s" % (spec, to_native(e)))

        return package_file.name

    def _ensure_dnf(self):
        if not HAS_DNF:
            if PY2:
                package = 'python2-dnf'
            else:
                package = 'python3-dnf'

            if self.module.check_mode:
                self.module.fail_json(
                    msg="`{0}` is not installed, but it is required"
                    "for the Ansible dnf module.".format(package)
                )

            self.module.run_command(['dnf', 'install', '-y', package], check_rc=True)
            global dnf
            try:
                import dnf
                import dnf.cli
                import dnf.const
                import dnf.exceptions
                import dnf.subject
                import dnf.util
            except ImportError:
                self.module.fail_json(
                    msg="Could not import the dnf python module. "
                    "Please install `{0}` package.".format(package)
                )

    def _configure_base(self, base, conf_file, disable_gpg_check, installroot='/'):
        """Configure the dnf Base object."""

        if self.enable_plugin and self.disable_plugin:
            base.init_plugins(self.disable_plugin, self.enable_plugin)
        elif self.enable_plugin:
            base.init_plugins(enable_plugins=self.enable_plugin)
        elif self.disable_plugin:
            base.init_plugins(self.disable_plugin)

        conf = base.conf

        # Turn off debug messages in the output
        conf.debuglevel = 0

        # Set whether to check gpg signatures
        conf.gpgcheck = not disable_gpg_check

        # Don't prompt for user confirmations
        conf.assumeyes = True

        # Set installroot
        conf.installroot = installroot

        # Set excludes
        if self.exclude:
            conf.exclude(self.exclude)

        # Set disable_excludes
        if self.disable_excludes:
            conf.disable_excludes = [self.disable_excludes]

        # Set releasever
        if self.releasever is not None:
            conf.substitutions['releasever'] = self.releasever

        # Set skip_broken (in dnf this is strict=0)
        if self.skip_broken:
            conf.strict = 0

        if self.download_only:
            conf.downloadonly = True

        # Change the configuration file path if provided
        if conf_file:
            # Fail if we can't read the configuration file.
            if not os.access(conf_file, os.R_OK):
                self.module.fail_json(
                    msg="cannot read configuration file", conf_file=conf_file)
            else:
                conf.config_file_path = conf_file

        # Read the configuration file
        conf.read()

    def _specify_repositories(self, base, disablerepo, enablerepo):
        """Enable and disable repositories matching the provided patterns."""
        base.read_all_repos()
        repos = base.repos

        # Disable repositories
        for repo_pattern in disablerepo:
            for repo in repos.get_matching(repo_pattern):
                repo.disable()

        # Enable repositories
        for repo_pattern in enablerepo:
            for repo in repos.get_matching(repo_pattern):
                repo.enable()

    def _base(self, conf_file, disable_gpg_check, disablerepo, enablerepo, installroot):
        """Return a fully configured dnf Base object."""
        base = dnf.Base()
        self._configure_base(base, conf_file, disable_gpg_check, installroot)
        self._specify_repositories(base, disablerepo, enablerepo)
        base.fill_sack(load_system_repo='auto')
        if self.bugfix:
            key = {'advisory_type__eq': 'bugfix'}
            base._update_security_filters = [base.sack.query().filter(**key)]
        if self.security:
            key = {'advisory_type__eq': 'security'}
            base._update_security_filters = [base.sack.query().filter(**key)]
        if self.update_cache:
            base.update_cache()
        return base

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

        return result

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

        self.module.exit_json(results=results)

    def _mark_package_install(self, pkg_spec):
        """Mark the package for install."""
        try:
            self.base.install(pkg_spec)
        except dnf.exceptions.MarkingError:
            self.module.fail_json(msg="No package {0} available.".format(pkg_spec))

    def _parse_spec_group_file(self):
        pkg_specs, grp_specs, filenames = [], [], []
        for name in self.names:
            if name.endswith(".rpm"):
                if '://' in name:
                    name = self.fetch_rpm_from_url(name)
                filenames.append(name)
            elif name.startswith("@"):
                grp_specs.append(name[1:])
            else:
                pkg_specs.append(name)
        return pkg_specs, grp_specs, filenames

    def _update_only(self, pkgs):
        installed = self.base.sack.query().installed()
        for pkg in pkgs:
            if installed.filter(name=pkg):
                self.base.package_upgrade(pkg)

    def _install_remote_rpms(self, filenames):
        if int(dnf.__version__.split(".")[0]) >= 2:
            pkgs = list(sorted(self.base.add_remote_rpms(list(filenames)), reverse=True))
        else:
            pkgs = []
            for filename in filenames:
                pkgs.append(self.base.add_remote_rpm(filename))
        if self.update_only:
            self._update_only(pkgs)
        else:
            for pkg in pkgs:
                self.base.package_install(pkg)

    def ensure(self):
        # Accumulate failures.  Package management modules install what they can
        # and fail with a message about what they can't.
        failures = []
        allow_erasing = False

        # Autoremove is called alone
        # Jump to remove path where base.autoremove() is run
        if not self.names and self.autoremove:
            self.names = []
            self.state = 'absent'

        if self.names == ['*'] and self.state == 'latest':
            self.base.upgrade_all()
        else:
            pkg_specs, group_specs, filenames = self._parse_spec_group_file()
            if group_specs:
                self.base.read_comps()

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
                            msg="No group {0} available.".format(group_spec))

            if self.state in ['installed', 'present']:
                # Install files.
                self._install_remote_rpms(filenames)

                # Install groups.
                for group in groups:
                    try:
                        self.base.group_install(group, dnf.const.GROUP_PACKAGE_TYPES)
                    except dnf.exceptions.Error as e:
                        # In dnf 2.0 if all the mandatory packages in a group do
                        # not install, an error is raised.  We want to capture
                        # this but still install as much as possible.
                        failures.append((group, to_native(e)))

                for environment in environments:
                    try:
                        self.base.environment_install(environment, dnf.const.GROUP_PACKAGE_TYPES)
                    except dnf.exceptions.Error as e:
                        failures.append((environment, to_native(e)))

                # Install packages.
                if self.update_only:
                    self._update_only(pkg_specs)
                else:
                    for pkg_spec in pkg_specs:
                        self._mark_package_install(pkg_spec)

            elif self.state == 'latest':
                # "latest" is same as "installed" for filenames.
                self._install_remote_rpms(filenames)

                for group in groups:
                    try:
                        try:
                            self.base.group_upgrade(group)
                        except dnf.exceptions.CompsError:
                            # If not already installed, try to install.
                            self.base.group_install(group, dnf.const.GROUP_PACKAGE_TYPES)
                    except dnf.exceptions.Error as e:
                        failures.append((group, to_native(e)))

                for environment in environments:
                    try:
                        try:
                            self.base.environment_upgrade(environment)
                        except dnf.exceptions.CompsError:
                            # If not already installed, try to install.
                            self.base.environment_install(environment, dnf.const.GROUP_PACKAGE_TYPES)
                    except dnf.exceptions.Error as e:
                        failures.append((environment, to_native(e)))

                if self.update_only:
                    self._update_only(pkg_specs)
                else:
                    for pkg_spec in pkg_specs:
                        # best effort causes to install the latest package
                        # even if not previously installed
                        self.base.conf.best = True
                        try:
                            self.base.install(pkg_spec)
                        except dnf.exceptions.MarkingError as e:
                            failures.append((pkg_spec, to_native(e)))

            else:
                # state == absent
                if self.autoremove:
                    self.base.conf.clean_requirements_on_remove = self.autoremove

                if filenames:
                    self.module.fail_json(
                        msg="Cannot remove paths -- please specify package name.")

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

                installed = self.base.sack.query().installed()
                for pkg_spec in pkg_specs:
                    if installed.filter(name=pkg_spec):
                        self.base.remove(pkg_spec)

                # Like the dnf CLI we want to allow recursive removal of dependent
                # packages
                allow_erasing = True

                if self.autoremove:
                    self.base.autoremove()

        if not self.base.resolve(allow_erasing=allow_erasing):
            if failures:
                self.module.fail_json(
                    msg='Failed to install some of the specified packages',
                    failures=failures
                )
            self.module.exit_json(msg="Nothing to do")
        else:
            if self.module.check_mode:
                if failures:
                    self.module.fail_json(
                        msg='Failed to install some of the specified packages',
                        failures=failures
                    )
                self.module.exit_json(changed=True)

            try:
                self.base.download_packages(self.base.transaction.install_set)
            except dnf.exceptions.DownloadError as e:
                self.module.fail_json(msg="Failed to download packages: {0}".format(to_text(e)))

            response = {'changed': True, 'results': []}
            if self.download_only:
                for package in self.base.transaction.install_set:
                    response['results'].append("Downloaded: {0}".format(package))
                self.module.exit_json(**response)
            else:
                self.base.do_transaction()
                for package in self.base.transaction.install_set:
                    response['results'].append("Installed: {0}".format(package))
                for package in self.base.transaction.remove_set:
                    response['results'].append("Removed: {0}".format(package))

            if failures:
                self.module.fail_json(
                    msg='Failed to install some of the specified packages',
                    failures=failures
                )
            self.module.exit_json(**response)

    @staticmethod
    def has_dnf():
        return HAS_DNF

    def run(self):
        """The main function."""

        # Check if autoremove is called correctly
        if self.autoremove:
            if LooseVersion(dnf.__version__) < LooseVersion('2.0.1'):
                self.module.fail_json(msg="Autoremove requires dnf>=2.0.1. Current dnf version is %s" % dnf.__version__)
            if self.state not in ["absent", None]:
                self.module.fail_json(msg="Autoremove should be used alone or with state=absent")

        # Set state as installed by default
        # This is not set in AnsibleModule() because the following shouldn't happend
        # - dnf: autoremove=yes state=installed
        if self.state is None:
            self.state = 'installed'

        if self.list:
            self.base = self._base(
                self.conf_file, self.disable_gpg_check, self.disablerepo,
                self.enablerepo, self.installroot
            )
            self.list_items(self.module, self.list)
        else:
            # Note: base takes a long time to run so we want to check for failure
            # before running it.
            if not dnf.util.am_i_root():
                self.module.fail_json(msg="This command has to be run under the root user.")
            self.base = self._base(
                self.conf_file, self.disable_gpg_check, self.disablerepo,
                self.enablerepo, self.installroot
            )

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

    module = AnsibleModule(
        **yumdnf_argument_spec
    )

    module_implementation = DnfModule(module)
    try:
        module_implementation.run()
    except dnf.exceptions.RepoError as de:
        module.exit_json(msg="Failed to synchronize repodata: {0}".format(de))


if __name__ == '__main__':
    main()
