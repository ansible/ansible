#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

# Written by Igor Gnatenko <i.gnatenko.brain@gmail.com>
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
version_added: historical
short_description: Manages packages with the I(dnf) package manager
description:
     - Installs, upgrade, removes, and lists packages and groups with the I(dnf) package manager.
options:
  name:
    description:
      - "Package name, or package specifier with version, like C(name-1.0). When using state=latest, this can be '*' which means run: dnf -y update. You can also pass a url or a local path to a rpm file."
    required: true
    version_added: "1.8"
    default: null
    aliases: []
  list:
    description:
      - Various (non-idempotent) commands for usage with C(/usr/bin/ansible) and I(not) playbooks. See examples.
    required: false
    version_added: "1.8"
    default: null
  state:
    description:
      - Whether to install (C(present), C(latest)), or remove (C(absent)) a package.
    required: false
    choices: [ "present", "latest", "absent" ]
    version_added: "1.8"
    default: "present"
  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    version_added: "1.8"
    default: null
    aliases: []
    
  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        These repos will not persist beyond the transaction.
        When specifying multiple repos, separate them with a ",".
    required: false
    version_added: "1.8"
    default: null
    aliases: []

  conf_file:
    description:
      - The remote dnf configuration file to use for the transaction.
    required: false
    version_added: "1.8"
    default: null
    aliases: []

  disable_gpg_check:
    description:
      - Whether to disable the GPG checking of signatures of packages being
        installed. Has an effect only if state is I(present) or I(latest).
    required: false
    version_added: "1.8"
    default: "no"
    choices: ["yes", "no"]
    aliases: []

notes: []
# informational: requirements for nodes
requirements: [ dnf ]
author: '"Igor Gnatenko" <i.gnatenko.brain@gmail.com>'
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

import syslog

def log(msg):
    syslog.openlog('ansible-dnf', 0, syslog.LOG_USER)
    syslog.syslog(syslog.LOG_NOTICE, msg)

def dnf_base(conf_file=None):
    my = dnf.Base()
    my.conf.debuglevel = 0
    if conf_file and os.path.exists(conf_file):
        my.conf.config_file_path = conf_file
        my.conf.read()
    my.read_all_repos()
    my.fill_sack()

    return my

def pkg_to_dict(pkg):
    """
    Args:
      pkg (hawkey.Package): The package
    """

    d = {
        'name': pkg.name,
        'arch': pkg.arch,
        'epoch': str(pkg.epoch),
        'release': pkg.release,
        'version': pkg.version,
        'repo': pkg.repoid,
        'nevra': str(pkg)
    }

    if pkg.installed:
        d['dnfstate'] = 'installed'
    else:
        d['dnfstate'] = 'available'

    return d

def list_stuff(module, conf_file, stuff):
    my = dnf_base(conf_file)

    if stuff == 'installed':
        return [pkg_to_dict(p) for p in my.sack.query().installed()]
    elif stuff == 'updates':
        return [pkg_to_dict(p) for p in  my.sack.query().upgrades()]
    elif stuff == 'available':
        return [pkg_to_dict(p) for p in my.sack.query().available()]
    elif stuff == 'repos':
        return [dict(repoid=repo.id, state='enabled') for repo in my.repos.iter_enabled()]
    else:
        return [pkg_to_dict(p) for p in dnf.subject.Subject(stuff).get_best_query(my.sack)]

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
            state=dict(default='installed', choices=['absent', 'present', 'installed', 'removed', 'latest']),
            enablerepo=dict(),
            disablerepo=dict(),
            list=dict(),
            conf_file=dict(default=None),
            disable_gpg_check=dict(required=False, default="no", type='bool'),
        ),
        required_one_of = [['name','list']],
        mutually_exclusive = [['name','list']],
        supports_check_mode = True
    )

    params = module.params

    if not repoquery:
        module.fail_json(msg="repoquery is required to use this module at this time. Please install the yum-utils package.")
    if params['list']:
        results = dict(results=list_stuff(module, params['conf_file'], params['list']))
        module.exit_json(**results)

    else:
        return
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

