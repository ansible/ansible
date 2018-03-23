# Copyright (c) 2018 CloudGenix Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os

from ansible.module_utils.six import string_types, binary_type, text_type

try:
    import cloudgenix

    HAS_CLOUDGENIX = True
except ImportError:
    cloudgenix = object()
    HAS_CLOUDGENIX = False

try:
    # Although this is to allow Python 3 the ability to use the custom comparison as a key, Python 2.7 also
    # uses this (and it works as expected). Python 2.6 will trigger the ImportError.
    # taken from /lib/ansible/module_utils/ec2.py
    from functools import cmp_to_key

    PY3_COMPARISON = True
except ImportError:
    PY3_COMPARISON = False

# try:
#     from __main__ import display
# except ImportError:
#     from ansible.utils.display import Display
#     display = Display()


def cloudgenix_common_arguments():
    return dict(
        auth_token=dict(aliases=['x_auth_token'], no_log=True),
        tenant_id=dict(type='str', required=False),
        controller=dict(type='str', required=False),
        ssl_verify=dict(type='bool', required=False, default=True),
        ignore_region=dict(type='bool', required=False, default=False)
    )


def setup_cloudgenix_connection(module=None, auth_token=None, controller=None, tenant_id=None, ssl_verify=None,
                                ignore_region=None, display=None):

    if module is not None:
        # Check module args, if not present fall back to args or env vars.
        auth_token_mod = module.params.get('auth_token')
        controller_mod = module.params.get('controller')
        tenant_id_mod = module.params.get('tenant_id')
        ssl_verify_mod = module.params.get('ssl_verify')
        ignore_region_mod = module.params.get('ignore_region')

        if auth_token_mod:
            auth_token = auth_token_mod
        if controller_mod:
            controller = controller_mod
        if tenant_id_mod:
            tenant_id = tenant_id_mod
        if ssl_verify_mod:
            ssl_verify = ssl_verify_mod
        if ignore_region_mod:
            ignore_region = ignore_region_mod

    if not auth_token:
        if 'X_AUTH_TOKEN' in os.environ:
            auth_token = os.environ['X_AUTH_TOKEN']

    if not controller:
        # can recreate controller if REGION
        if 'REGION' in os.environ:
            if 'ENV' in os.environ:
                controller = "https://api-" + string_types(os.environ.get('ENV')) + "." + \
                             string_types(os.environ.get('REGION')) + ".cloudgenix.com"
            else:
                controller = "https://api." + string_types(os.environ.get('REGION')) + ".cloudgenix.com"
        else:
            # use default API endpoint if all else fails.
            controller = "https://api.elcapitan.cloudgenix.com"

    # instantiate the SDK object
    cgx_session = cloudgenix.API(controller=controller, ssl_verify=ssl_verify)
    cgx_session.ignore_region = ignore_region
    cgx_session.add_headers({
        'X-Auth-Token': auth_token
    })

    if not tenant_id:
        if 'TENANT_ID' in os.environ:
            tenant_id = os.environ['TENANT_ID']
        else:
            # we need to get this from the API. If we have the auth_token, we're good.
            if auth_token:
                profile_response = cgx_session.get.profile()
                if profile_response.cgx_status:
                    tenant_id = profile_response.cgx_content.get('tenant_id', tenant_id)
                else:
                    # if we can log, please do.
                    if display:
                        display.vvvv('cloudgenix_util\n'
                                     '\tAUTH_TOKEN / GET Profile failed: {0}'.format(profile_response.cgx_content))
                    tenant_id = None

    cgx_session.tenant_id = tenant_id

    return auth_token, controller, tenant_id, cgx_session
