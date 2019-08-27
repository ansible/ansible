# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ingate Systems AB
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    DOCUMENTATION = r'''
options:
  client:
    description:
      - A dict object containing connection details.
    suboptions:
      version:
        description:
          - REST API version.
        type: str
        choices: [ v1 ]
        default: v1
      scheme:
        description:
          - Which HTTP protocol to use.
        type: str
        required: true
        choices: [ http, https ]
      address:
        description:
          - The hostname or IP address to the unit.
        type: str
        required: true
      username:
        description:
          - The username of the REST API user.
        type: str
        required: true
      password:
        description:
          - The password for the REST API user.
        type: str
        required: true
      port:
        description:
          - Which HTTP(S) port to connect to.
        type: int
      timeout:
        description:
          - The timeout (in seconds) for REST API requests.
        type: int
      validate_certs:
        description:
          - Verify the unit's HTTPS certificate.
        type: bool
        default: yes
        aliases: [ verify_ssl ]
notes:
  - This module requires that the Ingate Python SDK is installed on the
    host. To install the SDK use the pip command from your shell
    C(pip install ingatesdk).
requirements:
  - ingatesdk >= 1.0.6
'''
