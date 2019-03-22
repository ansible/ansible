#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Gordeev

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: apt_repo
short_description: Manage APT repositories via apt-repo
description:
  - Manages APT repositories using apt-repo tool.
  - See U(https://www.altlinux.org/Apt-repo) for details about apt-repo
notes:
    - This module works on ALT based distros.
    - Does NOT support checkmode, due to a limitation in apt-repo tool.
version_added: "2.8"
options:
  repo:
    description:
      - Name of the repository to add or remove.
    required: true
  state:
    description:
      - Indicates the desired repository state.
    choices: [ absent, present ]
    default: present
  remove_others:
    description:
      - Remove other then added repositories
      - Used if I(state=present)
    type: bool
    default: 'no'
  update:
    description:
      - Update the package database after changing repositories.
    type: bool
    default: 'no'
author:
- Mikhail Gordeev (@obirvalger)
'''

EXAMPLES = '''
- name: Remove all repositories
  apt_repo:
    repo: all
    state: absent

- name: Add repository `Sisysphus` and remove other repositories
  apt_repo:
    repo: Sisysphus
    state: present
    remove_others: yes

- name: Add local repository `/space/ALT/Sisyphus` and update package cache
  apt_repo:
    repo: copy:///space/ALT/Sisyphus
    state: present
    update: yes
'''

RETURN = ''' # '''

import os

from ansible.module_utils.basic import AnsibleModule

APT_REPO_PATH = "/usr/bin/apt-repo"


def apt_repo(module, *args):
    """run apt-repo with args and return its output"""
    # make args list to use in concatenation
    args = list(args)
    rc, out, err = module.run_command([APT_REPO_PATH] + args)

    if rc != 0:
        module.fail_json(msg="'%s' failed: %s" % (' '.join(['apt-repo'] + args), err))

    return out


def add_repo(module, repo):
    """add a repository"""
    apt_repo(module, 'add', repo)


def rm_repo(module, repo):
    """remove a repository"""
    apt_repo(module, 'rm', repo)


def set_repo(module, repo):
    """add a repository and remove other repositories"""
    # first add to validate repository
    apt_repo(module, 'add', repo)
    apt_repo(module, 'rm', 'all')
    apt_repo(module, 'add', repo)


def update(module):
    """update package cache"""
    apt_repo(module, 'update')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            remove_others=dict(type='bool', default=False),
            update=dict(type='bool', default=False),
        ),
    )

    if not os.path.exists(APT_REPO_PATH):
        module.fail_json(msg='cannot find /usr/bin/apt-repo')

    params = module.params
    repo = params['repo']
    state = params['state']
    old_repositories = apt_repo(module)

    if state == 'present':
        if params['remove_others']:
            set_repo(module, repo)
        else:
            add_repo(module, repo)
    elif state == 'absent':
        rm_repo(module, repo)

    if params['update']:
        update(module)

    new_repositories = apt_repo(module)
    changed = old_repositories != new_repositories
    module.exit_json(changed=changed, repo=repo, state=state)


if __name__ == '__main__':
    main()
