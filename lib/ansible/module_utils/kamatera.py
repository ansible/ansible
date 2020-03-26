# Copyright: (c) 2020, Ori Hoch
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from ansible.module_utils.urls import open_url, urllib_error


def request(module, path, method='GET', request_data=None):
    url = module.params['api_url'].strip('/') + '/' + path.strip('/')
    if request_data:
        request_data = module.jsonify(request_data)
    headers = dict(
        AuthClientId=module.params['api_client_id'],
        AuthSecret=module.params['api_secret'],
        Accept='application/json'
    )
    headers['Content-Type'] = 'application/json'
    try:
        r = open_url(url, request_data, headers, method, timeout=module.params['wait_timeout_seconds'])
        is_error = r.status != 200
    except urllib_error.HTTPError as e:
        r = e
        is_error = True
    res_text = None
    try:
        res_text = r.read()
        data = module.from_json(res_text)
    except Exception as e:
        data = {'message': 'invalid response (' + str(e) + ')'}
        is_error = True
    if is_error:
        if 'message' in data:
            error_msg = data['message']
        elif res_text:
            error_msg = res_text
        else:
            error_msg = 'unexpected error'
        module.fail_json(msg=error_msg)
    else:
        return data
