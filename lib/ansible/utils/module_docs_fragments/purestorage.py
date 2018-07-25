#
# (c) 2017,  Simon Dodsley <simon@purestorage.com>
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

    # Standard Pure Storage documentation fragment
    DOCUMENTATION = '''
options:
  - See seperate platform section for more details
requirements:
  - See seperate platform section for more details
notes:
  - Ansible modules are available for the following Pure Storage products: FlashArray, FlashBlade
'''

    # Documentation fragment for FlashBlade
    FB = '''
options:
  fb_url:
    description:
      - FlashBlade management IP address or Hostname.
  api_token:
    description:
      - FlashBlade API token for admin privilaed user.
notes:
  - This module requires the ```purity_fb``` python library
  - You must set PUREFB_URL and PUREFB_API environment variables
    if fb_url and api_token arguments are not passed to the module directly
requirements:
  - "python >= 2.7"
  - "purity_fb >= 1.1"
'''

    # Documentation fragment for FlashArray
    FA = '''
options:
  fa_url:
    description:
      - FlashArray management IPv4 address or Hostname.
    required: true
  api_token:
    description:
      - FlashArray API token for admin privilaged user.
    required: true
notes:
  - This module requires purestorage python library
  - You must set C(PUREFA_URL) and C(PUREFA_API) environment variables
    if I(url) and I(api_token) arguments are not passed to the module directly
requirements:
  - "python >= 2.7"
  - purestorage
'''
