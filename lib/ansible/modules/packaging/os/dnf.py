#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Cristian van Ee <cristian at cvee.org>
# Copyright 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com>
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
        parity/compatibility with the YUM module.
    type: bool
    default: "yes"
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.dnf import DnfModuleUtil
from ansible.module_utils.yumdnf import yumdnf_argument_spec


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

    module_implementation = DnfModuleUtil(module)
    try:
        module_implementation.run()
    except dnf.exceptions.RepoError as de:
        module.exit_json(msg="Failed to synchronize repodata: {}".format(de))

if __name__ == '__main__':
    main()
