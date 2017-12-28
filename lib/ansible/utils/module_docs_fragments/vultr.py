# -*- coding: utf-8 -*-
# Copyright (c) 2017 René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = '''
options:
  api_key:
    description:
      - API key of the Vultr API.
      - The ENV variable C(VULTR_API_KEY) is used as default, when defined.
  api_timeout:
    description:
      - HTTP timeout to Vultr API.
      - The ENV variable C(VULTR_API_TIMEOUT) is used as default, when defined.
    default: 10
  api_retries:
    description:
      - Amount of retries in case of the Vultr API retuns an HTTP 503 code.
      - The ENV variable C(VULTR_API_RETRIES) is used as default, when defined.
    default: 10
  api_account:
    description:
      - Name of the ini section in the C(vultr.ini) file.
      - The ENV variable C(VULTR_API_ACCOUNT) is used as default, when defined.
    default: default
  validate_certs:
    description:
      - Validate SSL certs of the Vultr API.
    default: true
    type: bool
requirements:
  - "python >= 2.6"
notes:
  - Also see the API documentation on https://www.vultr.com/api/.
'''
