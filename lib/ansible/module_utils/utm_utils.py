import json

from ansible.module_utils.urls import fetch_url


def lookup_entry(module, request_url):
    """
Lookup for existing entry
    :param module:
    :param request_url:
    :return:
    """
    response, info = fetch_url(module, request_url, method="GET", headers={"Accept": "application/json"})
    result = None
    if response is not None:
        results = json.loads(response.read())
        result = next(iter(filter(lambda d: d['name'] == module.params.get('name'), results)), None)
    return info, result


def clean_result(result):
    """
Will clean the result from irrelevant fields
    :param result:
    :return:
    """
    del result['utm_host']
    del result['utm_port']
    del result['utm_token']
    del result['utm_protocol']
    del result['validate_certs']
    del result['url_username']
    del result['url_password']
    del result['state']
    return result


def is_object_changed(keys, module, result):
    """
Check if my object is changed
    :param keys:
    :param module:
    :param result:
    :return:
    """
    for key in keys:
        if module.params.get(key) != result[key]:
            return True
    return False
