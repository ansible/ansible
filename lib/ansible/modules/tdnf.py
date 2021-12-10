#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2021 VMware, Inc. All Rights Reserved.
#
# GNU General Public License v3.0+ (https://www.gnu.org/licenses/gpl-3.0.txt)
#

''' tdnf ansible module for Photon OS  '''

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: tdnf
short_description: Tiny DNF package manager
description:
  - Manages rpm packages for VMware Photon OS.
version_added: "2.13"
options:
  name:
    description:
      - A package name, like C(foo), or multiple packages, like C(foo, bar).
    aliases:
      - pkg
    type: list
    elements: str

  state:
    description:
      - Indicates the desired package(s) state.
      - C(present) ensures the package(s) is/are present.
      - C(absent) ensures the package(s) is/are absent.
      - C(latest) ensures the package(s) is/are present and the latest version(s).
    type: str
    default: present
    choices: ['present', 'installed', 'absent', 'removed', 'latest']

  update_cache:
    description:
      - Update repo metadata cache. Can be run with other steps or on it's own.
    type: bool
    default: 'no'

  upgrade:
    description:
      - Upgrade all installed packages to their latest version.
    type: bool
    default: 'no'

  enablerepo:
    description:
      - I(Repoid) of repositories to enable for the install/update operation.
        When specifying multiple repos, separate them with a ",".
    type: list
    elements: str

  disablerepo:
    description:
      - I(Repoid) of repositories to disable for the install/update operation.
        When specifying multiple repos, separate them with a ",".
    type: list
    elements: str

  conf_file:
    description:
      - The tdnf configuration file to use for the transaction.
    type: str

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
    type: str
    default: '/'

  security_severity:
    description:
      - Specifies the CVSS v3 score above which to install updates for packages
    type: str

  releasever:
    description:
      - Specifies an alternative release from which all packages will be
        installed.
    type: str

  exclude:
    description:
      - Package name(s) to exclude when state=present, or latest. This can be a
        list or a comma separated string.
    type: list
    elements: str

author:
  - Anish Swaminathan (@suezzelur) <anishs@vmware.com>
  - Shreenidhi Shedi (@sshedi) <sshedi@vmware.com>

notes:
  - '"name" and "upgrade" are mutually exclusive.'
  - When used with a `loop:` each package will be processed individually, it is much more efficient to pass the list directly to the `name` option.
'''

EXAMPLES = '''
# Update repositories and install "foo" package
- tdnf:
    name: foo
    update_cache: yes

# Update repositories and install "foo" and "bar" packages
- tdnf:
    name: foo,bar
    update_cache: yes

# Remove "foo" package
- tdnf:
    name: foo
    state: absent

# Remove "foo" and "bar" packages
- tdnf:
    name: foo,bar
    state: absent

# Install the package "foo"
- tdnf:
    name: foo
    state: present

# Install the packages "foo" and "bar"
- tdnf:
    name: foo,bar
    state: present

# Update repositories and update package "foo" to latest version
- tdnf:
    name: foo
    state: latest
    update_cache: yes

# Update repositories and update packages "foo" and "bar" to latest versions
- tdnf:
    name: foo,bar
    state: latest
    update_cache: yes

# Update all installed packages to the latest versions
- tdnf:
    upgrade: yes

# Update repositories as a separate step
- tdnf:
    update_cache: yes
'''

from ansible.module_utils.basic import AnsibleModule


def prep_tdnf_cmd(cmd, p_dict):
    ''' Prepare tdnf command based on given configs '''
    if p_dict['excludelist']:
        cmd = '%s --exclude %s' % (cmd, ','.join(p_dict['excludelist']))

    if p_dict['disable_gpg_check']:
        cmd = '%s --nogpgcheck' % cmd

    if p_dict['releasever']:
        cmd = '%s --releasever %s' % (cmd, p_dict['releasever'])

    if p_dict['conf_file']:
        cmd = '%s -c %s' % (cmd, p_dict['conf_file'])

    if p_dict['installroot'] != '/':
        cmd = '%s --installroot %s' % (cmd, p_dict['installroot'])

    for repo in p_dict['enablerepolist']:
        cmd = '%s --enablerepo=%s' % (cmd, repo)

    for repo in p_dict['disablerepolist']:
        cmd = '%s --disablerepo=%s' % (cmd, repo)

    if p_dict['security_severity']:
        cmd = '%s --sec-severity %s' % (cmd, p_dict['security_severity'])

    return cmd


def exec_cmd(module, params):
    '''
    Run the final command
    get_out is a special value from update_package_db
    if it's set, we just update the db cache and exit
    '''
    get_out = params.get('get_out', False)
    check_rc = params.get('check_rc', False)

    ret_val, stdout, stderr = module.run_command(params['cmd'], check_rc=check_rc)
    if ret_val:
        module.fail_json(msg=params['msg_f'], stdout=stdout, stderr=stderr)
    elif ('get_out' not in params and ret_val == 0) or get_out:
        module.exit_json(changed=True, msg=params['msg_s'], stdout=stdout, stderr=stderr)


def update_package_db(module, get_out, p_dict):
    ''' Update tdnf cache metadata  '''
    cmd = '%s makecache --refresh -q' % (p_dict['tdnf'])
    cmd = prep_tdnf_cmd(cmd, p_dict)

    params = {
        'cmd': cmd,
        'msg_s': 'Updated package db',
        'msg_f': 'Could not update package db',
        'get_out': get_out,
    }
    exec_cmd(module, params)


def upgrade_packages(module, p_dict):
    ''' Upgrade all packages  '''
    cmd = '%s upgrade -y' % (p_dict['tdnf'])
    cmd = prep_tdnf_cmd(cmd, p_dict)
    params = {
        'cmd': cmd,
        'msg_s': 'Upgraded packages',
        'msg_f': 'Failed to upgrade packages',
    }

    exec_cmd(module, params)


def install_packages(module, p_dict):
    ''' Install given packages '''
    packages = ' '.join(p_dict['pkglist'])
    cmd = '%s install -y' % (p_dict['tdnf'])
    cmd = prep_tdnf_cmd(cmd, p_dict)
    cmd = '%s %s' % (cmd, packages)

    params = {
        'cmd': cmd,
        'msg_s': 'Installed %s package(s)' % (packages),
        'msg_f': 'Failed to install %s' % (packages),
    }

    exec_cmd(module, params)


def remove_packages(module, p_dict):
    ''' Erase/Uninstall packages '''
    packages = ' '.join(p_dict['pkglist'])
    cmd = '%s erase -y %s' % (p_dict['tdnf'], packages)

    params = {
        'cmd': cmd,
        'msg_s': 'Removed %s package(s)' % (packages),
        'msg_f': 'Failed to remove %s package(s)' % (packages),
    }

    exec_cmd(module, params)


def convert_to_list(input_list):
    ''' Convert nested list into flat list '''
    flat_list = []

    for sublist in input_list:
        if not isinstance(sublist, list):
            flat_list.append(sublist)
            continue
        for item in sublist:
            flat_list.append(item)

    return flat_list


def main():
    ''' Trigger point function '''
    choices = ['present', 'installed', 'absent', 'removed', 'latest']
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=choices),
            name=dict(type='list', elements='str', aliases=['pkg']),
            update_cache=dict(default=False, type='bool'),
            upgrade=dict(default=False, type='bool'),
            enablerepo=dict(type='list', default=[], elements='str'),
            disablerepo=dict(type='list', default=[], elements='str'),
            disable_gpg_check=dict(type='bool', default=False),
            exclude=dict(type='list', default=[], elements='str'),
            installroot=dict(type='str', default='/'),
            security_severity=dict(type='str', default=None),
            releasever=dict(default=None),
            conf_file=dict(type='str', default=None),
        ),
        required_one_of=[['name', 'update_cache', 'upgrade', 'security_severity']],
        mutually_exclusive=[['name', 'upgrade'], ['name', 'security_severity']],
        supports_check_mode=True
    )

    # Set LANG env since we parse stdout
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    p_dict = module.params

    pkglist = convert_to_list(p_dict['name'])
    enablerepolist = convert_to_list(p_dict['enablerepo'])
    disablerepolist = convert_to_list(p_dict['disablerepo'])
    excludelist = convert_to_list(p_dict['exclude'])

    p_dict['tdnf'] = module.get_bin_path('tdnf', required=True)
    p_dict['pkglist'] = pkglist
    p_dict['enablerepolist'] = enablerepolist
    p_dict['disablerepolist'] = disablerepolist
    p_dict['excludelist'] = excludelist

    # normalize the state parameter
    if p_dict['state'] in ['present', 'installed', 'latest']:
        p_dict['state'] = 'present'

    if p_dict['state'] in ['absent', 'removed']:
        p_dict['state'] = 'absent'

    if p_dict['update_cache']:
        get_out = True
        for key in ['name', 'upgrade', 'security_severity']:
            if p_dict[key]:
                get_out = False
                break
        update_package_db(module, get_out, p_dict)

    if p_dict['upgrade']:
        upgrade_packages(module, p_dict)

    if p_dict['state'] == 'present':
        install_packages(module, p_dict)
    else:
        remove_packages(module, p_dict)


if __name__ == '__main__':
    main()
