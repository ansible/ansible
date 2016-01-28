#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Paul Durivage <paul.durivage@rackspace.com>, and others
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_get_url
version_added: "1.7"
short_description: Fetches a file from a given URL
description:
 - Fetches a file from a URL and saves to locally
author:
    - "Paul Durivage (@angstwad)"
    - "Takeshi Kuramochi (tksarah)"
options:
  url:
    description:
      - The full URL of a file to download
    required: true
    default: null
  dest:
    description:
      - The absolute path of the location to save the file at the URL. Be sure
        to include a filename and extension as appropriate.
    required: true
    default: null
  force:
    description:
      - If C(yes), will always download the file.  If C(no), will only
        download the file if it does not exist or the remote file has been
        modified more recently than the local file.
    version_added: "2.0"
    required: false
    choices: [ "yes", "no" ]
    default: yes
  username:
    description:
      - Basic authentication username
    required: false
    default: null
  password:
    description:
      - Basic authentication password
    required: false
    default: null
  skip_certificate_validation:
    description:
      - Skip SSL certificate validation if true
    required: false
    default: false
  proxy_url:
    description:
      - The full URL of the proxy server to download through.
    version_added: "2.0"
    required: false
  proxy_username:
    description:
      - Proxy authentication username
    version_added: "2.0"
    required: false
  proxy_password:
    description:
      - Proxy authentication password
    version_added: "2.0"
    required: false
'''

EXAMPLES = '''
# Downloading a JPEG and saving it to a file with the ansible command.
# Note the "dest" is quoted rather instead of escaping the backslashes
$ ansible -i hosts -c winrm -m win_get_url -a "url=http://www.example.com/earthrise.jpg dest='C:\Users\Administrator\earthrise.jpg'" all

# Playbook example
- name: Download earthrise.jpg to 'C:\Users\RandomUser\earthrise.jpg'
  win_get_url:
    url: 'http://www.example.com/earthrise.jpg'
    dest: 'C:\Users\RandomUser\earthrise.jpg'

- name: Download earthrise.jpg to 'C:\Users\RandomUser\earthrise.jpg' only if modified
  win_get_url:
    url: 'http://www.example.com/earthrise.jpg'
    dest: 'C:\Users\RandomUser\earthrise.jpg'
    force: no

- name: Download earthrise.jpg to 'C:\Users\RandomUser\earthrise.jpg' through a proxy server.
  win_get_url:
    url: 'http://www.example.com/earthrise.jpg'
    dest: 'C:\Users\RandomUser\earthrise.jpg'
    proxy_url: 'http://10.0.0.1:8080'
    proxy_username: 'username'
    proxy_password: 'password'
'''
