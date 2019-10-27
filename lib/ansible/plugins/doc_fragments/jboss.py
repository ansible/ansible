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
      type: str
      required: True
    password:
      description:
        - JBoss Management Password. This option can be omitted if the environment variable C(JBOSS_MANAGEMENT_PASSWORD) is set.
      type: str
      required: True
    host:
      description:
        - JBoss Management Host. This option can be omitted if the environment variable C(JBOSS_MANAGEMENT_HOST) is set.
      type: str
      default: localhost
    port:
      description:
        - JBoss Management Port. This option can be omitted if the environment variable C(JBOSS_MANAGEMENT_PORT) is set.
      type: int
      default: 9990
    timeout:
      description:
        - HTTP Request timeout.
      default: 300
      type: int
    operation_headers:
      description:
        - Special headers that help control how the operation executes.
      type: dict
seealso:
- name: WildFly Model Reference Documentation
  description: This site provides reference for the management model for the WildFly application server, 
               as well as other application servers in the same family such as JBoss EAP 6+, JBoss EAP7 & JBoss AS 7
  link: https://wildscribe.github.io/
'''
