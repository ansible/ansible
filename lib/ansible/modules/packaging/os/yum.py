#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# (c) 2012, Red Hat, Inc
# Written by Seth Vidal <skvidal at fedoraproject.org>
# (c) 2014, Epic Games, Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: yum
version_added: historical
short_description: Manages packages with the I(yum) package manager
description:
     - Installs, upgrade, removes, and lists packages and groups with the I(yum) package manager.
options:
  name:
    description:
      - "Package name, or package specifier with version, like C(name-1.0). When using state=latest, this can be '*' which means run: yum -y update.
         You can also pass a url or a local path to a rpm file (using state=present).  To operate on several packages this can accept a comma separated list
         of packages or (as of 2.0) a list of packages."
    required: true
    default: null
    aliases: [ 'pkg' ]
  exclude:
    description:
      - "Package name(s) to exclude when state=present, or latest"
    required: false
    version_added: "2.0"
    default: null
  list:
    description:
      - Package name to run the equivalent of yum list <package> against.
    required: false
    default: null
  state:
    description:
      - Whether to install (C(present) or C(installed), C(latest)), or remove (C(absent) or C(removed)) a package.
    required: false
    choices: [ "present", "installed", "latest", "absent", "removed" ]
    default: "present"
  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    version_added: "0.9"
    default: null
    aliases: []

  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    version_added: "0.9"
    default: null
    aliases: []

  conf_file:
    description:
      - The remote yum configuration file to use for the transaction.
    required: false
    version_added: "0.6"
    default: null
    aliases: []

  disable_gpg_check:
    description:
      - Whether to disable the GPG checking of signatures of packages being
        installed. Has an effect only if state is I(present) or I(latest).
    required: false
    version_added: "1.2"
    default: "no"
    choices: ["yes", "no"]
    aliases: []

  skip_broken:
    description:
      - Resolve depsolve problems by removing packages that are causing problems from the trans‐
        action.
    required: false
    version_added: "2.3"
    default: "no"
    choices: ["yes", "no"]
    aliases: []

  update_cache:
    description:
      - Force yum to check if cache is out of date and redownload if needed.
        Has an effect only if state is I(present) or I(latest).
    required: false
    version_added: "1.9"
    default: "no"
    choices: ["yes", "no"]
    aliases: [ "expire-cache" ]

  validate_certs:
    description:
      - This only applies if using a https url as the source of the rpm. e.g. for localinstall. If set to C(no), the SSL certificates will not be validated.
      - This should only set to C(no) used on personally controlled sites using self-signed certificates as it avoids verifying the source site.
      - Prior to 2.1 the code worked as if this was set to C(yes).
    required: false
    default: "yes"
    choices: ["yes", "no"]
    version_added: "2.1"

  installroot:
    description:
      - Specifies an alternative installroot, relative to which all packages
        will be installed.
    required: false
    version_added: "2.3"
    default: "/"
    aliases: []

notes:
  - When used with a loop of package names in a playbook, ansible optimizes
    the call to the yum module.  Instead of calling the module with a single
    package each time through the loop, ansible calls the module once with all
    of the package names from the loop.
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
requirements: [ yum ]
author:
    - "Ansible Core Team"
    - "Seth Vidal"
    - "Eduard Snesarev (github.com/verm666)"
    - "Berend De Schouwer (github.com/berenddeschouwer)"
'''

EXAMPLES = '''
- name: install the latest version of Apache
  yum:
    name: httpd
    state: latest

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
'''

import os
import re
import shutil
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
    from rpmUtils.miscutils import splitFilename
    transaction_helpers = True
except:
    transaction_helpers = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import fetch_url

# 64k.  Number of bytes to read at a time when manually downloading pkgs via a url
BUFSIZE = 65536

def_qf = "%{name}-%{version}-%{release}.%{arch}"
rpmbin = None


def yum_base(conf_file=None, installroot='/'):

    my = yum.YumBase()
    my.preconf.debuglevel = 0
    my.preconf.errorlevel = 0
    my.preconf.plugins = True
    #my.preconf.releasever = '/'
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

    return my

def ensure_yum_utils(module):

    repoquerybin = module.get_bin_path('repoquery', required=False)

    if module.params['install_repoquery'] and not repoquerybin and not module.check_mode:
        yum_path = module.get_bin_path('yum')
        if yum_path:
            rc, so, se = module.run_command('%s -y install yum-utils' % yum_path)
        repoquerybin = module.get_bin_path('repoquery', required=False)

    return repoquerybin

def fetch_rpm_from_url(spec, module=None):
    # download package so that we can query it
    package_name, _ = os.path.splitext(str(spec.rsplit('/', 1)[1]))
    package_file = tempfile.NamedTemporaryFile(prefix=package_name, suffix='.rpm', delete=False)
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
    except Exception:
        e = get_exception()
        if module:
            module.fail_json(msg="Failure downloading %s, %s" % (spec, e))
    return package_file.name

def po_to_nevra(po):

    if hasattr(po, 'ui_nevra'):
        return po.ui_nevra
    else:
        return '%s-%s-%s.%s' % (po.name, po.version, po.release, po.arch)

def is_installed(module, repoq, pkgspec, conf_file, qf=def_qf, en_repos=None, dis_repos=None, is_pkg=False, installroot='/'):
    if en_repos is None:
        en_repos = []
    if dis_repos is None:
        dis_repos = []

    if not repoq:
        pkgs = []
        try:
            my = yum_base(conf_file, installroot)
            for rid in dis_repos:
                my.repos.disableRepo(rid)
            for rid in en_repos:
                my.repos.enableRepo(rid)

            e, m, u = my.rpmdb.matchPackageNames([pkgspec])
            pkgs = e + m
            if not pkgs and not is_pkg:
                pkgs.extend(my.returnInstalledPackagesByDep(pkgspec))
        except Exception:
            e = get_exception()
            module.fail_json(msg="Failure talking to yum: %s" % e)

        return [po_to_nevra(p) for p in pkgs]

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

def is_available(module, repoq, pkgspec, conf_file, qf=def_qf, en_repos=None, dis_repos=None, installroot='/'):
    if en_repos is None:
        en_repos = []
    if dis_repos is None:
        dis_repos = []

    if not repoq:

        pkgs = []
        try:
            my = yum_base(conf_file, installroot)
            for rid in dis_repos:
                my.repos.disableRepo(rid)
            for rid in en_repos:
                my.repos.enableRepo(rid)

            e, m, u = my.pkgSack.matchPackageNames([pkgspec])
            pkgs = e + m
            if not pkgs:
                pkgs.extend(my.returnPackagesByDep(pkgspec))
        except Exception:
            e = get_exception()
            module.fail_json(msg="Failure talking to yum: %s" % e)

        return [po_to_nevra(p) for p in pkgs]

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

def is_update(module, repoq, pkgspec, conf_file, qf=def_qf, en_repos=None, dis_repos=None, installroot='/'):
    if en_repos is None:
        en_repos = []
    if dis_repos is None:
        dis_repos = []

    if not repoq:

        retpkgs = []
        pkgs = []
        updates = []

        try:
            my = yum_base(conf_file, installroot)
            for rid in dis_repos:
                my.repos.disableRepo(rid)
            for rid in en_repos:
                my.repos.enableRepo(rid)

            pkgs = my.returnPackagesByDep(pkgspec) + my.returnInstalledPackagesByDep(pkgspec)
            if not pkgs:
                e, m, u = my.pkgSack.matchPackageNames([pkgspec])
                pkgs = e + m
            updates = my.doPackageLists(pkgnarrow='updates').updates
        except Exception:
            e = get_exception()
            module.fail_json(msg="Failure talking to yum: %s" % e)

        for pkg in pkgs:
            if pkg in updates:
                retpkgs.append(pkg)

        return set([po_to_nevra(p) for p in retpkgs])

    else:
        myrepoq = list(repoq)
        r_cmd = ['--disablerepo', ','.join(dis_repos)]
        myrepoq.extend(r_cmd)

        r_cmd = ['--enablerepo', ','.join(en_repos)]
        myrepoq.extend(r_cmd)

        cmd = myrepoq + ["--pkgnarrow=updates", "--qf", qf, pkgspec]
        rc, out, err = module.run_command(cmd)

        if rc == 0:
            return set([p for p in out.split('\n') if p.strip()])
        else:
            module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err))

    return set()

def what_provides(module, repoq, req_spec, conf_file, qf=def_qf, en_repos=None, dis_repos=None, installroot='/'):
    if en_repos is None:
        en_repos = []
    if dis_repos is None:
        dis_repos = []

    if not repoq:

        pkgs = []
        try:
            my = yum_base(conf_file, installroot)
            for rid in dis_repos:
                my.repos.disableRepo(rid)
            for rid in en_repos:
                my.repos.enableRepo(rid)

            pkgs = my.returnPackagesByDep(req_spec) + my.returnInstalledPackagesByDep(req_spec)
            if not pkgs:
                e, m, u = my.pkgSack.matchPackageNames([req_spec])
                pkgs.extend(e)
                pkgs.extend(m)
                e, m, u = my.rpmdb.matchPackageNames([req_spec])
                pkgs.extend(e)
                pkgs.extend(m)
        except Exception:
            e = get_exception()
            module.fail_json(msg="Failure talking to yum: %s" % e)

        return set([po_to_nevra(p) for p in pkgs])

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
            pkgs = set([p for p in out.split('\n') if p.strip()])
            if not pkgs:
                pkgs = is_installed(module, repoq, req_spec, conf_file, qf=qf, installroot=installroot)
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
    pkglist_nvreas = []
    for pkg in pkglist:
        pkglist_nvreas.append(splitFilename(pkg))

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

def local_nvra(module, path):
    """return nvra of a local rpm passed in"""

    ts = rpm.TransactionSet()
    ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
    fd = os.open(path, os.O_RDONLY)
    try:
        header = ts.hdrFromFdno(fd)
    finally:
        os.close(fd)

    return '%s-%s-%s.%s' % (header[rpm.RPMTAG_NAME],
                            header[rpm.RPMTAG_VERSION],
                            header[rpm.RPMTAG_RELEASE],
                            header[rpm.RPMTAG_ARCH])

def pkg_to_dict(pkgstr):

    if pkgstr.strip():
        n, e, v, r, a, repo = pkgstr.split('|')
    else:
        return {'error_parsing': pkgstr}

    d = {
        'name':n,
        'arch':a,
        'epoch':e,
        'release':r,
        'version':v,
        'repo':repo,
        'nevra': '%s:%s-%s-%s.%s' % (e, n, v, r, a)
    }

    if repo == 'installed':
        d['yumstate'] = 'installed'
    else:
        d['yumstate'] = 'available'

    return d

def repolist(module, repoq, qf="%{repoid}"):

    cmd = repoq + ["--qf", qf, "-a"]
    rc, out, err = module.run_command(cmd)
    ret = []
    if rc == 0:
        ret = set([p for p in out.split('\n') if p.strip()])
    return ret

def list_stuff(module, repoquerybin, conf_file, stuff, installroot='/', disablerepo='', enablerepo=''):

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
        return [pkg_to_dict(p) for p in sorted(is_installed(module, repoq, '-a', conf_file, qf=is_installed_qf, installroot=installroot)) if p.strip()]
    elif stuff == 'updates':
        return [pkg_to_dict(p) for p in sorted(is_update(module, repoq, '-a', conf_file, qf=qf, installroot=installroot)) if p.strip()]
    elif stuff == 'available':
        return [pkg_to_dict(p) for p in sorted(is_available(module, repoq, '-a', conf_file, qf=qf, installroot=installroot)) if p.strip()]
    elif stuff == 'repos':
        return [dict(repoid=name, state='enabled') for name in sorted(repolist(module, repoq)) if name.strip()]
    else:
        return [pkg_to_dict(p) for p in sorted(is_installed(module, repoq, stuff, conf_file, qf=is_installed_qf, installroot=installroot)+
                                                is_available(module, repoq, stuff, conf_file, qf=qf, installroot=installroot)) if p.strip()]

def install(module, items, repoq, yum_basecmd, conf_file, en_repos, dis_repos, installroot='/'):

    pkgs = []
    res = {}
    res['results'] = []
    res['msg'] = ''
    res['rc'] = 0
    res['changed'] = False

    for spec in items:
        pkg = None

        # check if pkgspec is installed (if possible for idempotence)
        # localpkg
        if spec.endswith('.rpm') and '://' not in spec:
            # get the pkg name-v-r.arch
            if not os.path.exists(spec):
                res['msg'] += "No RPM file matching '%s' found on system" % spec
                res['results'].append("No RPM file matching '%s' found on system" % spec)
                res['rc'] = 127 # Ensure the task fails in with-loop
                module.fail_json(**res)

            nvra = local_nvra(module, spec)

            # look for them in the rpmdb
            if is_installed(module, repoq, nvra, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot):
                # if they are there, skip it
                continue
            pkg = spec

        # URL
        elif '://' in spec:
            # download package so that we can check if it's already installed
            package = fetch_rpm_from_url(spec, module=module)
            nvra = local_nvra(module, package)
            if is_installed(module, repoq, nvra, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot):
                # if it's there, skip it
                continue
            pkg = package

        #groups :(
        elif spec.startswith('@'):
            # complete wild ass guess b/c it's a group
            pkg = spec

        # range requires or file-requires or pkgname :(
        else:
            # most common case is the pkg is already installed and done
            # short circuit all the bs - and search for it as a pkg in is_installed
            # if you find it then we're done
            if not set(['*', '?']).intersection(set(spec)):
                installed_pkgs = is_installed(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos, is_pkg=True, installroot=installroot)
                if installed_pkgs:
                    res['results'].append('%s providing %s is already installed' % (installed_pkgs[0], spec))
                    continue

            # look up what pkgs provide this
            pkglist = what_provides(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot)
            if not pkglist:
                res['msg'] += "No package matching '%s' found available, installed or updated" % spec
                res['results'].append("No package matching '%s' found available, installed or updated" % spec)
                res['rc'] = 126 # Ensure the task fails in with-loop
                module.fail_json(**res)

            # if any of the packages are involved in a transaction, fail now
            # so that we don't hang on the yum operation later
            conflicts = transaction_exists(pkglist)
            if len(conflicts) > 0:
                res['msg'] += "The following packages have pending transactions: %s" % ", ".join(conflicts)
                res['rc'] = 125 # Ensure the task fails in with-loop
                module.fail_json(**res)

            # if any of them are installed
            # then nothing to do

            found = False
            for this in pkglist:
                if is_installed(module, repoq, this, conf_file, en_repos=en_repos, dis_repos=dis_repos, is_pkg=True, installroot=installroot):
                    found = True
                    res['results'].append('%s providing %s is already installed' % (this, spec))
                    break

            # if the version of the pkg you have installed is not in ANY repo, but there are
            # other versions in the repos (both higher and lower) then the previous checks won't work.
            # so we check one more time. This really only works for pkgname - not for file provides or virt provides
            # but virt provides should be all caught in what_provides on its own.
            # highly irritating
            if not found:
                if is_installed(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot):
                    found = True
                    res['results'].append('package providing %s is already installed' % (spec))

            if found:
                continue

            # if not - then pass in the spec as what to install
            # we could get here if nothing provides it but that's not
            # the error we're catching here
            pkg = spec

        pkgs.append(pkg)

    if pkgs:
        cmd = yum_basecmd + ['install'] + pkgs

        if module.check_mode:
            module.exit_json(changed=True, results=res['results'], changes=dict(installed=pkgs))

        changed = True

        lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
        rc, out, err = module.run_command(cmd, environ_update=lang_env)

        if rc == 1:
            for spec in items:
                # Fail on invalid urls:
                if '://' in spec and ('No package %s available.' % spec in out or 'Cannot open: %s. Skipping.' % spec in err):
                    module.fail_json(msg='Package at %s could not be installed' % spec, rc=1, changed=False)
        if (rc != 0 and 'Nothing to do' in err) or 'Nothing to do' in out:
            # avoid failing in the 'Nothing To Do' case
            # this may happen with an URL spec.
            # for an already installed group,
            # we get rc = 0 and 'Nothing to do' in out, not in err.
            rc = 0
            err = ''
            out = '%s: Nothing to do' % spec
            changed = False

        res['rc'] = rc
        res['results'].append(out)
        res['msg'] += err

        # FIXME - if we did an install - go and check the rpmdb to see if it actually installed
        # look for each pkg in rpmdb
        # look for each pkg via obsoletes

        # Record change
        res['changed'] = changed

    return res


def remove(module, items, repoq, yum_basecmd, conf_file, en_repos, dis_repos, installroot='/'):

    pkgs = []
    res = {}
    res['results'] = []
    res['msg'] = ''
    res['changed'] = False
    res['rc'] = 0

    for pkg in items:
        is_group = False
        # group remove - this is doom on a stick
        if pkg.startswith('@'):
            is_group = True # nopep8 this will be fixed in next MR this module needs major rewrite anyway.
        else:
            if not is_installed(module, repoq, pkg, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot):
                res['results'].append('%s is not installed' % pkg)
                continue

        pkgs.append(pkg)

    if pkgs:
        # run an actual yum transaction
        cmd = yum_basecmd + ["remove"] + pkgs

        if module.check_mode:
            module.exit_json(changed=True, results=res['results'], changes=dict(removed=pkgs))

        rc, out, err = module.run_command(cmd)

        res['rc'] = rc
        res['results'].append(out)
        res['msg'] = err

        # compile the results into one batch. If anything is changed
        # then mark changed
        # at the end - if we've end up failed then fail out of the rest
        # of the process

        # at this point we should check to see if the pkg is no longer present

        for pkg in pkgs:
            if not pkg.startswith('@'): # we can't sensibly check for a group being uninstalled reliably
                # look to see if the pkg shows up from is_installed. If it doesn't
                if not is_installed(module, repoq, pkg, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot):
                    res['changed'] = True
                else:
                    module.fail_json(**res)

        if rc != 0:
            module.fail_json(**res)

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


def latest(module, items, repoq, yum_basecmd, conf_file, en_repos, dis_repos, installroot='/'):

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
                    res['rc'] = 127 # Ensure the task fails in with-loop
                    module.fail_json(**res)

                # get the pkg name-v-r.arch
                nvra = local_nvra(module, spec)

                # local rpm files can't be updated
                if not is_installed(module, repoq, nvra, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot):
                    pkgs['install'].append(spec)
                continue

            # URL
            elif '://' in spec:
                # download package so that we can check if it's already installed
                package = fetch_rpm_from_url(spec, module=module)
                nvra = local_nvra(module, package)

                # local rpm files can't be updated
                if not is_installed(module, repoq, nvra, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot):
                    pkgs['install'].append(package)
                continue

            # dep/pkgname  - find it
            else:
                if is_installed(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot):
                    pkgs['update'].append(spec)
                else:
                    pkgs['install'].append(spec)
            pkglist = what_provides(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot)
            # FIXME..? may not be desirable to throw an exception here if a single package is missing
            if not pkglist:
                res['msg'] += "No package matching '%s' found available, installed or updated" % spec
                res['results'].append("No package matching '%s' found available, installed or updated" % spec)
                res['rc'] = 126 # Ensure the task fails in with-loop
                module.fail_json(**res)

            nothing_to_do = True
            for this in pkglist:
                if spec in pkgs['install'] and is_available(module, repoq, this, conf_file, en_repos=en_repos, dis_repos=dis_repos, installroot=installroot):
                    nothing_to_do = False
                    break


                # this contains the full NVR and spec could contain wildcards
                # or virtual provides (like "python-*" or "smtp-daemon") while
                # updates contains name only.
                this_name_only = '-'.join(this.split('-')[:-2])
                if spec in pkgs['update'] and this_name_only in updates:
                    nothing_to_do = False
                    will_update.add(spec)
                    # Massage the updates list
                    if spec != this_name_only:
                        # For reporting what packages would be updated more
                        # succinctly
                        will_update_from_other_package[spec] = this_name_only
                    break

            if nothing_to_do:
                res['results'].append("All packages providing %s are up to date" % spec)
                continue

            # if any of the packages are involved in a transaction, fail now
            # so that we don't hang on the yum operation later
            conflicts = transaction_exists(pkglist)
            if len(conflicts) > 0:
                res['msg'] += "The following packages have pending transactions: %s" % ", ".join(conflicts)
                res['results'].append("The following packages have pending transactions: %s" % ", ".join(conflicts))
                res['rc'] = 128 # Ensure the task fails in with-loop
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

        if len(will_update) > 0 or len(pkgs['install']) > 0:
            res['changed'] = True

        return res

    # run commands
    if cmd:     # update all
        rc, out, err = module.run_command(cmd)
        res['changed'] = True
    else:
        if len(pkgs['install']) > 0:    # install missing
            cmd = yum_basecmd + ['install'] + pkgs['install']
            rc, out, err = module.run_command(cmd)
            if not out.strip().lower().endswith("no packages marked for update"):
                res['changed'] = True
        else:
            rc, out, err = [0, '', '']

        if len(will_update) > 0:     # update present
            cmd = yum_basecmd + ['update'] + pkgs['update']
            rc2, out2, err2 = module.run_command(cmd)
            if not out2.strip().lower().endswith("no packages marked for update"):
                res['changed'] = True
        else:
            rc2, out2, err2 = [0, '', '']

    if not update_all:
        rc += rc2
        out += out2
        err += err2

    res['rc'] += rc
    res['msg'] += err
    res['results'].append(out)

    if rc:
        res['failed'] = True

    return res

def ensure(module, state, pkgs, conf_file, enablerepo, disablerepo,
           disable_gpg_check, exclude, repoq, skip_broken, installroot='/'):

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

    if exclude:
        e_cmd = ['--exclude=%s' % exclude]
        yum_basecmd.extend(e_cmd)

    if installroot != '/':
        # do not setup installroot by default, because of error
        # CRITICAL:yum.cli:Config Error: Error accessing file for config file:////etc/yum.conf
        # in old yum version (like in CentOS 6.6)
        e_cmd = ['--installroot=%s' % installroot]
        yum_basecmd.extend(e_cmd)

    if state in ['installed', 'present', 'latest']:
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

        my = yum_base(conf_file, installroot)
        try:
            if disablerepo:
                my.repos.disableRepo(disablerepo)
            current_repos = my.repos.repos.keys()
            if enablerepo:
                try:
                    my.repos.enableRepo(enablerepo)
                    new_repos = my.repos.repos.keys()
                    for i in new_repos:
                        if not i in current_repos:
                            rid = my.repos.getRepo(i)
                            a = rid.repoXML.repoid # nopep8 - https://github.com/ansible/ansible/pull/21475#pullrequestreview-22404868
                    current_repos = new_repos
                except yum.Errors.YumBaseError:
                    e = get_exception()
                    module.fail_json(msg="Error setting/accessing repos: %s" % (e))
        except yum.Errors.YumBaseError:
            e = get_exception()
            module.fail_json(msg="Error accessing repos: %s" % e)
    if state in ['installed', 'present']:
        if disable_gpg_check:
            yum_basecmd.append('--nogpgcheck')
        res = install(module, pkgs, repoq, yum_basecmd, conf_file, en_repos, dis_repos, installroot=installroot)
    elif state in ['removed', 'absent']:
        res = remove(module, pkgs, repoq, yum_basecmd, conf_file, en_repos, dis_repos, installroot=installroot)
    elif state == 'latest':
        if disable_gpg_check:
            yum_basecmd.append('--nogpgcheck')
        res = latest(module, pkgs, repoq, yum_basecmd, conf_file, en_repos, dis_repos, installroot=installroot)
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
            name=dict(aliases=['pkg'], type="list"),
            exclude=dict(required=False, default=None),
            # removed==absent, installed==present, these are accepted as aliases
            state=dict(default='installed', choices=['absent', 'present',
                                                     'installed', 'removed',
                                                     'latest']),
            enablerepo=dict(),
            disablerepo=dict(),
            list=dict(),
            conf_file=dict(default=None),
            disable_gpg_check=dict(required=False, default="no", type='bool'),
            skip_broken=dict(required=False, default="no", aliases=[], type='bool'),
            update_cache=dict(required=False, default="no", aliases=['expire-cache'], type='bool'),
            validate_certs=dict(required=False, default="yes", type='bool'),
            installroot=dict(required=False, default="/", type='str'),
            # this should not be needed, but exists as a failsafe
            install_repoquery=dict(required=False, default="yes", type='bool'),
        ),
        required_one_of=[['name', 'list']],
        mutually_exclusive=[['name', 'list']],
        supports_check_mode=True
    )

    error_msgs = []
    if not HAS_RPM_PYTHON:
        error_msgs.append('python2 bindings for rpm are needed for this module')
    if not HAS_YUM_PYTHON:
        error_msgs.append('python2 yum module is needed for this  module')

    if error_msgs:
        module.fail_json(msg='. '.join(error_msgs))

    params = module.params

    if params['list']:
        repoquerybin = ensure_yum_utils(module)
        if not repoquerybin:
            module.fail_json(msg="repoquery is required to use list= with this module. Please install the yum-utils package.")
        results = {'results': list_stuff(module, repoquerybin, params['conf_file'],
                                         params['list'], params['installroot'],
                                         params['disablerepo'], params['enablerepo'])}

    else:
        # If rhn-plugin is installed and no rhn-certificate is available on
        # the system then users will see an error message using the yum API.
        # Use repoquery in those cases.

        my = yum_base(params['conf_file'], params['installroot'])
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
        results = ensure(module, state, pkg, params['conf_file'], enablerepo,
                         disablerepo, disable_gpg_check, exclude, repoquery,
                         skip_broken, params['installroot'])
        if repoquery:
            results['msg'] = '%s %s' % (results.get('msg', ''),
                    'Warning: Due to potential bad behaviour with rhnplugin and certificates, used slower repoquery calls instead of Yum API.')

    module.exit_json(**results)


if __name__ == '__main__':
    main()
