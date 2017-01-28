#!/usr/bin/python
# -*- coding: utf-8 -*-

#
#
# Anatoliy Ivashina <tivrobo@gmail.com>
#
#


# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_git
version_added: "2.0"
short_description: Deploy software (or files) from git checkouts
description:
    - Deploy software (or files) from git checkouts
    - SSH only
notes:
    - git for Windows need to be installed
    - SSH only
options:
  name:
    description:
      - address of the repository
    required: true
  dest:
    description:
      - destination folder
    required: true
  replace_dest:
    description:
      - replace destination folder if exists (recursive!)
    required: false
    default: false
  accept_hostkey:
    description:
      - add hostkey to known_hosts (before connecting to git)
    required: false
    default: false
author: Anatoliy Ivashina
'''

EXAMPLES = '''
  # git clone cool-thing.
  win_git:
    name: "git@github.com:tivrobo/Ansible-win_git.git"
    dest: "{{ ansible_env.TEMP }}\\Ansible-win_git"
    replace_dest: no
    accept_hostkey: yes

'''

ANSIBLE_METADATA = {
    'version': '0.1',
    'supported_by': 'unmaintained',
    'status': ['preview']
}
