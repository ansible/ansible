# Collect facts related to selinux
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.facts.collector import BaseFactCollector

try:
    from ansible.module_utils.compat import selinux
    HAVE_SELINUX = True
except ImportError:
    HAVE_SELINUX = False

SELINUX_MODE_DICT = {
    1: 'enforcing',
    0: 'permissive',
    -1: 'disabled'
}


class SelinuxFactCollector(BaseFactCollector):
    name = 'selinux'
    _fact_ids = set()

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}
        selinux_facts = {}

        # If selinux library is missing, only set the status and selinux_python_present since
        # there is no way to tell if SELinux is enabled or disabled on the system
        # without the library.
        if not HAVE_SELINUX:
            selinux_facts['status'] = 'Missing selinux Python library'
            facts_dict['selinux'] = selinux_facts
            facts_dict['selinux_python_present'] = False
            return facts_dict

        # Set a boolean for testing whether the Python library is present
        facts_dict['selinux_python_present'] = True

        if not selinux.is_selinux_enabled():
            selinux_facts['status'] = 'disabled'
        else:
            selinux_facts['status'] = 'enabled'

            try:
                selinux_facts['policyvers'] = selinux.security_policyvers()
            except (AttributeError, OSError):
                selinux_facts['policyvers'] = 'unknown'

            try:
                (rc, configmode) = selinux.selinux_getenforcemode()
                if rc == 0:
                    selinux_facts['config_mode'] = SELINUX_MODE_DICT.get(configmode, 'unknown')
                else:
                    selinux_facts['config_mode'] = 'unknown'
            except (AttributeError, OSError):
                selinux_facts['config_mode'] = 'unknown'

            try:
                mode = selinux.security_getenforce()
                selinux_facts['mode'] = SELINUX_MODE_DICT.get(mode, 'unknown')
            except (AttributeError, OSError):
                selinux_facts['mode'] = 'unknown'

            try:
                (rc, policytype) = selinux.selinux_getpolicytype()
                if rc == 0:
                    selinux_facts['type'] = policytype
                else:
                    selinux_facts['type'] = 'unknown'
            except (AttributeError, OSError):
                selinux_facts['type'] = 'unknown'

        facts_dict['selinux'] = selinux_facts
        return facts_dict
