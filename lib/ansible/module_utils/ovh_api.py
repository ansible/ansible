# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Loïc Latreille (@psykotox)
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import time

try:
    import ovh
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def ovh_argument_spec():
    return dict(
        endpoint=dict(required=True),
        application_key=dict(required=True, no_log=True),
        application_secret=dict(required=True, no_log=True),
        consumer_key=dict(required=True, no_log=True)
    )


def ovh_connect_to_api(module):
    if not HAS_OVH:
        module.fail_json(msg='ovh python module is required '
                             'to run this module')

    try:
        ovhClient = ovh.Client(
            endpoint=module.params.get('endpoint'),
            application_key=module.params.get('application_key'),
            application_secret=module.params.get('application_secret'),
            consumer_key=module.params.get('consumer_key')
        )
    except ovh.APIError as apiError:
        module.fail_json(
            msg='Unable to connect to the OVH api, check application key, '
                'secret key, consumer key and parameters. '
                'Error returned by OVH api was : {0}'.format(apiError))

    return ovhClient
