# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard files for documentation fragment
    DOCUMENTATION = '''
notes:
- More information about the Meraki API can be found at U(https://dashboard.meraki.com/api_docs).
- Some of the options are likely only used for developers within Meraki
options:
    auth_key:
        description:
        - Authentication key provided by the dashboard. Required if environmental variable MERAKI_KEY is not set.
    host:
        description:
        - Hostname for Meraki dashboard
        - Only useful for internal Meraki developers
        type: string
        default: 'api.meraki.com'
    use_proxy:
        description:
        - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
        type: bool
    use_https:
        description:
        - If C(no), it will use HTTP. Otherwise it will use HTTPS.
        - Only useful for internal Meraki developers
        type: bool
        default: 'yes'
    output_level:
        description:
        - Set amount of debug output during module execution
        choices: ['normal', 'debug']
        default: 'normal'
    timeout:
        description:
        - Time to timeout for HTTP requests.
        type: int
        default: 30
    validate_certs:
        description:
        - Whether to validate HTTP certificates.
        type: bool
        default: 'yes'
    org_name:
        description:
        - Name of organization.
        aliases: [ organization ]
    org_id:
        description:
        - ID of organization.
'''
