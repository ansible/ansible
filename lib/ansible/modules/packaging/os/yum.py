#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Red Hat, Inc
# Written by Seth Vidal <skvidal at fedoraproject.org>
# Copyright: (c) 2014, Epic Games, Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: yum
version_added: historical
short_description: Manages packages with the I(yum) package manager
description:
     - Installs, upgrade, downgrades, removes, and lists packages and groups with the I(yum) package manager.
     - This module only works on Python 2. If you require Python 3 support see the M(dnf) module.
options:
  name:
    description:
      - A package name or package specifier with version, like C(name-1.0).
      - If a previous version is specified, the task also needs to turn C(allow_downgrade) on.
        See the C(allow_downgrade) documentation for caveats with downgrading packages.
      - When using state=latest, this can be C('*') which means run C(yum -y update).
      - You can also pass a url or a local path to a rpm file (using state=present).
        To operate on several packages this can accept a comma separated list of packages or (as of 2.0) a list of packages.
    aliases: [ pkg ]
  exclude:
    description:
      - Package name(s) to exclude when state=present, or latest
    version_added: "2.0"
  list:
    description:
      - "Package name to run the equivalent of yum list <package> against. In addition to listing packages,
        use can also list the following: C(installed), C(updates), C(available) and C(repos)."
  state:
    description:
      - Whether to install (C(present) or C(installed), C(latest)), or remove (C(absent) or C(removed)) a package.
      - C(present) and C(installed) will simply ensure that a desired package is installed.
      - C(latest) will update the specified package if it's not of the latest available version.
      - C(absent) and C(removed) will remove the specified package.
    choices: [ absent, installed, latest, present, removed ]
    default: present
  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a C(",").
    version_added: "0.9"
  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a C(",").
    version_added: "0.9"
  conf_file:
    description:
      - The remote yum configuration file to use for the transaction.
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
    required: false
    default: "no"
    type: bool
    version_added: "2.5"

  installroot:
    description:
      - Specifies an alternative installroot, relative to which all packages
        will be installed.
    default: "/"
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
    required: false
    default: "no"
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
    required: false
    version_added: "2.5"
  disable_plugin:
    description:
      - I(Plugin) name to disable for the install/update operation.
        The disabled plugins will not persist beyond the transaction.
    required: false
    version_added: "2.5"
  disable_excludes:
    description:
      - Disable the excludes defined in YUM config files.
      - If set to C(all), disables all excludes.
      - If set to C(main), disable excludes defined in [main] in yum.conf.
      - If set to C(repoid), disable excludes defined for given repo id.
    required: false
    choices: [ all, main, repoid ]
    version_added: "2.7"
  download_only:
    description:
      - Only download the packages, do not install them.
    required: false
    default: "no"
    type: bool
    version_added: "2.7"
notes:
  - When used with a `loop:` each package will be processed individually,
    it is much more efficient to pass the list directly to the `name` option.
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
    Use the "yum group list" command to see which category of group the group
    you want to install falls into.'
# informational: requirements for nodes
requirements:
- yum
author:
    - Ansible Core Team
    - Seth Vidal
    - Eduard Snesarev (@verm666)
    - Berend De Schouwer (@berenddeschouwer)
    - Abhijeet Kasurde (@Akasurde)
'''

EXAMPLES = '''
- name: install the latest version of Apache
  yum:
    name: httpd
    state: latest

- name: ensure a list of packages installed
  yum:
    name: "{{ packages }}"
  vars:
    packages:
    - httpd
    - httpd-tools

- name: remove the Apache package
  yum:
    name: httpd
    state: absent

- name: install the latest version of Apache from the testing repo
  yum:
    name: httpd
    enablerepo: testing
    state: present

- name: install one specific version of Apache
  yum:
    name: httpd-2.2.29-1.4.amzn1
    state: present

- name: upgrade all packages
  yum:
    name: '*'
    state: latest

- name: upgrade all packages, excluding kernel & foo related packages
  yum:
    name: '*'
    state: latest
    exclude: kernel*,foo*

- name: install the nginx rpm from a remote repo
  yum:
    name: http://nginx.org/packages/centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm
    state: present

- name: install nginx rpm from a local file
  yum:
    name: /usr/local/src/nginx-release-centos-6-0.el6.ngx.noarch.rpm
    state: present

- name: install the 'Development tools' package group
  yum:
    name: "@Development tools"
    state: present

- name: install the 'Gnome desktop' environment group
  yum:
    name: "@^gnome-desktop-environment"
    state: present

- name: List ansible packages and register result to print with debug later.
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

- name: Install a list of packages
  yum:
    name:
      - nginx
      - postgresql
      - postgresql-server
    state: present

- name: Download the nginx package but do not install it
  yum:
    name:
      - nginx
    state: latest
    download_only: true
'''

import os
import re
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url

# 64k.  Number of bytes to read at a time when manually downloading pkgs via a url
BUFSIZE = 65536

def_qf = "%{epoch}:%{name}-%{version}-%{release}.%{arch}"
rpmbin = None


def yum_base(conf_file=None, installroot='/', enabled_plugins=None,
             disabled_plugins=None, disable_excludes=None):
    my = yum.YumBase()
    my.preconf.debuglevel = 0
    my.preconf.errorlevel = 0
    my.preconf.plugins = True
    my.preconf.enabled_plugins = enabled_plugins
    my.preconf.disabled_plugins = disabled_plugins
    # my.preconf.releasever = '/'
    if installroot != '/':
        # do not setup installroot by default, because of error
        # CRITICAL:yum.cli:Config Error: Error accessing file for config file:////etc/yum.conf
        # in old yum version (like in CentOS 6.6)
        my.preconf.root = installroot
        my.conf.installroot = installroot
    if conf_file and os.path.exists(conf_file):
        my.preconf.fn = conf_file
    if os.geteuid() != 0:
        if hasattr(my, 'setCacheDir'):
            my.setCacheDir()
        else:
            cachedir = yum.misc.getCacheDir()
            my.repos.setCacheDir(cachedir)
            my.conf.cache = 0
    if disable_excludes:
        my.conf.disable_excludes = disable_excludes

    return my


def ensure_yum_utils(module):
    repoquerybin = module.get_bin_path('repoquery', required=False)

    if module.params['install_repoquery'] and not repoquerybin and not module.check_mode:
        yum_path = module.get_bin_path('yum')
        if yum_path:
            module.run_command('%s -y install yum-utils' % yum_path)
        repoquerybin = module.get_bin_path('repoquery', required=False)

    return repoquerybin


def fetch_rpm_from_url(spec, module=None):
    # download package so that we can query it
    package_name, _ = os.path.splitext(str(spec.rsplit('/', 1)[1]))
    package_file = tempfile.NamedTemporaryFile(dir=module.tmpdir, prefix=package_name, suffix='.rpm', delete=False)
    module.add_cleanup_file(package_file.name)
    try:
        rsp, info = fetch_url(module, spec)
        if not rsp:
            module.fail_json(msg="Failure downloading %s, %s" % (spec, info['msg']))
        data = rsp.read(BUFSIZE)
        while data:
            package_file.write(data)
            data = rsp.read(BUFSIZE)
        package_file.close()
    except Exception as e:
        if module:
            module.fail_json(msg="Failure downloading %s, %s" % (spec, to_native(e)))
        else:
            raise e

    return package_file.name


def po_to_envra(po):
    if hasattr(po, 'ui_envra'):
        return po.ui_envra

    return '%s:%s-%s-%s.%s' % (po.epoch, po.name, po.version, po.release, po.arch)


def is_group_env_installed(name, conf_file, en_plugins=None, dis_plugins=None,
                           installroot='/', disable_excludes=None):
    name_lower = name.lower()

    my = yum_base(conf_file, installroot, en_plugins, dis_plugins, disable_excludes)
    if yum.__version_info__ >= (3, 4):
        groups_list = my.doGroupLists(return_evgrps=True)
    else:
        groups_list = my.doGroupLists()

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


def is_installed(module, repoq, pkgspec, conf_file, qf=None, en_repos=None, dis_repos=None, en_plugins=None, dis_plugins=None, is_pkg=False,
                 installroot='/', disable_excludes=None):
    if en_repos is None:
        en_repos = []
    if dis_repos is None:
        dis_repos = []
    if qf is None:
        qf = "%{epoch}:%{name}-%{version}-%{release}.%{arch}\n"

    if not repoq:
        pkgs = []
        try:
            my = yum_base(conf_file, installroot, en_plugins, dis_plugins, disable_excludes)
            for rid in dis_repos:
                my.repos.disableRepo(rid)
            for rid in en_repos:
                my.repos.enableRepo(rid)

            e, m, _ = my.rpmdb.matchPackageNames([pkgspec])
            pkgs = e + m
            if not pkgs and not is_pkg:
                pkgs.extend(my.returnInstalledPackagesByDep(pkgspec))
        except Exception as e:
            module.fail_json(msg="Failure talking to yum: %s" % to_native(e))

        return [po_to_envra(p) for p in pkgs]

    else:
        global rpmbin
        if not rpmbin:
            rpmbin = module.get_bin_path('rpm', required=True)

        cmd = [rpmbin, '-q', '--qf', qf, pkgspec]
        if installroot != '/':
            cmd.extend(['--root', installroot])
        # rpm localizes messages and we're screen scraping so make sure we use
        # the C locale
        lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
        rc, out, err = module.run_command(cmd, environ_update=lang_env)
        if rc != 0 and 'is not installed' not in out:
            module.fail_json(msg='Error from rpm: %s: %s' % (cmd, err))
        if 'is not installed' in out:
            out = ''

        pkgs = [p for p in out.replace('(none)', '0').split('\n') if p.strip()]
        if not pkgs and not is_pkg:
            cmd = [rpmbin, '-q', '--qf', qf, '--whatprovides', pkgspec]
            if installroot != '/':
                cmd.extend(['--root', installroot])
            rc2, out2, err2 = module.run_command(cmd, environ_update=lang_env)
        else:
            rc2, out2, err2 = (0, '', '')

        if rc2 != 0 and 'no package provides' not in out2:
            module.fail_json(msg='Error from rpm: %s: %s' % (cmd, err + err2))
        if 'no package provides' in out2:
            out2 = ''
        pkgs += [p for p in out2.replace('(none)', '0').split('\n') if p.strip()]
        return pkgs

    return []


def is_available(module, repoq, pkgspec, conf_file, qf=def_qf, en_repos=None, dis_repos=None, en_plugins=None, dis_plugins=None,
                 installroot='/', disable_excludes=None):
    if en_repos is None:
        en_repos = []
    if dis_repos is None:
        dis_repos = []

    if not repoq:

        pkgs = []
        try:
            my = yum_base(conf_file, installroot, en_plugins, dis_plugins, disable_excludes)
            for rid in dis_repos:
                my.repos.disableRepo(rid)
            for rid in en_repos:
                my.repos.enableRepo(rid)

            e, m, _ = my.pkgSack.matchPackageNames([pkgspec])
            pkgs = e + m
            if not pkgs:
                pkgs.extend(my.returnPackagesByDep(pkgspec))
        except Exception as e:
            module.fail_json(msg="Failure talking to yum: %s" % to_native(e))

        return [po_to_envra(p) for p in pkgs]

    else:
        myrepoq = list(repoq)

        r_cmd = ['--disablerepo', ','.join(dis_repos)]
        myrepoq.extend(r_cmd)

        r_cmd = ['--enablerepo', ','.join(en_repos)]
        myrepoq.extend(r_cmd)

        cmd = myrepoq + ["--qf", qf, pkgspec]
        rc, out, err = module.run_command(cmd)
        if rc == 0:
            return [p for p in out.split('\n') if p.strip()]
        else:
            module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err))

    return []


def is_update(module, repoq, pkgspec, conf_file, qf=def_qf, en_repos=None, dis_repos=None, en_plugins=None, dis_plugins=None,
              installroot='/', disable_excludes=None):
    if en_repos is None:
        en_repos = []
    if dis_repos is None:
        dis_repos = []

    if not repoq:

        pkgs = []
        updates = []

        try:
            my = yum_base(conf_file, installroot, en_plugins, dis_plugins, disable_excludes)
            for rid in dis_repos:
                my.repos.disableRepo(rid)
            for rid in en_repos:
                my.repos.enableRepo(rid)

            pkgs = my.returnPackagesByDep(pkgspec) + my.returnInstalledPackagesByDep(pkgspec)
            if not pkgs:
                e, m, _ = my.pkgSack.matchPackageNames([pkgspec])
                pkgs = e + m
            updates = my.doPackageLists(pkgnarrow='updates').updates
        except Exception as e:
            module.fail_json(msg="Failure talking to yum: %s" % to_native(e))

        retpkgs = (pkg for pkg in pkgs if pkg in updates)

        return set(po_to_envra(p) for p in retpkgs)

    else:
        myrepoq = list(repoq)
        r_cmd = ['--disablerepo', ','.join(dis_repos)]
        myrepoq.extend(r_cmd)

        r_cmd = ['--enablerepo', ','.join(en_repos)]
        myrepoq.extend(r_cmd)

        cmd = myrepoq + ["--pkgnarrow=updates", "--qf", qf, pkgspec]
        rc, out, err = module.run_command(cmd)

        if rc == 0:
            return set(p for p in out.split('\n') if p.strip())
        else:
            module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err))

    return set()


def what_provides(module, repoq, yum_basecmd, req_spec, conf_file, qf=def_qf,
                  en_repos=None, dis_repos=None, en_plugins=None,
                  dis_plugins=None, installroot='/', disable_excludes=None):
    if en_repos is None:
        en_repos = []
    if dis_repos is None:
        dis_repos = []

    if not repoq:

        pkgs = []
        try:
            my = yum_base(conf_file, installroot, en_plugins, dis_plugins, disable_excludes)
            for rid in dis_repos:
                my.repos.disableRepo(rid)
            for rid in en_repos:
                my.repos.enableRepo(rid)

            try:
                pkgs = my.returnPackagesByDep(req_spec) + my.returnInstalledPackagesByDep(req_spec)
            except Exception as e:
                # If a repo with `repo_gpgcheck=1` is added and the repo GPG
                # key was never accepted, quering this repo will throw an
                # error: 'repomd.xml signature could not be verified'. In that
                # situation we need to run `yum -y makecache` which will accept
                # the key and try again.
                if 'repomd.xml signature could not be verified' in to_native(e):
                    module.run_command(yum_basecmd + ['makecache'])
                    pkgs = my.returnPackagesByDep(req_spec) + my.returnInstalledPackagesByDep(req_spec)
                else:
                    raise
            if not pkgs:
                e, m, _ = my.pkgSack.matchPackageNames([req_spec])
                pkgs.extend(e)
                pkgs.extend(m)
                e, m, _ = my.rpmdb.matchPackageNames([req_spec])
                pkgs.extend(e)
                pkgs.extend(m)
        except Exception as e:
            module.fail_json(msg="Failure talking to yum: %s" % to_native(e))

        return set(po_to_envra(p) for p in pkgs)

    else:
        myrepoq = list(repoq)
        r_cmd = ['--disablerepo', ','.join(dis_repos)]
        myrepoq.extend(r_cmd)

        r_cmd = ['--enablerepo', ','.join(en_repos)]
        myrepoq.extend(r_cmd)

        cmd = myrepoq + ["--qf", qf, "--whatprovides", req_spec]
        rc, out, err = module.run_command(cmd)
        cmd = myrepoq + ["--qf", qf, req_spec]
        rc2, out2, err2 = module.run_command(cmd)
        if rc == 0 and rc2 == 0:
            out += out2
            pkgs = set(p for p in out.split('\n') if p.strip())
            if not pkgs:
                pkgs = is_installed(module, repoq, req_spec, conf_file, qf=qf, installroot=installroot, disable_excludes=disable_excludes)
            return pkgs
        else:
            module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err + err2))

    return set()


def transaction_exists(pkglist):
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


def local_envra(path):
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

    return '%s:%s-%s-%s.%s' % (header[rpm.RPMTAG_EPOCH] or '0',
                               header[rpm.RPMTAG_NAME],
                               header[rpm.RPMTAG_VERSION],
                               header[rpm.RPMTAG_RELEASE],
                               header[rpm.RPMTAG_ARCH])


@contextmanager
def set_env_proxy(conf_file, installroot):
    # setting system proxy environment and saving old, if exists
    my = yum_base(conf_file, installroot)
    namepass = ""
    scheme = ["http", "https"]
    old_proxy_env = [os.getenv("http_proxy"), os.getenv("https_proxy")]
    try:
        if my.conf.proxy:
            if my.conf.proxy_username:
                namepass = namepass + my.conf.proxy_username
                if my.conf.proxy_password:
                    namepass = namepass + ":" + my.conf.proxy_password
            namepass = namepass + '@'
            for item in scheme:
                os.environ[item + "_proxy"] = re.sub(r"(http://)",
                                                     r"\1" + namepass, my.conf.proxy)
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


def pkg_to_dict(pkgstr):
    if pkgstr.strip():
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


def repolist(module, repoq, qf="%{repoid}"):
    cmd = repoq + ["--qf", qf, "-a"]
    rc, out, _ = module.run_command(cmd)
    if rc == 0:
        return set(p for p in out.split('\n') if p.strip())
    else:
        return []


def list_stuff(module, repoquerybin, conf_file, stuff, installroot='/', disablerepo='', enablerepo='', disable_excludes=None):

    qf = "%{name}|%{epoch}|%{version}|%{release}|%{arch}|%{repoid}"
    # is_installed goes through rpm instead of repoquery so it needs a slightly different format
    is_installed_qf = "%{name}|%{epoch}|%{version}|%{release}|%{arch}|installed\n"
    repoq = [repoquerybin, '--show-duplicates', '--plugins', '--quiet']
    if disablerepo:
        repoq.extend(['--disablerepo', disablerepo])
    if enablerepo:
        repoq.extend(['--enablerepo', enablerepo])
    if installroot != '/':
        repoq.extend(['--installroot', installroot])
    if conf_file and os.path.exists(conf_file):
        repoq += ['-c', conf_file]

    if stuff == 'installed':
        return [pkg_to_dict(p) for p in sorted(is_installed(module, repoq, '-a', conf_file, qf=is_installed_qf,
                                                            installroot=installroot, disable_excludes=disable_excludes)) if p.strip()]

    if stuff == 'updates':
        return [pkg_to_dict(p) for p in sorted(is_update(module, repoq, '-a', conf_file, qf=qf,
                                                         installroot=installroot, disable_excludes=disable_excludes)) if p.strip()]

    if stuff == 'available':
        return [pkg_to_dict(p) for p in sorted(is_available(module, repoq, '-a', conf_file, qf=qf,
                                                            installroot=installroot, disable_excludes=disable_excludes)) if p.strip()]

    if stuff == 'repos':
        return [dict(repoid=name, state='enabled') for name in sorted(repolist(module, repoq)) if name.strip()]

    return [pkg_to_dict(p) for p in sorted(is_installed(module, repoq, stuff, conf_file, qf=is_installed_qf,
                                                        installroot=installroot, disable_excludes=disable_excludes) +
                                           is_available(module, repoq, stuff, conf_file, qf=qf, installroot=installroot,
                                                        disable_excludes=disable_excludes)) if p.strip()]


def exec_install(module, items, action, pkgs, res, yum_basecmd):
    cmd = yum_basecmd + [action] + pkgs

    if module.check_mode:
        module.exit_json(changed=True, results=res['results'], changes=dict(installed=pkgs))

    lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
    rc, out, err = module.run_command(cmd, environ_update=lang_env)

    if rc == 1:
        for spec in items:
            # Fail on invalid urls:
            if ('://' in spec and ('No package %s available.' % spec in out or 'Cannot open: %s. Skipping.' % spec in err)):
                err = 'Package at %s could not be installed' % spec
                module.fail_json(changed=False, msg=err, rc=rc)

    res['rc'] = rc
    res['results'].append(out)
    res['msg'] += err
    res['changed'] = True

    if ('Nothing to do' in out and rc == 0) or ('does not have any packages' in err):
        res['changed'] = False

    if rc != 0:
        res['changed'] = False
        module.fail_json(**res)

    # FIXME - if we did an install - go and check the rpmdb to see if it actually installed
    # look for each pkg in rpmdb
    # look for each pkg via obsoletes

    return res


def install(module, items, repoq, yum_basecmd, conf_file, en_repos, dis_repos, en_plugins, dis_plugins, installroot='/',
            allow_downgrade=False, disable_excludes=None):

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
        if spec.endswith('.rpm'):
            if '://' not in spec and not os.path.exists(spec):
                res['msg'] += "No RPM file matching '%s' found on system" % spec
                res['results'].append("No RPM file matching '%s' found on system" % spec)
                res['rc'] = 127  # Ensure the task fails in with-loop
                module.fail_json(**res)

            if '://' in spec:
                with set_env_proxy(conf_file, installroot):
                    package = fetch_rpm_from_url(spec, module=module)
            else:
                package = spec

            # most common case is the pkg is already installed
            envra = local_envra(package)
            if envra is None:
                module.fail_json(msg="Failed to get nevra information from RPM package: %s" % spec)
            installed_pkgs = is_installed(module, repoq, envra, conf_file, en_repos=en_repos,
                                          dis_repos=dis_repos, en_plugins=en_plugins,
                                          dis_plugins=dis_plugins, installroot=installroot, disable_excludes=disable_excludes)
            if installed_pkgs:
                res['results'].append('%s providing %s is already installed' % (installed_pkgs[0], package))
                continue

            (name, ver, rel, epoch, arch) = splitFilename(envra)
            installed_pkgs = is_installed(module, repoq, name, conf_file, en_repos=en_repos,
                                          dis_repos=dis_repos, en_plugins=en_plugins, dis_plugins=dis_plugins,
                                          installroot=installroot, disable_excludes=disable_excludes)

            # case for two same envr but differrent archs like x86_64 and i686
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
                if compare > 0 and allow_downgrade:
                    downgrade_candidate = True
                elif compare >= 0:
                    continue

            # else: if there are more installed packages with the same name, that would mean
            # kernel, gpg-pubkey or like, so just let yum deal with it and try to install it

            pkg = package

        # groups
        elif spec.startswith('@'):
            if is_group_env_installed(spec, conf_file, en_plugins=en_plugins, dis_plugins=dis_plugins, installroot=installroot,
                                      disable_excludes=disable_excludes):
                continue

            pkg = spec

        # range requires or file-requires or pkgname :(
        else:
            # most common case is the pkg is already installed and done
            # short circuit all the bs - and search for it as a pkg in is_installed
            # if you find it then we're done
            if not set(['*', '?']).intersection(set(spec)):
                installed_pkgs = is_installed(module, repoq, spec, conf_file, en_repos=en_repos,
                                              dis_repos=dis_repos, en_plugins=en_plugins,
                                              dis_plugins=dis_plugins, is_pkg=True,
                                              installroot=installroot, disable_excludes=disable_excludes)
                if installed_pkgs:
                    res['results'].append('%s providing %s is already installed' % (installed_pkgs[0], spec))
                    continue

            # look up what pkgs provide this
            pkglist = what_provides(module, repoq, yum_basecmd, spec, conf_file, en_repos=en_repos,
                                    dis_repos=dis_repos, en_plugins=en_plugins, dis_plugins=dis_plugins,
                                    installroot=installroot, disable_excludes=disable_excludes)
            if not pkglist:
                res['msg'] += "No package matching '%s' found available, installed or updated" % spec
                res['results'].append("No package matching '%s' found available, installed or updated" % spec)
                res['rc'] = 126  # Ensure the task fails in with-loop
                module.fail_json(**res)

            # if any of the packages are involved in a transaction, fail now
            # so that we don't hang on the yum operation later
            conflicts = transaction_exists(pkglist)
            if conflicts:
                res['msg'] += "The following packages have pending transactions: %s" % ", ".join(conflicts)
                res['rc'] = 125  # Ensure the task fails in with-loop
                module.fail_json(**res)

            # if any of them are installed
            # then nothing to do

            found = False
            for this in pkglist:
                if is_installed(module, repoq, this, conf_file, en_repos=en_repos, dis_repos=dis_repos,
                                en_plugins=en_plugins, dis_plugins=dis_plugins, is_pkg=True,
                                installroot=installroot, disable_excludes=disable_excludes):
                    found = True
                    res['results'].append('%s providing %s is already installed' % (this, spec))
                    break

            # if the version of the pkg you have installed is not in ANY repo, but there are
            # other versions in the repos (both higher and lower) then the previous checks won't work.
            # so we check one more time. This really only works for pkgname - not for file provides or virt provides
            # but virt provides should be all caught in what_provides on its own.
            # highly irritating
            if not found:
                if is_installed(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos,
                                en_plugins=en_plugins, dis_plugins=dis_plugins, installroot=installroot,
                                disable_excludes=disable_excludes):
                    found = True
                    res['results'].append('package providing %s is already installed' % (spec))

            if found:
                continue

            # Downgrade - The yum install command will only install or upgrade to a spec version, it will
            # not install an older version of an RPM even if specified by the install spec. So we need to
            # determine if this is a downgrade, and then use the yum downgrade command to install the RPM.
            if allow_downgrade:
                for package in pkglist:
                    # Get the NEVRA of the requested package using pkglist instead of spec because pkglist
                    #  contains consistently-formatted package names returned by yum, rather than user input
                    #  that is often not parsed correctly by splitFilename().
                    (name, ver, rel, epoch, arch) = splitFilename(package)

                    # Check if any version of the requested package is installed
                    inst_pkgs = is_installed(module, repoq, name, conf_file, en_repos=en_repos,
                                             dis_repos=dis_repos, en_plugins=en_plugins,
                                             dis_plugins=dis_plugins, is_pkg=True, disable_excludes=disable_excludes)
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

        if downgrade_candidate and allow_downgrade:
            downgrade_pkgs.append(pkg)
        else:
            pkgs.append(pkg)

    if downgrade_pkgs:
        res = exec_install(module, items, 'downgrade', downgrade_pkgs, res, yum_basecmd)

    if pkgs:
        res = exec_install(module, items, 'install', pkgs, res, yum_basecmd)

    return res


def remove(module, items, repoq, yum_basecmd, conf_file, en_repos, dis_repos, en_plugins, dis_plugins,
           installroot='/', disable_excludes=None):

    pkgs = []
    res = {}
    res['results'] = []
    res['msg'] = ''
    res['changed'] = False
    res['rc'] = 0

    for pkg in items:
        if pkg.startswith('@'):
            installed = is_group_env_installed(pkg, conf_file, en_plugins=en_plugins, dis_plugins=dis_plugins, installroot=installroot,
                                               disable_excludes=disable_excludes)
        else:
            installed = is_installed(module, repoq, pkg, conf_file, en_repos=en_repos, dis_repos=dis_repos, en_plugins=en_plugins,
                                     dis_plugins=dis_plugins, installroot=installroot, disable_excludes=disable_excludes)

        if installed:
            pkgs.append(pkg)
        else:
            res['results'].append('%s is not installed' % pkg)

    if pkgs:
        if module.check_mode:
            module.exit_json(changed=True, results=res['results'], changes=dict(removed=pkgs))

        # run an actual yum transaction
        cmd = yum_basecmd + ["remove"] + pkgs

        rc, out, err = module.run_command(cmd)

        res['rc'] = rc
        res['results'].append(out)
        res['msg'] = err

        if rc != 0:
            module.fail_json(**res)

        # compile the results into one batch. If anything is changed
        # then mark changed
        # at the end - if we've end up failed then fail out of the rest
        # of the process

        # at this point we check to see if the pkg is no longer present
        for pkg in pkgs:
            if pkg.startswith('@'):
                installed = is_group_env_installed(pkg, conf_file, en_plugins=en_plugins, dis_plugins=dis_plugins,
                                                   installroot=installroot, disable_excludes=disable_excludes)
            else:
                installed = is_installed(module, repoq, pkg, conf_file, en_repos=en_repos, dis_repos=dis_repos, en_plugins=en_plugins,
                                         dis_plugins=dis_plugins, installroot=installroot, disable_excludes=disable_excludes)

            if installed:
                module.fail_json(**res)

        res['changed'] = True

    return res


def run_check_update(module, yum_basecmd):
    # run check-update to see if we have packages pending
    rc, out, err = module.run_command(yum_basecmd + ['check-update'])
    return rc, out, err


def parse_check_update(check_update_output):
    updates = {}

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
    out = re.sub(r'\n[^\w]\W+(.*)', r' \1',
                 check_update_output)

    available_updates = out.split('\n')

    # build update dictionary
    for line in available_updates:
        line = line.split()
        # ignore irrelevant lines
        # '*' in line matches lines like mirror lists:
        #      * base: mirror.corbina.net
        # len(line) != 3 could be junk or a continuation
        #
        # FIXME: what is  the '.' not in line  conditional for?

        if '*' in line or len(line) != 3 or '.' not in line[0]:
            continue
        else:
            pkg, version, repo = line
            name, dist = pkg.rsplit('.', 1)
            updates.update({name: {'version': version, 'dist': dist, 'repo': repo}})
    return updates


def latest(module, items, repoq, yum_basecmd, conf_file, en_repos, dis_repos, en_plugins, dis_plugins, update_only,
           installroot='/', disable_excludes=None):

    res = {}
    res['results'] = []
    res['msg'] = ''
    res['changed'] = False
    res['rc'] = 0
    pkgs = {}
    pkgs['update'] = []
    pkgs['install'] = []
    updates = {}
    update_all = False
    cmd = None

    # determine if we're doing an update all
    if '*' in items:
        update_all = True

    rc, out, err = run_check_update(module, yum_basecmd)

    if rc == 0 and update_all:
        res['results'].append('Nothing to do here, all packages are up to date')
        return res
    elif rc == 100:
        updates = parse_check_update(out)
    elif rc == 1:
        res['msg'] = err
        res['rc'] = rc
        module.fail_json(**res)

    if update_all:
        cmd = yum_basecmd + ['update']
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
            elif spec.endswith('.rpm') and '://' not in spec:
                if not os.path.exists(spec):
                    res['msg'] += "No RPM file matching '%s' found on system" % spec
                    res['results'].append("No RPM file matching '%s' found on system" % spec)
                    res['rc'] = 127  # Ensure the task fails in with-loop
                    module.fail_json(**res)

                # get the pkg e:name-v-r.arch
                envra = local_envra(spec)

                if envra is None:
                    module.fail_json(msg="Failed to get nevra information from RPM package: %s" % spec)

                # local rpm files can't be updated
                if not is_installed(module, repoq, envra, conf_file, en_repos=en_repos, dis_repos=dis_repos, en_plugins=en_plugins,
                                    dis_plugins=dis_plugins, installroot=installroot, disable_excludes=disable_excludes):
                    pkgs['install'].append(spec)
                continue

            # URL
            elif '://' in spec:
                # download package so that we can check if it's already installed
                with set_env_proxy(conf_file, installroot):
                    package = fetch_rpm_from_url(spec, module=module)
                envra = local_envra(package)

                if envra is None:
                    module.fail_json(msg="Failed to get nevra information from RPM package: %s" % spec)

                # local rpm files can't be updated
                if not is_installed(module, repoq, envra, conf_file, en_repos=en_repos, dis_repos=dis_repos, en_plugins=en_plugins,
                                    dis_plugins=dis_plugins, installroot=installroot, disable_excludes=disable_excludes):
                    pkgs['install'].append(package)
                continue

            # dep/pkgname  - find it
            else:
                if is_installed(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos,
                                en_plugins=en_plugins, dis_plugins=dis_plugins, installroot=installroot,
                                disable_excludes=disable_excludes) or update_only:
                    pkgs['update'].append(spec)
                else:
                    pkgs['install'].append(spec)
            pkglist = what_provides(module, repoq, yum_basecmd, spec, conf_file, en_repos=en_repos,
                                    dis_repos=dis_repos, en_plugins=en_plugins, dis_plugins=dis_plugins,
                                    installroot=installroot, disable_excludes=disable_excludes)
            # FIXME..? may not be desirable to throw an exception here if a single package is missing
            if not pkglist:
                res['msg'] += "No package matching '%s' found available, installed or updated" % spec
                res['results'].append("No package matching '%s' found available, installed or updated" % spec)
                res['rc'] = 126  # Ensure the task fails in with-loop
                module.fail_json(**res)

            nothing_to_do = True
            for pkg in pkglist:
                if spec in pkgs['install'] and is_available(module, repoq, pkg, conf_file,
                                                            en_repos=en_repos, dis_repos=dis_repos,
                                                            en_plugins=en_plugins, dis_plugins=dis_plugins,
                                                            installroot=installroot, disable_excludes=disable_excludes):
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

            if not is_installed(module, repoq, spec, conf_file, en_repos=en_repos,
                                dis_repos=dis_repos, en_plugins=en_plugins,
                                dis_plugins=dis_plugins, installroot=installroot, disable_excludes=disable_excludes) and update_only:
                res['results'].append("Packages providing %s not installed due to update_only specified" % spec)
                continue
            if nothing_to_do:
                res['results'].append("All packages providing %s are up to date" % spec)
                continue

            # if any of the packages are involved in a transaction, fail now
            # so that we don't hang on the yum operation later
            conflicts = transaction_exists(pkglist)
            if conflicts:
                res['msg'] += "The following packages have pending transactions: %s" % ", ".join(conflicts)
                res['results'].append("The following packages have pending transactions: %s" % ", ".join(conflicts))
                res['rc'] = 128  # Ensure the task fails in with-loop
                module.fail_json(**res)

    # check_mode output
    if module.check_mode:
        to_update = []
        for w in will_update:
            if w.startswith('@'):
                to_update.append((w, None))
            elif w not in updates:
                other_pkg = will_update_from_other_package[w]
                to_update.append((w, 'because of (at least) %s-%s.%s from %s' % (other_pkg,
                                                                                 updates[other_pkg]['version'],
                                                                                 updates[other_pkg]['dist'],
                                                                                 updates[other_pkg]['repo'])))
            else:
                to_update.append((w, '%s.%s from %s' % (updates[w]['version'], updates[w]['dist'], updates[w]['repo'])))

        res['changes'] = dict(installed=pkgs['install'], updated=to_update)

        if will_update or pkgs['install']:
            res['changed'] = True

        return res

    # run commands
    if cmd:     # update all
        rc, out, err = module.run_command(cmd)
        res['changed'] = True
    elif pkgs['install'] or will_update:
        cmd = yum_basecmd + ['install'] + pkgs['install'] + pkgs['update']
        lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
        rc, out, err = module.run_command(cmd, environ_update=lang_env)
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


def ensure(module, state, pkgs, conf_file, enablerepo, disablerepo,
           disable_gpg_check, exclude, repoq, skip_broken, update_only, security,
           bugfix, installroot='/', allow_downgrade=False, disable_plugin=None,
           enable_plugin=None, disable_excludes=None, download_only=False):

    # fedora will redirect yum to dnf, which has incompatibilities
    # with how this module expects yum to operate. If yum-deprecated
    # is available, use that instead to emulate the old behaviors.
    if module.get_bin_path('yum-deprecated'):
        yumbin = module.get_bin_path('yum-deprecated')
    else:
        yumbin = module.get_bin_path('yum')

    # need debug level 2 to get 'Nothing to do' for groupinstall.
    yum_basecmd = [yumbin, '-d', '2', '-y']

    if conf_file and os.path.exists(conf_file):
        yum_basecmd += ['-c', conf_file]
        if repoq:
            repoq += ['-c', conf_file]

    dis_repos = []
    en_repos = []

    if skip_broken:
        yum_basecmd.extend(['--skip-broken'])

    if disablerepo:
        dis_repos = disablerepo.split(',')
        r_cmd = ['--disablerepo=%s' % disablerepo]
        yum_basecmd.extend(r_cmd)
    if enablerepo:
        en_repos = enablerepo.split(',')
        r_cmd = ['--enablerepo=%s' % enablerepo]
        yum_basecmd.extend(r_cmd)

    if enable_plugin:
        yum_basecmd.extend(['--enableplugin', ','.join(enable_plugin)])

    if disable_plugin:
        yum_basecmd.extend(['--disableplugin', ','.join(disable_plugin)])

    if exclude:
        e_cmd = ['--exclude=%s' % exclude]
        yum_basecmd.extend(e_cmd)

    if disable_excludes:
        yum_basecmd.extend(['--disableexcludes=%s' % disable_excludes])

    if download_only:
        yum_basecmd.extend(['--downloadonly'])

    if installroot != '/':
        # do not setup installroot by default, because of error
        # CRITICAL:yum.cli:Config Error: Error accessing file for config file:////etc/yum.conf
        # in old yum version (like in CentOS 6.6)
        e_cmd = ['--installroot=%s' % installroot]
        yum_basecmd.extend(e_cmd)

    if state in ('installed', 'present', 'latest'):
        """ The need of this entire if conditional has to be chalanged
            this function is the ensure function that is called
            in the main section.

            This conditional tends to disable/enable repo for
            install present latest action, same actually
            can be done for remove and absent action

            As solution I would advice to cal
            try: my.repos.disableRepo(disablerepo)
            and
            try: my.repos.enableRepo(enablerepo)
            right before any yum_cmd is actually called regardless
            of yum action.

            Please note that enable/disablerepo options are general
            options, this means that we can call those with any action
            option.  https://linux.die.net/man/8/yum

            This docstring will be removed together when issue: #21619
            will be solved.

            This has been triggered by: #19587
        """

        if module.params.get('update_cache'):
            module.run_command(yum_basecmd + ['clean', 'expire-cache'])

        my = yum_base(conf_file, installroot, enable_plugin, disable_plugin, disable_excludes)
        try:
            if disablerepo:
                my.repos.disableRepo(disablerepo)
            current_repos = my.repos.repos.keys()
            if enablerepo:
                try:
                    my.repos.enableRepo(enablerepo)
                    new_repos = my.repos.repos.keys()
                    for i in new_repos:
                        if i not in current_repos:
                            rid = my.repos.getRepo(i)
                            a = rid.repoXML.repoid  # nopep8 - https://github.com/ansible/ansible/pull/21475#pullrequestreview-22404868
                    current_repos = new_repos
                except yum.Errors.YumBaseError as e:
                    module.fail_json(msg="Error setting/accessing repos: %s" % to_native(e))
        except yum.Errors.YumBaseError as e:
            module.fail_json(msg="Error accessing repos: %s" % to_native(e))
    if state in ['installed', 'present']:
        if disable_gpg_check:
            yum_basecmd.append('--nogpgcheck')
        res = install(module, pkgs, repoq, yum_basecmd, conf_file, en_repos, dis_repos,
                      enable_plugin, disable_plugin, installroot=installroot,
                      allow_downgrade=allow_downgrade, disable_excludes=disable_excludes)
    elif state in ['removed', 'absent']:
        res = remove(module, pkgs, repoq, yum_basecmd, conf_file, en_repos, dis_repos, enable_plugin, disable_plugin,
                     installroot=installroot, disable_excludes=disable_excludes)
    elif state == 'latest':
        if disable_gpg_check:
            yum_basecmd.append('--nogpgcheck')
        if security:
            yum_basecmd.append('--security')
        if bugfix:
            yum_basecmd.append('--bugfix')
        res = latest(module, pkgs, repoq, yum_basecmd, conf_file, en_repos, dis_repos, enable_plugin, disable_plugin, update_only,
                     installroot=installroot, disable_excludes=disable_excludes)
    else:
        # should be caught by AnsibleModule argument_spec
        module.fail_json(msg="we should never get here unless this all failed",
                         changed=False, results='', errors='unexpected state')
    return res


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
        argument_spec=dict(
            name=dict(type='list', aliases=['pkg']),
            exclude=dict(type='str'),
            # removed==absent, installed==present, these are accepted as aliases
            state=dict(type='str', default='installed', choices=['absent', 'installed', 'latest', 'present', 'removed']),
            enablerepo=dict(type='str'),
            disablerepo=dict(type='str'),
            list=dict(type='str'),
            conf_file=dict(type='str'),
            disable_gpg_check=dict(type='bool', default=False),
            skip_broken=dict(type='bool', default=False),
            update_cache=dict(type='bool', default=False, aliases=['expire-cache']),
            validate_certs=dict(type='bool', default=True),
            installroot=dict(type='str', default="/"),
            update_only=dict(required=False, default="no", type='bool'),
            # this should not be needed, but exists as a failsafe
            install_repoquery=dict(type='bool', default=True),
            allow_downgrade=dict(type='bool', default=False),
            security=dict(type='bool', default=False),
            bugfix=dict(required=False, type='bool', default=False),
            enable_plugin=dict(type='list', default=[]),
            disable_plugin=dict(type='list', default=[]),
            disable_excludes=dict(type='str', default=None, choices=['all', 'main', 'repoid']),
            download_only=dict(type='bool', default=False),
        ),
        required_one_of=[['name', 'list']],
        mutually_exclusive=[['name', 'list']],
        supports_check_mode=True,
    )

    error_msgs = []
    if not HAS_RPM_PYTHON:
        error_msgs.append('The Python 2 bindings for rpm are needed for this module. If you require Python 3 support use the `dnf` Ansible module instead.')
    if not HAS_YUM_PYTHON:
        error_msgs.append('The Python 2 yum module is needed for this module. If you require Python 3 support use the `dnf` Ansible module instead.')

    if error_msgs:
        module.fail_json(msg='. '.join(error_msgs))

    params = module.params
    enable_plugin = params.get('enable_plugin')
    disable_plugin = params.get('disable_plugin')
    if params['disable_excludes'] and yum.__version_info__ < (3, 4):
        module.fail_json(msg="'disable_includes' is available in yum version 3.4 and onwards.")

    if params['list']:
        repoquerybin = ensure_yum_utils(module)
        if not repoquerybin:
            module.fail_json(msg="repoquery is required to use list= with this module. Please install the yum-utils package.")
        results = {'results': list_stuff(module, repoquerybin, params['conf_file'],
                                         params['list'], params['installroot'],
                                         params['disablerepo'], params['enablerepo'], params['disable_excludes'])}
    else:
        # If rhn-plugin is installed and no rhn-certificate is available on
        # the system then users will see an error message using the yum API.
        # Use repoquery in those cases.

        my = yum_base(params['conf_file'], params['installroot'], enable_plugin, disable_plugin, params['disable_excludes'])
        # A sideeffect of accessing conf is that the configuration is
        # loaded and plugins are discovered
        my.conf
        repoquery = None
        try:
            yum_plugins = my.plugins._plugins
        except AttributeError:
            pass
        else:
            if 'rhnplugin' in yum_plugins:
                repoquerybin = ensure_yum_utils(module)
                if repoquerybin:
                    repoquery = [repoquerybin, '--show-duplicates', '--plugins', '--quiet']
                    if params['installroot'] != '/':
                        repoquery.extend(['--installroot', params['installroot']])

        pkg = [p.strip() for p in params['name']]
        exclude = params['exclude']
        state = params['state']
        enablerepo = params.get('enablerepo', '')
        disablerepo = params.get('disablerepo', '')
        disable_gpg_check = params['disable_gpg_check']
        skip_broken = params['skip_broken']
        update_only = params['update_only']
        security = params['security']
        bugfix = params['bugfix']
        allow_downgrade = params['allow_downgrade']
        download_only = params['download_only']
        results = ensure(module, state, pkg, params['conf_file'], enablerepo,
                         disablerepo, disable_gpg_check, exclude, repoquery,
                         skip_broken, update_only, security, bugfix, params['installroot'], allow_downgrade,
                         disable_plugin=disable_plugin, enable_plugin=enable_plugin,
                         disable_excludes=params['disable_excludes'], download_only=download_only)
        if repoquery:
            results['msg'] = '%s %s' % (
                results.get('msg', ''),
                'Warning: Due to potential bad behaviour with rhnplugin and certificates, used slower repoquery calls instead of Yum API.'
            )

    module.exit_json(**results)


if __name__ == '__main__':
    main()
