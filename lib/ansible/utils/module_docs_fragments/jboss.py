# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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


class ModuleDocFragment(object):
    DOCUMENTATION = '''
options:
    username:
      description:
        - JBoss Management User. This option can be omitted if the environment variable C(JBOSS_MANAGEMENT_USER) is set.
    password:
      description:
        - JBoss Management Password. This option can be omitted if the environment variable C(JBOSS_MANAGEMENT_PASSWORD) is set.
    host:
      description:
        - JBoss Management Host. This option can be omitted if the environment variable C(JBOSS_MANAGEMENT_HOST) is set.
    port:
      description:
        - JBoss Management Port. This option can be omitted if the environment variable C(JBOSS_MANAGEMENT_PORT) is set.
    timeout:
      description:
        - HTTP Request timeout.
      default: 300
    operation_headers:
      description:
        - Special headers that help control how the operation executes.
notes:
    - Requires jboss-py Python package on the host.
requirements:
    - jboss-py >= 1.0.0
'''
