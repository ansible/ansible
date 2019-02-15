# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard documentation fragment
    DOCUMENTATION = r'''
options:
  api_token:
    description:
      - Scaleway OAuth token.
    type: str
    aliases: [ oauth_token ]
  api_url:
    description:
      - Scaleway API URL.
    type: str
    default: https://api.scaleway.com
    aliases: [ base_url ]
  api_timeout:
    description:
      - HTTP timeout to Scaleway API in seconds.
    type: int
    default: 30
    aliases: [ timeout ]
  query_parameters:
    description:
    - List of parameters passed to the query string.
    type: dict
    default: {}
  validate_certs:
    description:
      - Validate SSL certs of the Scaleway API.
    type: bool
    default: yes
notes:
  - Also see the API documentation on U(https://developer.scaleway.com/)
  - If C(api_token) is not set within the module, the following
    environment variables can be used in decreasing order of precedence
    C(SCW_TOKEN), C(SCW_API_KEY), C(SCW_OAUTH_TOKEN) or C(SCW_API_TOKEN).
  - If one wants to use a different C(api_url) one can also set the C(SCW_API_URL)
    environment variable.
'''
