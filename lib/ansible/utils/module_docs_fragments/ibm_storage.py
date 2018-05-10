#
# Copyright (C) 2018 IBM CORPORATION
# Author(s): Tzur Eliyahu <tzure@il.ibm.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


class ModuleDocFragment(object):

    # ibm_storage documentation fragment
    DOCUMENTATION = '''
options:
    username:
        description:
            - Management user on the spectrum accelerate storage system.
        required: True
    password:
        description:
            - Password for username on the spectrum accelerate storage system.
        required: True
    endpoints:
        description:
            - The hostname or management IP of
                Spectrum Accelerate storage system.
        required: True
notes:
  - This module requires pyxcli python library.
      Use 'pip install pyxcli' in order to get pyxcli.
requirements:
  - "python >= 2.7"
  - pyxcli
'''
