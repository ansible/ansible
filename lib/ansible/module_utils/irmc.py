
# FUJITSU LIMITED
# Copyright 2018 FUJITSU LIMITED
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division)
__metaclass__ = type

import traceback
import json

from ansible.module_utils.urls import fetch_url


def irmc_redfish_get(module, uri):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    url = "https://{0}/{1}".format(module.params['irmc_url'], uri)

    msg = "OK"
    try:
        module.params['url_username'] = module.params['irmc_username']
        module.params['url_password'] = module.params['irmc_password']
        data, info = fetch_url(module, method="GET", url=url, headers=headers)

        status = info["status"]
        if status != 200:
            try:
                msg = "GET request was not successful ({0}): status {1}, '{2}'". \
                      format(url, status, info["msg"])
            except Exception:
                msg = "GET request was not successful ({0}), status {1}.".format(url, status)
        else:
            data = json.loads(data.read())

    except Exception as e:
        status = 99
        data = traceback.format_exc()
        msg = "GET request encountered exception ({0}): {1}".format(url, str(e))

    return status, data, msg


def irmc_redfish_patch(module, uri, body, etag):
    etag = str(etag)
    if not etag.isdigit():
        msg = "etag is no number: {0}".format(etag)
        data = msg
        return 97, data, msg

    if body != "":
        try:
            json.loads(body)
        except ValueError as e:
            data = traceback.format_exc()
            msg = "PATCH request got invalid JSON body: {0}".format(body)
            return 98, data, msg

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "If-Match": etag
    }
    url = "https://{0}/{1}".format(module.params['irmc_url'], uri)

    msg = "OK"
    try:
        module.params['url_username'] = module.params['irmc_username']
        module.params['url_password'] = module.params['irmc_password']
        data, info = fetch_url(module, method="GET", url=url, headers=headers, data=body)

        status = info["status"]
        if status != 200:
            try:
                msg = "PATCH request was not successful ({0}): status {1}, '{2}'". \
                      format(url, status, info["msg"])
            except Exception:
                msg = "PATCH request was not successful ({0}), status {1}.".format(url, status)
        else:
            data = data.read()

    except Exception as e:
        status = 99
        data = traceback.format_exc()
        msg = "PATCH request encountered exception ({0}): {1}".format(url, str(e))

    return status, data, msg


def get_irmc_json(jsondata, keys):
    if isinstance(keys, list):
        jsonkey = " ".join(keys)
    else:
        jsonkey = keys
        keys = [keys]

    keylen = len(keys)
    try:
        if keylen == 1:
            data = jsondata[keys[0]]
        elif keylen == 2:
            data = jsondata[keys[0]][keys[1]]
        elif keylen == 3:
            data = jsondata[keys[0]][keys[1]][keys[2]]
        elif keylen == 4:
            data = jsondata[keys[0]][keys[1]][keys[2]][keys[3]]
        elif keylen == 5:
            data = jsondata[keys[0]][keys[1]][keys[2]][keys[3]][keys[4]]
        elif keylen == 6:
            data = jsondata[keys[0]][keys[1]][keys[2]][keys[3]][keys[4]][keys[5]]
        else:
            data = "Key too long ({0} levels): '{1}'".format(keylen, jsonkey)
    except Exception:
        data = "Key does not exist: '{0}'".format(jsonkey)

    return data
