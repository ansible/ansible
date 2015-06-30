# -*- coding: utf-8 -*-
# (c) 2015, Marc Abramowitz <msabramo@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

import os
import sys
import tempfile

from ansible.utils.display import Display


def role_apply(hosts, roles,
               show_playbook=False, options=None, display=None):
    if options is None:
        options = get_options()

    if display is None:
        display = Display()

    playbook_content = get_playbook_content(hosts, roles)
    if show_playbook:
        display.display(79 * '-')
        display.display(playbook_content)
        display.display(79 * '-')

    with tempfile.NamedTemporaryFile(suffix='.yml') as tmpf:
        tmpf.write(playbook_content)
        tmpf.flush()
        cmd = 'ansible-playbook {options_str} {playbook}'.format(
            options_str=' '.join(options),
            playbook=tmpf.name)
        display.display('Executing: {cmd}'.format(cmd=cmd))
        os.system(cmd)


def get_options():
    options = []
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            continue
        if arg.startswith('--r') or arg.startswith('-r'):
            continue
        options.append(arg)

    return options


def get_playbook_hosts(hosts):
    playbook_hosts = '\n'.join([
        '    - {host}'.format(host=host) for host in hosts])
    return playbook_hosts


def get_playbook_roles(roles):
    playbook_roles = '\n'.join([
        '    - {role}'.format(role=role) for role in roles])
    return playbook_roles


def get_playbook_content(hosts, roles):
    playbook_hosts = get_playbook_hosts(hosts)
    playbook_roles = get_playbook_roles(roles)
    playbook_content = """\
#!/usr/bin/env ansible-playbook
---
- hosts:
{playbook_hosts}
  roles:
{playbook_roles}
        """.format(
            playbook_hosts=playbook_hosts,
            playbook_roles=playbook_roles
        ).rstrip()
    return playbook_content


