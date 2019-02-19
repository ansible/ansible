# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  api_url:
    description:
      - The resolvable endpoint for the API
    type: str
  api_username:
    description:
      - The username to use for authentication against the API
    type: str
  api_password:
    description:
      - The password to use for authentication against the API
    type: str
  validate_certs:
    description:
      - Whether or not to validate SSL certs when supplying a https endpoint.
    type: bool
    default: yes
'''
