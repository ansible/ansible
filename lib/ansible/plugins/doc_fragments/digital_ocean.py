# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde (akasurde@redhat.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Parameters for DigitalOcean modules
    DOCUMENTATION = r'''
options:
  oauth_token:
    description:
     - DigitalOcean OAuth token.
     - "There are several other environment variables which can be used to provide this value."
     - "i.e., - 'DO_API_TOKEN', 'DO_API_KEY', 'DO_OAUTH_TOKEN' and 'OAUTH_TOKEN'"
    type: str
    aliases: [ api_token ]
  timeout:
    description:
    - The timeout in seconds used for polling DigitalOcean's API.
    type: int
    default: 30
  validate_certs:
    description:
    - If set to C(no), the SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    type: bool
    default: yes
'''
