#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a windows documentation stub.  Actual code lives in the .ps1
# file of the same name.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_mssql_login
version_added: '2.7'
short_description: adds or removes a MSSQL Server login
description:
    - Adds or removes MSSQL Server login
requirements:
  - Powershell module sqlps or Powershell module SqlServer on the remote host
options:
  server_instance:
    description:
      - Name of the sql server instance where the user has to be created
    default: computername
  server_instance_user:
    description:
      - Name of a sql user with sufficient privileges to create users
  server_instance_password:
    description:
      - Password for server_instance_user
  login_name:
    description:
      - Login name
    required: yes
  password:
    description:
      - Password of the new login
  default_database:
    description:
      - Name of the login default database
    default: master
  default_language:
    description:
      - The login default language
    default: us_english
  check_expiration:
    description:
      - Enforces password expiration
    type: bool
    default: 'yes'
  check_policy:
    description:
      - Enforces password policy
    type: bool
    default: 'yes'
  login_type:
    description: specifies what type of login has to be created (sql or windows)
    default: sql
    choices:
      - sql
      - windows
  state:
    description:
      - If C(present), it creates the new user
      - If C(absent), it removes the new user
    default: present
author:
  - Daniele Lazzari
notes:
  - If the user that runs ansible has the appropriate permission on the database server,
  - you don't need to set C(server_instance_user) and C(server_instance_password)
'''

EXAMPLES = r'''
---
# install SqlServer module on the target server if needed
- name: install SqlServer powershell module
  win_psmodule:
    name: SqlServer
    state: present
    allow_clobber: yes

- name: add a new login
  win_mssql_login:
    server_instance: 'MYSQLSERVER\MSSQLSERVER1'
    login_name: john_doe
    password: "{{ my_super_secret }}"
    state: present

- name: add a new login without password expiration enforcing
  win_mssql_login:
    server_instance: localhost
    server_instance_user: sa
    server_instance_password: "{{ sa }}"
    login_name: jane_doe
    password: "{{ my_super_secret }}"
    check_expiration: no
    state: present

- name: add a new windows login
  win_mssql_login:
    server_instance: MYSQLSERVER
    server_instance_user: sa
    server_instance_password: "{{ sa }}"
    login_name: 'MYSQLSERVER\jane_doe'
    login_type: windows
    state: present

- name: remove a sql login
  server_instance: 'myserver'
  login_name: john_doe
  state: absent
'''

RETURN = r'''
---
output:
  description: a message describing the task result
  returned: always
  sample: "login john_doe created"
  type: string
'''
