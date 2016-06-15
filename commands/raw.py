# this is a virtual module that is entirely implemented server side

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

DOCUMENTATION = '''
---
module: raw
short_description: Executes a low-down and dirty SSH command
version_added: historical
options:
  free_form:
    description:
      - the raw module takes a free form command to run
    required: true
  executable:
    description:
      - change the shell used to execute the command. Should be an absolute path to the executable.
      - when using privilege escalation (C(become)), a default shell will be assigned if one is not provided
        as privilege escalation requires a shell.
    required: false
    version_added: "1.0"
description:
     - Executes a low-down and dirty SSH command, not going through the module
       subsystem. This is useful and should only be done in two cases. The
       first case is installing C(python-simplejson) on older (Python 2.4 and
       before) hosts that need it as a dependency to run modules, since nearly
       all core modules require it. Another is speaking to any devices such as
       routers that do not have any Python installed. In any other case, using
       the M(shell) or M(command) module is much more appropriate. Arguments
       given to M(raw) are run directly through the configured remote shell.
       Standard output, error output and return code are returned when
       available. There is no change handler support for this module.
     - This module does not require python on the remote system, much like
       the M(script) module.
notes:
    - "If using raw from a playbook, you may need to disable fact gathering
      using C(gather_facts: no) if you're using C(raw) to bootstrap python
      onto the machine."
    - If you want to execute a command securely and predictably, it may be
      better to use the M(command) or M(shell) modules instead.
    - the C(environment) keyword does not work with raw normally, it requires a shell
      which means it only works if C(executable) is set or using the module
      with privilege escalation (C(become)).
author:
    - Ansible Core Team
    - Michael DeHaan
'''

EXAMPLES = '''
# Bootstrap a legacy python 2.4 host
- raw: yum -y install python-simplejson

# Bootstrap a host without python2 installed
- raw: dnf install -y python2 python2-dnf libselinux-python

# Run a command that uses non-posix shell-isms (in this example /bin/sh
# doesn't handle redirection and wildcards together but bash does)
- raw: cat < /tmp/*txt
  args:
    executable: /bin/bash
'''
