# -*- coding: utf-8 -*-
# Copyright (C) 2018 Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = '''
options:
  api_token:
    description:
      - Scaleway OAuth token.
    aliases: ['oauth_token']
  api_url:
    description:
      - Scaleway API URL
    default: 'https://api.scaleway.com'
    aliases: ['base_url']
  api_timeout:
    description:
      - HTTP timeout to Scaleway API in seconds.
    default: 30
    aliases: ['timeout']
  validate_certs:
    description:
      - Validate SSL certs of the Scaleway API.
    default: yes
    type: bool
notes:
  - Also see the API documentation on U(https://developer.scaleway.com/)
  - If C(api_token) is not set within the module, the following
    environment variables can be used in decreasing order of precedence
    C(SCW_TOKEN), C(SCW_API_KEY), C(SCW_OAUTH_TOKEN) or C(SCW_API_TOKEN).
  - If one wants to use a different C(api_url) one can also set the C(SCW_API_URL)
    environment variable.
'''
