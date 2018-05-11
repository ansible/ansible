#
# (c) 2016, Gregory Shulov <gregory.shulov@gmail.com>
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


class ModuleDocFragment(object):

    # Standard Infinibox documentation fragment
    DOCUMENTATION = '''
options:
  system:
    description:
      - Infinibox Hostname or IPv4 Address.
    required: true
  user:
    description:
      - Infinibox User username with sufficient priveledges ( see notes ).
    required: false
  password:
    description:
      - Infinibox User password.
    required: false
notes:
  - This module requires infinisdk python library
  - You must set INFINIBOX_USER and INFINIBOX_PASSWORD environment variables
    if user and password arguments are not passed to the module directly
  - Ansible uses the infinisdk configuration file C(~/.infinidat/infinisdk.ini) if no credentials are provided.
    See U(http://infinisdk.readthedocs.io/en/latest/getting_started.html)
requirements:
  - "python >= 2.7"
  - infinisdk
'''
