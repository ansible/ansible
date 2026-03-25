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

import json
import sys

from ansible.module_utils.urls import fetch_file
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.respawn import get_env_with_pythonpath, probe_interpreters_for_module
from ansible.module_utils.embed import EmbedManager
from ansible.module_utils.yumdnf import YumDnf, yumdnf_argument_spec


dnfscript = EmbedManager.embed('..module_utils._embed', 'dnf.py')


class DnfModule(YumDnf):
    """
    DNF Ansible module back-end implementation
    """

    def __init__(self, module):
        # This populates instance vars for all argument spec params
        super(DnfModule, self).__init__(module)

        self._interpreter = self._probe_interpreters()
        self.pkg_mgr_name = "dnf"

    def _build_config(self):
        """Build configuration dictionary for module_utils functions."""
        return {
            'conf_file': self.conf_file,
            'disable_gpg_check': self.disable_gpg_check,
            'sslverify': self.sslverify,
            'installroot': self.installroot,
            'exclude': self.exclude,
            'disable_excludes': self.disable_excludes,
            'releasever': self.releasever,
            'skip_broken': self.skip_broken,
            'nobest': self.nobest,
            'best': self.best,
            'download_only': self.download_only,
            'download_dir': self.download_dir,
            'cacheonly': self.cacheonly,
            'autoremove': self.autoremove,
            'install_weak_deps': self.install_weak_deps,
            'disablerepo': self.disablerepo,
            'enablerepo': self.enablerepo,
            'disable_plugin': self.disable_plugin,
            'enable_plugin': self.enable_plugin,
            'update_cache': self.update_cache,
            'bugfix': self.bugfix,
            'security': self.security,
        }

    def _probe_interpreters(self):
        interpreters = [
            sys.executable,
            '/usr/libexec/platform-python',
            '/usr/bin/python3',
            '/usr/bin/python'
        ]

        # probe well-known system Python locations for accessible bindings, favoring py3
        interpreter = probe_interpreters_for_module(interpreters, module_names=['dnf'])

        if not interpreter:
            # done all we can do, something is just broken (auto-install isn't useful anymore with respawn, so it was removed)
            self.module.fail_json(
                msg='Could not import the dnf python module. '
                    f'Please install `python3-dnf` package. (attempted {interpreters})',
                results=[]
            )

        return interpreter

    def _execute_dnf_script(self, command, config, params=None):
        """Execute the dnf module_utils script via subprocess with JSON RPC."""
        request = {'command': command, 'config': config}
        if params:
            request['params'] = params

        request_json = json.dumps(request)
        python_executable = self._interpreter or sys.executable
        env = get_env_with_pythonpath()

        try:
            rc, stdout, stderr = self.module.run_command(
                [python_executable, '-m', dnfscript.python_module_ref],
                data=request_json,
                check_rc=False,
                handle_exceptions=False,
                environ_update=env,
            )

            if stdout:
                return json.loads(stdout)
            else:
                return {
                    'failed': True,
                    'msg': f'No output from dnf script. stderr: {stderr}',
                    'results': [],
                    'rc': rc
                }
        except json.JSONDecodeError as e:
            return {
                'failed': True,
                'msg': f'Failed to parse JSON from dnf script: {e}. stdout: {stdout}',
                'results': [],
                'rc': 1
            }
        except Exception as e:
            return {
                'failed': True,
                'msg': f'Failed to execute dnf script: {e}',
                'results': [],
                'rc': 1
            }

    def list_items(self, command):
        """List package info based on the command."""
        config = self._build_config()

        result = self._execute_dnf_script(
            command='list',
            config=config,
            params={'list_command': command},
        )

        if result.get('failed'):
            self.module.fail_json(msg=result['msg'], results=[], rc=1)

        for warning in result.get('warnings', []):
            self.module.warn(warning)

        self.module.exit_json(msg='', results=result['results'])

    def ensure(self):
        names = [fetch_file(self.module, name) if '://' in name else name for name in self.names]

        config = self._build_config()
        params = {
            'names': names,
            'state': self.state,
            'autoremove': self.autoremove,
            'update_only': self.update_only,
            'allow_downgrade': self.allow_downgrade,
            'download_only': self.download_only,
            'disable_gpg_check': self.disable_gpg_check,
            'check_mode': self.module.check_mode,
            'download_dir': self.download_dir,
            'allowerasing': self.allowerasing,
        }

        result = self._execute_dnf_script(
            command='ensure',
            config=config,
            params=params,
        )

        for warning in result.get('warnings', []):
            self.module.warn(warning)

        if result.get('failed'):
            error_msg = result.get('msg', 'Unknown error occurred')
            if result.get('failures'):
                self.module.fail_json(
                    msg=error_msg,
                    failures=result['failures'],
                    results=result.get('results', []),
                    rc=result.get('rc', 1)
                )
            else:
                self.module.fail_json(
                    msg=error_msg,
                    results=result.get('results', []),
                    rc=result.get('rc', 1)
                )

        if result.get('changed', False):
            self.module.exit_json(
                msg=result.get('msg', ''),
                changed=True,
                results=result.get('results', []),
                rc=result.get('rc', 0)
            )
        else:
            self.module.exit_json(
                msg=result.get('msg', 'Nothing to do'),
                changed=False,
                results=result.get('results', []),
                rc=result.get('rc', 0)
            )

    def update_cache_only(self):
        config = self._build_config()

        result = self._execute_dnf_script(
            command='update-cache',
            config=config,
        )

        if result.get('failed'):
            self.module.fail_json(
                msg=result['msg'],
                results=[],
                rc=1
            )

        for warning in result.get('warnings', []):
            self.module.warn(warning)

        self.module.exit_json(
            msg='Cache updated',
            changed=result.get('changed', False),
            results=[],
            rc=0
        )

    def run(self):
        if self.update_cache and not self.names and not self.list:
            self.update_cache_only()
            return

        # Set state as installed by default
        # This is not set in AnsibleModule() because the following shouldn't happen
        # - dnf: autoremove=yes state=installed
        if self.state is None:
            self.state = 'installed'

        if self.list:
            self.list_items(self.list)
        else:
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

    yumdnf_argument_spec['argument_spec']['use_backend'] = dict(default='auto', choices=['auto', 'dnf', 'yum', 'yum4', 'dnf4', 'dnf5'])

    module = AnsibleModule(
        **yumdnf_argument_spec
    )

    module_implementation = DnfModule(module)
    module_implementation.run()


if __name__ == '__main__':
    main()
