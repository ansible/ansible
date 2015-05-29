#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# Written by Cristian van Ee <cristian at cvee.org>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#


import traceback
import os
import dnf

try:
    from dnf import find_unfinished_transactions, find_ts_remaining
    from rpmUtils.miscutils import splitFilename
    transaction_helpers = True
except:
    transaction_helpers = False

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
      - "Package name, or package specifier with version, like C(name-1.0). When using state=latest, this can be '*' which means run: dnf -y update. You can also pass a url or a local path to a rpm file."
    required: true
    default: null
    aliases: []
  list:
    description:
      - Various (non-idempotent) commands for usage with C(/usr/bin/ansible) and I(not) playbooks. See examples.
    required: false
    default: null
  state:
    description:
      - Whether to install (C(present), C(latest)), or remove (C(absent)) a package.
    required: false
    choices: [ "present", "latest", "absent" ]
    default: "present"
  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    default: null
    aliases: []

  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    default: null
    aliases: []

  conf_file:
    description:
      - The remote dnf configuration file to use for the transaction.
    required: false
    default: null
    aliases: []

  disable_gpg_check:
    description:
      - Whether to disable the GPG checking of signatures of packages being
        installed. Has an effect only if state is I(present) or I(latest).
    required: false
    default: "no"
    choices: ["yes", "no"]
    aliases: []

notes: []
# informational: requirements for nodes
requirements:
  - dnf
  - yum-utils (for repoquery)
author: '"Cristian van Ee (@DJMuggs)" <cristian at cvee.org>'
'''

EXAMPLES = '''
- name: install the latest version of Apache
  dnf: name=httpd state=latest

- name: remove the Apache package
  dnf: name=httpd state=absent

- name: install the latest version of Apache from the testing repo
  dnf: name=httpd enablerepo=testing state=present

- name: upgrade all packages
  dnf: name=* state=latest

- name: install the nginx rpm from a remote repo
  dnf: name=http://nginx.org/packages/centos/6/noarch/RPMS/nginx-release-centos-6-0.el6.ngx.noarch.rpm state=present

- name: install nginx rpm from a local file
  dnf: name=/usr/local/src/nginx-release-centos-6-0.el6.ngx.noarch.rpm state=present

- name: install the 'Development tools' package group
  dnf: name="@Development tools" state=present

'''

def_qf = "%{name}-%{version}-%{release}.%{arch}"

repoquery='/usr/bin/repoquery'
if not os.path.exists(repoquery):
    repoquery = None

dnfbin='/usr/bin/dnf'

import syslog

def log(msg):
    syslog.openlog('ansible-dnf', 0, syslog.LOG_USER)
    syslog.syslog(syslog.LOG_NOTICE, msg)

def dnf_base(conf_file=None, cachedir=False):

    my = dnf.Base()
    my.conf.debuglevel=0
    if conf_file and os.path.exists(conf_file):
        my.conf.config_file_path = conf_file
        my.conf.read()
    my.read_all_repos()
    my.fill_sack()

    return my

def install_dnf_utils(module):

    if not module.check_mode:
        dnf_path = module.get_bin_path('dnf')
        if dnf_path:
            rc, so, se = module.run_command('%s -y install yum-utils' % dnf_path)
            if rc == 0:
                this_path = module.get_bin_path('repoquery')
                global repoquery
                repoquery = this_path

def po_to_nevra(po):

    if hasattr(po, 'ui_nevra'):
        return po.ui_nevra
    else:
        return '%s-%s-%s.%s' % (po.name, po.version, po.release, po.arch)

def is_installed(module, repoq, pkgspec, conf_file, qf=def_qf, en_repos=[], dis_repos=[], is_pkg=False):

    if not repoq:

        pkgs = []
        try:
            my = dnf_base(conf_file)
            for rid in en_repos:
                my.repos.enableRepo(rid)
            for rid in dis_repos:
                my.repos.disableRepo(rid)
                
            e,m,u = my.rpmdb.matchPackageNames([pkgspec])
            pkgs = e + m
            if not pkgs:
                pkgs.extend(my.returnInstalledPackagesByDep(pkgspec))
        except Exception, e:
            module.fail_json(msg="Failure talking to dnf: %s" % e)

        return [ po_to_nevra(p) for p in pkgs ]

    else:

        cmd = repoq + ["--disablerepo=*", "--pkgnarrow=installed", "--qf", qf, pkgspec]
        rc,out,err = module.run_command(cmd)
        if not is_pkg:
            cmd = repoq + ["--disablerepo=*", "--pkgnarrow=installed", "--qf", qf, "--whatprovides", pkgspec]
            rc2,out2,err2 = module.run_command(cmd)
        else:
            rc2,out2,err2 = (0, '', '')
            
        if rc == 0 and rc2 == 0:
            out += out2
            return [ p for p in out.split('\n') if p.strip() ]
        else:
            module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err + err2))
            
    return []

def is_available(module, repoq, pkgspec, conf_file, qf=def_qf, en_repos=[], dis_repos=[]):

    if not repoq:

        pkgs = []
        try:
            my = dnf_base(conf_file)
            for rid in en_repos:
                my.repos.enableRepo(rid)
            for rid in dis_repos:
                my.repos.disableRepo(rid)

            e,m,u = my.pkgSack.matchPackageNames([pkgspec])
            pkgs = e + m
            if not pkgs:
                pkgs.extend(my.returnPackagesByDep(pkgspec))
        except Exception, e:
            module.fail_json(msg="Failure talking to dnf: %s" % e)
            
        return [ po_to_nevra(p) for p in pkgs ]

    else:
        myrepoq = list(repoq)
                 
        for repoid in dis_repos:
            r_cmd = ['--disablerepo', repoid]
            myrepoq.extend(r_cmd)

        for repoid in en_repos:
            r_cmd = ['--enablerepo', repoid]
            myrepoq.extend(r_cmd)

        cmd = myrepoq + ["--qf", qf, pkgspec]
        rc,out,err = module.run_command(cmd)
        if rc == 0:
            return [ p for p in out.split('\n') if p.strip() ]
        else:
            module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err))

            
    return []

def is_update(module, repoq, pkgspec, conf_file, qf=def_qf, en_repos=[], dis_repos=[]):

    if not repoq:

        retpkgs = []
        pkgs = []
        updates = []

        try:
            my = dnf_base(conf_file)
            for rid in en_repos:
                my.repos.enableRepo(rid)
            for rid in dis_repos:
                my.repos.disableRepo(rid)

            pkgs = my.returnPackagesByDep(pkgspec) + my.returnInstalledPackagesByDep(pkgspec)
            if not pkgs:
                e,m,u = my.pkgSack.matchPackageNames([pkgspec])
                pkgs = e + m
            updates = my.doPackageLists(pkgnarrow='updates').updates 
        except Exception, e:
            module.fail_json(msg="Failure talking to dnf: %s" % e)

        for pkg in pkgs:
            if pkg in updates:
                retpkgs.append(pkg)
            
        return set([ po_to_nevra(p) for p in retpkgs ])

    else:
        myrepoq = list(repoq)
        for repoid in dis_repos:
            r_cmd = ['--disablerepo', repoid]
            myrepoq.extend(r_cmd)

        for repoid in en_repos:
            r_cmd = ['--enablerepo', repoid]
            myrepoq.extend(r_cmd)

        cmd = myrepoq + ["--pkgnarrow=updates", "--qf", qf, pkgspec]
        rc,out,err = module.run_command(cmd)
        
        if rc == 0:
            return set([ p for p in out.split('\n') if p.strip() ])
        else:
            module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err))
            
    return []

def what_provides(module, repoq, req_spec, conf_file,  qf=def_qf, en_repos=[], dis_repos=[]):

    if not repoq:

        pkgs = []
        try:
            my = dnf_base(conf_file)
            for rid in en_repos:
                my.repos.enableRepo(rid)
            for rid in dis_repos:
                my.repos.disableRepo(rid)

            pkgs = my.returnPackagesByDep(req_spec) + my.returnInstalledPackagesByDep(req_spec)
            if not pkgs:
                e,m,u = my.pkgSack.matchPackageNames([req_spec])
                pkgs.extend(e)
                pkgs.extend(m)
                e,m,u = my.rpmdb.matchPackageNames([req_spec])
                pkgs.extend(e)
                pkgs.extend(m)
        except Exception, e:
            module.fail_json(msg="Failure talking to dnf: %s" % e)

        return set([ po_to_nevra(p) for p in pkgs ])

    else:
        myrepoq = list(repoq)
        for repoid in dis_repos:
            r_cmd = ['--disablerepo', repoid]
            myrepoq.extend(r_cmd)

        for repoid in en_repos:
            r_cmd = ['--enablerepo', repoid]
            myrepoq.extend(r_cmd)

        cmd = myrepoq + ["--qf", qf, "--whatprovides", req_spec]
        rc,out,err = module.run_command(cmd)
        cmd = myrepoq + ["--qf", qf, req_spec]
        rc2,out2,err2 = module.run_command(cmd)
        if rc == 0 and rc2 == 0:
            out += out2
            pkgs = set([ p for p in out.split('\n') if p.strip() ])
            if not pkgs:
                pkgs = is_installed(module, repoq, req_spec, conf_file, qf=qf)
            return pkgs
        else:
            module.fail_json(msg='Error from repoquery: %s: %s' % (cmd, err + err2))

    return []

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
            (n,v,r,e,a) = splitFilename(step_spec)
            # and see if that spec is in the list of packages
            # requested for installation/updating
            for pkg in pkglist_nvreas:
                # if the name and arch match, we're going to assume
                # this package is part of a pending transaction
                # the label is just for display purposes
                label = "%s-%s" % (n,a)
                if n == pkg[0] and a == pkg[4]:
                    if label not in conflicts:
                        conflicts.append("%s-%s" % (n,a))
                    break
    return conflicts

def local_nvra(module, path):
    """return nvra of a local rpm passed in"""
    
    cmd = ['/bin/rpm', '-qp' ,'--qf', 
            '%{name}-%{version}-%{release}.%{arch}\n', path ]
    rc, out, err = module.run_command(cmd)
    if rc != 0:
        return None
    nvra = out.split('\n')[0]
    return nvra
    
def pkg_to_dict(pkgstr):

    if pkgstr.strip():
        n,e,v,r,a,repo = pkgstr.split('|')
    else:
        return {'error_parsing': pkgstr}

    d = {
        'name':n,
        'arch':a,
        'epoch':e,
        'release':r,
        'version':v,
        'repo':repo,
        'nevra': '%s:%s-%s-%s.%s' % (e,n,v,r,a)
    }

    if repo == 'installed':
        d['dnfstate'] = 'installed'
    else:
        d['dnfstate'] = 'available'

    return d

def repolist(module, repoq, qf="%{repoid}"):

    cmd = repoq + ["--qf", qf, "-a"]
    rc,out,err = module.run_command(cmd)
    ret = []
    if rc == 0:
        ret = set([ p for p in out.split('\n') if p.strip() ])
    return ret

def list_stuff(module, conf_file, stuff):

    qf = "%{name}|%{epoch}|%{version}|%{release}|%{arch}|%{repoid}"
    repoq = [repoquery, '--show-duplicates', '--plugins', '--quiet', '-q']
    if conf_file and os.path.exists(conf_file):
        repoq += ['-c', conf_file]

    if stuff == 'installed':
        return [ pkg_to_dict(p) for p in is_installed(module, repoq, '-a', conf_file, qf=qf) if p.strip() ]
    elif stuff == 'updates':
        return [ pkg_to_dict(p) for p in is_update(module, repoq, '-a', conf_file, qf=qf) if p.strip() ]
    elif stuff == 'available':
        return [ pkg_to_dict(p) for p in is_available(module, repoq, '-a', conf_file, qf=qf) if p.strip() ]
    elif stuff == 'repos':
        return [ dict(repoid=name, state='enabled') for name in repolist(module, repoq) if name.strip() ]
    else:
        return [ pkg_to_dict(p) for p in is_installed(module, repoq, stuff, conf_file, qf=qf) + is_available(module, repoq, stuff, conf_file, qf=qf) if p.strip() ]

def install(module, items, repoq, dnf_basecmd, conf_file, en_repos, dis_repos):

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
                res['msg'] += "No Package file matching '%s' found on system" % spec
                module.fail_json(**res)

            nvra = local_nvra(module, spec)
            # look for them in the rpmdb
            if is_installed(module, repoq, nvra, conf_file, en_repos=en_repos, dis_repos=dis_repos):
                # if they are there, skip it
                continue
            pkg = spec

        # URL
        elif '://' in spec:
            pkg = spec

        #groups :(
        elif  spec.startswith('@'):
            # complete wild ass guess b/c it's a group
            pkg = spec

        # range requires or file-requires or pkgname :(
        else:
            # most common case is the pkg is already installed and done
            # short circuit all the bs - and search for it as a pkg in is_installed
            # if you find it then we're done
            if not set(['*','?']).intersection(set(spec)):
                pkgs = is_installed(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos, is_pkg=True)
                if pkgs:
                    res['results'].append('%s providing %s is already installed' % (pkgs[0], spec))
                    continue
            
            # look up what pkgs provide this
            pkglist = what_provides(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos)
            if not pkglist:
                res['msg'] += "No Package matching '%s' found available, installed or updated" % spec
                module.fail_json(**res)

            # if any of the packages are involved in a transaction, fail now
            # so that we don't hang on the dnf operation later
            conflicts = transaction_exists(pkglist)
            if len(conflicts) > 0:
                res['msg'] += "The following packages have pending transactions: %s" % ", ".join(conflicts)
                module.fail_json(**res)

            # if any of them are installed
            # then nothing to do

            found = False
            for this in pkglist:
                if is_installed(module, repoq, this, conf_file, en_repos=en_repos, dis_repos=dis_repos, is_pkg=True):
                    found = True
                    res['results'].append('%s providing %s is already installed' % (this, spec))
                    break

            # if the version of the pkg you have installed is not in ANY repo, but there are
            # other versions in the repos (both higher and lower) then the previous checks won't work.
            # so we check one more time. This really only works for pkgname - not for file provides or virt provides
            # but virt provides should be all caught in what_provides on its own.
            # highly irritating
            if not found:
                if is_installed(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos):
                    found = True
                    res['results'].append('package providing %s is already installed' % (spec))
                    
            if found:
                continue

            # if not - then pass in the spec as what to install
            # we could get here if nothing provides it but that's not
            # the error we're catching here
            pkg = spec

        cmd = dnf_basecmd + ['install', pkg]

        if module.check_mode:
            module.exit_json(changed=True)

        changed = True

        rc, out, err = module.run_command(cmd)

        # Fail on invalid urls:
        if (rc == 1 and '://' in spec and ('No package %s available.' % spec in out or 'Cannot open: %s. Skipping.' % spec in err)):
            err = 'Package at %s could not be installed' % spec
            module.fail_json(changed=False,msg=err,rc=1)
        elif (rc != 0 and 'Nothing to do' in err) or 'Nothing to do' in out:
            # avoid failing in the 'Nothing To Do' case
            # this may happen with an URL spec.
            # for an already installed group,
            # we get rc = 0 and 'Nothing to do' in out, not in err.
            rc = 0
            err = ''
            out = '%s: Nothing to do' % spec
            changed = False

        res['rc'] += rc
        res['results'].append(out)
        res['msg'] += err

        # FIXME - if we did an install - go and check the rpmdb to see if it actually installed
        # look for the pkg in rpmdb
        # look for the pkg via obsoletes

        # accumulate any changes
        res['changed'] |= changed

    module.exit_json(**res)


def remove(module, items, repoq, dnf_basecmd, conf_file, en_repos, dis_repos):

    res = {}
    res['results'] = []
    res['msg'] = ''
    res['changed'] = False
    res['rc'] = 0

    for pkg in items:
        is_group = False
        # group remove - this is doom on a stick
        if pkg.startswith('@'):
            is_group = True
        else:
            if not is_installed(module, repoq, pkg, conf_file, en_repos=en_repos, dis_repos=dis_repos):
                res['results'].append('%s is not installed' % pkg)
                continue

        # run an actual dnf transaction
        cmd = dnf_basecmd + ["remove", pkg]

        if module.check_mode:
            module.exit_json(changed=True)

        rc, out, err = module.run_command(cmd)

        res['rc'] += rc
        res['results'].append(out)
        res['msg'] += err

        # compile the results into one batch. If anything is changed 
        # then mark changed
        # at the end - if we've end up failed then fail out of the rest
        # of the process

        # at this point we should check to see if the pkg is no longer present
        
        if not is_group: # we can't sensibly check for a group being uninstalled reliably
            # look to see if the pkg shows up from is_installed. If it doesn't
            if not is_installed(module, repoq, pkg, conf_file, en_repos=en_repos, dis_repos=dis_repos):
                res['changed'] = True
            else:
                module.fail_json(**res)

        if rc != 0:
            module.fail_json(**res)
            
    module.exit_json(**res)

def latest(module, items, repoq, dnf_basecmd, conf_file, en_repos, dis_repos):

    res = {}
    res['results'] = []
    res['msg'] = ''
    res['changed'] = False
    res['rc'] = 0

    for spec in items:

        pkg = None
        basecmd = 'update'
        cmd = ''
        # groups, again
        if spec.startswith('@'):
            pkg = spec
        
        elif spec == '*': #update all
            # use check-update to see if there is any need
            rc,out,err = module.run_command(dnf_basecmd + ['check-update'])
            if rc == 100:
                cmd = dnf_basecmd + [basecmd]
            else:
                res['results'].append('All packages up to date')
                continue
        
        # dep/pkgname  - find it
        else:
            if is_installed(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos):
                basecmd = 'update'
            else:
                basecmd = 'install'

            pkglist = what_provides(module, repoq, spec, conf_file, en_repos=en_repos, dis_repos=dis_repos)
            if not pkglist:
                res['msg'] += "No Package matching '%s' found available, installed or updated" % spec
                module.fail_json(**res)
            
            nothing_to_do = True
            for this in pkglist:
                if basecmd == 'install' and is_available(module, repoq, this, conf_file, en_repos=en_repos, dis_repos=dis_repos):
                    nothing_to_do = False
                    break
                    
                if basecmd == 'update' and is_update(module, repoq, this, conf_file, en_repos=en_repos, dis_repos=en_repos):
                    nothing_to_do = False
                    break
                    
            if nothing_to_do:
                res['results'].append("All packages providing %s are up to date" % spec)
                continue

            # if any of the packages are involved in a transaction, fail now
            # so that we don't hang on the dnf operation later
            conflicts = transaction_exists(pkglist)
            if len(conflicts) > 0:
                res['msg'] += "The following packages have pending transactions: %s" % ", ".join(conflicts)
                module.fail_json(**res)

            pkg = spec
        if not cmd:
            cmd = dnf_basecmd + [basecmd, pkg]

        if module.check_mode:
            return module.exit_json(changed=True)

        rc, out, err = module.run_command(cmd)

        res['rc'] += rc
        res['results'].append(out)
        res['msg'] += err

        # FIXME if it is - update it and check to see if it applied
        # check to see if there is no longer an update available for the pkgspec

        if rc:
            res['failed'] = True
        else:
            res['changed'] = True

    module.exit_json(**res)

def ensure(module, state, pkgspec, conf_file, enablerepo, disablerepo,
           disable_gpg_check):

    # take multiple args comma separated
    items = pkgspec.split(',')

    # need debug level 2 to get 'Nothing to do' for groupinstall.
    dnf_basecmd = [dnfbin, '-d', '2', '-y']

        
    if not repoquery:
        repoq = None
    else:
        repoq = [repoquery, '--show-duplicates', '--plugins', '--quiet', '-q']

    if conf_file and os.path.exists(conf_file):
        dnf_basecmd += ['-c', conf_file]
        if repoq:
            repoq += ['-c', conf_file]

    dis_repos =[]
    en_repos = []
    if disablerepo:
        dis_repos = disablerepo.split(',')
    if enablerepo:
        en_repos = enablerepo.split(',')
           
    for repoid in dis_repos:
        r_cmd = ['--disablerepo=%s' % repoid]
        dnf_basecmd.extend(r_cmd)

    for repoid in en_repos:
        r_cmd = ['--enablerepo=%s' % repoid]
        dnf_basecmd.extend(r_cmd)

    if state in ['installed', 'present', 'latest']:
        my = dnf_base(conf_file)
        try:
            for r in dis_repos:
                my.repos.disableRepo(r)

            current_repos = dnf.yum.config.RepoConf()
            for r in en_repos:
                try:
                    my.repos.enableRepo(r)
                    new_repos = my.repos.repos.keys()
                    for i in new_repos:
                        if not i in current_repos:
                            rid = my.repos.getRepo(i)
                            a = rid.repoXML.repoid
                    current_repos = new_repos
                except dnf.exceptions.Error, e:
                    module.fail_json(msg="Error setting/accessing repo %s: %s" % (r, e))
        except dnf.exceptions.Error, e:
            module.fail_json(msg="Error accessing repos: %s" % e)

    if state in ['installed', 'present']:
        if disable_gpg_check:
            dnf_basecmd.append('--nogpgcheck')
        install(module, items, repoq, dnf_basecmd, conf_file, en_repos, dis_repos)
    elif state in ['removed', 'absent']:
        remove(module, items, repoq, dnf_basecmd, conf_file, en_repos, dis_repos)
    elif state == 'latest':
        if disable_gpg_check:
            dnf_basecmd.append('--nogpgcheck')
        latest(module, items, repoq, dnf_basecmd, conf_file, en_repos, dis_repos)

    # should be caught by AnsibleModule argument_spec
    return dict(changed=False, failed=True, results='', errors='unexpected state')

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
        argument_spec = dict(
            name=dict(aliases=['pkg']),
            # removed==absent, installed==present, these are accepted as aliases
            state=dict(default='installed', choices=['absent','present','installed','removed','latest']),
            enablerepo=dict(),
            disablerepo=dict(),
            list=dict(),
            conf_file=dict(default=None),
            disable_gpg_check=dict(required=False, default="no", type='bool'),
            # this should not be needed, but exists as a failsafe
            install_repoquery=dict(required=False, default="yes", type='bool'),
        ),
        required_one_of = [['name','list']],
        mutually_exclusive = [['name','list']],
        supports_check_mode = True
    )

    # this should not be needed, but exists as a failsafe
    params = module.params
    if params['install_repoquery'] and not repoquery and not module.check_mode:
        install_dnf_utils(module)

    if not repoquery:
        module.fail_json(msg="repoquery is required to use this module at this time. Please install the yum-utils package.")
    if params['list']:
        results = dict(results=list_stuff(module, params['conf_file'], params['list']))
        module.exit_json(**results)

    else:
        pkg = params['name']
        state = params['state']
        enablerepo = params.get('enablerepo', '')
        disablerepo = params.get('disablerepo', '')
        disable_gpg_check = params['disable_gpg_check']
        res = ensure(module, state, pkg, params['conf_file'], enablerepo,
                     disablerepo, disable_gpg_check)
        module.fail_json(msg="we should never get here unless this all failed", **res)

# import module snippets
from ansible.module_utils.basic import *
main()

