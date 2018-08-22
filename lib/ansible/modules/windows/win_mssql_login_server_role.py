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
module: win_mssql_login_server_role
version_added: '2.7'
short_description: adds or removes a server role to a sql login
description:
    - Adds or removes a server role to a sql login.
    - Refer to https://docs.microsoft.com/en-us/sql/relational-databases/security/authentication-access/server-level-roles?view=sql-server-2017
    - for more informations on how server roles work
requirements:
  - Powershell module sqlps or Powershell module SqlServer
options:
  server_instance:
    description:
      - Name of the sql server instance
    default: computername
  server_instance_user:
    description:
      - Name of a sql user with sufficient privileges
  server_instance_password:
    description:
      - Password for server_instance_user
  login_name:
    description:
      - SQL loging name
    required: yes
  server_role:
    description:
      - Name of the server role to add or remove
    required: yes
  state:
    description:
      - If C(present), adds a server role
      - If C(absent), removes a server role
    default: present
author:
  - Daniele Lazzari
notes:
  - If the user that runs ansible has the appropriate permission on the database server,
  - you don't need to set C(server_instance_user) and C(server_instance_password)
'''

EXAMPLES = r'''
---
- name: add a server role to a login
  win_mssql_login_server_role:
    server_instance: 'myserver\instance'
    login_name: john_doe
    server_role: setupadmin
    state: present

- name: remove a server role from a sql login
  win_mssql_login_server_role:
    server_instance: 'myserver\instance'
    server_instance_user: sysadminUser
    server_instance_password: "{{ sysadmin_password }}"
    login_name: jane_doe
    server_role: setupadmin
    state: absent

- name: add more than a server role
  win_mssql_login_server_role:
    server_instance: 'myserver\instance'
    login_name: jane_doe
    server_role: "{{ item }}"
    loop:
      - setupadmin
      - securityadmin

# working with win_mssql_login module

- name: add a new login
  win_mssql_login:
    server_instance: MYSQLSERVER
    login_name: john_doe
    password: "{{ my_super_secret }}"
    state: present

- name: add a server role to a login
  win_mssql_login_server_role:
    server_instance: MYSQLSERVER
    login_name: john_doe
    server_role: sysadmin
'''

RETURN = r'''
---
output:
  description: a message describing the task result
  returned: always
  sample: "role added"
  type: string
role:
  description: name of the server role
  returned: always
  sample: "setupadmin"
  type: string
'''
