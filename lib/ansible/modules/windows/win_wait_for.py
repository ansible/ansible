#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub, actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_wait_for
version_added: '2.4'
short_description: Waits for a condition before continuing
description:
- You can wait for a set amount of time C(timeout), this is the default if
  nothing is specified.
- Waiting for a port to become available is useful for when services are not
  immediately available after their init scripts return which is true of
  certain Java application servers.
- You can wait for a file to exist or not exist on the filesystem.
- This module can also be used to wait for a regex match string to be present
  in a file.
- You can wait for active connections to be closed before continuing on a
  local port.
options:
  connect_timeout:
    description:
    - The maximum number of seconds to wait for a connection to happen before
      closing and retrying.
    type: int
    default: 5
  delay:
    description:
    - The number of seconds to wait before starting to poll.
    type: int
  exclude_hosts:
    description:
    - The list of hosts or IPs to ignore when looking for active TCP
      connections when C(state=drained).
    type: list
  host:
    description:
    - A resolvable hostname or IP address to wait for.
    - If C(state=drained) then it will only check for connections on the IP
      specified, you can use '0.0.0.0' to use all host IPs.
    type: str
    default: '127.0.0.1'
  path:
    description:
    - The path to a file on the filesystem to check.
    - If C(state) is present or started then it will wait until the file
      exists.
    - If C(state) is absent then it will wait until the file does not exist.
    type: path
  port:
    description:
    - The port number to poll on C(host).
    type: int
  search_regex:
    description:
    - Can be used to match a string in a file.
    - If C(state) is present or started then it will wait until the regex
      matches.
    - If C(state) is absent then it will wait until the regex does not match.
    - Defaults to a multiline regex.
    type: str
  sleep:
    description:
    - Number of seconds to sleep between checks.
    type: int
    default: 1
  state:
    description:
    - When checking a port, C(started) will ensure the port is open, C(stopped)
      will check that is it closed and C(drained) will check for active
      connections.
    - When checking for a file or a search string C(present) or C(started) will
      ensure that the file or string is present, C(absent) will check that the
      file or search string is absent or removed.
    type: str
    choices: [ absent, drained, present, started, stopped ]
    default: started
  timeout:
    description:
    - The maximum number of seconds to wait for.
    type: int
    default: 300
seealso:
- module: wait_for
- module: win_wait_for_process
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Wait 300 seconds for port 8000 to become open on the host, don't start checking for 10 seconds
  win_wait_for:
    port: 8000
    delay: 10

- name: Wait 150 seconds for port 8000 of any IP to close active connections
  win_wait_for:
    host: 0.0.0.0
    port: 8000
    state: drained
    timeout: 150

- name: Wait for port 8000 of any IP to close active connection, ignoring certain hosts
  win_wait_for:
    host: 0.0.0.0
    port: 8000
    state: drained
    exclude_hosts: ['10.2.1.2', '10.2.1.3']

- name: Wait for file C:\temp\log.txt to exist before continuing
  win_wait_for:
    path: C:\temp\log.txt

- name: Wait until process complete is in the file before continuing
  win_wait_for:
    path: C:\temp\log.txt
    search_regex: process complete

- name: Wait until file is removed
  win_wait_for:
    path: C:\temp\log.txt
    state: absent

- name: Wait until port 1234 is offline but try every 10 seconds
  win_wait_for:
    port: 1234
    state: absent
    sleep: 10
'''

RETURN = r'''
wait_attempts:
  description: The number of attempts to poll the file or port before module
    finishes.
  returned: always
  type: int
  sample: 1
elapsed:
  description: The elapsed seconds between the start of poll and the end of the
    module. This includes the delay if the option is set.
  returned: always
  type: float
  sample: 2.1406487
'''
