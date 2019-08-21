# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Luc Stroobant <luc.stroobant@wdc.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.urls import url_argument_spec, fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlencode
import json


def host_list(module, url, org, content_host=None):
    """Get a list of hosts from the satellite"""

    params = dict(
        organization_id=org,
        sort_by="name",
        sort_order="ASC"
    )

    if content_host:
        if '=' in content_host:
            # this is a already a search query, don't search for hostnames
            params["search"] = str(content_host)
        else:
            # treat other patterns as hostnames
            params["search"] = "name={0}".format(content_host)

    url = "{0}/api/hosts?{1}".format(url, urlencode(params))
    hosts = request(module, url, True, params)

    return hosts


def request(module, url, pagination=False, params=None):
    """"Execute a Satellite GET API request"""

    timeout = 120
    per_page = 200
    if not params:
        params = dict()
        req_url = url
    if params != {} or pagination:
        params.update(page=1, per_page=per_page, paged=True)
        req_url = '{0}?{1}'.format(url, urlencode(params))

    results = []
    done = 0
    resp, info = fetch_url(module, req_url, timeout=timeout)
    if info["status"] == 200:
        response = json.loads(resp.read())
    else:
        module.fail_json(msg="Bad api call return status", error=info)

    done += per_page
    # pagination: check if we need more requests
    if pagination:
        results.extend(response["results"])
        if response["subtotal"]:
            while done < response["subtotal"]:
                response = None
                params["page"] += 1
                req_url = '{0}?{1}'.format(url, urlencode(params))
                resp, info = fetch_url(module, req_url, timeout=timeout)
                if info["status"] == 200:
                    response = json.loads(resp.read())
                    results.extend(response["results"])
                    done += per_page
                else:
                    module.fail_json(msg="Bad api call return status", error=info)
    # not pagination: just return the response
    else:
        return response

    return results


def put(module, url, data):
    """"Execute a Satellite PUT API request"""

    resp, info = fetch_url(module,
                           url,
                           data=module.jsonify(data),
                           method='PUT',
                           headers={'Content-type': 'application/json'},
                           timeout=120)
    if info["status"] == 200:
        return json.loads(resp.read())
    else:
        module.fail_json(msg="Bad api call return status", error=info)
