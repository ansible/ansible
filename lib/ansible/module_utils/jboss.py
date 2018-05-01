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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback


JBOSS_COMMON_ARGS = dict(
    username=dict(type='str', fallback=(env_fallback, ['JBOSS_MANAGEMENT_USER'])),
    password=dict(no_log=True, type='str', fallback=(env_fallback, ['JBOSS_MANAGEMENT_PASSWORD'])),
    host=dict(type='str', fallback=(env_fallback, ['JBOSS_MANAGEMENT_HOST'])),
    port=dict(type='int', fallback=(env_fallback, ['JBOSS_MANAGEMENT_PORT'])),
    timeout=dict(type='int', default=300),
    operation_headers=dict(type='dict', require=False))


class JBossAnsibleModule(AnsibleModule):

    def __init__(self, argument_spec, supports_check_mode):
        argument_spec.update(JBOSS_COMMON_ARGS)

        AnsibleModule.__init__(self, argument_spec=argument_spec, supports_check_mode=supports_check_mode)
