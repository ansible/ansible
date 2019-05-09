# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Felix Fontein <felix@fontein.de>, 2019
#
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlencode

HETZNER_DEFAULT_ARGUMENT_SPEC = dict(
    hetzner_user=dict(type='str', required=True),
    hetzner_password=dict(type='str', required=True, no_log=True),
)

# The API endpoint is fixed.
BASE_URL = "https://robot-ws.your-server.de"


def fetch_url_json(module, url, method='GET', timeout=10, data=None, headers=None, accept_errors=None):
    '''
    Make general request to Hetzner's JSON robot API.
    '''
    module.params['url_username'] = module.params['hetzner_user']
    module.params['url_password'] = module.params['hetzner_password']
    resp, info = fetch_url(module, url, method=method, timeout=timeout, data=data, headers=headers)
    try:
        content = resp.read()
    except AttributeError:
        content = info.pop('body', None)

    if not content:
        module.fail_json(msg='Cannot retrieve content from {0}'.format(url))

    try:
        result = module.from_json(content.decode('utf8'))
        if 'error' in result:
            if accept_errors:
                if result['error']['code'] in accept_errors:
                    return result, result['error']['code']
            module.fail_json(msg='Request failed: {0} {1} ({2})'.format(
                result['error']['status'],
                result['error']['code'],
                result['error']['message']
            ))
        return result, None
    except ValueError:
        module.fail_json(msg='Cannot decode content retrieved from {0}'.format(url))


# #####################################################################################
# ## FAILOVER IP ######################################################################

def get_failover_record(module, ip):
    '''
    Get information record of failover IP.

    See https://robot.your-server.de/doc/webservice/en.html#get-failover-failover-ip
    '''
    url = "{0}/failover/{1}".format(BASE_URL, ip)
    result, error = fetch_url_json(module, url)
    if 'failover' not in result:
        module.fail_json(msg='Cannot interpret result: {0}'.format(result))
    return result['failover']


def get_failover(module, ip):
    '''
    Get current routing target of failover IP.

    The value ``None`` represents unrouted.

    See https://robot.your-server.de/doc/webservice/en.html#get-failover-failover-ip
    '''
    return get_failover_record(module, ip)['active_server_ip']


def set_failover(module, ip, value, timeout=180):
    '''
    Set current routing target of failover IP.

    Return a pair ``(value, changed)``. The value ``None`` for ``value`` represents unrouted.

    See https://robot.your-server.de/doc/webservice/en.html#post-failover-failover-ip
    and https://robot.your-server.de/doc/webservice/en.html#delete-failover-failover-ip
    '''
    url = "{0}/failover/{1}".format(BASE_URL, ip)
    if value is None:
        result, error = fetch_url_json(
            module,
            url,
            method='DELETE',
            timeout=timeout,
            accept_errors=['FAILOVER_ALREADY_ROUTED']
        )
    else:
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        data = dict(
            active_server_ip=value,
        )
        result, error = fetch_url_json(
            module,
            url,
            method='POST',
            timeout=timeout,
            data=urlencode(data),
            headers=headers,
            accept_errors=['FAILOVER_ALREADY_ROUTED']
        )
    if error is not None:
        return value, False
    else:
        return result['failover']['active_server_ip'], True


def get_failover_state(value):
    '''
    Create result dictionary for failover IP's value.

    The value ``None`` represents unrouted.
    '''
    return dict(
        value=value,
        state='routed' if value else 'unrouted'
    )
