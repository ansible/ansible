#!/usr/bin/python
# -*- coding: utf-8 -*-

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

# Copyright: (c) 2018, Anatoliy Ivashina <tivrobo@gmail.com>, Pablo Estigarribia <pablodav@gmail.com>,
# Michael Hay <project.hay@gmail.com>, Ripon Banik <ripon.banik@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_git
author:
  - Anatoliy Ivashina (@thetiv)
  - Pablo Estigarribia (@pestigarribia)
  - Michael Hay (@mhay)
  - Ripon Banik (@riponbanik)
version_added: "2.8"
short_description: Deploy software (or files) from git checkouts.
description:
    - Deploy software (or files) from git checkouts.
options:
  repo:
    description:
        - git, SSH, or HTTP(S) protocol address of the git repository.
    required: true
    aliases: [ name ]
  dest:
    description:
        - The path of where the repository should be checked out. If
          not specified creates the direcctory under user profile folder.
    required: false
  version:
    description:
        - What version of the repository to check out.  This can be
          the literal string C(HEAD), a branch name, a tag name.
          It can also be a I(SHA-1) hash, in which case C(refspec) needs
          to be specified if the given revision is not already available.
    default: "HEAD"
  remote:
    description:
        - Name of the remote.
    default: "origin"
  replace_dest:
    description:
      - replace destination folder if exists (recursive!)
    type: bool
    default: no
  accept_hostkey:
    description:
      - add hostkey to known_hosts (before connecting to git)
    type: bool
    default: yes
  clone:
      description:
          - If C(no), do not clone the repository if it does not exist locally
      type: bool
      default: 'yes'
  update:
    description:
      - do we want to update the repo (use git pull origin branch)
    type: bool
    default: no
  depth:
    description:
        - Create a shallow clone with a history truncated to the specified
          number or revisions. The minimum possible value is C(1), otherwise
          ignored. Needs I(git>=2.19.0) to work correctly.
  key_file:
        description:
            - Specify an optional private key file path, on the target host, to use for the checkout.
requirements:
    - git>=2.19.0
notes:
    - git for Windows need to be installed.
    - "If the task seems to be hanging for ssh, first verify remote host is in C(known_hosts).
       and id_rsa is correct under user profile; Re-Run the task"
'''

EXAMPLES = r'''
# Example git clone using https
- name: git clone using https
  win_git:
    repo: "https://github.com/githubtraining/hellogitworld"
    dest: "{{ ansible_env.TEMP }}\\hellogitworld"

# Example git clone using specific version
- name: git clone using specific version
  win_git:
    repo: 'https://foosball.example.org/path/to/repo.git'
    dest: "{{ ansible_env.TEMP }}\\hellogitworld"
    version: release-0.22

# Example git clone using ssh. Also clean up existing directory
- name: git clone using ssh
  win_git:
    repo: git@github.com:githubtraining/hellogitworld.git
    dest: c:\windows\temp\hellogitworld_ssh
    replace_dest: yes
    key_file: 'c:\windows\temp\id_rsa'

# Example git clone using git protocol. Update if the folder already cloned
- name: git clone using git protocol
  win_git:
      repo: git://github.com/githubtraining/hellogitworld.git
      dest: c:\windows\temp\hellogitworld_git
      update: yes
'''

RETURN = r'''
dest:
  description: The repo path
  returned: always
  type: str
  sample: /tmp/hellogitworld
method:
  description: git method used
  returned: always
  type: str
  sample: pull
branch_status:
  description: branch name
  returned: always
  type: str
  sample: master
return_code:
  description: return code of running git command
  returned: always
  type: int
  sample: 0
git_opts:
  description: git command options
  returned: always
  type: str
  sample:  "--no-pager clone"
git_output:
  description: raw git output
  returned: always
  type: str
  sample: error occured while cloning
status:
  description: success or error message
  returned: always
  type: str
  sample: Successfuly updated
'''
