#
# (c) 2018, Sandeep Kasargod <sandeep@vexata.com>
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

    DOCUMENTATION = """
options:
    - See respective platform section for more details
requirements:
    - See respective platform section for more details
notes:
    - Ansible modules are available for Vexata VX100 arrays.
"""

    # Documentation fragment for Vexata VX100 series
    VX100 = '''
options:
  array:
    description:
      - Vexata VX100 array hostname or IPv4 Address.
    required: true
  user:
    description:
      - Vexata API user with administrative privileges.
    required: false
  password:
    description:
      - Vexata API user password.
    required: false

requirements:
  - Vexata VX100 storage array with VXOS >= v3.5.0 on storage array
  - "vexatapi >= 0.0.1"
  - "python >= 2.7"
  - VEXATA_USER and VEXATA_PASSWORD environment variables must be set if
    user and password arguments are not passed to the module directly.
'''
