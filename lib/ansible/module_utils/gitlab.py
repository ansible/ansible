# -*- coding: utf-8 -*-

# (c) 2018, Marcus Watkins <marwatk@marcuswatkins.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

from ansible.module_utils.urls import fetch_url

try:
    from urllib import quote_plus  # Python 2.X
except ImportError:
    from urllib.parse import quote_plus  # Python 3+


def request(module, api_url, project, path, access_token, private_token, rawdata='', method='GET'):
    url = "%s/v4/projects/%s%s" % (api_url, quote_plus(project), path)
    headers = {}
    if access_token:
        headers['Authorization'] = "Bearer %s" % access_token
    else:
        headers['Private-Token'] = private_token

    headers['Accept'] = "application/json"
    headers['Content-Type'] = "application/json"

    response, info = fetch_url(module=module, url=url, headers=headers, data=rawdata, method=method)
    status = info['status']
    content = ""
    if response:
        content = response.read()
    if status == 204:
        return True, content
    elif status == 200 or status == 201:
        return True, json.loads(content)
    else:
        return False, str(status) + ": " + content
