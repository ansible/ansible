#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Red Hat, Inc
# Written by Seth Vidal <skvidal at fedoraproject.org>
# Copyright: (c) 2014, Epic Games, Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: yum
version_added: historical
short_description: Manages packages with the I(yum) package manager
description:
     - Installs, upgrade, downgrades, removes, and lists packages and groups with the I(yum) package manager.
     - This module only works on Python 2. If you require Python 3 support see the M(ansible.builtin.dnf) module.
options:
  use_backend:
    description:
      - This module supports C(yum) (as it always has), this is known as C(yum3)/C(YUM3)/C(yum-deprecated) by
        upstream yum developers. As of Ansible 2.7+, this module also supports C(YUM4), which is the
        "new yum" and it has an C(dnf) backend.
      - By default, this module will select the backend based on the C(ansible_pkg_mgr) fact.
    default: "auto"
    choices: [ auto, yum, yum4, dnf ]
    type: str
    version_added: "2.7"
  name:
    description:
      - A package name or package specifier with version, like C(name-1.0).
      - Comparison operators for package version are valid here C(>), C(<), C(>=), C(<=). Example - C(name>=1.0)
      - If a previous version is specified, the task also needs to turn C(allow_downgrade) on.
        See the C(allow_downgrade) documentation for caveats with downgrading packages.
      - When using state=latest, this can be C('*') which means run C(yum -y update).
      - You can also pass a url or a local path to a rpm file (using state=present).
        To operate on several packages this can accept a comma separated string of packages or (as of 2.0) a list of packages.
    aliases: [ pkg ]
    type: list
    elements: str
  exclude:
    description:
      - Package name(s) to exclude when state=present, or latest
    type: list
    elements: str
    version_added: "2.0"
  list:
    description:
      - "Package name to run the equivalent of yum list C(--show-duplicates <package>) against. In addition to listing packages,
        use can also list the following: C(installed), C(updates), C(available) and C(repos)."
      - This parameter is mutually exclusive with I(name).
    type: str
  state:
    description:
      - Whether to install (C(present) or C(installed), C(latest)), or remove (C(absent) or C(removed)) a package.
      - C(present) and C(installed) will simply ensure that a desired package is installed.
      - C(latest) will update the specified package if it's not of the latest available version.
      - C(absent) and C(removed) will remove the specified package.
      - Default is C(None), however in effect the default action is C(present) unless the C(autoremove) option is
        enabled for this module, then C(absent) is inferred.
    type: str
    choices: [ absent, installed, latest, present, removed ]
  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a C(",").
      - As of Ansible 2.7, this can alternatively be a list instead of C(",")
        separated string
    type: list
    elements: str
    version_added: "0.9"
  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a C(",").
      - As of Ansible 2.7, this can alternatively be a list instead of C(",")
        separated string
    type: list
    elements: str
    version_added: "0.9"
  conf_file:
    description:
      - The remote yum configuration file to use for the transaction.
    type: str
    version_added: "0.6"
  disable_gpg_check:
    description:
      - Whether to disable the GPG checking of signatures of packages being
        installed. Has an effect only if state is I(present) or I(latest).
    type: bool
    default: "no"
    version_added: "1.2"
  skip_broken:
    description:
      - Skip packages with broken dependencies(devsolve) and are causing problems.
    type: bool
    default: "no"
    version_added: "2.3"
  update_cache:
    description:
      - Force yum to check if cache is out of date and redownload if needed.
        Has an effect only if state is I(present) or I(latest).
    type: bool
    default: "no"
    aliases: [ expire-cache ]
    version_added: "1.9"
  validate_certs:
    description:
      - This only applies if using a https url as the source of the rpm. e.g. for localinstall. If set to C(no), the SSL certificates will not be validated.
      - This should only set to C(no) used on personally controlled sites using self-signed certificates as it avoids verifying the source site.
      - Prior to 2.1 the code worked as if this was set to C(yes).
    type: bool
    default: "yes"
    version_added: "2.1"

  update_only:
    description:
      - When using latest, only update installed packages. Do not install packages.
      - Has an effect only if state is I(latest)
    default: "no"
    type: bool
    version_added: "2.5"

  installroot:
    description:
      - Specifies an alternative installroot, relative to which all packages
        will be installed.
    default: "/"
    type: str
    version_added: "2.3"
  security:
    description:
      - If set to C(yes), and C(state=latest) then only installs updates that have been marked security related.
    type: bool
    default: "no"
    version_added: "2.4"
  bugfix:
    description:
      - If set to C(yes), and C(state=latest) then only installs updates that have been marked bugfix related.
    default: "no"
    type: bool
    version_added: "2.6"
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
    version_added: "2.4"
  enable_plugin:
    description:
      - I(Plugin) name to enable for the install/update operation.
        The enabled plugin will not persist beyond the transaction.
    type: list
    elements: str
    version_added: "2.5"
  disable_plugin:
    description:
      - I(Plugin) name to disable for the install/update operation.
        The disabled plugins will not persist beyond the transaction.
    type: list
    elements: str
    version_added: "2.5"
  releasever:
    description:
      - Specifies an alternative release from which all packages will be
        installed.
    type: str
    version_added: "2.7"
  autoremove:
    description:
      - If C(yes), removes all "leaf" packages from the system that were originally
        installed as dependencies of user-installed packages but which are no longer
        required by any such package. Should be used alone or when state is I(absent)
      - "NOTE: This feature requires yum >= 3.4.3 (RHEL/CentOS 7+)"
    type: bool
    default: "no"
    version_added: "2.7"
  disable_excludes:
    description:
      - Disable the excludes defined in YUM config files.
      - If set to C(all), disables all excludes.
      - If set to C(main), disable excludes defined in [main] in yum.conf.
      - If set to C(repoid), disable excludes defined for given repo id.
    type: str
    version_added: "2.7"
  download_only:
    description:
      - Only download the packages, do not install them.
    default: "no"
    type: bool
    version_added: "2.7"
  lock_timeout:
    description:
      - Amount of time to wait for the yum lockfile to be freed.
    required: false
    default: 30
    type: int
    version_added: "2.8"
  install_weak_deps:
    description:
      - Will also install all packages linked by a weak dependency relation.
      - "NOTE: This feature requires yum >= 4 (RHEL/CentOS 8+)"
    type: bool
    default: "yes"
    version_added: "2.8"
  download_dir:
    description:
      - Specifies an alternate directory to store packages.
      - Has an effect only if I(download_only) is specified.
    type: str
    version_added: "2.8"
  install_repoquery:
    description:
      - If repoquery is not available, install yum-utils. If the system is
        registered to RHN or an RHN Satellite, repoquery allows for querying
        all channels assigned to the system. It is also required to use the
        'list' parameter.
      - "NOTE: This will run and be logged as a separate yum transation which
        takes place before any other installation or removal."
      - "NOTE: This will use the system's default enabled repositories without
        regard for disablerepo/enablerepo given to the module."
    required: false
    version_added: "1.5"
    default: "yes"
    type: bool
notes:
  - When used with a C(loop:) each package will be processed individually,
    it is much more efficient to pass the list directly to the I(name) option.
  - In versions prior to 1.9.2 this module installed and removed each package
    given to the yum module separately. This caused problems when packages
    specified by filename or url had to be installed or removed together. In
    1.9.2 this was fixed so that packages are installed in one yum
    transaction. However, if one of the packages adds a new yum repository
    that the other packages come from (such as epel-release) then that package
    needs to be installed in a separate task. This mimics yum's command line
    behaviour.
  - 'Yum itself has two types of groups.  "Package groups" are specified in the
    rpm itself while "environment groups" are specified in a separate file
    (usually by the distribution).  Unfortunately, this division becomes
    apparent to ansible users because ansible needs to operate on the group
    of packages in a single transaction and yum requires groups to be specified
    in different ways when used in that way.  Package groups are specified as
    "@development-tools" and environment groups are "@^gnome-desktop-environment".
    Use the "yum group list hidden ids" command to see which category of group the group
    you want to install falls into.'
  - 'The yum module does not support clearing yum cache in an idempotent way, so it
    was decided not to implement it, the only method is to use command and call the yum
    command directly, namely "command: yum clean all"
    https://github.com/ansible/ansible/pull/31450#issuecomment-352889579'
# informational: requirements for nodes
requirements:
- yum
author:
    - Ansible Core Team
    - Seth Vidal (@skvidal)
    - Eduard Snesarev (@verm666)
    - Berend De Schouwer (@berenddeschouwer)
    - Abhijeet Kasurde (@Akasurde)
    - Adam Miller (@maxamillion)
'''

EXAMPLES = '''
- name: Install the latest version of Apache
  yum:
    name: httpd
    state: latest

- name: Install Apache >= 2.4
  yum:
    name: httpd>=2.4
    state: present

- name: Install a list of packages (suitable replacement for 2.11 loop deprecation warning)
  yum:
    name:
      - nginx
      - postgresql
      - postgresql-server
    state: present

- name: Install a list of packages with a list variable
  yum:
    name: "{{ packages }}"
  vars:
    packages:
    - httpd
    - httpd-tools

- name: Remove the Apache package
  yum:
    name: httpd
    state: absent

- name: Install the latest version of Apache from the testing repo
  yum:
    name: httpd
    enablerepo: testing
    state: present

- name: Install one specific version of Apache
  yum:
    name: httpd-2.2.29-1.4.amzn1
    state: present

- name: Upgrade all packages
  yum:
    name: '*'
    state: latest

- name: Upgrade all packages, excluding kernel & foo related packages
  yum:
    name: '*'
    state: latest
    exclude: kernel*,foo*

- name: Install the nginx rpm from a remote repo
  yum:
    name: http://nginx.org/packages/centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm
    state: present

- name: Install nginx rpm from a local file
  yum:
    name: /usr/local/src/nginx-release-centos-6-0.el6.ngx.noarch.rpm
    state: present

- name: Install the 'Development tools' package group
  yum:
    name: "@Development tools"
    state: present

- name: Install the 'Gnome desktop' environment group
  yum:
    name: "@^gnome-desktop-environment"
    state: present

- name: List ansible packages and register result to print with debug later
  yum:
    list: ansible
  register: result

- name: Install package with multiple repos enabled
  yum:
    name: sos
    enablerepo: "epel,ol7_latest"

- name: Install package with multiple repos disabled
  yum:
    name: sos
    disablerepo: "epel,ol7_latest"

- name: Download the nginx package but do not install it
  yum:
    name:
      - nginx
    state: latest
    download_only: true
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.respawn import has_respawned, respawn_module
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.yumdnf import YumDnf, yumdnf_argument_spec

import errno
import os
import re
import sys
import tempfile

try:
    import rpm
    HAS_RPM_PYTHON = True
except ImportError:
    HAS_RPM_PYTHON = False

try:
    import yum
    HAS_YUM_PYTHON = True
except ImportError:
    HAS_YUM_PYTHON = False

try:
    from yum.misc import find_unfinished_transactions, find_ts_remaining
    from rpmUtils.miscutils import splitFilename, compareEVR
    transaction_helpers = True
except ImportError:
    transaction_helpers = False

from contextlib import contextmanager
from ansible.module_utils.urls import fetch_file

def_qf = "%{epoch}:%{name}-%{version}-%{release}.%{arch}"
rpmbin = None


class YumModule(YumDnf):
    """
    Yum Ansible module back-end implementation
    """

    def __init__(self, module):

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

        # This populates instance vars for all argument spec params
        super(YumModule, self).__init__(module)

        self.pkg_mgr_name = "yum"
        self.lockfile = '/var/run/yum.pid'
        self._yum_base = None

    def _enablerepos_with_error_checking(self):
        # NOTE: This seems unintuitive, but it mirrors yum's CLI behavior
        if len(self.enablerepo) == 1:
            try:
                self.yum_base.repos.enableRepo(self.enablerepo[0])
            except yum.Errors.YumBaseError as e:
                if u'repository not found' in to_text(e):
                    self.module.fail_json(msg="Repository %s not found." % self.enablerepo[0])
                else:
                    raise e
        else:
            for rid in self.enablerepo:
                try:
                    self.yum_base.repos.enableRepo(rid)
                except yum.Errors.YumBaseError as e:
                    if u'repository not found' in to_text(e):
                        self.module.warn("Repository %s not found." % rid)
                    else:
                        raise e

    def is_lockfile_pid_valid(self):
        try:
            try:
                with open(self.lockfile, 'r') as f:
                    oldpid = int(f.readline())
            except ValueError:
                # invalid data
                os.unlink(self.lockfile)
                return False

            if oldpid == os.getpid():
                # that's us?
                os.unlink(self.lockfile)
                return False

            try:
                with open("/proc/%d/stat" % oldpid, 'r') as f:
                    stat = f.readline()

                if stat.split()[2] == 'Z':
                    # Zombie
                    os.unlink(self.lockfile)
                    return False
            except IOError:
                # either /proc is not mounted or the process is already dead
                try:
                    # check the state of the process
                    os.kill(oldpid, 0)
                except OSError as e:
                    if e.errno == errno.ESRCH:
                        # No such process
                        os.unlink(self.lockfile)
                        return False

                    self.module.fail_json(msg="Unable to check PID %s in  %s: %s" % (oldpid, self.lockfile, to_native(e)))
        except (IOError, OSError) as e:
            # lockfile disappeared?
            return False

        # another copy seems to be running
        return True

    @property
    def yum_base(self):
        if self._yum_base:
            return self._yum_base
        else:
            # Only init once
            self._yum_base = yum.YumBase()
            self._yum_base.preconf.debuglevel = 0
            self._yum_base.preconf.errorlevel = 0
            self._yum_base.preconf.plugins = True
            self._yum_base.preconf.enabled_plugins = self.enable_plugin
            self._yum_base.preconf.disabled_plugins = self.disable_plugin
            if self.releasever:
                self._yum_base.preconf.releasever = self.releasever
            if self.installroot != '/':
                # do not setup installroot by default, because of error
                # CRITICAL:yum.cli:Config Error: Error accessing file for config file:////etc/yum.conf
                # in old yum version (like in CentOS 6.6)
                self._yum_base.preconf.root = self.installroot
                self._yum_base.conf.installroot = self.installroot
            if self.conf_file and os.path.exists(self.conf_file):
                self._yum_base.preconf.fn = self.conf_file
            if os.geteuid() != 0:
                if hasattr(self._yum_base, 'setCacheDir'):
                    self._yum_base.setCacheDir()
                else:
                    cachedir = yum.misc.getCacheDir()
                    self._yum_base.repos.setCacheDir(cachedir)
                    self._yum_base.conf.cache = 0
            if self.disable_excludes:
                self._yum_base.conf.disable_excludes = self.disable_excludes

            # A sideeffect of accessing conf is that the configuration is
            # loaded and plugins are discovered
            self.yum_base.conf

            try:
                for rid in self.disablerepo:
                    self.yum_base.repos.disableRepo(rid)

                self._enablerepos_with_error_checking()

            except Exception as e:
                self.module.fail_json(msg="Failure talking to yum: %s" % to_native(e))

        return self._yum_base

    def po_to_envra(self, po):
        if hasattr(po, 'ui_envra'):
            return po.ui_envra

        return '%s:%s-%s-%s.%s' % (po.epoch, po.name, po.version, po.release, po.arch)

    def is_group_env_installed(self, name):
        name_lower = name.lower()

        if yum.__version_info__ >= (3, 4):
            groups_list = self.yum_base.doGroupLists(return_evgrps=True)
        else:
            groups_list = self.yum_base.doGroupLists()

        # list of the installed groups on the first index
        groups = groups_list[0]
        for group in groups:
            if name_lower.endswith(group.name.lower()) or name_lower.endswith(group.groupid.lower()):
                return True

        if yum.__version_info__ >= (3, 4):
            # list of the installed env_groups on the third index
            envs = groups_list[2]
            for env in envs:
                if name_lower.endswith(env.name.lower()) or name_lower.endswith(env.environmentid.lower()):
                    return True

        return False

    def is_installed(self, repoq, pkgspec, qf=None, is_pkg=False):
        if qf is None:
            qf = "%{epoch}:%{name}-%{version}-%{release}.%{arch}\n"

        if not repoq:
            pkgs = []
            try:
                e, m, _ = self.yum_base.rpmdb.matchPackageNames([pkgspec])
                pkgs = e + m
                if not pkgs and not is_pkg:
                    pkgs.extend(self.yum_base.returnInstalledPackagesByDep(pkgspec))
            except Exception as e:
                self.module.fail_json(msg="Failure talking to yum: %s" % to_native(e))

            return [self.po_to_envra(p) for p in pkgs]

        else:
            global rpmbin
            if not rpmbin:
                rpmbin = self.module.get_bin_path('rpm', required=True)

            cmd = [rpmbin, '-q', '--qf', qf, pkgspec]
            if self.installroot != '/':
                cmd.extend(['--root', self.installroot])
            # rpm localizes messages and we're screen scraping so make sure we use
            # the C locale
            lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
            rc, out, err = self.module.run_command(cmd, environ_update=lang_env)
            if rc != 0 and 'is not installed' not in out:
                self.module.fail_json(msg='Error from rpm: %s: %s' % (cmd, err))
            if 'is not installed' in out:
                out = ''

            pkgs = [p for p in out.replace('(none)', '0').split('\n') if p.strip()]
            if not pkgs and not is_pkg:
                cmd = [rpmbin, '-q', '--qf', qf, '--whatprovides', pkgspec]
                if self.installroot != '/':
                    cmd.extend(['--root', self.installroot])
                rc2, out2, err2 = self.module.run_command(cmd, environ_update=lang_env)
            else:
                rc2, out2, err2 = (0, '', '')

            if rc2 != 0 and 'no package provides' not in out2:
                self.module.fail_json(msg='Error from rpm: %s: %s' % (cmd, err + err2))
            if 'no package provides' in out2:
                out2 = ''
            pkgs += [p for p in out2.replace('(none)', '0').split('\n') if p.strip()]
            return pkgs

        return []

    def is_available(self, repoq, pkgspec, qf=def_qf):
        if not repoq:

            pkgs = []
            try:
                e, m, _ = self.yum_base.pkgSack.matchPackageNames([pkgspec])
                pkgs = e + m
                if not pkgs:
                    pkgs.extend(self.yum_base.returnPackagesByDep(pkgspec))
            except Exception as e:
                self.module.fail_json(msg="Failure talking to yum: %s" % to_native(e))

            return [self.po_to_envra(p) for p in pkgs]

        else:
            myrepoq = list(repoq)

            r_cmd = ['--disablerepo', ','.join(self.disablerepo)]
            myrepoq.extend(r_cmd)

            r_cmd = ['--enablerepo', ','.join(self.enablerepo)]
            myrepoq.extend(r_cmd)

            if self.releasever:
                myrepoq.extend('--releasever=%s' % self.releasever)

            cmd = myrepoq + ["--qf", qf, pkgspec]
            rc, out, err = self.module.run_command(cmd)
            if rc == 0:
                return [p for p in out.split('\n') if p.strip()]
            else:
                self.module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err))

        return []

    def is_update(self, repoq, pkgspec, qf=def_qf):
        if not repoq:

            pkgs = []
            updates = []

            try:
                pkgs = self.yum_base.returnPackagesByDep(pkgspec) + \
                    self.yum_base.returnInstalledPackagesByDep(pkgspec)
                if not pkgs:
                    e, m, _ = self.yum_base.pkgSack.matchPackageNames([pkgspec])
                    pkgs = e + m
                updates = self.yum_base.doPackageLists(pkgnarrow='updates').updates
            except Exception as e:
                self.module.fail_json(msg="Failure talking to yum: %s" % to_native(e))

            retpkgs = (pkg for pkg in pkgs if pkg in updates)

            return set(self.po_to_envra(p) for p in retpkgs)

        else:
            myrepoq = list(repoq)
            r_cmd = ['--disablerepo', ','.join(self.disablerepo)]
            myrepoq.extend(r_cmd)

            r_cmd = ['--enablerepo', ','.join(self.enablerepo)]
            myrepoq.extend(r_cmd)

            if self.releasever:
                myrepoq.extend('--releasever=%s' % self.releasever)

            cmd = myrepoq + ["--pkgnarrow=updates", "--qf", qf, pkgspec]
            rc, out, err = self.module.run_command(cmd)

            if rc == 0:
                return set(p for p in out.split('\n') if p.strip())
            else:
                self.module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err))

        return set()

    def what_provides(self, repoq, req_spec, qf=def_qf):
        if not repoq:

            pkgs = []
            try:
                try:
                    pkgs = self.yum_base.returnPackagesByDep(req_spec) + \
                        self.yum_base.returnInstalledPackagesByDep(req_spec)
                except Exception as e:
                    # If a repo with `repo_gpgcheck=1` is added and the repo GPG
                    # key was never accepted, querying this repo will throw an
                    # error: 'repomd.xml signature could not be verified'. In that
                    # situation we need to run `yum -y makecache` which will accept
                    # the key and try again.
                    if 'repomd.xml signature could not be verified' in to_native(e):
                        if self.releasever:
                            self.module.run_command(self.yum_basecmd + ['makecache'] + ['--releasever=%s' % self.releasever])
                        else:
                            self.module.run_command(self.yum_basecmd + ['makecache'])
                        pkgs = self.yum_base.returnPackagesByDep(req_spec) + \
                            self.yum_base.returnInstalledPackagesByDep(req_spec)
                    else:
                        raise
                if not pkgs:
                    e, m, _ = self.yum_base.pkgSack.matchPackageNames([req_spec])
                    pkgs.extend(e)
                    pkgs.extend(m)
                    e, m, _ = self.yum_base.rpmdb.matchPackageNames([req_spec])
                    pkgs.extend(e)
                    pkgs.extend(m)
            except Exception as e:
                self.module.fail_json(msg="Failure talking to yum: %s" % to_native(e))

            return set(self.po_to_envra(p) for p in pkgs)

        else:
            myrepoq = list(repoq)
            r_cmd = ['--disablerepo', ','.join(self.disablerepo)]
            myrepoq.extend(r_cmd)

            r_cmd = ['--enablerepo', ','.join(self.enablerepo)]
            myrepoq.extend(r_cmd)

            if self.releasever:
                myrepoq.extend('--releasever=%s' % self.releasever)

            cmd = myrepoq + ["--qf", qf, "--whatprovides", req_spec]
            rc, out, err = self.module.run_command(cmd)
            cmd = myrepoq + ["--qf", qf, req_spec]
            rc2, out2, err2 = self.module.run_command(cmd)
            if rc == 0 and rc2 == 0:
                out += out2
                pkgs = set([p for p in out.split('\n') if p.strip()])
                if not pkgs:
                    pkgs = self.is_installed(repoq, req_spec, qf=qf)
                return pkgs
            else:
                self.module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err + err2))

        return set()

    def transaction_exists(self, pkglist):
        """
        checks the package list to see if any packages are
        involved in an incomplete transaction
        """

        conflicts = []
        if not transaction_helpers:
            return conflicts

        # first, we create a list of the package 'nvreas'
        # so we can compare the pieces later more easily
        pkglist_nvreas = (splitFilename(pkg) for pkg in pkglist)

        # next, we build the list of packages that are
        # contained within an unfinished transaction
        unfinished_transactions = find_unfinished_transactions()
        for trans in unfinished_transactions:
            steps = find_ts_remaining(trans)
            for step in steps:
                # the action is install/erase/etc., but we only
                # care about the package spec contained in the step
                (action, step_spec) = step
                (n, v, r, e, a) = splitFilename(step_spec)
                # and see if that spec is in the list of packages
                # requested for installation/updating
                for pkg in pkglist_nvreas:
                    # if the name and arch match, we're going to assume
                    # this package is part of a pending transaction
                    # the label is just for display purposes
                    label = "%s-%s" % (n, a)
                    if n == pkg[0] and a == pkg[4]:
                        if label not in conflicts:
                            conflicts.append("%s-%s" % (n, a))
                        break
        return conflicts

    def local_envra(self, path):
        """return envra of a local rpm passed in"""

        ts = rpm.TransactionSet()
        ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
        fd = os.open(path, os.O_RDONLY)
        try:
            header = ts.hdrFromFdno(fd)
        except rpm.error as e:
            return None
        finally:
            os.close(fd)

        return '%s:%s-%s-%s.%s' % (
            header[rpm.RPMTAG_EPOCH] or '0',
            header[rpm.RPMTAG_NAME],
            header[rpm.RPMTAG_VERSION],
            header[rpm.RPMTAG_RELEASE],
            header[rpm.RPMTAG_ARCH]
        )

    @contextmanager
    def set_env_proxy(self):
        # setting system proxy environment and saving old, if exists
        namepass = ""
        scheme = ["http", "https"]
        old_proxy_env = [os.getenv("http_proxy"), os.getenv("https_proxy")]
        try:
            # "_none_" is a special value to disable proxy in yum.conf/*.repo
            if self.yum_base.conf.proxy and self.yum_base.conf.proxy not in ("_none_",):
                if self.yum_base.conf.proxy_username:
                    namepass = namepass + self.yum_base.conf.proxy_username
                    proxy_url = self.yum_base.conf.proxy
                    if self.yum_base.conf.proxy_password:
                        namepass = namepass + ":" + self.yum_base.conf.proxy_password
                elif '@' in self.yum_base.conf.proxy:
                    namepass = self.yum_base.conf.proxy.split('@')[0].split('//')[-1]
                    proxy_url = self.yum_base.conf.proxy.replace("{0}@".format(namepass), "")

                if namepass:
                    namepass = namepass + '@'
                    for item in scheme:
                        os.environ[item + "_proxy"] = re.sub(
                            r"(http://)",
                            r"\g<1>" + namepass, proxy_url
                        )
                else:
                    for item in scheme:
                        os.environ[item + "_proxy"] = self.yum_base.conf.proxy
            yield
        except yum.Errors.YumBaseError:
            raise
        finally:
            # revert back to previously system configuration
            for item in scheme:
                if os.getenv("{0}_proxy".format(item)):
                    del os.environ["{0}_proxy".format(item)]
            if old_proxy_env[0]:
                os.environ["http_proxy"] = old_proxy_env[0]
            if old_proxy_env[1]:
                os.environ["https_proxy"] = old_proxy_env[1]

    def pkg_to_dict(self, pkgstr):
        if pkgstr.strip() and pkgstr.count('|') == 5:
            n, e, v, r, a, repo = pkgstr.split('|')
        else:
            return {'error_parsing': pkgstr}

        d = {
            'name': n,
            'arch': a,
            'epoch': e,
            'release': r,
            'version': v,
            'repo': repo,
            'envra': '%s:%s-%s-%s.%s' % (e, n, v, r, a)
        }

        if repo == 'installed':
            d['yumstate'] = 'installed'
        else:
            d['yumstate'] = 'available'

        return d

    def repolist(self, repoq, qf="%{repoid}"):
        cmd = repoq + ["--qf", qf, "-a"]
        if self.releasever:
            cmd.extend(['--releasever=%s' % self.releasever])
        rc, out, _ = self.module.run_command(cmd)
        if rc == 0:
            return set(p for p in out.split('\n') if p.strip())
        else:
            return []

    def list_stuff(self, repoquerybin, stuff):

        qf = "%{name}|%{epoch}|%{version}|%{release}|%{arch}|%{repoid}"
        # is_installed goes through rpm instead of repoquery so it needs a slightly different format
        is_installed_qf = "%{name}|%{epoch}|%{version}|%{release}|%{arch}|installed\n"
        repoq = [repoquerybin, '--show-duplicates', '--plugins', '--quiet']
        if self.disablerepo:
            repoq.extend(['--disablerepo', ','.join(self.disablerepo)])
        if self.enablerepo:
            repoq.extend(['--enablerepo', ','.join(self.enablerepo)])
        if self.installroot != '/':
            repoq.extend(['--installroot', self.installroot])
        if self.conf_file and os.path.exists(self.conf_file):
            repoq += ['-c', self.conf_file]

        if stuff == 'installed':
            return [self.pkg_to_dict(p) for p in sorted(self.is_installed(repoq, '-a', qf=is_installed_qf)) if p.strip()]

        if stuff == 'updates':
            return [self.pkg_to_dict(p) for p in sorted(self.is_update(repoq, '-a', qf=qf)) if p.strip()]

        if stuff == 'available':
            return [self.pkg_to_dict(p) for p in sorted(self.is_available(repoq, '-a', qf=qf)) if p.strip()]

        if stuff == 'repos':
            return [dict(repoid=name, state='enabled') for name in sorted(self.repolist(repoq)) if name.strip()]

        return [
            self.pkg_to_dict(p) for p in
            sorted(self.is_installed(repoq, stuff, qf=is_installed_qf) + self.is_available(repoq, stuff, qf=qf))
            if p.strip()
        ]

    def exec_install(self, items, action, pkgs, res):
        cmd = self.yum_basecmd + [action] + pkgs
        if self.releasever:
            cmd.extend(['--releasever=%s' % self.releasever])

        if self.module.check_mode:
            self.module.exit_json(changed=True, results=res['results'], changes=dict(installed=pkgs))
        else:
            res['changes'] = dict(installed=pkgs)

        lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
        rc, out, err = self.module.run_command(cmd, environ_update=lang_env)

        if rc == 1:
            for spec in items:
                # Fail on invalid urls:
                if ('://' in spec and ('No package %s available.' % spec in out or 'Cannot open: %s. Skipping.' % spec in err)):
                    err = 'Package at %s could not be installed' % spec
                    self.module.fail_json(changed=False, msg=err, rc=rc)

        res['rc'] = rc
        res['results'].append(out)
        res['msg'] += err
        res['changed'] = True

        if ('Nothing to do' in out and rc == 0) or ('does not have any packages' in err):
            res['changed'] = False

        if rc != 0:
            res['changed'] = False
            self.module.fail_json(**res)

        # Fail if yum prints 'No space left on device' because that means some
        # packages failed executing their post install scripts because of lack of
        # free space (e.g. kernel package couldn't generate initramfs). Note that
        # yum can still exit with rc=0 even if some post scripts didn't execute
        # correctly.
        if 'No space left on device' in (out or err):
            res['changed'] = False
            res['msg'] = 'No space left on device'
            self.module.fail_json(**res)

        # FIXME - if we did an install - go and check the rpmdb to see if it actually installed
        # look for each pkg in rpmdb
        # look for each pkg via obsoletes

        return res

    def install(self, items, repoq):

        pkgs = []
        downgrade_pkgs = []
        res = {}
        res['results'] = []
        res['msg'] = ''
        res['rc'] = 0
        res['changed'] = False

        for spec in items:
            pkg = None
            downgrade_candidate = False

            # check if pkgspec is installed (if possible for idempotence)
            if spec.endswith('.rpm') or '://' in spec:
                if '://' not in spec and not os.path.exists(spec):
                    res['msg'] += "No RPM file matching '%s' found on system" % spec
                    res['results'].append("No RPM file matching '%s' found on system" % spec)
                    res['rc'] = 127  # Ensure the task fails in with-loop
                    self.module.fail_json(**res)

                if '://' in spec:
                    with self.set_env_proxy():
                        package = fetch_file(self.module, spec)
                        if not package.endswith('.rpm'):
                            # yum requires a local file to have the extension of .rpm and we
                            # can not guarantee that from an URL (redirects, proxies, etc)
                            new_package_path = '%s.rpm' % package
                            os.rename(package, new_package_path)
                            package = new_package_path
                else:
                    package = spec

                # most common case is the pkg is already installed
                envra = self.local_envra(package)
                if envra is None:
                    self.module.fail_json(msg="Failed to get nevra information from RPM package: %s" % spec)
                installed_pkgs = self.is_installed(repoq, envra)
                if installed_pkgs:
                    res['results'].append('%s providing %s is already installed' % (installed_pkgs[0], package))
                    continue

                (name, ver, rel, epoch, arch) = splitFilename(envra)
                installed_pkgs = self.is_installed(repoq, name)

                # case for two same envr but different archs like x86_64 and i686
                if len(installed_pkgs) == 2:
                    (cur_name0, cur_ver0, cur_rel0, cur_epoch0, cur_arch0) = splitFilename(installed_pkgs[0])
                    (cur_name1, cur_ver1, cur_rel1, cur_epoch1, cur_arch1) = splitFilename(installed_pkgs[1])
                    cur_epoch0 = cur_epoch0 or '0'
                    cur_epoch1 = cur_epoch1 or '0'
                    compare = compareEVR((cur_epoch0, cur_ver0, cur_rel0), (cur_epoch1, cur_ver1, cur_rel1))
                    if compare == 0 and cur_arch0 != cur_arch1:
                        for installed_pkg in installed_pkgs:
                            if installed_pkg.endswith(arch):
                                installed_pkgs = [installed_pkg]

                if len(installed_pkgs) == 1:
                    installed_pkg = installed_pkgs[0]
                    (cur_name, cur_ver, cur_rel, cur_epoch, cur_arch) = splitFilename(installed_pkg)
                    cur_epoch = cur_epoch or '0'
                    compare = compareEVR((cur_epoch, cur_ver, cur_rel), (epoch, ver, rel))

                    # compare > 0 -> higher version is installed
                    # compare == 0 -> exact version is installed
                    # compare < 0 -> lower version is installed
                    if compare > 0 and self.allow_downgrade:
                        downgrade_candidate = True
                    elif compare >= 0:
                        continue

                # else: if there are more installed packages with the same name, that would mean
                # kernel, gpg-pubkey or like, so just let yum deal with it and try to install it

                pkg = package

            # groups
            elif spec.startswith('@'):
                if self.is_group_env_installed(spec):
                    continue

                pkg = spec

            # range requires or file-requires or pkgname :(
            else:
                # most common case is the pkg is already installed and done
                # short circuit all the bs - and search for it as a pkg in is_installed
                # if you find it then we're done
                if not set(['*', '?']).intersection(set(spec)):
                    installed_pkgs = self.is_installed(repoq, spec, is_pkg=True)
                    if installed_pkgs:
                        res['results'].append('%s providing %s is already installed' % (installed_pkgs[0], spec))
                        continue

                # look up what pkgs provide this
                pkglist = self.what_provides(repoq, spec)
                if not pkglist:
                    res['msg'] += "No package matching '%s' found available, installed or updated" % spec
                    res['results'].append("No package matching '%s' found available, installed or updated" % spec)
                    res['rc'] = 126  # Ensure the task fails in with-loop
                    self.module.fail_json(**res)

                # if any of the packages are involved in a transaction, fail now
                # so that we don't hang on the yum operation later
                conflicts = self.transaction_exists(pkglist)
                if conflicts:
                    res['msg'] += "The following packages have pending transactions: %s" % ", ".join(conflicts)
                    res['rc'] = 125  # Ensure the task fails in with-loop
                    self.module.fail_json(**res)

                # if any of them are installed
                # then nothing to do

                found = False
                for this in pkglist:
                    if self.is_installed(repoq, this, is_pkg=True):
                        found = True
                        res['results'].append('%s providing %s is already installed' % (this, spec))
                        break

                # if the version of the pkg you have installed is not in ANY repo, but there are
                # other versions in the repos (both higher and lower) then the previous checks won't work.
                # so we check one more time. This really only works for pkgname - not for file provides or virt provides
                # but virt provides should be all caught in what_provides on its own.
                # highly irritating
                if not found:
                    if self.is_installed(repoq, spec):
                        found = True
                        res['results'].append('package providing %s is already installed' % (spec))

                if found:
                    continue

                # Downgrade - The yum install command will only install or upgrade to a spec version, it will
                # not install an older version of an RPM even if specified by the install spec. So we need to
                # determine if this is a downgrade, and then use the yum downgrade command to install the RPM.
                if self.allow_downgrade:
                    for package in pkglist:
                        # Get the NEVRA of the requested package using pkglist instead of spec because pkglist
                        #  contains consistently-formatted package names returned by yum, rather than user input
                        #  that is often not parsed correctly by splitFilename().
                        (name, ver, rel, epoch, arch) = splitFilename(package)

                        # Check if any version of the requested package is installed
                        inst_pkgs = self.is_installed(repoq, name, is_pkg=True)
                        if inst_pkgs:
                            (cur_name, cur_ver, cur_rel, cur_epoch, cur_arch) = splitFilename(inst_pkgs[0])
                            compare = compareEVR((cur_epoch, cur_ver, cur_rel), (epoch, ver, rel))
                            if compare > 0:
                                downgrade_candidate = True
                            else:
                                downgrade_candidate = False
                                break

                # If package needs to be installed/upgraded/downgraded, then pass in the spec
                # we could get here if nothing provides it but that's not
                # the error we're catching here
                pkg = spec

            if downgrade_candidate and self.allow_downgrade:
                downgrade_pkgs.append(pkg)
            else:
                pkgs.append(pkg)

        if downgrade_pkgs:
            res = self.exec_install(items, 'downgrade', downgrade_pkgs, res)

        if pkgs:
            res = self.exec_install(items, 'install', pkgs, res)

        return res

    def remove(self, items, repoq):

        pkgs = []
        res = {}
        res['results'] = []
        res['msg'] = ''
        res['changed'] = False
        res['rc'] = 0

        for pkg in items:
            if pkg.startswith('@'):
                installed = self.is_group_env_installed(pkg)
            else:
                installed = self.is_installed(repoq, pkg)

            if installed:
                pkgs.append(pkg)
            else:
                res['results'].append('%s is not installed' % pkg)

        if pkgs:
            if self.module.check_mode:
                self.module.exit_json(changed=True, results=res['results'], changes=dict(removed=pkgs))
            else:
                res['changes'] = dict(removed=pkgs)

            # run an actual yum transaction
            if self.autoremove:
                cmd = self.yum_basecmd + ["autoremove"] + pkgs
            else:
                cmd = self.yum_basecmd + ["remove"] + pkgs
            rc, out, err = self.module.run_command(cmd)

            res['rc'] = rc
            res['results'].append(out)
            res['msg'] = err

            if rc != 0:
                if self.autoremove and 'No such command' in out:
                    self.module.fail_json(msg='Version of YUM too old for autoremove: Requires yum 3.4.3 (RHEL/CentOS 7+)')
                else:
                    self.module.fail_json(**res)

            # compile the results into one batch. If anything is changed
            # then mark changed
            # at the end - if we've end up failed then fail out of the rest
            # of the process

            # at this point we check to see if the pkg is no longer present
            self._yum_base = None  # previous YumBase package index is now invalid
            for pkg in pkgs:
                if pkg.startswith('@'):
                    installed = self.is_group_env_installed(pkg)
                else:
                    installed = self.is_installed(repoq, pkg, is_pkg=True)

                if installed:
                    # Return a message so it's obvious to the user why yum failed
                    # and which package couldn't be removed. More details:
                    # https://github.com/ansible/ansible/issues/35672
                    res['msg'] = "Package '%s' couldn't be removed!" % pkg
                    self.module.fail_json(**res)

            res['changed'] = True

        return res

    def run_check_update(self):
        # run check-update to see if we have packages pending
        if self.releasever:
            rc, out, err = self.module.run_command(self.yum_basecmd + ['check-update'] + ['--releasever=%s' % self.releasever])
        else:
            rc, out, err = self.module.run_command(self.yum_basecmd + ['check-update'])
        return rc, out, err

    @staticmethod
    def parse_check_update(check_update_output):
        updates = {}
        obsoletes = {}

        # remove incorrect new lines in longer columns in output from yum check-update
        # yum line wrapping can move the repo to the next line
        #
        # Meant to filter out sets of lines like:
        #  some_looooooooooooooooooooooooooooooooooooong_package_name   1:1.2.3-1.el7
        #                                                                    some-repo-label
        #
        # But it also needs to avoid catching lines like:
        # Loading mirror speeds from cached hostfile
        #
        # ceph.x86_64                               1:11.2.0-0.el7                    ceph

        # preprocess string and filter out empty lines so the regex below works
        out = re.sub(r'\n[^\w]\W+(.*)', r' \1', check_update_output)

        available_updates = out.split('\n')

        # build update dictionary
        for line in available_updates:
            line = line.split()
            # ignore irrelevant lines
            # '*' in line matches lines like mirror lists:
            #      * base: mirror.corbina.net
            # len(line) != 3 or 6 could be junk or a continuation
            # len(line) = 6 is package obsoletes
            #
            # FIXME: what is  the '.' not in line  conditional for?

            if '*' in line or len(line) not in [3, 6] or '.' not in line[0]:
                continue

            pkg, version, repo = line[0], line[1], line[2]
            name, dist = pkg.rsplit('.', 1)
            updates.update({name: {'version': version, 'dist': dist, 'repo': repo}})

            if len(line) == 6:
                obsolete_pkg, obsolete_version, obsolete_repo = line[3], line[4], line[5]
                obsolete_name, obsolete_dist = obsolete_pkg.rsplit('.', 1)
                obsoletes.update({obsolete_name: {'version': obsolete_version, 'dist': obsolete_dist, 'repo': obsolete_repo}})

        return updates, obsoletes

    def latest(self, items, repoq):

        res = {}
        res['results'] = []
        res['msg'] = ''
        res['changed'] = False
        res['rc'] = 0
        pkgs = {}
        pkgs['update'] = []
        pkgs['install'] = []
        updates = {}
        obsoletes = {}
        update_all = False
        cmd = None

        # determine if we're doing an update all
        if '*' in items:
            update_all = True

        rc, out, err = self.run_check_update()

        if rc == 0 and update_all:
            res['results'].append('Nothing to do here, all packages are up to date')
            return res
        elif rc == 100:
            updates, obsoletes = self.parse_check_update(out)
        elif rc == 1:
            res['msg'] = err
            res['rc'] = rc
            self.module.fail_json(**res)

        if update_all:
            cmd = self.yum_basecmd + ['update']
            will_update = set(updates.keys())
            will_update_from_other_package = dict()
        else:
            will_update = set()
            will_update_from_other_package = dict()
            for spec in items:
                # some guess work involved with groups. update @<group> will install the group if missing
                if spec.startswith('@'):
                    pkgs['update'].append(spec)
                    will_update.add(spec)
                    continue

                # check if pkgspec is installed (if possible for idempotence)
                # localpkg
                if spec.endswith('.rpm') and '://' not in spec:
                    if not os.path.exists(spec):
                        res['msg'] += "No RPM file matching '%s' found on system" % spec
                        res['results'].append("No RPM file matching '%s' found on system" % spec)
                        res['rc'] = 127  # Ensure the task fails in with-loop
                        self.module.fail_json(**res)

                    # get the pkg e:name-v-r.arch
                    envra = self.local_envra(spec)

                    if envra is None:
                        self.module.fail_json(msg="Failed to get nevra information from RPM package: %s" % spec)

                    # local rpm files can't be updated
                    if self.is_installed(repoq, envra):
                        pkgs['update'].append(spec)
                    else:
                        pkgs['install'].append(spec)
                    continue

                # URL
                if '://' in spec:
                    # download package so that we can check if it's already installed
                    with self.set_env_proxy():
                        package = fetch_file(self.module, spec)
                    envra = self.local_envra(package)

                    if envra is None:
                        self.module.fail_json(msg="Failed to get nevra information from RPM package: %s" % spec)

                    # local rpm files can't be updated
                    if self.is_installed(repoq, envra):
                        pkgs['update'].append(spec)
                    else:
                        pkgs['install'].append(spec)
                    continue

                # dep/pkgname  - find it
                if self.is_installed(repoq, spec):
                    pkgs['update'].append(spec)
                else:
                    pkgs['install'].append(spec)
                pkglist = self.what_provides(repoq, spec)
                # FIXME..? may not be desirable to throw an exception here if a single package is missing
                if not pkglist:
                    res['msg'] += "No package matching '%s' found available, installed or updated" % spec
                    res['results'].append("No package matching '%s' found available, installed or updated" % spec)
                    res['rc'] = 126  # Ensure the task fails in with-loop
                    self.module.fail_json(**res)

                nothing_to_do = True
                for pkg in pkglist:
                    if spec in pkgs['install'] and self.is_available(repoq, pkg):
                        nothing_to_do = False
                        break

                    # this contains the full NVR and spec could contain wildcards
                    # or virtual provides (like "python-*" or "smtp-daemon") while
                    # updates contains name only.
                    pkgname, _, _, _, _ = splitFilename(pkg)
                    if spec in pkgs['update'] and pkgname in updates:
                        nothing_to_do = False
                        will_update.add(spec)
                        # Massage the updates list
                        if spec != pkgname:
                            # For reporting what packages would be updated more
                            # succinctly
                            will_update_from_other_package[spec] = pkgname
                        break

                if not self.is_installed(repoq, spec) and self.update_only:
                    res['results'].append("Packages providing %s not installed due to update_only specified" % spec)
                    continue
                if nothing_to_do:
                    res['results'].append("All packages providing %s are up to date" % spec)
                    continue

                # if any of the packages are involved in a transaction, fail now
                # so that we don't hang on the yum operation later
                conflicts = self.transaction_exists(pkglist)
                if conflicts:
                    res['msg'] += "The following packages have pending transactions: %s" % ", ".join(conflicts)
                    res['results'].append("The following packages have pending transactions: %s" % ", ".join(conflicts))
                    res['rc'] = 128  # Ensure the task fails in with-loop
                    self.module.fail_json(**res)

        # check_mode output
        to_update = []
        for w in will_update:
            if w.startswith('@'):
                to_update.append((w, None))
            elif w not in updates:
                other_pkg = will_update_from_other_package[w]
                to_update.append(
                    (
                        w,
                        'because of (at least) %s-%s.%s from %s' % (
                            other_pkg,
                            updates[other_pkg]['version'],
                            updates[other_pkg]['dist'],
                            updates[other_pkg]['repo']
                        )
                    )
                )
            else:
                to_update.append((w, '%s.%s from %s' % (updates[w]['version'], updates[w]['dist'], updates[w]['repo'])))

        if self.update_only:
            res['changes'] = dict(installed=[], updated=to_update)
        else:
            res['changes'] = dict(installed=pkgs['install'], updated=to_update)

        if obsoletes:
            res['obsoletes'] = obsoletes

        # return results before we actually execute stuff
        if self.module.check_mode:
            if will_update or pkgs['install']:
                res['changed'] = True
            return res

        if self.releasever:
            cmd.extend(['--releasever=%s' % self.releasever])

        # run commands
        if cmd:     # update all
            rc, out, err = self.module.run_command(cmd)
            res['changed'] = True
        elif self.update_only:
            if pkgs['update']:
                cmd = self.yum_basecmd + ['update'] + pkgs['update']
                lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
                rc, out, err = self.module.run_command(cmd, environ_update=lang_env)
                out_lower = out.strip().lower()
                if not out_lower.endswith("no packages marked for update") and \
                        not out_lower.endswith("nothing to do"):
                    res['changed'] = True
            else:
                rc, out, err = [0, '', '']
        elif pkgs['install'] or will_update and not self.update_only:
            cmd = self.yum_basecmd + ['install'] + pkgs['install'] + pkgs['update']
            lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
            rc, out, err = self.module.run_command(cmd, environ_update=lang_env)
            out_lower = out.strip().lower()
            if not out_lower.endswith("no packages marked for update") and \
                    not out_lower.endswith("nothing to do"):
                res['changed'] = True
        else:
            rc, out, err = [0, '', '']

        res['rc'] = rc
        res['msg'] += err
        res['results'].append(out)

        if rc:
            res['failed'] = True

        return res

    def ensure(self, repoq):
        pkgs = self.names

        # autoremove was provided without `name`
        if not self.names and self.autoremove:
            pkgs = []
            self.state = 'absent'

        if self.conf_file and os.path.exists(self.conf_file):
            self.yum_basecmd += ['-c', self.conf_file]

            if repoq:
                repoq += ['-c', self.conf_file]

        if self.skip_broken:
            self.yum_basecmd.extend(['--skip-broken'])

        if self.disablerepo:
            self.yum_basecmd.extend(['--disablerepo=%s' % ','.join(self.disablerepo)])

        if self.enablerepo:
            self.yum_basecmd.extend(['--enablerepo=%s' % ','.join(self.enablerepo)])

        if self.enable_plugin:
            self.yum_basecmd.extend(['--enableplugin', ','.join(self.enable_plugin)])

        if self.disable_plugin:
            self.yum_basecmd.extend(['--disableplugin', ','.join(self.disable_plugin)])

        if self.exclude:
            e_cmd = ['--exclude=%s' % ','.join(self.exclude)]
            self.yum_basecmd.extend(e_cmd)

        if self.disable_excludes:
            self.yum_basecmd.extend(['--disableexcludes=%s' % self.disable_excludes])

        if self.download_only:
            self.yum_basecmd.extend(['--downloadonly'])

            if self.download_dir:
                self.yum_basecmd.extend(['--downloaddir=%s' % self.download_dir])

        if self.releasever:
            self.yum_basecmd.extend(['--releasever=%s' % self.releasever])

        if self.installroot != '/':
            # do not setup installroot by default, because of error
            # CRITICAL:yum.cli:Config Error: Error accessing file for config file:////etc/yum.conf
            # in old yum version (like in CentOS 6.6)
            e_cmd = ['--installroot=%s' % self.installroot]
            self.yum_basecmd.extend(e_cmd)

        if self.state in ('installed', 'present', 'latest'):
            """ The need of this entire if conditional has to be changed
                this function is the ensure function that is called
                in the main section.

                This conditional tends to disable/enable repo for
                install present latest action, same actually
                can be done for remove and absent action

                As solution I would advice to cal
                try: self.yum_base.repos.disableRepo(disablerepo)
                and
                try: self.yum_base.repos.enableRepo(enablerepo)
                right before any yum_cmd is actually called regardless
                of yum action.

                Please note that enable/disablerepo options are general
                options, this means that we can call those with any action
                option.  https://linux.die.net/man/8/yum

                This docstring will be removed together when issue: #21619
                will be solved.

                This has been triggered by: #19587
            """

            if self.update_cache:
                self.module.run_command(self.yum_basecmd + ['clean', 'expire-cache'])

            try:
                current_repos = self.yum_base.repos.repos.keys()
                if self.enablerepo:
                    try:
                        new_repos = self.yum_base.repos.repos.keys()
                        for i in new_repos:
                            if i not in current_repos:
                                rid = self.yum_base.repos.getRepo(i)
                                a = rid.repoXML.repoid  # nopep8 - https://github.com/ansible/ansible/pull/21475#pullrequestreview-22404868
                        current_repos = new_repos
                    except yum.Errors.YumBaseError as e:
                        self.module.fail_json(msg="Error setting/accessing repos: %s" % to_native(e))
            except yum.Errors.YumBaseError as e:
                self.module.fail_json(msg="Error accessing repos: %s" % to_native(e))
        if self.state == 'latest' or self.update_only:
            if self.disable_gpg_check:
                self.yum_basecmd.append('--nogpgcheck')
            if self.security:
                self.yum_basecmd.append('--security')
            if self.bugfix:
                self.yum_basecmd.append('--bugfix')
            res = self.latest(pkgs, repoq)
        elif self.state in ('installed', 'present'):
            if self.disable_gpg_check:
                self.yum_basecmd.append('--nogpgcheck')
            res = self.install(pkgs, repoq)
        elif self.state in ('removed', 'absent'):
            res = self.remove(pkgs, repoq)
        else:
            # should be caught by AnsibleModule argument_spec
            self.module.fail_json(
                msg="we should never get here unless this all failed",
                changed=False,
                results='',
                errors='unexpected state'
            )
        return res

    @staticmethod
    def has_yum():
        return HAS_YUM_PYTHON

    def run(self):
        """
        actually execute the module code backend
        """

        if (not HAS_RPM_PYTHON or not HAS_YUM_PYTHON) and sys.executable != '/usr/bin/python' and not has_respawned():
            respawn_module('/usr/bin/python')
            # end of the line for this process; we'll exit here once the respawned module has completed

        error_msgs = []
        if not HAS_RPM_PYTHON:
            error_msgs.append('The Python 2 bindings for rpm are needed for this module. If you require Python 3 support use the `dnf` Ansible module instead.')
        if not HAS_YUM_PYTHON:
            error_msgs.append('The Python 2 yum module is needed for this module. If you require Python 3 support use the `dnf` Ansible module instead.')

        self.wait_for_lock()

        if error_msgs:
            self.module.fail_json(msg='. '.join(error_msgs))

        # fedora will redirect yum to dnf, which has incompatibilities
        # with how this module expects yum to operate. If yum-deprecated
        # is available, use that instead to emulate the old behaviors.
        if self.module.get_bin_path('yum-deprecated'):
            yumbin = self.module.get_bin_path('yum-deprecated')
        else:
            yumbin = self.module.get_bin_path('yum')

        # need debug level 2 to get 'Nothing to do' for groupinstall.
        self.yum_basecmd = [yumbin, '-d', '2', '-y']

        if self.update_cache and not self.names and not self.list:
            rc, stdout, stderr = self.module.run_command(self.yum_basecmd + ['clean', 'expire-cache'])
            if rc == 0:
                self.module.exit_json(
                    changed=False,
                    msg="Cache updated",
                    rc=rc,
                    results=[]
                )
            else:
                self.module.exit_json(
                    changed=False,
                    msg="Failed to update cache",
                    rc=rc,
                    results=[stderr],
                )

        repoquerybin = self.module.get_bin_path('repoquery', required=False)

        if self.install_repoquery and not repoquerybin and not self.module.check_mode:
            yum_path = self.module.get_bin_path('yum')
            if yum_path:
                if self.releasever:
                    self.module.run_command('%s -y install yum-utils --releasever %s' % (yum_path, self.releasever))
                else:
                    self.module.run_command('%s -y install yum-utils' % yum_path)
            repoquerybin = self.module.get_bin_path('repoquery', required=False)

        if self.list:
            if not repoquerybin:
                self.module.fail_json(msg="repoquery is required to use list= with this module. Please install the yum-utils package.")
            results = {'results': self.list_stuff(repoquerybin, self.list)}
        else:
            # If rhn-plugin is installed and no rhn-certificate is available on
            # the system then users will see an error message using the yum API.
            # Use repoquery in those cases.

            repoquery = None
            try:
                yum_plugins = self.yum_base.plugins._plugins
            except AttributeError:
                pass
            else:
                if 'rhnplugin' in yum_plugins:
                    if repoquerybin:
                        repoquery = [repoquerybin, '--show-duplicates', '--plugins', '--quiet']
                        if self.installroot != '/':
                            repoquery.extend(['--installroot', self.installroot])

                        if self.disable_excludes:
                            # repoquery does not support --disableexcludes,
                            # so make a temp copy of yum.conf and get rid of the 'exclude=' line there
                            try:
                                with open('/etc/yum.conf', 'r') as f:
                                    content = f.readlines()

                                tmp_conf_file = tempfile.NamedTemporaryFile(dir=self.module.tmpdir, delete=False)
                                self.module.add_cleanup_file(tmp_conf_file.name)

                                tmp_conf_file.writelines([c for c in content if not c.startswith("exclude=")])
                                tmp_conf_file.close()
                            except Exception as e:
                                self.module.fail_json(msg="Failure setting up repoquery: %s" % to_native(e))

                            repoquery.extend(['-c', tmp_conf_file.name])

            results = self.ensure(repoquery)
            if repoquery:
                results['msg'] = '%s %s' % (
                    results.get('msg', ''),
                    'Warning: Due to potential bad behaviour with rhnplugin and certificates, used slower repoquery calls instead of Yum API.'
                )

        self.module.exit_json(**results)


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

    yumdnf_argument_spec['argument_spec']['use_backend'] = dict(default='auto', choices=['auto', 'yum', 'yum4', 'dnf'])

    module = AnsibleModule(
        **yumdnf_argument_spec
    )

    module_implementation = YumModule(module)
    module_implementation.run()


if __name__ == '__main__':
    main()
