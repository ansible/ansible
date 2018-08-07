# -*- coding: utf-8 -*-
# Copyright (C) 2018 Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = '''
options:
  oauth_token:
    description:
      - Scaleway OAuth token.
    aliases: ['api_token']
  timeout:
    description:
      - HTTP timeout to Scaleway API in seconds.
    default: 30
  validate_certs:
    description:
      - Validate SSL certs of the Scaleway API.
    default: yes
    type: bool
notes:
  - Also see the API documentation on U(https://developer.scaleway.com/)
  - If parameters are not set within the module, the following
    environment variables can be used in decreasing order of precedence
    C(SCW_TOKEN), C(SCW_API_KEY) or C(SCW_OAUTH_TOKEN).
'''
