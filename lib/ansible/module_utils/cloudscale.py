# -*- coding: utf-8 -*-
#
# (c) 2017, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_text

API_URL = 'https://api.cloudscale.ch/v1/'


def cloudscale_argument_spec():
    return dict(
        api_token=dict(fallback=(env_fallback, ['CLOUDSCALE_API_TOKEN']),
                       no_log=True,
                       required=True),
        api_timeout=dict(default=30, type='int'),
    )


class AnsibleCloudscaleBase(object):

    def __init__(self, module):
        self._module = module
        self._auth_header = {'Authorization': 'Bearer %s' % module.params['api_token']}
        self._result = {
            'changed': False,
            'diff': dict(before=dict(), after=dict()),
        }

    def _get(self, api_call):
        resp, info = fetch_url(self._module, API_URL + api_call,
                               headers=self._auth_header,
                               timeout=self._module.params['api_timeout'])

        if info['status'] == 200:
            return self._module.from_json(to_text(resp.read(), errors='surrogate_or_strict'))
        elif info['status'] == 404:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with GET for '
                                       '"%s".' % api_call, fetch_url_info=info)

    def _post_or_patch(self, api_call, method, data):
        headers = self._auth_header.copy()
        if data is not None:
            # Sanitize data dictionary
            # Deepcopy: Duplicate the data object for iteration, because
            # iterating an object and changing it at the same time is insecure
            for k, v in deepcopy(data).items():
                if v is None:
                    del data[k]

            data = self._module.jsonify(data)
            headers['Content-type'] = 'application/json'

        resp, info = fetch_url(self._module,
                               API_URL + api_call,
                               headers=headers,
                               method=method,
                               data=data,
                               timeout=self._module.params['api_timeout'])

        if info['status'] in (200, 201):
            return self._module.from_json(to_text(resp.read(), errors='surrogate_or_strict'))
        elif info['status'] == 204:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with %s for '
                                       '"%s".' % (method, api_call), fetch_url_info=info)

    def _post(self, api_call, data=None):
        return self._post_or_patch(api_call, 'POST', data)

    def _patch(self, api_call, data=None):
        return self._post_or_patch(api_call, 'PATCH', data)

    def _delete(self, api_call):
        resp, info = fetch_url(self._module,
                               API_URL + api_call,
                               headers=self._auth_header,
                               method='DELETE',
                               timeout=self._module.params['api_timeout'])

        if info['status'] == 204:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with DELETE for '
                                       '"%s".' % api_call, fetch_url_info=info)

    def get_result(self, resource):
        if resource:
            for k, v in resource.items():
                self._result[k] = v
        return self._result
