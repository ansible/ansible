#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (c) 2018, Luc Stroobant (luc.stroobant@wdc.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import requests
    from requests.auth import HTTPBasicAuth
    requests.packages.urllib3.disable_warnings()
    requests_available = True
except ImportError:
    requests_available = False


def host_list(sat_url, user, password, org, verify, content_host=None):
    """Get a list of hosts from the satellite"""

    apicall = "{}/api/hosts".format(sat_url)
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
            params["search"] = "name={}".format(content_host)

    hosts = request(apicall, user, password, verify, True, params)

    return hosts


def request(url, user, password, verify=True, pagination=False, params={}):
    """"Execute a Satellite GET API request"""

    per_page = 200
    if params != {} or pagination:
        params["page"] = 1
        params["paged"] = True
        params["per_page"] = per_page

    items = []
    done = 0
    req = requests.get(url, timeout=60, verify=verify, params=params,
                       auth=HTTPBasicAuth(user, password))
    req.raise_for_status()
    response = req.json()

    done += per_page
    # pagination: check if we need more requests
    if pagination:
        items.extend(response["results"])
        if response["subtotal"]:
            while done < response["subtotal"]:
                    response = None
                    params["page"] += 1
                    req = requests.get(url, timeout=60, verify=verify, params=params,
                                       auth=HTTPBasicAuth(user, password))
                    req.raise_for_status()
                    response = req.json()
                    items.extend(response["results"])
                    done += per_page
    # not pagination: just return the response
    else:
        return response

    return items


def put(url, user, password, data, verify=True):
    """"Execute a Satellite PUT API request"""

    req = requests.put(url, timeout=60, verify=verify, json=data,
                       auth=HTTPBasicAuth(user, password))
    req.raise_for_status()

    return req.json()
