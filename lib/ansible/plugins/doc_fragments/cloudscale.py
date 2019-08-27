# -*- coding: utf-8 -*-
# Copyright (c) 2019, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard cloudstack documentation fragment
    DOCUMENTATION = '''
options:
  api_token:
    description:
      - cloudscale.ch API token.
      - This can also be passed in the C(CLOUDSCALE_API_TOKEN) environment variable.
  api_timeout:
    description:
      - Timeout in seconds for calls to the cloudscale.ch API.
    default: 30
notes:
  - Instead of the api_token parameter the C(CLOUDSCALE_API_TOKEN) environment variable can be used.
  - All operations are performed using the cloudscale.ch public API v1.
  - "For details consult the full API documentation: U(https://www.cloudscale.ch/en/api/v1)."
  - A valid API token is required for all operations. You can create as many tokens as you like using the cloudscale.ch control panel at
    U(https://control.cloudscale.ch).
'''
