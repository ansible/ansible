import json

from ansible.module_utils.urls import fetch_url


class UTM:

    def __init__(self, module, endpoint, important_keys):
        """
        Initialize UTM Class
        :param module: The ansible module
        :param endpoint: The corresponing endpoint to the module
        :param important_keys: The keys of the object to check for changes
        """
        self.module = module
        self.request_url = module.params.get('utm_protocol') + "://" + module.params.get('utm_host') + ":" + str(
            module.params.get('utm_port')) + "/api/objects/" + endpoint + "/"

        """
        The important_keys will be checked for changes to determine whether the object needs to be updated
        """
        self.important_keys = important_keys
        self.module.params['url_username'] = 'token'
        self.module.params['url_password'] = module.params.get('utm_token')
        if self.important_keys not in module.params.keys():
            self.module.fail_json(msg="The keys to check don't match the modules keys")

    def add(self):
        """
        adds or updates a host object on utm
        """
        is_changed = False
        info, result = self._lookup_entry(self.module, self.request_url)
        if info["status"] >= 400:
            self.module.fail_json(result=json.loads(info))
        else:
            if result is None:
                response, info = fetch_url(self.module, self.request_url, method="POST",
                                           headers={"Accept": "application/json", "Content-type": "application/json"},
                                           data=self.module.jsonify(self.module.params))
                if info["status"] >= 400:
                    self.module.fail_json(result=json.loads(info))
                is_changed = True
                result = self._clean_result(json.loads(response.read()))
            else:
                if self._is_object_changed(self.important_keys, self.module, result):
                    response, info = fetch_url(self.module, self.request_url + result['_ref'], method="PUT",
                                               headers={"Accept": "application/json",
                                                        "Content-type": "application/json"},
                                               data=self.module.jsonify(self.module.params))
                    if info['status'] >= 400:
                        self.module.fail_json(result=json.loads(info))
                    is_changed = True
                    result = self._clean_result(json.loads(response.read()))
            self.module.exit_json(result=result, changed=is_changed)

    def remove(self):
        """
removes an object from utm
        """
        is_changed = False
        info, result = self._lookup_entry(self.module, self.request_url)
        if result is not None:
            response, info = fetch_url(self.module, self.request_url + result['_ref'], method="DELETE",
                                       headers={"Accept": "application/json", "X-Restd-Err-Ack": "all"},
                                       data=self.module.jsonify(self.module.params))
            if info["status"] >= 400:
                self.module.fail_json(result=json.loads(info))
            else:
                is_changed = True
        self.module.exit_json(changed=is_changed)

    def _lookup_entry(self, module, request_url):
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

    def _clean_result(self, result):
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

    def _is_object_changed(self, keys, module, result):
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
